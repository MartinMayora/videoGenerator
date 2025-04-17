import requests
import os
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time  # For rate limiting

load_dotenv()
client_id = os.getenv("client_id")
client_secret = os.getenv("client_secret")

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
def get_video_url(clip_id):
    """Scrape the video URL from Twitch clip page"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    # Try multiple endpoints to find the video URL
    endpoints = [
        f"https://clips.twitch.tv/{clip_id}",
        f"https://clips.twitch.tv/embed?clip={clip_id}",
        f"https://www.twitch.tv/clips/{clip_id}" #ACA <==
    ]
    
    for url in endpoints:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Method 1: Check for video tag
            soup = BeautifulSoup(response.text, 'html.parser')
            video_tag = soup.find('video')
            if video_tag and video_tag.get('src'):
                return video_tag['src']
            
            # Method 2: Search for MP4 in JSON data
            match = re.search(r'"quality_options":\[(.*?)\]', response.text)
            if match:
                sources = re.findall(r'"source":"(https://[^"]+\.mp4)"', match.group(1))
                if sources:
                    return sources[0]  # Return highest quality
                    
        except Exception as e:
            continue
    
    return None

def download_video(clip_id, video_number):
    """Download video by scraping the URL"""
    video_url = get_video_url(clip_id)
    if not video_url:
        print(f"Could not find video URL for clip {clip_id}")
        return False
    
    output_dir = './Videos'
    os.makedirs(output_dir, exist_ok=True)
    video_path = os.path.join(output_dir, f"{video_number}.mp4")
    
    try:
        with requests.get(video_url, stream=True, timeout=20) as response:
            response.raise_for_status()
            with open(video_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"Downloaded video {video_number}.mp4")
        return True
    except Exception as e:
        print(f"Failed to download video: {str(e)}")
        return False

def download_thumbnail(thumbnail_url, video_number):
    """Download thumbnail through API"""
    if not thumbnail_url:
        return False
        
    output_dir = './Videos'
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
    
    # Download video through scraping
    video_success = download_video(clip_info['id'], video_number)
    
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
            time.sleep(1)  # Respectful rate limiting
            
        return [{
            'name': clip['broadcaster_name'],
            'video': f"{idx}.mp4",
            'thumbnail': f"{idx}.jpg",
            'x': '',
            'y': ''
        } for idx, clip in enumerate(downloaded_clips, 1)]
    
    return []