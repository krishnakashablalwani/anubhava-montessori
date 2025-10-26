"""
Download images from Google Sites using Selenium with browser automation.
This script opens a browser, waits for you to log in to Google Sites,
then automatically downloads all images.
"""

import os
import re
import time
import json
from pathlib import Path
from urllib.parse import urlparse, unquote

# Check for selenium
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    print("ERROR: Selenium not installed!")
    print("Please install it with: pip install selenium")
    exit(1)

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
        url = match.group(1).split()[0]  # srcset can have multiple URLs
        if url.startswith('http') and 'googleusercontent.com' in url:
            image_urls.add(url)
    
    # Pattern 3: background-image: url(...)
    bg_pattern = r'background-image:\s*url\(["\']?([^"\'()]+)["\']?\)'
    for match in re.finditer(bg_pattern, html_content, re.IGNORECASE):
        url = match.group(1)
        if url.startswith('http') and 'googleusercontent.com' in url:
            image_urls.add(url)
    
    # Pattern 4: <link href="..." (for favicons, etc.)
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
    
    # Check for common extensions in path
    for ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico']:
        if ext in path.lower():
            return ext
    
    # Default to .jpg for Google content
    if 'googleusercontent.com' in url:
        return '.jpg'
    
    return '.jpg'

def setup_selenium_driver():
    """Setup Chrome driver with options"""
    print("\nSetting up Chrome browser...")
    
    chrome_options = Options()
    # Don't run headless - we need user to log in
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Set download preferences
    prefs = {
        "download.default_directory": os.getcwd(),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    try:
        # Try using webdriver-manager for automatic driver management
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service as ChromeService
            print("Using webdriver-manager for automatic ChromeDriver installation...")
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            return driver
        except ImportError:
            print("webdriver-manager not found, trying default Chrome driver...")
            driver = webdriver.Chrome(options=chrome_options)
            return driver
    except Exception as e:
        print(f"\nERROR: Could not start Chrome browser: {e}")
        print("\nPlease install webdriver-manager:")
        print("  pip install webdriver-manager")
        print("\nOr make sure Chrome browser and ChromeDriver are installed.")
        return None

def wait_for_login(driver):
    """Wait for user to log in to Google Sites"""
    print("\n" + "="*70)
    print("PLEASE LOG IN TO GOOGLE SITES")
    print("="*70)
    print("\nA Chrome browser window has opened.")
    print("Please:")
    print("  1. Log in to your Google account if prompted")
    print("  2. Navigate to any Google Sites page from your course")
    print("  3. Make sure the page loads completely with all images")
    print("  4. Come back to this terminal and press ENTER when ready")
    print("\nThis ensures the browser has the right cookies to download images.")
    print("="*70)
    
    input("\nPress ENTER when you're logged in and ready to continue...")
    print("\nGreat! Starting image download process...\n")

def download_image_with_selenium(driver, url, output_path):
    """Download an image using Selenium by navigating to it"""
    try:
        # Navigate to the image URL
        driver.get(url)
        
        # Wait a moment for the image to load
        time.sleep(0.5)
        
        # Get the image data from the page source
        # For images, the browser should display them directly
        screenshot_path = output_path + '.png'
        
        # Try to find img element and get screenshot
        try:
            img_element = driver.find_element(By.TAG_NAME, 'img')
            # Take screenshot of the image element
            img_element.screenshot(output_path)
            return True
        except:
            # If no img tag, might be viewing the image directly
            # Save screenshot of entire page
            driver.save_screenshot(output_path)
            return True
            
    except Exception as e:
        return False

def download_images_selenium(base_dir):
    """Main function to download images using Selenium"""
    
    # Step 1: Collect all unique image URLs
    print("\nStep 1: Scanning HTML files for external images...")
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
    
    image_urls = sorted(list(image_urls))
    print(f"Found {len(image_urls)} unique external images")
    print(f"Scanned {len(html_files)} HTML files")
    
    if not image_urls:
        print("No external images found!")
        return
    
    # Filter to only Google Sites CDN images that previously failed
    sites_cdn_images = [url for url in image_urls if 'lh3.googleusercontent.com/sitesv/' in url]
    print(f"\nFound {len(sites_cdn_images)} Google Sites CDN images to download")
    
    if not sites_cdn_images:
        print("No Google Sites CDN images found (these were the ones failing)!")
        return
    
    # Step 2: Setup Selenium
    driver = setup_selenium_driver()
    if not driver:
        return
    
    try:
        # Step 3: Navigate to Google Sites and wait for login
        print("\nOpening Google Sites...")
        driver.get("https://sites.google.com")
        wait_for_login(driver)
        
        # Step 4: Download images
        print(f"\nStep 2: Downloading {len(sites_cdn_images)} images using browser session...")
        print("="*70)
        
        downloaded_count = 0
        failed_urls = []
        image_mapping = {}
        
        for idx, url in enumerate(sites_cdn_images, 1):
            ext = get_image_extension(url)
            filename = f"image_{idx}{ext}"
            
            # Save to images folder in base directory
            images_dir = os.path.join(base_dir, 'images')
            os.makedirs(images_dir, exist_ok=True)
            output_path = os.path.join(images_dir, filename)
            
            print(f"[{idx}/{len(sites_cdn_images)}] Downloading: {url[:80]}...")
            
            if download_image_with_selenium(driver, url, output_path):
                file_size = os.path.getsize(output_path) / 1024
                print(f"  ✓ Downloaded ({file_size:.2f} KB)")
                downloaded_count += 1
                image_mapping[url] = filename
            else:
                print(f"  ✗ Failed")
                failed_urls.append(url)
            
            # Small delay between downloads
            time.sleep(0.3)
        
        print("\n" + "="*70)
        print(f"\nImages downloaded: {downloaded_count}/{len(sites_cdn_images)}")
        
        if failed_urls:
            print(f"\nFailed to download {len(failed_urls)} images:")
            for url in failed_urls[:5]:
                print(f"  - {url[:80]}...")
            if len(failed_urls) > 5:
                print(f"  ... and {len(failed_urls) - 5} more")
        
        # Save mapping for later use
        if image_mapping:
            mapping_file = os.path.join(base_dir, 'image_mapping_selenium.json')
            with open(mapping_file, 'w') as f:
                json.dump(image_mapping, f, indent=2)
            print(f"\nImage mapping saved to: {mapping_file}")
        
        print("\n✓ Selenium download complete!")
        print("\nNote: Images were downloaded as screenshots. Quality may vary.")
        print("You may need to update HTML files to use these local images.")
        
    finally:
        # Close browser
        print("\nClosing browser...")
        driver.quit()

if __name__ == '__main__':
    base_dir = r'c:\Users\Admin\Downloads\Montessori Training\sites.google.com\view\montessoricoreprinciples-mtrt'
    
    print("="*70)
    print("Google Sites Image Downloader - Selenium Method")
    print("="*70)
    print(f"\nBase directory: {base_dir}")
    
    download_images_selenium(base_dir)
    
    print("\n" + "="*70)
    print("All done!")
    print("="*70)
