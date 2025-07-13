#!/usr/bin/env python3
"""
Script to create a new CSV file (apis_v2.csv) that excludes inactive API links.
"""

import csv
import sys

def read_inactive_urls(filename):
    """Read the list of inactive URLs from the inactive_apis.txt file."""
    inactive_urls = set()
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('https://'):
                    # Extract the URL from the line
                    url = line.split(' (Status:')[0].strip()
                    inactive_urls.add(url)
    except FileNotFoundError:
        print(f"Warning: {filename} not found. No URLs will be filtered.")
    return inactive_urls

def create_clean_csv(input_file, output_file, inactive_urls):
    """Create a new CSV file excluding inactive URLs."""
    total_rows = 0
    filtered_rows = 0
    
    try:
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8', newline='') as outfile:
            
            reader = csv.DictReader(infile, delimiter=';')
            fieldnames = ['title', 'x-apisguru-categories', 'openapiVer', 'swaggerUrl']
            writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=';')
            
            # Write header
            writer.writeheader()
            
            # Process each row
            for row in reader:
                total_rows += 1
                swagger_url = row.get('swaggerUrl', '').strip()
                
                # Skip if this URL is in the inactive list
                if swagger_url in inactive_urls:
                    filtered_rows += 1
                    continue
                
                # Create a clean row with only the expected fields
                clean_row = {
                    'title': row.get('title', ''),
                    'x-apisguru-categories': row.get('x-apisguru-categories', ''),
                    'openapiVer': row.get('openapiVer', ''),
                    'swaggerUrl': swagger_url
                }
                
                # Write the row to the new file
                writer.writerow(clean_row)
                
    except FileNotFoundError:
        print(f"Error: {input_file} not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing CSV: {e}")
        sys.exit(1)
    
    return total_rows, filtered_rows

def main():
    input_file = 'apis.csv'
    output_file = 'apis_v2.csv'
    inactive_file = 'inactive_apis.txt'
    
    print("Creating clean CSV file...")
    
    # Read inactive URLs
    inactive_urls = read_inactive_urls(inactive_file)
    print(f"Found {len(inactive_urls)} inactive URLs to filter out")
    
    # Create the clean CSV
    total_rows, filtered_rows = create_clean_csv(input_file, output_file, inactive_urls)
    
    # Print summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"Original CSV rows: {total_rows}")
    print(f"Filtered out rows: {filtered_rows}")
    print(f"Remaining rows: {total_rows - filtered_rows}")
    print(f"Output file: {output_file}")
    
    if total_rows > 0:
        success_rate = ((total_rows - filtered_rows) / total_rows) * 100
        print(f"Success rate: {success_rate:.1f}%")

if __name__ == "__main__":
    main() 