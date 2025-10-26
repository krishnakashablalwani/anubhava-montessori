#!/usr/bin/env python3
"""
Script to find Google Drive video links in HTML files and download them using gdown
Requires: pip install gdown
"""
import os
import re
import sys
from pathlib import Path

try:
    import gdown
except ImportError:
    print("Error: gdown library not found.")
    print("Please install it using: pip install gdown")
    sys.exit(1)

def extract_google_drive_file_ids(html_content):
    """Extract Google Drive file IDs from HTML content"""
    # Pattern for Google Drive links
    patterns = [
        r'https://drive\.google\.com/file/d/([a-zA-Z0-9_-]+)',
        r'https://drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)',
        r'https://docs\.google\.com/file/d/([a-zA-Z0-9_-]+)',
        r'drive\.google\.com/uc\?export=download&amp;id=([a-zA-Z0-9_-]+)',
        r'drive\.google\.com/uc\?id=([a-zA-Z0-9_-]+)',
    ]
    
    file_ids = set()
    for pattern in patterns:
        matches = re.findall(pattern, html_content)
        file_ids.update(matches)
    
    return list(file_ids)

def download_video(file_id, destination_folder, file_number):
    """Download a video from Google Drive using gdown"""
    try:
        # Create destination folder if it doesn't exist
        os.makedirs(destination_folder, exist_ok=True)
        
        # Generate URL
        url = f'https://drive.google.com/uc?id={file_id}'
        
        # Generate output path
        output_path = os.path.join(destination_folder, f'video_{file_number}.mp4')
        
        # Check if file already exists
        if os.path.exists(output_path):
            print(f"    ⊖ Already exists: video_{file_number}.mp4")
            return True
        
        print(f"    ⬇ Downloading video_{file_number}.mp4 (ID: {file_id[:10]}...)...")
        
        # Download the file
        gdown.download(url, output_path, quiet=False, fuzzy=True)
        
        # Check if download was successful
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"    ✓ Downloaded: video_{file_number}.mp4 ({size_mb:.2f} MB)")
            return True
        else:
            print(f"    ✗ Download failed or file is empty")
            if os.path.exists(output_path):
                os.remove(output_path)
            return False
        
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return False

def process_html_file(filepath):
    """Process a single HTML file and download its videos"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract Google Drive file IDs
        file_ids = extract_google_drive_file_ids(content)
        
        if not file_ids:
            return 0
        
        rel_path = filepath.relative_to(filepath.parents[3])
        print(f"\n📄 {rel_path}")
        print(f"  Found {len(file_ids)} Google Drive video(s)")
        
        # Get the folder where the HTML file is located
        destination_folder = filepath.parent / 'videos'
        
        downloaded = 0
        for i, file_id in enumerate(file_ids, 1):
            if download_video(file_id, destination_folder, i):
                downloaded += 1
        
        return downloaded
        
    except Exception as e:
        print(f"  ✗ Error processing {filepath.name}: {e}")
        return 0

def scan_for_links(base_dir):
    """Scan all HTML files and list Google Drive links"""
    html_files = list(base_dir.rglob('*.html'))
    
    all_links = {}
    
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_ids = extract_google_drive_file_ids(content)
            if file_ids:
                rel_path = str(html_file.relative_to(base_dir))
                all_links[rel_path] = file_ids
        except:
            pass
    
    return all_links

def main():
    # Find the base directory
    base_dir = Path(__file__).parent / 'sites.google.com'
    
    if not base_dir.exists():
        print(f"❌ Error: Directory not found: {base_dir}")
        return
    
    print("🔍 Scanning for Google Drive video links...")
    print("="*70)
    
    # First, scan for all links
    all_links = scan_for_links(base_dir)
    
    if not all_links:
        print("\n❌ No Google Drive links found in any HTML files.")
        return
    
    total_videos = sum(len(ids) for ids in all_links.values())
    
    print(f"\n✓ Found {total_videos} Google Drive video(s) in {len(all_links)} file(s)")
    print("\n" + "="*70)
    print("Files with videos:")
    print("="*70)
    
    for file_path, file_ids in sorted(all_links.items()):
        print(f"\n📄 {file_path}")
        for i, file_id in enumerate(file_ids, 1):
            print(f"   {i}. https://drive.google.com/file/d/{file_id}")
    
    print("\n" + "="*70)
    print("\n⚠️  Note:")
    print("  - Videos will be downloaded to a 'videos' folder in each directory")
    print("  - Some videos may require authentication if they're private")
    print("  - Download may take time depending on file sizes")
    print("="*70)
    
    # Ask user if they want to proceed
    response = input("\n▶️  Start downloading videos? (y/n): ").strip().lower()
    
    if response != 'y':
        print("\n❌ Download cancelled.")
        return
    
    print("\n🚀 Starting downloads...")
    print("="*70)
    
    # Process all HTML files
    html_files = list(base_dir.rglob('*.html'))
    
    total_downloaded = 0
    files_with_videos = 0
    
    for html_file in html_files:
        downloaded = process_html_file(html_file)
        if downloaded > 0:
            files_with_videos += 1
            total_downloaded += downloaded
    
    print(f"\n{'='*70}")
    print(f"📊 Summary:")
    print(f"  Files scanned: {len(html_files)}")
    print(f"  Files with videos: {files_with_videos}")
    print(f"  Videos downloaded: {total_downloaded}/{total_videos}")
    print(f"{'='*70}")
    
    if total_downloaded < total_videos:
        print("\n⚠️  Some videos failed to download. They may be private or deleted.")

if __name__ == '__main__':
    main()
