import os
import re

def extract_panopto_links(html_content):
    """Extract Panopto video links from HTML content."""
    panopto_links = []
    
    # Pattern for Panopto hosted links
    patterns = [
        r'https?://[^/]*panopto\.com/Panopto/Pages/Viewer\.aspx\?id=([^&\s"\'<>]+)',
        r'https?://[^/]*panopto\.com/Panopto/Pages/Embed\.aspx\?id=([^&\s"\'<>]+)',
        r'src=["\']([^"\']*panopto\.com[^"\']*)["\']',
        r'href=["\']([^"\']*panopto\.com[^"\']*)["\']',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        for match in matches:
            if 'panopto.com' in match:
                panopto_links.append(match)
            else:
                # If match is just the ID, construct full URL
                full_url = f'https://montessori-ami.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id={match}'
                panopto_links.append(full_url)
    
    return list(set(panopto_links))

def scan_all_files():
    """Scan all HTML files for Panopto video links."""
    base_dir = r'c:\Users\Admin\Downloads\Montessori Training\sites.google.com'
    
    all_panopto_links = {}
    
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, base_dir)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    panopto_links = extract_panopto_links(content)
                    
                    if panopto_links:
                        all_panopto_links[rel_path] = panopto_links
                        
                except Exception as e:
                    print(f"Error reading {rel_path}: {e}")
    
    return all_panopto_links

if __name__ == "__main__":
    print("Scanning for Panopto videos...\n")
    
    panopto_links = scan_all_files()
    
    if panopto_links:
        print(f"Found Panopto videos in {len(panopto_links)} files:\n")
        
        total_videos = 0
        for file_path, links in panopto_links.items():
            print(f"\n{file_path}:")
            for link in links:
                print(f"  - {link}")
                total_videos += 1
        
        print(f"\n\nTotal Panopto videos found: {total_videos}")
    else:
        print("No Panopto videos found.")
