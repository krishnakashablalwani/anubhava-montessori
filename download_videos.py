#!/usr/bin/env python3
"""
Script to find Google Drive video links in HTML files and download them
"""
import os
import re
from pathlib import Path
import urllib.request
import urllib.parse

def extract_google_drive_links(html_content):
    """Extract Google Drive links from HTML content"""
    # Pattern for Google Drive links
    patterns = [
        r'https://drive\.google\.com/file/d/([a-zA-Z0-9_-]+)',
        r'https://drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)',
        r'https://docs\.google\.com/file/d/([a-zA-Z0-9_-]+)',
    ]
    
    links = []
    for pattern in patterns:
        matches = re.findall(pattern, html_content)
        for file_id in matches:
            links.append(f'https://drive.google.com/uc?export=download&id={file_id}')
    
    return links

def download_file(url, destination_folder, file_number):
    """Download a file from Google Drive"""
    try:
        # Create destination folder if it doesn't exist
        os.makedirs(destination_folder, exist_ok=True)
        
        # Generate filename
        filename = f'video_{file_number}.mp4'
        filepath = os.path.join(destination_folder, filename)
        
        # Check if file already exists
        if os.path.exists(filepath):
            print(f"    File already exists: {filename}")
            return True
        
        print(f"    Downloading: {filename}...")
        
        # Download the file
        # Note: This basic approach may not work for all Google Drive files
        # For protected files, you may need authentication
        urllib.request.urlretrieve(url, filepath)
        
        print(f"    ✓ Downloaded: {filename}")
        return True
        
    except Exception as e:
        print(f"    ✗ Error downloading: {e}")
        return False

def process_html_file(filepath):
    """Process a single HTML file and download its videos"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract Google Drive links
        links = extract_google_drive_links(content)
        
        if not links:
            return 0
        
        print(f"\n{filepath.name}")
        print(f"  Found {len(links)} Google Drive link(s)")
        
        # Get the folder where the HTML file is located
        destination_folder = filepath.parent / 'videos'
        
        downloaded = 0
        for i, link in enumerate(links, 1):
            if download_file(link, destination_folder, i):
                downloaded += 1
        
        return downloaded
        
    except Exception as e:
        print(f"  ✗ Error processing {filepath.name}: {e}")
        return 0

def create_download_list(base_dir):
    """Create a list of all Google Drive links found"""
    html_files = list(base_dir.rglob('*.html'))
    
    all_links = {}
    
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            links = extract_google_drive_links(content)
            if links:
                all_links[str(html_file.relative_to(base_dir))] = links
        except:
            pass
    
    return all_links

def main():
    # Find the base directory
    base_dir = Path(__file__).parent / 'sites.google.com'
    
    if not base_dir.exists():
        print(f"Error: Directory not found: {base_dir}")
        return
    
    print("Scanning for Google Drive links...")
    
    # First, create a list of all links
    all_links = create_download_list(base_dir)
    
    if not all_links:
        print("\nNo Google Drive links found in any HTML files.")
        return
    
    print(f"\nFound Google Drive links in {len(all_links)} file(s)")
    print("\n" + "="*60)
    print("Links found:")
    print("="*60)
    
    for file_path, links in all_links.items():
        print(f"\n{file_path}")
        for i, link in enumerate(links, 1):
            # Extract file ID for display
            file_id = re.search(r'id=([a-zA-Z0-9_-]+)', link)
            if file_id:
                print(f"  {i}. File ID: {file_id.group(1)}")
    
    print("\n" + "="*60)
    print("\nNote: Google Drive downloads may require authentication.")
    print("For private files, you may need to:")
    print("1. Use gdown library: pip install gdown")
    print("2. Or manually download files from Google Drive")
    print("="*60)
    
    # Ask user if they want to proceed
    print("\nWould you like to attempt downloading? (y/n): ", end='')
    response = input().strip().lower()
    
    if response != 'y':
        print("Download cancelled.")
        return
    
    print("\nStarting downloads...")
    print("="*60)
    
    # Find all HTML files and process them
    html_files = list(base_dir.rglob('*.html'))
    
    total_downloaded = 0
    files_with_videos = 0
    
    for html_file in html_files:
        downloaded = process_html_file(html_file)
        if downloaded > 0:
            files_with_videos += 1
            total_downloaded += downloaded
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Files scanned: {len(html_files)}")
    print(f"  Files with videos: {files_with_videos}")
    print(f"  Total videos downloaded: {total_downloaded}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
