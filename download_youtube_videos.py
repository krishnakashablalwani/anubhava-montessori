#!/usr/bin/env python3
"""
Script to download YouTube videos and update links in HTML files
"""
import os
import re
import sys
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    print("Error: yt-dlp library not found.")
    print("Please install it using: pip install yt-dlp")
    sys.exit(1)

def extract_youtube_links(html_content):
    """Extract YouTube video IDs and URLs from HTML content"""
    youtube_data = []
    
    # Patterns for YouTube links
    patterns = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
        r'https?://(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]+)',
        r'https?://youtu\.be/([a-zA-Z0-9_-]+)',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, html_content, re.IGNORECASE)
        for match in matches:
            video_id = match.group(1)
            full_url = match.group(0)
            youtube_data.append({
                'id': video_id,
                'url': full_url,
                'watch_url': f'https://www.youtube.com/watch?v={video_id}'
            })
    
    # Remove duplicates based on video ID
    unique_videos = {}
    for video in youtube_data:
        if video['id'] not in unique_videos:
            unique_videos[video['id']] = video
    
    return list(unique_videos.values())

def download_youtube_video(video_id, destination_folder, video_number):
    """Download a YouTube video using yt-dlp"""
    try:
        os.makedirs(destination_folder, exist_ok=True)
        
        output_path = os.path.join(destination_folder, f'youtube_{video_number}.mp4')
        
        # Check if file already exists
        if os.path.exists(output_path):
            print(f"    ⊖ Already exists: youtube_{video_number}.mp4")
            return True
        
        print(f"    ⬇ Downloading youtube_{video_number}.mp4 (ID: {video_id})...")
        
        # yt-dlp options
        ydl_opts = {
            'format': 'best[ext=mp4]/best',  # Prefer mp4
            'outtmpl': output_path,
            'quiet': True,
            'no_warnings': True,
        }
        
        url = f'https://www.youtube.com/watch?v={video_id}'
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"    ✓ Downloaded: youtube_{video_number}.mp4 ({size_mb:.2f} MB)")
            return True
        else:
            print(f"    ✗ Download failed or file is empty")
            if os.path.exists(output_path):
                os.remove(output_path)
            return False
            
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return False

def replace_youtube_links(html_content, video_id_mapping):
    """Replace YouTube links with local video paths"""
    modified_content = html_content
    replacements = 0
    
    for video_id, local_path in video_id_mapping.items():
        # Pattern to match YouTube URLs with this video ID
        patterns = [
            rf'https?://(?:www\.)?youtube\.com/watch\?v={video_id}[^"\'<>\s]*',
            rf'https?://(?:www\.)?youtube\.com/embed/{video_id}[^"\'<>\s]*',
            rf'https?://youtu\.be/{video_id}[^"\'<>\s]*',
        ]
        
        for pattern in patterns:
            new_content = re.sub(pattern, local_path, modified_content, flags=re.IGNORECASE)
            if new_content != modified_content:
                replacements += 1
                modified_content = new_content
    
    return modified_content, replacements

def process_html_file(filepath):
    """Process a single HTML file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract YouTube videos
        youtube_videos = extract_youtube_links(content)
        
        if not youtube_videos:
            return 0
        
        rel_path = filepath.relative_to(filepath.parents[3])
        print(f"\n📄 {rel_path}")
        print(f"  Found {len(youtube_videos)} YouTube video(s)")
        
        # Get the folder where the HTML file is located
        destination_folder = filepath.parent / 'videos'
        
        # Download videos and create mapping
        video_id_mapping = {}
        downloaded = 0
        
        for i, video in enumerate(youtube_videos, 1):
            video_id = video['id']
            local_path = f'videos/youtube_{i}.mp4'
            
            if download_youtube_video(video_id, destination_folder, i):
                video_id_mapping[video_id] = local_path
                downloaded += 1
        
        # Replace links in HTML
        if video_id_mapping:
            modified_content, replacements = replace_youtube_links(content, video_id_mapping)
            
            if replacements > 0:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                print(f"  ✓ Replaced {replacements} YouTube link(s)")
        
        return downloaded
        
    except Exception as e:
        print(f"  ✗ Error processing {filepath.name}: {e}")
        return 0

def main():
    base_dir = Path(__file__).parent / 'sites.google.com'
    
    if not base_dir.exists():
        print(f"❌ Error: Directory not found: {base_dir}")
        return
    
    print("🔍 Scanning for YouTube videos...")
    print("="*70)
    
    # First, scan for all YouTube videos
    html_files = list(base_dir.rglob('*.html'))
    files_with_youtube = []
    
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            videos = extract_youtube_links(content)
            if videos:
                files_with_youtube.append((html_file, videos))
        except:
            pass
    
    if not files_with_youtube:
        print("\n✅ No YouTube videos found!")
        return
    
    total_videos = sum(len(videos) for _, videos in files_with_youtube)
    
    print(f"\n✓ Found {total_videos} YouTube video(s) in {len(files_with_youtube)} file(s)")
    print("\n" + "="*70)
    print("Videos to download:")
    print("="*70)
    
    for html_file, videos in files_with_youtube:
        rel_path = html_file.relative_to(base_dir)
        print(f"\n📄 {rel_path}")
        for i, video in enumerate(videos, 1):
            print(f"   {i}. https://www.youtube.com/watch?v={video['id']}")
    
    print("\n" + "="*70)
    response = input("\n▶️  Start downloading YouTube videos? (y/n): ").strip().lower()
    
    if response != 'y':
        print("\n❌ Download cancelled.")
        return
    
    print("\n🚀 Starting downloads...")
    print("="*70)
    
    total_downloaded = 0
    files_modified = 0
    
    for html_file, _ in files_with_youtube:
        downloaded = process_html_file(html_file)
        if downloaded > 0:
            files_modified += 1
            total_downloaded += downloaded
    
    print(f"\n{'='*70}")
    print(f"📊 Summary:")
    print(f"  Files processed: {len(files_with_youtube)}")
    print(f"  Videos downloaded: {total_downloaded}/{total_videos}")
    print(f"  Files modified: {files_modified}")
    print(f"{'='*70}")
    
    if total_downloaded > 0:
        print("\n✅ YouTube videos downloaded and links updated!")

if __name__ == '__main__':
    main()
