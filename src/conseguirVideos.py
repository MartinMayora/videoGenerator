import requests
import os
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
import yt_dlp

load_dotenv()
client_id = os.getenv("twitch_client_id")
client_secret = os.getenv("twitch_client_secret")

def get_access_token(client_id, client_secret):
    response = requests.post(
        'https://id.twitch.tv/oauth2/token',
        params={
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials'
        }
    )
    return response.json().get('access_token')

def get_category_id(category_name, client_id, access_token):
    response = requests.get(
        "https://api.twitch.tv/helix/games",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Client-Id": client_id
        },
        params={"name": category_name}
    )
    data = response.json()
    return data.get('data', [{}])[0].get('id')

def get_top_clips(category_id, client_id, access_token, amount, month_year):
    headers = {
        "Authorization": f"Bearer {access_token}", 
        "Client-Id": client_id
    }

    try:
        month, year = map(int, month_year.split('/'))
        start = datetime(year, month, 1)
        end = start + relativedelta(months=1)
    except ValueError:
        start = datetime.now() - timedelta(days=7)
        end = datetime.now()

    clips = []
    cursor = None
    
    while len(clips) < int(amount):
        params = {
            "game_id": category_id,
            "first": min(100, int(amount) - len(clips)),
            "started_at": start.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "ended_at": end.strftime('%Y-%m-%dT%H:%M:%SZ'),
            **({"after": cursor} if cursor else {})
        }
        
        response = requests.get("https://api.twitch.tv/helix/clips", headers=headers, params=params)
        data = response.json()
        clips.extend(data.get('data', []))
        cursor = data.get('pagination', {}).get('cursor')
        if not cursor:
            break
    
    return clips
def get_creator_id(username, client_id, access_token):
    """Get the Twitch user ID from a username"""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Client-Id": client_id
    }
    
    params = {"login": username}
    
    try:
        response = requests.get(
            "https://api.twitch.tv/helix/users",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        
        data = response.json()
        if data.get('data'):
            return data['data'][0]['id']
            
    except Exception as e:
        print(f"Error getting creator ID: {str(e)}")
    
    return None

def get_top_clips_creator(creator_id, client_id, access_token, amount, period="all"):
    """Get top clips for a specific creator"""
    headers = {
        "Authorization": f"Bearer {access_token}", 
        "Client-Id": client_id
    }

    clips = []
    cursor = None
    
    while len(clips) < int(amount):
        params = {
            "broadcaster_id": creator_id,
            "first": min(100, int(amount) - len(clips)),
            **({"after": cursor} if cursor else {})
        }
        
        # Add period filter if specified
        if period in ["day", "week", "month", "all"]:
            params["period"] = period
        
        try:
            response = requests.get(
                "https://api.twitch.tv/helix/clips",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            clips.extend(data.get('data', []))
            cursor = data.get('pagination', {}).get('cursor')
            
            if not cursor:
                break
                
        except Exception as e:
            print(f"Error getting creator clips: {str(e)}")
            break
    
    return clips


def download_video(clip_info, video_number):
    url = clip_info['url']
    
    download_dir = os.path.expanduser("./build/videos") 
    os.makedirs(download_dir, exist_ok=True)  
   
    output_template = os.path.join(download_dir, f"{video_number}.mp4")

    ydl_opts = {
        'format': 'best',
        'outtmpl': output_template,  
        'restrictfilenames': True,   
        'quiet': True,               
    }
    
    # 4. Download
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"Downloaded: {output_template}")
    except Exception as e:
        print(f"Error downloading {url}: {e}")

def download_thumbnail(thumbnail_url, video_number):
    if not thumbnail_url:
        return False
        
    output_dir = './build/videos'
    os.makedirs(output_dir, exist_ok=True)
    thumbnail_path = os.path.join(output_dir, f"{video_number}.jpg")
    
    try:
        with requests.get(thumbnail_url, timeout=10) as response:
            response.raise_for_status()
            with open(thumbnail_path, 'wb') as f:
                f.write(response.content)
        print(f"Downloaded thumbnail {video_number}.jpg")
        return True
    except Exception as e:
        print(f"Failed to download thumbnail: {str(e)}")
        return False

def download_clip(clip_info, video_number):
    # Download thumbnail through API
    thumbnail_success = download_thumbnail(clip_info.get('thumbnail_url'), video_number)
    
    # Download video through scraping the clip URL
    video_success = download_video(clip_info, video_number)
    
    return thumbnail_success and video_success

def conseguirVids(choice, language):
    token = get_access_token(client_id, client_secret)
    if not token:
        print("Failed to get access token")
        return []

    if choice == '1':
        category = input("Enter Category Name: ")
        amount = input("Enter amount of videos: ")
        date = input("Enter month/year (MM/YYYY): ")

        cat_id = get_category_id(category, client_id, token)
        if not cat_id:
            print(f"Category '{category}' not found")
            return []

        all_clips = get_top_clips(cat_id, client_id, token, amount, date)
        print(f"Found {len(all_clips)} clips")
        
        downloaded_clips = []
        for i, clip in enumerate(all_clips[:int(amount)], 1):
            if download_clip(clip, i):
                downloaded_clips.append(clip)
            time.sleep(1)  # Rate limiting
            
        return [{
            'name': clip['broadcaster_name'],
            'video': f"{idx}.mp4",
            'thumbnail': f"{idx}.jpg",
            'x': '',
            'y': ''
        } for idx, clip in enumerate(all_clips, 1)]
        
    elif choice == '2':
        creator_name = input("Enter Creator Username: ")
        amount = input("Enter amount of videos: ")

        creator_id = get_creator_id(creator_name, client_id, token)
        if not creator_id:
            print(f"Category '{category}' not found")
            return []

        all_clips = get_top_clips_creator(creator_id, client_id, token, amount)
        print(f"Found {len(all_clips)} clips")
        
        downloaded_clips = []
        for i, clip in enumerate(all_clips[:int(amount)], 1):
            if download_clip(clip, i):
                downloaded_clips.append(clip)
            time.sleep(1)  # Rate limiting
            
        return [{
            'name': clip['broadcaster_name'],
            'video': f"{idx}.mp4",
            'thumbnail': f"{idx}.jpg",
            'x': '',
            'y': ''
        } for idx, clip in enumerate(all_clips, 1)]
    return []