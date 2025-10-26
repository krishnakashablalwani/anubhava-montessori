"""
Manual image download helper - generates a downloadable list and update script.
Since Google blocks automated logins, this approach:
1. Creates a list of image URLs
2. You manually download them using your logged-in browser
3. Script updates HTML files to use local images
""" 

import os
import re
import json
from pathlib import Path
from urllib.parse import urlparse, unquote

def extract_image_links(html_content):
    """Extract all external image URLs from HTML"""
    image_urls = set()
    
    # Pattern 1: <img src="...">
    img_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
    for match in re.finditer(img_pattern, html_content, re.IGNORECASE):
        url = match.group(1)
        if url.startswith('http') and 'googleusercontent.com' in url:
            image_urls.add(url)
    
    # Pattern 2: <source srcset="...">
    srcset_pattern = r'<source[^>]+srcset=["\']([^"\']+)["\']'
    for match in re.finditer(srcset_pattern, html_content, re.IGNORECASE):
        url = match.group(1).split()[0]
        if url.startswith('http') and 'googleusercontent.com' in url:
            image_urls.add(url)
    
    # Pattern 3: background-image: url(...)
    bg_pattern = r'background-image:\s*url\(["\']?([^"\'()]+)["\']?\)'
    for match in re.finditer(bg_pattern, html_content, re.IGNORECASE):
        url = match.group(1)
        if url.startswith('http') and 'googleusercontent.com' in url:
            image_urls.add(url)
    
    # Pattern 4: <link href="..."
    link_pattern = r'<link[^>]+href=["\']([^"\']+\.(?:png|jpg|jpeg|gif|svg|webp|ico))["\']'
    for match in re.finditer(link_pattern, html_content, re.IGNORECASE):
        url = match.group(1)
        if url.startswith('http') and 'googleusercontent.com' in url:
            image_urls.add(url)
    
    return sorted(list(image_urls))

def get_image_extension(url):
    """Determine image file extension from URL"""
    parsed = urlparse(url)
    path = unquote(parsed.path)
    
    for ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico']:
        if ext in path.lower():
            return ext
    
    return '.jpg'

def create_download_list(base_dir):
    """Create a list of images that need to be downloaded"""
    
    print("\nScanning HTML files for Google Sites CDN images...")
    image_urls = set()
    html_files = []
    
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                html_files.append(file_path)
                
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    urls = extract_image_links(content)
                    image_urls.update(urls)
    
    # Filter to only Google Sites CDN images
    sites_cdn_images = sorted([url for url in image_urls if 'lh3.googleusercontent.com/sitesv/' in url])
    
    print(f"Found {len(sites_cdn_images)} Google Sites CDN images")
    print(f"Scanned {len(html_files)} HTML files")
    
    if not sites_cdn_images:
        print("\nNo Google Sites CDN images found!")
        return
    
    # Create download mapping
    image_mapping = {}
    for idx, url in enumerate(sites_cdn_images, 1):
        ext = get_image_extension(url)
        filename = f"sites_image_{idx}{ext}"
        image_mapping[url] = filename
    
    # Save mapping
    mapping_file = os.path.join(base_dir, 'image_download_list.json')
    with open(mapping_file, 'w') as f:
        json.dump(image_mapping, f, indent=2)
    
    print(f"\n✓ Mapping saved to: {mapping_file}")
    
    # Create HTML file with download links
    html_file = os.path.join(base_dir, 'download_images.html')
    
    html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Download Google Sites Images</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        h1 { color: #1a73e8; }
        .instructions { background: #e8f0fe; padding: 15px; border-radius: 4px; margin: 20px 0; }
        .instructions ol { margin: 10px 0; }
        .instructions li { margin: 8px 0; }
        .image-list { margin-top: 20px; }
        .image-item { 
            display: flex; 
            align-items: center; 
            padding: 10px; 
            border-bottom: 1px solid #e0e0e0;
            background: white;
        }
        .image-item:hover { background: #f8f8f8; }
        .image-number { 
            font-weight: bold; 
            width: 60px; 
            color: #5f6368;
        }
        .filename { 
            width: 200px; 
            font-family: monospace; 
            color: #1967d2;
        }
        .download-link { 
            flex: 1;
            margin: 0 10px;
        }
        .download-link a { 
            color: #1a73e8; 
            text-decoration: none;
            word-break: break-all;
        }
        .download-link a:hover { text-decoration: underline; }
        .status { 
            width: 100px; 
            text-align: center;
            font-size: 12px;
            color: #5f6368;
        }
        button { 
            background: #1a73e8; 
            color: white; 
            border: none; 
            padding: 12px 24px; 
            border-radius: 4px; 
            cursor: pointer; 
            font-size: 14px;
            margin: 10px 5px;
        }
        button:hover { background: #1557b0; }
        .success { color: #188038; font-weight: bold; }
        .warning { background: #fef7e0; padding: 15px; border-radius: 4px; border-left: 4px solid #f9ab00; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📥 Download Google Sites Images</h1>
        
        <div class="instructions">
            <h3>Instructions:</h3>
            <ol>
                <li><strong>Make sure you're logged in to Google Sites</strong> in this browser</li>
                <li>Right-click each image link below and select <strong>"Save link as..."</strong></li>
                <li>Save the file with the <strong>exact filename shown</strong> (e.g., sites_image_1.jpg)</li>
                <li>Save all images to a folder called <strong>"downloaded_images"</strong></li>
                <li>When done, run the Python script to update HTML files</li>
            </ol>
        </div>
        
        <div class="warning">
            <strong>⚠️ Important:</strong> You must be logged in to Google Sites for these links to work!
            Open one of your course pages in another tab first.
        </div>
        
        <button onclick="downloadAll()">📋 Copy All Links</button>
        <button onclick="window.print()">🖨️ Print List</button>
        
        <h2>Images to Download ({count} total)</h2>
        
        <div class="image-list">
{image_items}
        </div>
        
        <div style="margin-top: 30px; padding: 20px; background: #e8f0fe; border-radius: 4px;">
            <h3>After downloading all images:</h3>
            <p>Run this command to update your HTML files:</p>
            <code style="background: white; padding: 10px; display: block; margin: 10px 0;">
                python update_image_links.py
            </code>
        </div>
    </div>
    
    <script>
        function downloadAll() {
            const urls = {urls_json};
            const text = Object.keys(urls).join('\\n');
            navigator.clipboard.writeText(text).then(() => {
                alert('All ' + Object.keys(urls).length + ' URLs copied to clipboard!');
            });
        }
    </script>
</body>
</html>"""
    
    # Generate image items HTML
    items_html = []
    for idx, (url, filename) in enumerate(image_mapping.items(), 1):
        item = f'''            <div class="image-item">
                <div class="image-number">#{idx}</div>
                <div class="filename">{filename}</div>
                <div class="download-link">
                    <a href="{url}" download="{filename}" target="_blank">{url[:100]}...</a>
                </div>
                <div class="status">📥 Download</div>
            </div>'''
        items_html.append(item)
    
    html_content = html_content.replace('{count}', str(len(image_mapping)))
    html_content = html_content.replace('{image_items}', '\n'.join(items_html))
    html_content = html_content.replace('{urls_json}', json.dumps(image_mapping))
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ Download page created: {html_file}")
    print(f"\n{'='*70}")
    print("NEXT STEPS:")
    print("="*70)
    print(f"1. Open this file in your browser: {html_file}")
    print("2. Make sure you're logged in to Google Sites in that browser")
    print("3. Download all images to a folder called 'downloaded_images'")
    print("4. Run: python update_image_links.py")
    print("="*70)

if __name__ == '__main__':
    base_dir = r'c:\Users\Admin\Downloads\Montessori Training\sites.google.com\view\montessoricoreprinciples-mtrt'
    
    print("="*70)
    print("Google Sites Image Download Helper")
    print("="*70)
    
    create_download_list(base_dir)
    
    print("\n✓ All done!")
