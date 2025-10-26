#!/usr/bin/env python3
"""
Script to find and list video links from various platforms in HTML files
"""
import re
from pathlib import Path
from collections import defaultdict

def extract_video_links(html_content):
    """Extract video links from various platforms"""
    video_links = defaultdict(list)
    
    # YouTube patterns
    youtube_patterns = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
        r'https?://(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]+)',
        r'https?://youtu\.be/([a-zA-Z0-9_-]+)',
        r'youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
    ]
    
    for pattern in youtube_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        for video_id in matches:
            full_url = f'https://www.youtube.com/watch?v={video_id}'
            if full_url not in video_links['YouTube']:
                video_links['YouTube'].append(full_url)
    
    # Vimeo patterns
    vimeo_patterns = [
        r'https?://(?:www\.)?vimeo\.com/(\d+)',
        r'https?://player\.vimeo\.com/video/(\d+)',
    ]
    
    for pattern in vimeo_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        for video_id in matches:
            full_url = f'https://vimeo.com/{video_id}'
            if full_url not in video_links['Vimeo']:
                video_links['Vimeo'].append(full_url)
    
    # Dailymotion patterns
    dailymotion_patterns = [
        r'https?://(?:www\.)?dailymotion\.com/video/([a-zA-Z0-9]+)',
        r'https?://(?:www\.)?dai\.ly/([a-zA-Z0-9]+)',
    ]
    
    for pattern in dailymotion_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        for video_id in matches:
            full_url = f'https://www.dailymotion.com/video/{video_id}'
            if full_url not in video_links['Dailymotion']:
                video_links['Dailymotion'].append(full_url)
    
    # Generic video file patterns
    video_file_patterns = [
        r'https?://[^\s"\'<>]+\.mp4',
        r'https?://[^\s"\'<>]+\.webm',
        r'https?://[^\s"\'<>]+\.mov',
        r'https?://[^\s"\'<>]+\.avi',
        r'https?://[^\s"\'<>]+\.m4v',
    ]
    
    for pattern in video_file_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        for url in matches:
            # Skip if it's a local file
            if not url.startswith(('http://', 'https://')):
                continue
            if url not in video_links['Direct Video']:
                video_links['Direct Video'].append(url)
    
    # iframe video embeds
    iframe_pattern = r'<iframe[^>]+src=["\']([^"\']+)["\'][^>]*>'
    iframes = re.findall(iframe_pattern, html_content, re.IGNORECASE)
    for iframe_src in iframes:
        # Check if it's a video embed
        if any(platform in iframe_src.lower() for platform in ['youtube', 'vimeo', 'dailymotion', 'video']):
            if iframe_src not in video_links['Iframe Embeds']:
                video_links['Iframe Embeds'].append(iframe_src)
    
    # video tags
    video_tag_pattern = r'<video[^>]+src=["\']([^"\']+)["\'][^>]*>'
    video_tags = re.findall(video_tag_pattern, html_content, re.IGNORECASE)
    for video_src in video_tags:
        if video_src.startswith(('http://', 'https://')):
            if video_src not in video_links['Video Tags']:
                video_links['Video Tags'].append(video_src)
    
    # source tags inside video elements
    source_pattern = r'<source[^>]+src=["\']([^"\']+)["\'][^>]*>'
    sources = re.findall(source_pattern, html_content, re.IGNORECASE)
    for source_src in sources:
        if source_src.startswith(('http://', 'https://')):
            if source_src not in video_links['Source Tags']:
                video_links['Source Tags'].append(source_src)
    
    return dict(video_links)

def scan_all_files(base_dir):
    """Scan all HTML files for video links"""
    html_files = list(base_dir.rglob('*.html'))
    
    all_videos = defaultdict(lambda: defaultdict(list))
    
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            video_links = extract_video_links(content)
            
            if video_links:
                rel_path = str(html_file.relative_to(base_dir))
                for platform, links in video_links.items():
                    if links:
                        all_videos[platform][rel_path].extend(links)
        except Exception as e:
            print(f"Error reading {html_file.name}: {e}")
    
    return dict(all_videos)

def main():
    # Find the base directory
    base_dir = Path(__file__).parent / 'sites.google.com'
    
    if not base_dir.exists():
        print(f"Error: Directory not found: {base_dir}")
        return
    
    print("🔍 Scanning for video links from all platforms...")
    print("="*70)
    
    all_videos = scan_all_files(base_dir)
    
    if not all_videos:
        print("\n✓ No external video links found!")
        print("  (Only local video files detected)")
        return
    
    total_videos = sum(len(links) for platform_files in all_videos.values() 
                      for links in platform_files.values())
    
    print(f"\n📊 Found {total_videos} video link(s) from {len(all_videos)} platform(s)")
    print("="*70)
    
    for platform, files in sorted(all_videos.items()):
        platform_total = sum(len(links) for links in files.values())
        print(f"\n🎥 {platform} - {platform_total} video(s)")
        print("-"*70)
        
        for file_path, links in sorted(files.items()):
            print(f"\n  📄 {file_path}")
            for i, link in enumerate(links, 1):
                # Truncate long URLs
                display_link = link if len(link) <= 80 else link[:77] + '...'
                print(f"     {i}. {display_link}")
    
    print("\n" + "="*70)
    print("\n💡 Recommendations:")
    print("   - YouTube videos: Use yt-dlp (pip install yt-dlp)")
    print("   - Vimeo videos: Use yt-dlp (pip install yt-dlp)")
    print("   - Direct video files: Use wget or curl")
    print("   - Embedded iframes: May need manual inspection")
    print("="*70)

if __name__ == '__main__':
    main()
