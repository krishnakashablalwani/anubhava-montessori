import os
import re
import yt_dlp
from urllib.parse import unquote

def extract_panopto_id(url):
    """Extract the video ID from a Panopto URL."""
    # Handle URL-encoded URLs
    url = unquote(url)
    
    # Extract ID parameter
    match = re.search(r'[?&]id=([a-f0-9\-]+)', url, re.IGNORECASE)
    if match:
        return match.group(1)
    return None

def extract_panopto_links(html_content):
    """Extract Panopto video links from HTML content."""
    panopto_data = []
    
    # First, extract all Google redirect URLs and decode them
    google_redirect_pattern = r'https?://www\.google\.com/url\?q=([^&"\'<>\s]+)'
    google_matches = re.findall(google_redirect_pattern, html_content, re.IGNORECASE)
    
    all_urls = []
    for match in google_matches:
        decoded = unquote(match)
        if 'panopto.com' in decoded.lower():
            all_urls.append(decoded)
    
    # Also find direct Panopto URLs
    direct_patterns = [
        r'https?://[^/]*panopto\.com/Panopto/Pages/(?:Viewer|Embed)\.aspx\?[^"\'<>\s]+',
    ]
    
    for pattern in direct_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        all_urls.extend(matches)
    
    # Extract video IDs from all found URLs
    for url in all_urls:
        video_id = extract_panopto_id(url)
        if video_id:
            # Construct clean URL
            clean_url = f'https://montessori-ami.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id={video_id}'
            panopto_data.append({
                'url': clean_url,
                'id': video_id
            })
    
    # Remove duplicates based on ID
    seen_ids = set()
    unique_data = []
    for item in panopto_data:
        if item['id'] not in seen_ids:
            seen_ids.add(item['id'])
            unique_data.append(item)
    
    return unique_data

def download_panopto_video(url, output_path):
    """Download a Panopto video using yt-dlp."""
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': output_path,
        'quiet': False,
        'no_warnings': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def replace_panopto_links(html_content, video_mapping, rel_dir):
    """Replace Panopto URLs with local video paths."""
    modified = html_content
    replacements = 0
    
    for video_id, local_filename in video_mapping.items():
        # Create relative path to video
        local_path = f'videos/{local_filename}'
        
        # Pattern to find Google redirect URLs containing this Panopto video ID
        google_redirect_pattern = rf'https?://www\.google\.com/url\?q=https?(?:%3A|:)(?:%2F|/)(?:%2F|/)[^&"\'<>\s]*panopto\.com(?:%2F|/)[^&"\'<>\s]*(?:%3F|\\?)id(?:%3D|=){re.escape(video_id)}[^&"\'<>\s]*(?:&amp;|&)[^"\'<>\s]*'
        
        # Also find direct Panopto URLs
        direct_pattern = rf'https?://[^/]*panopto\.com/Panopto/Pages/(?:Viewer|Embed)\.aspx\?id={re.escape(video_id)}[^"\'<>\s]*'
        
        for pattern in [google_redirect_pattern, direct_pattern]:
            matches = re.findall(pattern, modified, re.IGNORECASE)
            if matches:
                modified = re.sub(pattern, local_path, modified, flags=re.IGNORECASE)
                replacements += len(matches)
    
    return modified, replacements

def main():
    base_dir = r'c:\Users\Admin\Downloads\Montessori Training\sites.google.com'
    
    # First, collect all unique Panopto videos
    print("Step 1: Scanning for Panopto videos...\n")
    all_videos = {}  # video_id -> {url, files}
    file_videos = {}  # file_path -> [video_data]
    
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, base_dir)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    videos = extract_panopto_links(content)
                    
                    if videos:
                        file_videos[file_path] = videos
                        for video in videos:
                            video_id = video['id']
                            if video_id not in all_videos:
                                all_videos[video_id] = {
                                    'url': video['url'],
                                    'files': []
                                }
                            all_videos[video_id]['files'].append(rel_path)
                            
                except Exception as e:
                    print(f"Error reading {rel_path}: {e}")
    
    print(f"Found {len(all_videos)} unique Panopto videos in {len(file_videos)} files\n")
    
    # Download videos
    print("Step 2: Downloading Panopto videos...\n")
    video_mapping = {}  # video_id -> local_filename
    downloaded = 0
    
    for idx, (video_id, data) in enumerate(all_videos.items(), 1):
        url = data['url']
        # Get the directory of the first file that uses this video
        first_file = None
        for file_path, videos in file_videos.items():
            if any(v['id'] == video_id for v in videos):
                first_file = file_path
                break
        
        if first_file:
            file_dir = os.path.dirname(first_file)
            videos_dir = os.path.join(file_dir, 'videos')
            os.makedirs(videos_dir, exist_ok=True)
            
            filename = f'panopto_{idx}.mp4'
            output_path = os.path.join(videos_dir, filename)
            
            print(f"[{idx}/{len(all_videos)}] Downloading: {video_id}")
            print(f"  URL: {url}")
            print(f"  Output: {output_path}")
            
            if download_panopto_video(url, output_path):
                video_mapping[video_id] = filename
                downloaded += 1
                # Get file size
                if os.path.exists(output_path):
                    size_mb = os.path.getsize(output_path) / (1024 * 1024)
                    print(f"  ✓ Downloaded ({size_mb:.2f} MB)\n")
            else:
                print(f"  ✗ Failed\n")
    
    print(f"\nVideos downloaded: {downloaded}/{len(all_videos)}\n")
    
    # Update HTML files
    print("Step 3: Updating HTML files with local video paths...\n")
    files_modified = 0
    total_replacements = 0
    
    for file_path, videos in file_videos.items():
        rel_path = os.path.relpath(file_path, base_dir)
        rel_dir = os.path.dirname(rel_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            modified_content, replacements = replace_panopto_links(content, video_mapping, rel_dir)
            
            if replacements > 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                files_modified += 1
                total_replacements += replacements
                print(f"✓ {rel_path}: {replacements} links updated")
                
        except Exception as e:
            print(f"✗ Error updating {rel_path}: {e}")
    
    print(f"\n\nSummary:")
    print(f"  Videos downloaded: {downloaded}/{len(all_videos)}")
    print(f"  Files modified: {files_modified}")
    print(f"  Total links replaced: {total_replacements}")

if __name__ == "__main__":
    main()
