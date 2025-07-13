import pandas as pd
import re
import numpy as np

def analyze_api_sizes():
    # Read the successful APIs from ai_robustness_results.csv
    successful_apis = []
    with open('01-robustness/ai_robustness_results.csv', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    # Extract API titles from the successful results
    for line in lines:
        if ' | ' in line and not line.startswith('title') and not line.startswith('---'):
            parts = line.strip().split(' | ')
            if len(parts) >= 2 and parts[1].isdigit():
                successful_apis.append(parts[0])
    
    print(f"Total successful APIs: {len(successful_apis)}")
    
    # Read the categorization data
    categorization_df = pd.read_csv('02-performance/api_information_categorisation_test.csv')
    
    # Create a mapping from API name to category and stats
    api_to_data = {}
    for _, row in categorization_df.iterrows():
        # Remove .json extension to match API titles
        api_name = row['file_name'].replace('.json', '')
        api_to_data[api_name] = {
            'category': row['category'],
            'file_size_mb': row['file_size_in_mb'],
            'number_paths': row['number_paths']
        }
    
    # Count categories for successful APIs and collect stats
    category_counts = {
        'very low': 0,
        'low': 0, 
        'medium': 0,
        'high': 0,
        'very high': 0,
        'huge': 0,
        'not_found': 0
    }
    
    # Collect statistics for each category
    category_stats = {
        'very low': {'file_sizes': [], 'path_counts': []},
        'low': {'file_sizes': [], 'path_counts': []},
        'medium': {'file_sizes': [], 'path_counts': []},
        'high': {'file_sizes': [], 'path_counts': []},
        'very high': {'file_sizes': [], 'path_counts': []},
        'huge': {'file_sizes': [], 'path_counts': []}
    }
    
    successful_with_categories = []
    not_found_apis = []
    
    for api in successful_apis:
        if api in api_to_data:
            data = api_to_data[api]
            category = data['category']
            category_counts[category] += 1
            successful_with_categories.append((api, category))
            
            # Collect statistics
            category_stats[category]['file_sizes'].append(data['file_size_mb'])
            category_stats[category]['path_counts'].append(data['number_paths'])
        else:
            category_counts['not_found'] += 1
            not_found_apis.append(api)
    
    # Print results
    print("\n" + "="*80)
    print("API SIZE DISTRIBUTION ANALYSIS")
    print("="*80)
    print(f"Total APIs successfully processed: {len(successful_apis)}")
    print(f"APIs with category information: {len(successful_apis) - category_counts['not_found']}")
    print(f"APIs without category information: {category_counts['not_found']}")
    
    print("\n" + "-"*80)
    print("SIZE CATEGORY BREAKDOWN WITH STATISTICS:")
    print("-"*80)
    print(f"{'Category':<12} {'Count':<6} {'%':<5} {'Median Paths':<15} {'Median Size (MB)':<15}")
    print("-"*80)
    
    # Map categories to more readable names
    category_mapping = {
        'very low': 'Very Small',
        'low': 'Small', 
        'medium': 'Medium',
        'high': 'Large',
        'very high': 'Very Large',
        'huge': 'Huge'
    }
    
    total_categorized = 0
    for category, count in category_counts.items():
        if category != 'not_found':
            readable_name = category_mapping.get(category, category)
            percentage = (count / len(successful_apis)) * 100
            total_categorized += count
            
            # Calculate medians
            if category_stats[category]['path_counts']:
                median_paths = np.median(category_stats[category]['path_counts'])
                median_size = np.median(category_stats[category]['file_sizes'])
                print(f"{readable_name:<12} {count:<6} {percentage:<5.1f} {median_paths:<15.1f} {median_size:<15.3f}")
            else:
                print(f"{readable_name:<12} {count:<6} {percentage:<5.1f} {'N/A':<15} {'N/A':<15}")
    
    print("-"*80)
    print(f"Total categorized: {total_categorized}")
    print(f"Not found:        {category_counts['not_found']}")
    print(f"Grand total:      {len(successful_apis)}")
    
    # Detailed statistics for each category
    print("\n" + "="*80)
    print("DETAILED STATISTICS BY CATEGORY:")
    print("="*80)
    
    for category in ['very low', 'low', 'medium', 'high', 'very high', 'huge']:
        if category_counts[category] > 0:
            readable_name = category_mapping.get(category, category)
            stats = category_stats[category]
            
            print(f"\n{readable_name} APIs ({category_counts[category]} APIs):")
            print("-" * 50)
            
            if stats['path_counts']:
                paths = np.array(stats['path_counts'])
                sizes = np.array(stats['file_sizes'])
                
                print(f"Number of Paths:")
                print(f"  Median: {np.median(paths):.1f}")
                print(f"  Mean:   {np.mean(paths):.1f}")
                print(f"  Min:    {np.min(paths):.0f}")
                print(f"  Max:    {np.max(paths):.0f}")
                print(f"  Std Dev: {np.std(paths):.1f}")
                
                print(f"\nFile Size (MB):")
                print(f"  Median: {np.median(sizes):.3f}")
                print(f"  Mean:   {np.mean(sizes):.3f}")
                print(f"  Min:    {np.min(sizes):.3f}")
                print(f"  Max:    {np.max(sizes):.3f}")
                print(f"  Std Dev: {np.std(sizes):.3f}")
            else:
                print("No data available")
    
    # Show some examples of APIs in each category
    print("\n" + "="*80)
    print("EXAMPLES BY CATEGORY:")
    print("="*80)
    
    for category in ['very low', 'low', 'medium', 'high', 'very high', 'huge']:
        if category_counts[category] > 0:
            readable_name = category_mapping.get(category, category)
            examples = [api for api, cat in successful_with_categories if cat == category][:5]
            print(f"\n{readable_name} APIs (showing first 5):")
            for example in examples:
                if example in api_to_data:
                    data = api_to_data[example]
                    print(f"  - {example} (paths: {data['number_paths']}, size: {data['file_size_mb']:.3f} MB)")
                else:
                    print(f"  - {example}")
    
    # Show APIs not found in categorization
    if category_counts['not_found'] > 0:
        print(f"\nAPIs not found in categorization (showing first 10):")
        for api in not_found_apis[:10]:
            print(f"  - {api}")
        if len(not_found_apis) > 10:
            print(f"  ... and {len(not_found_apis) - 10} more")
    
    # Summary statistics across all categories
    print("\n" + "="*80)
    print("OVERALL SUMMARY STATISTICS:")
    print("="*80)
    
    all_paths = []
    all_sizes = []
    
    for category in ['very low', 'low', 'medium', 'high', 'very high', 'huge']:
        all_paths.extend(category_stats[category]['path_counts'])
        all_sizes.extend(category_stats[category]['file_sizes'])
    
    if all_paths:
        print(f"All categorized APIs ({len(all_paths)} APIs):")
        print(f"  Number of Paths - Median: {np.median(all_paths):.1f}, Mean: {np.mean(all_paths):.1f}")
        print(f"  File Size (MB) - Median: {np.median(all_sizes):.3f}, Mean: {np.mean(all_sizes):.3f}")
    
    return category_counts, successful_apis, not_found_apis, category_stats

if __name__ == "__main__":
    analyze_api_sizes() 