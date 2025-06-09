import tkinter as tk
from tkinter import messagebox
from datetime import datetime, date
import os
import pytz
import time
import instaloader


L = instaloader.Instaloader()

# login with session
def login():
    username = username_entry.get()
    password = password_entry.get()
    
    session_file = f"{username}.session"
    
    try:
        # session check
        if os.path.exists(session_file):
            L.load_session_from_file(username)
            messagebox.showinfo("Session", "Session loaded successfully.")
            print("Session loaded successfully.")
        else:
          
            L.login(username, password)
            L.save_session_to_file(username)
            messagebox.showinfo("Login", "Login successful and session saved.")
            print("Logged in and session saved.")
    except Exception as e:
        messagebox.showerror("Login Error", f"Failed to login: {str(e)}")
        print(f"Failed to login: {str(e)}")

# date check
def make_aware(date_naive, timezone_str='Asia/Tehran'):
    tz = pytz.timezone(timezone_str)
    return tz.localize(date_naive)

# download stories
def download_stories(user_target):
    try:
        profile = instaloader.Profile.from_username(L.context, user_target)
        for story in L.get_stories(userids=[profile.userid]):
            
            for item in story.get_items():
                tehran_tz = pytz.timezone('Asia/Tehran')
                tehran_date = item.date_utc.astimezone(tehran_tz).strftime('%Y-%m-%d')
                folder_name = f"story_{profile.username}_{tehran_date}"
                os.makedirs(folder_name, exist_ok=True)
                file_name = f"{tehran_date}_{item.mediaid}"
                file_path = os.path.join(folder_name, file_name)
                L.download_storyitem(item, target=folder_name)
                
    except Exception as e:
        print(f"Error downloading stories: {e}")


#download posts
def download_posts(user_target, specific_date_str=None, start_date_str=None, end_date_str=None):
    try:
        profile = instaloader.Profile.from_username(L.context, user_target)
        tehran_tz = pytz.timezone('Asia/Tehran')
        
        if specific_date_str:
            specific_date_naive = datetime.strptime(specific_date_str, '%Y-%m-%d')
            start_date = make_aware(datetime.combine(specific_date_naive, datetime.min.time()))
            end_date = make_aware(datetime.combine(specific_date_naive, datetime.max.time()))
        elif start_date_str and end_date_str:
            start_date_naive = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date_naive = datetime.strptime(end_date_str, '%Y-%m-%d')
            start_date = make_aware(datetime.combine(start_date_naive, datetime.min.time()))
            end_date = make_aware(datetime.combine(end_date_naive, datetime.max.time()))
        else:
            today = date.today()
            start_date = make_aware(datetime.combine(today, datetime.min.time()))
            end_date = make_aware(datetime.combine(today, datetime.max.time()))

        for post in profile.get_posts():
            post_date_aware = post.date_utc.astimezone(tehran_tz)

            if (specific_date_str and specific_date_str == post_date_aware.strftime('%Y-%m-%d')) or \
               (start_date <= post_date_aware <= end_date):

                folder_name = f"post_{profile.username}_{post_date_aware.strftime('%Y-%m-%d')}"
                os.makedirs(folder_name, exist_ok=True)
                
                if post.typename == "GraphSidecar":
                    slide_number = 1
                    for slide in post.get_sidecar_nodes():
                        file_name = f"{post_date_aware.strftime('%Y-%m-%d')}_{slide_number}_{post.mediaid}"
                        file_path = os.path.join(folder_name, file_name)
                        L.download_pic(file_path, slide.display_url, post.date_utc)
                        slide_number += 1
                else:
                    file_name = f"{post_date_aware.strftime('%Y-%m-%d')}_{post.mediaid}"
                    file_path = os.path.join(folder_name, file_name)
                    L.download_post(post, target=folder_name)
    except Exception as e:
        print(f"Error downloading posts: {e}")



def validate_date(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        messagebox.showerror("Invalid Date", f"Invalid date format: {date_str}. Please use YYYY-MM-DD.")
        return None

# start
def start_download():
    user_targets = user_targets_entry.get().split(',')
    user_targets = [user.strip() for user in user_targets]
    operation = operation_entry.get().strip().lower()
    specific_date = None
    start_date = end_date = None
    
    if 'posts' in operation or 'both' in operation:
        date_choice = date_choice_entry.get().strip().lower()
        if date_choice == 'specific':
            specific_date_input = specific_date_entry.get().strip()
            if specific_date_input:
                specific_date = validate_date(specific_date_input)
        elif date_choice == 'range':
            start_date_input = start_date_entry.get().strip()
            end_date_input = end_date_entry.get().strip()
            if start_date_input:
                start_date = validate_date(start_date_input)
            if end_date_input:
                end_date = validate_date(end_date_input)

    while True:
        for user_target in user_targets:
            if operation in ['stories', 'both']:
                download_stories(user_target)
            if operation in ['posts', 'both']:
                download_posts(user_target, specific_date.strftime('%Y-%m-%d') if specific_date else None,
                               start_date.strftime('%Y-%m-%d') if start_date else None,
                               end_date.strftime('%Y-%m-%d') if end_date else None)
        time.sleep(600)


# UI 
root = tk.Tk()
root.title("Instagram Downloader")

tk.Label(root, text="Username:").grid(row=0, column=0)
username_entry = tk.Entry(root)
username_entry.grid(row=0, column=1)

tk.Label(root, text="Password:").grid(row=1, column=0)
password_entry = tk.Entry(root, show="*")
password_entry.grid(row=1, column=1)

login_button = tk.Button(root, text="Login", command=login)
login_button.grid(row=2, column=0, columnspan=2)


tk.Label(root, text="Target Usernames (comma-separated):").grid(row=3, column=0)
user_targets_entry = tk.Entry(root, width=40)
user_targets_entry.grid(row=3, column=1)

tk.Label(root, text="Operation (stories, posts, both):").grid(row=4, column=0)
operation_entry = tk.Entry(root)
operation_entry.grid(row=4, column=1)

tk.Label(root, text="Date Choice (specific, range):").grid(row=5, column=0)
date_choice_entry = tk.Entry(root)
date_choice_entry.grid(row=5, column=1)

tk.Label(root, text="Specific Date (YYYY-MM-DD):").grid(row=6, column=0)
specific_date_entry = tk.Entry(root)
specific_date_entry.grid(row=6, column=1)

tk.Label(root, text="Start Date (YYYY-MM-DD):").grid(row=7, column=0)
start_date_entry = tk.Entry(root)
start_date_entry.grid(row=7, column=1)

tk.Label(root, text="End Date (YYYY-MM-DD):").grid(row=8, column=0)
end_date_entry = tk.Entry(root)
end_date_entry.grid(row=8, column=1)

start_button = tk.Button(root, text="Start Download", command=start_download)
start_button.grid(row=9, column=0, columnspan=2)

root.mainloop()




































