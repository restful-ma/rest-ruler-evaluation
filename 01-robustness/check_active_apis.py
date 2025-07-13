#!/usr/bin/env python3
"""
Script to check how many API links in apis.csv are still active.
"""

import csv
import requests
import time
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

def check_url(url, timeout=10):
    """
    Check if a URL is accessible by making a HEAD request.
    Returns (url, status_code, is_active, error_message)
    """
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        is_active = response.status_code < 400
        return url, response.status_code, is_active, None
    except requests.exceptions.RequestException as e:
        return url, None, False, str(e)

def main():
    csv_file = 'apis.csv'
    
    # Read the CSV file
    urls = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter=';')
            for row in reader:
                if 'swaggerUrl' in row and row['swaggerUrl']:
                    urls.append(row['swaggerUrl'])
    except FileNotFoundError:
        print(f"Error: {csv_file} not found in current directory")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)
    
    print(f"Found {len(urls)} API URLs to check")
    print("Checking URLs... (this may take a while)")
    
    active_urls = []
    inactive_urls = []
    
    # Use ThreadPoolExecutor for concurrent requests
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all URL checks
        future_to_url = {executor.submit(check_url, url): url for url in urls}
        
        # Process completed checks
        for i, future in enumerate(as_completed(future_to_url), 1):
            url, status_code, is_active, error = future.result()
            
            if is_active:
                active_urls.append((url, status_code))
                print(f"[{i}/{len(urls)}] ✓ {url} (Status: {status_code})")
            else:
                inactive_urls.append((url, status_code, error))
                print(f"[{i}/{len(urls)}] ✗ {url} (Status: {status_code}, Error: {error})")
            
            # Add a small delay to be respectful to servers
            time.sleep(0.1)
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total APIs checked: {len(urls)}")
    print(f"Active APIs: {len(active_urls)}")
    print(f"Inactive APIs: {len(inactive_urls)}")
    print(f"Success rate: {(len(active_urls)/len(urls)*100):.1f}%")
    
    # Save results to files
    with open('active_apis.txt', 'w', encoding='utf-8') as f:
        f.write(f"Active APIs ({len(active_urls)}):\n")
        f.write("="*40 + "\n")
        for url, status_code in active_urls:
            f.write(f"{url} (Status: {status_code})\n")
    
    with open('inactive_apis.txt', 'w', encoding='utf-8') as f:
        f.write(f"Inactive APIs ({len(inactive_urls)}):\n")
        f.write("="*40 + "\n")
        for url, status_code, error in inactive_urls:
            f.write(f"{url} (Status: {status_code}, Error: {error})\n")
    
    print(f"\nResults saved to:")
    print("- active_apis.txt")
    print("- inactive_apis.txt")

if __name__ == "__main__":
    main() 