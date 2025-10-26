import os
import re
import requests
from urllib.parse import urlparse, unquote
import time

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

def download_image(url, output_path):
    """Download an image from URL to output_path."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def get_image_extension(url):
    """Guess image extension from URL or content type."""
    # Try to get from URL first
    parsed = urlparse(url)
    path = parsed.path.lower()
    
    for ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico']:
        if ext in path:
            return ext
    
    # Default to .jpg for Google user content
    if 'googleusercontent.com' in url or 'drive.google.com' in url:
        return '.jpg'
    
    return '.png'

def replace_image_links(html_content, image_mapping, rel_dir):
    """Replace external image URLs with local image paths."""
    modified = html_content
    replacements = 0
    
    for url, local_filename in image_mapping.items():
        # Create relative path to image
        local_path = f'images/{local_filename}'
        
        # Escape special regex characters in URL
        escaped_url = re.escape(url)
        
        # Replace in all contexts
        patterns = [
            rf'src=["\']({escaped_url})["\']',
            rf'srcset=["\']({escaped_url})["\']',
            rf'url\(["\']?({escaped_url})["\']?\)',
            rf'href=["\']({escaped_url})["\']',
        ]
        
        for pattern in patterns:
            count = len(re.findall(pattern, modified, re.IGNORECASE))
            if count > 0:
                modified = re.sub(pattern, lambda m: m.group(0).replace(url, local_path), modified, flags=re.IGNORECASE)
                replacements += count
    
    return modified, replacements

def main():
    base_dir = r'c:\Users\Admin\Downloads\Montessori Training\sites.google.com'
    
    # First, collect all unique images
    print("Step 1: Scanning for external images...\n")
    all_images = {}  # url -> {files}
    file_images = {}  # file_path -> [image_urls]
    
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
                        file_images[file_path] = images
                        for img_url in images:
                            if img_url not in all_images:
                                all_images[img_url] = []
                            all_images[img_url].append(rel_path)
                            
                except Exception as e:
                    print(f"Error reading {rel_path}: {e}")
    
    print(f"Found {len(all_images)} unique external images in {len(file_images)} files\n")
    
    # Download images
    print("Step 2: Downloading images...\n")
    image_mapping = {}  # url -> local_filename
    downloaded = 0
    
    for idx, (url, files) in enumerate(all_images.items(), 1):
        # Get the directory of the first file that uses this image
        first_file = None
        for file_path, images in file_images.items():
            if url in images:
                first_file = file_path
                break
        
        if first_file:
            file_dir = os.path.dirname(first_file)
            images_dir = os.path.join(file_dir, 'images')
            os.makedirs(images_dir, exist_ok=True)
            
            # Determine extension
            ext = get_image_extension(url)
            filename = f'image_{idx}{ext}'
            output_path = os.path.join(images_dir, filename)
            
            print(f"[{idx}/{len(all_images)}] Downloading: {url[:100]}...")
            
            if download_image(url, output_path):
                image_mapping[url] = filename
                downloaded += 1
                # Get file size
                if os.path.exists(output_path):
                    size_kb = os.path.getsize(output_path) / 1024
                    print(f"  ✓ Downloaded ({size_kb:.2f} KB)\n")
                
                # Small delay to avoid rate limiting
                time.sleep(0.1)
            else:
                print(f"  ✗ Failed\n")
    
    print(f"\nImages downloaded: {downloaded}/{len(all_images)}\n")
    
    # Update HTML files
    print("Step 3: Updating HTML files with local image paths...\n")
    files_modified = 0
    total_replacements = 0
    
    for file_path, images in file_images.items():
        rel_path = os.path.relpath(file_path, base_dir)
        rel_dir = os.path.dirname(rel_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            modified_content, replacements = replace_image_links(content, image_mapping, rel_dir)
            
            if replacements > 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                files_modified += 1
                total_replacements += replacements
                print(f"✓ {rel_path}: {replacements} links updated")
                
        except Exception as e:
            print(f"✗ Error updating {rel_path}: {e}")
    
    print(f"\n\nSummary:")
    print(f"  Images downloaded: {downloaded}/{len(all_images)}")
    print(f"  Files modified: {files_modified}")
    print(f"  Total links replaced: {total_replacements}")

if __name__ == "__main__":
    main()
