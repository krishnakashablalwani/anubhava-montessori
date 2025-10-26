#!/usr/bin/env python3
"""
Script to replace Google Drive video links with local video file links
"""
import os
import re
from pathlib import Path

def extract_and_replace_drive_links(html_content, html_file_path):
    """Extract Google Drive links and replace with local video links"""
    # Patterns for Google Drive links in various formats
    patterns = [
        (r'https://drive\.google\.com/file/d/([a-zA-Z0-9_-]+)[^"\']*', 'full_url'),
        (r'https://drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)[^"\']*', 'open_url'),
        (r'https://docs\.google\.com/file/d/([a-zA-Z0-9_-]+)[^"\']*', 'docs_url'),
        (r'drive\.google\.com/uc\?export=download&amp;id=([a-zA-Z0-9_-]+)', 'uc_amp'),
        (r'drive\.google\.com/uc\?id=([a-zA-Z0-9_-]+)', 'uc_url'),
    ]
    
    # Find all unique file IDs in order
    file_ids = []
    for pattern, _ in patterns:
        matches = re.finditer(pattern, html_content)
        for match in matches:
            file_id = match.group(1)
            if file_id not in file_ids:
                file_ids.append(file_id)
    
    if not file_ids:
        return html_content, 0
    
    # Replace each occurrence with local video path
    modified_content = html_content
    replacements = 0
    
    for i, file_id in enumerate(file_ids, 1):
        # Create the local video path relative to the HTML file
        local_video_path = f'videos/video_{i}.mp4'
        
        # Replace all patterns for this file_id
        for pattern, _ in patterns:
            # Find the full URL pattern including quotes
            full_pattern = f'(["\'])({pattern.replace("([a-zA-Z0-9_-]+)", file_id)})(["\'])'
            
            def replace_func(match):
                quote = match.group(1)
                return f'{quote}{local_video_path}{quote}'
            
            new_content = re.sub(full_pattern, replace_func, modified_content)
            if new_content != modified_content:
                replacements += 1
                modified_content = new_content
    
    return modified_content, replacements

def process_html_file(filepath):
    """Process a single HTML file and update video links"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if file has Google Drive links
        if 'drive.google.com' not in content:
            return 0
        
        # Replace links
        modified_content, replacements = extract_and_replace_drive_links(content, filepath)
        
        if replacements > 0:
            # Write back the modified content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            rel_path = filepath.relative_to(filepath.parents[3])
            print(f"✓ {rel_path}")
            print(f"  Replaced {replacements} video link(s)")
            return replacements
        
        return 0
        
    except Exception as e:
        print(f"✗ Error processing {filepath.name}: {e}")
        return 0

def main():
    # Find the base directory
    base_dir = Path(__file__).parent / 'sites.google.com'
    
    if not base_dir.exists():
        print(f"Error: Directory not found: {base_dir}")
        return
    
    print("🔄 Updating Google Drive video links to local files...")
    print("="*70)
    
    # Find all HTML files
    html_files = list(base_dir.rglob('*.html'))
    
    total_replacements = 0
    files_modified = 0
    
    for html_file in html_files:
        replacements = process_html_file(html_file)
        if replacements > 0:
            files_modified += 1
            total_replacements += replacements
    
    print(f"\n{'='*70}")
    print(f"📊 Summary:")
    print(f"  Files scanned: {len(html_files)}")
    print(f"  Files modified: {files_modified}")
    print(f"  Total links replaced: {total_replacements}")
    print(f"{'='*70}")
    
    if files_modified > 0:
        print("\n✅ Video links have been updated to local files!")
        print("   You can now open the HTML files and play videos locally.")

if __name__ == '__main__':
    main()
