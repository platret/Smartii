#!/usr/bin/env python3
"""
Image Fetcher Script
Downloads images from URLs and saves them locally with format detection
"""

import sys
import requests
from pathlib import Path
from urllib.parse import urlparse, unquote
import mimetypes

def get_file_extension(url, content_type):
    """
    Determine file extension from URL or content-type header
    """
    # Try to get extension from URL
    parsed_url = urlparse(url)
    path = unquote(parsed_url.path)
    _, ext = Path(path).stem, Path(path).suffix
    
    if ext and ext.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg', '.ico', '.tiff', '.tif']:
        return ext
    
    # If no extension in URL, try content-type
    if content_type:
        extension = mimetypes.guess_extension(content_type.split(';')[0].strip())
        if extension:
            # Convert .jpe to .jpg
            if extension == '.jpe':
                return '.jpg'
            return extension
    
    # Default to .jpg if all else fails
    return '.jpg'

def fetch_image(url, output_path=None, filename=None):
    """
    Fetch an image from a URL and save it locally
    
    Args:
        url: URL of the image to fetch
        output_path: Directory to save the image (default: current directory)
        filename: Custom filename (default: derived from URL)
    
    Returns:
        Path to the saved image file
    """
    try:
        # Set a user agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Fetch the image
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()
        
        # Get content type
        content_type = response.headers.get('content-type', '')
        
        # Determine output path and filename
        if output_path is None:
            output_path = Path.cwd()
        else:
            output_path = Path(output_path)
            output_path.mkdir(parents=True, exist_ok=True)
        
        # Determine filename if not provided
        if filename is None:
            # Try to get filename from URL
            parsed_url = urlparse(url)
            url_filename = Path(unquote(parsed_url.path)).name
            
            if url_filename and url_filename != '':
                filename = url_filename
            else:
                # Generate a filename
                filename = f"image_{hash(url) % 10000}"
        
        # Ensure filename has proper extension
        file_path = Path(filename)
        if not file_path.suffix or file_path.suffix.lower() not in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg', '.ico', '.tiff', '.tif']:
            extension = get_file_extension(url, content_type)
            filename = f"{file_path.stem}{extension}"
        
        # Full output path
        full_path = output_path / filename
        
        # Save the image
        with open(full_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ Image downloaded successfully: {full_path}")
        print(f"   Size: {full_path.stat().st_size / 1024:.2f} KB")
        print(f"   Content-Type: {content_type}")
        return str(full_path)
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching image from {url}: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: python fetch_image.py <image_url> [output_directory] [filename]")
        print("\nExamples:")
        print("  python fetch_image.py https://example.com/image.jpg")
        print("  python fetch_image.py https://example.com/image.jpg ./downloads")
        print("  python fetch_image.py https://example.com/image.jpg ./downloads myimage.jpg")
        sys.exit(1)
    
    url = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    filename = sys.argv[3] if len(sys.argv) > 3 else None
    
    fetch_image(url, output_path, filename)

if __name__ == "__main__":
    main()
