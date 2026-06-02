#!/usr/bin/env python3
"""
Batch Image Fetcher Script
Downloads multiple images from a list of URLs
"""

import sys
import json
from pathlib import Path
from fetch_image import fetch_image

def fetch_multiple_images(urls, output_path=None):
    """
    Fetch multiple images from a list of URLs
    
    Args:
        urls: List of image URLs
        output_path: Directory to save images (default: current directory)
    
    Returns:
        List of paths to saved images
    """
    if output_path is None:
        output_path = Path.cwd()
    else:
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
    
    results = []
    successful = 0
    failed = 0
    
    print(f"📥 Fetching {len(urls)} images...")
    print(f"   Output directory: {output_path}\n")
    
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] Fetching: {url}")
        try:
            result = fetch_image(url, output_path)
            results.append({
                'url': url,
                'path': result,
                'success': True
            })
            successful += 1
        except Exception as e:
            print(f"❌ Failed: {e}")
            results.append({
                'url': url,
                'error': str(e),
                'success': False
            })
            failed += 1
        print()
    
    print(f"\n{'='*60}")
    print(f"📊 Summary:")
    print(f"   Total: {len(urls)}")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"{'='*60}")
    
    return results

def main():
    if len(sys.argv) < 2:
        print("Usage: python fetch_images_batch.py <urls_file_or_json> [output_directory]")
        print("\nInput formats:")
        print("  1. Text file with one URL per line")
        print("  2. JSON file with array of URLs: [\"url1\", \"url2\", ...]")
        print("\nExamples:")
        print("  python fetch_images_batch.py urls.txt")
        print("  python fetch_images_batch.py urls.json ./downloads")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Read URLs from file
    try:
        with open(input_file, 'r') as f:
            content = f.read().strip()
            
            # Try to parse as JSON first
            try:
                urls = json.loads(content)
                if not isinstance(urls, list):
                    raise ValueError("JSON must be an array of URLs")
            except json.JSONDecodeError:
                # If not JSON, treat as text file with one URL per line
                urls = [line.strip() for line in content.split('\n') if line.strip()]
        
        if not urls:
            print("❌ No URLs found in input file")
            sys.exit(1)
        
        results = fetch_multiple_images(urls, output_path)
        
        # Save results to JSON
        results_file = Path(output_path or '.') / 'fetch_results.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to: {results_file}")
        
    except FileNotFoundError:
        print(f"❌ File not found: {input_file}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
