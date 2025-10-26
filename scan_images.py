import os
import re
from urllib.parse import urlparse

def extract_image_links(html_content):
    """Extract image links from HTML content."""
    image_data = []
    
    # Patterns for image sources
    patterns = [
        r'<img[^>]+src=["\']([^"\']+)["\']',
        r'<source[^>]+srcset=["\']([^"\']+)["\']',
        r'background-image:\s*url\(["\']?([^"\')\s]+)["\']?\)',
        r'<link[^>]+href=["\']([^"\']+\.(?:png|jpg|jpeg|gif|svg|webp|ico))["\']',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        image_data.extend(matches)
    
    # Filter for external URLs
    external_images = []
    for url in image_data:
        # Skip data URLs, local paths, and empty strings
        if url.startswith('data:') or url.startswith('#') or not url.strip():
            continue
        
        # Check if it's an external URL (http/https)
        if url.startswith('http://') or url.startswith('https://'):
            # Skip if it's already a local file reference
            if 'sites.google.com' not in url or url.startswith('http'):
                external_images.append(url)
        elif url.startswith('//'):
            # Protocol-relative URL
            external_images.append('https:' + url)
    
    return list(set(external_images))

def scan_all_files():
    """Scan all HTML files for external image links."""
    base_dir = r'c:\Users\Admin\Downloads\Montessori Training\sites.google.com'
    
    all_images = {}  # url -> [files that use it]
    file_images = {}  # file -> [images]
    
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, base_dir)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    images = extract_image_links(content)
                    
                    if images:
                        file_images[rel_path] = images
                        for img_url in images:
                            if img_url not in all_images:
                                all_images[img_url] = []
                            all_images[img_url].append(rel_path)
                            
                except Exception as e:
                    print(f"Error reading {rel_path}: {e}")
    
    return all_images, file_images

if __name__ == "__main__":
    print("Scanning for external images...\n")
    
    all_images, file_images = scan_all_files()
    
    if all_images:
        print(f"Found {len(all_images)} unique external images in {len(file_images)} files:\n")
        
        for idx, (url, files) in enumerate(all_images.items(), 1):
            print(f"{idx}. {url}")
            print(f"   Used in {len(files)} file(s)")
            if len(files) <= 3:
                for f in files:
                    print(f"     - {f}")
            else:
                for f in files[:2]:
                    print(f"     - {f}")
                print(f"     ... and {len(files) - 2} more")
            print()
    else:
        print("No external images found.")
    
    print(f"\nTotal external images: {len(all_images)}")
