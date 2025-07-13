#!/usr/bin/env python3
"""
Comprehensive REST-Ruler Performance Benchmarking Script

This script benchmarks the REST-Ruler tool across different API complexity categories:
- very low (≤10 paths)
- low (11-30 paths) 
- medium (31-70 paths)
- high (71-150 paths)
- very high (151-310 paths)

For each category, it tests up the APIs and measures:
- Execution time
- Memory utilization
- CPU utilization

Results are saved to category-specific folders with detailed statistics.
"""

import csv
import json
import os
import random
import re
import statistics
import time
import psutil
import threading
from subprocess import PIPE, Popen, TimeoutExpired
from collections import defaultdict
import pandas as pd


class PerformanceBenchmark:
    def __init__(self):
        # Run complete benchmark across all categories
        self.categories = ["very low", "low", "medium", "high", "very high"]
        self.max_apis_per_category = 30
        self.jar_path = "./rest-ruler.jar"
        self.results_dir = "./benchmark_results"
        
        # Create results directory
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Load API categorization data
        self.api_data = self.load_api_categorization()
        
        # Load API URLs
        self.api_urls = self.load_api_urls()
        
        # Results storage
        self.results = defaultdict(list)
        
    def load_api_categorization(self):
        """Load API categorization from CSV file"""
        api_data = defaultdict(list)
        
        try:
            with open('api_information_categorisation_test.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    category = row['category']
                    if category in self.categories:
                        api_data[category].append({
                            'file_name': row['file_name'],
                            'file_size_mb': float(row['file_size_in_mb']),
                            'number_paths': int(row['number_paths']),
                            'category': category
                        })
            
            print(f"Loaded API categorization data:")
            for category in self.categories:
                count = len(api_data[category])
                print(f"  {category}: {count} APIs")
                
        except FileNotFoundError:
            print("Error: api_information_categorisation_test.csv not found!")
            return defaultdict(list)
            
        return api_data
    
    def load_api_urls(self):
        """Load API URLs from apis_v2.csv"""
        api_urls = {}
        
        try:
            with open('../01-robustness/apis_v2.csv', 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter=';')
                next(reader)  # Skip header
                
                for row in reader:
                    if len(row) >= 4:
                        title = row[0]
                        url = row[3]
                        api_urls[title] = url
                        
            print(f"Loaded {len(api_urls)} API URLs")
            
        except FileNotFoundError:
            print("Error: ../01-robustness/apis_v2.csv not found!")
            return {}
            
        return api_urls
    
    def get_api_url(self, api_name):
        """Get URL for an API by name"""
        # Remove .json extension if present
        clean_name = api_name.replace('.json', '')
        return self.api_urls.get(clean_name, None)
    
    def monitor_process(self, process_pid, memory_samples, cpu_samples, stop_event):
        """Monitor the main and child processes (CPU and memory) until stop_event is set."""
        try:
            proc = psutil.Process(process_pid)
        except psutil.NoSuchProcess:
            return

        while not stop_event.is_set():
            try:
                # include all children
                all_procs = [proc] + proc.children(recursive=True)
                
                total_mem = 0
                total_cpu = 0

                for p in all_procs:
                    if p.is_running():
                        with p.oneshot():
                            total_mem += p.memory_info().rss
                            total_cpu += p.cpu_percent(interval=0.05)

                # Convert memory to MB, normalize CPU to % of a single core
                memory_samples.append(total_mem / (1024 * 1024))
                cpu_samples.append(total_cpu / psutil.cpu_count())

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break

    def execute_rest_ruler(self, api_name, api_url):
        """Execute REST-Ruler tool and measure performance with threading"""
        try:
            # Prepare command
            cmd = [
                'java', '-jar', self.jar_path,
                '-p', api_url,
                '-r', '-rn', api_name.replace('.json', ''),
                '-llm', '-n', 'camelcase'
            ]
            
            # Start timing
            start_time = time.time()
            
            # Execute process
            process = Popen(
                cmd,
                stdout=PIPE,
                stderr=PIPE,
                stdin=PIPE,
            )
            
            # Set up monitoring in a separate thread
            memory_samples = []
            cpu_samples = []
            stop_event = threading.Event()
            
            # Start monitoring thread
            monitor_thread = threading.Thread(
                target=self.monitor_process,
                args=(process.pid, memory_samples, cpu_samples, stop_event)
            )
            monitor_thread.start()
            
            try:
                stdout, stderr = process.communicate(input=b'no', timeout=120)
            except TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                stderr = (stderr or b'') + b'\nProcess timed out after 120 seconds.'
                return_code = -1
            else:
                return_code = process.returncode
            finally:
                stop_event.set()
                monitor_thread.join(timeout=2)
            
            # Calculate execution time
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Convert bytes to strings
            stdout = stdout.decode('utf-8', errors='ignore') if stdout else ''
            stderr = stderr.decode('utf-8', errors='ignore') if stderr else ''
            
            # Extract violation count
            violation_count = 0
            if stdout:
                pattern = re.compile(r'In total (\d+) rule violations were found')
                match = pattern.search(stdout)
                if match:
                    violation_count = int(match.group(1))
            
            # Calculate memory and CPU statistics
            avg_memory_mb = statistics.mean(memory_samples) if memory_samples else 0
            max_memory_mb = max(memory_samples) if memory_samples else 0
            avg_cpu = statistics.mean(cpu_samples) if cpu_samples else 0
            max_cpu = max(cpu_samples) if cpu_samples else 0
            
            return {
                'success': process.returncode == 0,
                'execution_time': execution_time,
                'avg_memory_mb': avg_memory_mb,
                'max_memory_mb': max_memory_mb,
                'avg_cpu': avg_cpu,
                'max_cpu': max_cpu,
                'violation_count': violation_count,
                'stdout': stdout,
                'stderr': stderr,
                'return_code': process.returncode
            }
            
        except Exception as e:
            return {
                'success': False,
                'execution_time': 0,
                'avg_memory_mb': 0,
                'max_memory_mb': 0,
                'avg_cpu': 0,
                'max_cpu': 0,
                'violation_count': 0,
                'stdout': '',
                'stderr': str(e),
                'return_code': -1
            }
    
    def benchmark_category(self, category):
        """Benchmark APIs in a specific category, trying to get max successful runs"""
        print(f"\n{'='*60}")
        print(f"Benchmarking {category} APIs")
        print(f"{'='*60}")
        
        apis = self.api_data[category]
        if not apis:
            print(f"No APIs found for category: {category}")
            return
        
        # Shuffle APIs to randomize order
        available_apis = apis.copy()
        random.shuffle(available_apis)
        
        target_successful_runs = min(self.max_apis_per_category, len(available_apis))
        print(f"Target: {target_successful_runs} successful runs from {len(available_apis)} available APIs")
        
        category_results = []
        successful_runs = 0
        attempted_runs = 0
        
        for api in available_apis:
            # Stop if we've reached our target successful runs
            if successful_runs >= target_successful_runs:
                break
                
            attempted_runs += 1
            api_name = api['file_name']
            api_url = self.get_api_url(api_name)
            
            if not api_url:
                print(f"  {attempted_runs:2d}. {api_name}: SKIPPED (URL not found)")
                continue
            
            print(f"  {attempted_runs:2d}. {api_name}: ", end="", flush=True)
            
            # Execute benchmark
            result = self.execute_rest_ruler(api_name, api_url)
            
            # Add API metadata to result
            result.update({
                'api_name': api_name,
                'api_url': api_url,
                'file_size_mb': api['file_size_mb'],
                'number_paths': api['number_paths'],
                'category': category
            })
            
            category_results.append(result)
            
            # Print result summary and count successful runs
            if result['success']:
                successful_runs += 1
                print(f"SUCCESS ({successful_runs}/{target_successful_runs}) - {result['execution_time']:.2f}s, "
                      f"Memory: {result['avg_memory_mb']:.1f}MB avg/{result['max_memory_mb']:.1f}MB max, "
                      f"CPU: {result['avg_cpu']:.1f}% avg/{result['max_cpu']:.1f}% max, "
                      f"Violations: {result['violation_count']}")
            else:
                print(f"FAILED - {result['stderr'][:100]}...")
            
            # Rate limiting delay
            time.sleep(1.0)
        
        print(f"\nCompleted: {successful_runs} successful runs out of {attempted_runs} attempts")
        
        # Save category results
        self.save_category_results(category, category_results)
        
        # Calculate and save statistics
        self.calculate_category_statistics(category, category_results)
        
        return category_results
    
    def save_category_results(self, category, results):
        """Save detailed results for a category"""
        category_dir = os.path.join(self.results_dir, category.replace(' ', '_'))
        os.makedirs(category_dir, exist_ok=True)
        
        # Save detailed CSV
        csv_file = os.path.join(category_dir, f"{category.replace(' ', '_')}_detailed_results.csv")
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            if results:
                writer = csv.DictWriter(f, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)
        
        # Save summary
        summary_file = os.path.join(category_dir, f"{category.replace(' ', '_')}_summary.txt")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"Benchmark Summary for {category} APIs\n")
            f.write("=" * 50 + "\n\n")
            
            successful = [r for r in results if r['success']]
            failed = [r for r in results if not r['success']]
            
            f.write(f"Total APIs tested: {len(results)}\n")
            f.write(f"Successful: {len(successful)}\n")
            f.write(f"Failed: {len(failed)}\n\n")
            
            if successful:
                f.write("Performance Statistics (Successful runs only):\n")
                f.write("-" * 40 + "\n")
                
                # Execution time stats
                times = [r['execution_time'] for r in successful]
                f.write(f"Execution Time (seconds):\n")
                f.write(f"  Min: {min(times):.2f}\n")
                f.write(f"  Max: {max(times):.2f}\n")
                f.write(f"  Mean: {statistics.mean(times):.2f}\n")
                f.write(f"  Median: {statistics.median(times):.2f}\n")
                f.write(f"  Std Dev: {statistics.stdev(times):.2f}\n\n")
                
                # Memory stats
                avg_memories = [r['avg_memory_mb'] for r in successful]
                max_memories = [r['max_memory_mb'] for r in successful]
                f.write(f"Average Memory Usage (MB):\n")
                f.write(f"  Min: {min(avg_memories):.1f}\n")
                f.write(f"  Max: {max(avg_memories):.1f}\n")
                f.write(f"  Mean: {statistics.mean(avg_memories):.1f}\n")
                f.write(f"  Median: {statistics.median(avg_memories):.1f}\n\n")
                f.write(f"Peak Memory Usage (MB):\n")
                f.write(f"  Min: {min(max_memories):.1f}\n")
                f.write(f"  Max: {max(max_memories):.1f}\n")
                f.write(f"  Mean: {statistics.mean(max_memories):.1f}\n")
                f.write(f"  Median: {statistics.median(max_memories):.1f}\n\n")
                
                # CPU stats
                avg_cpus = [r['avg_cpu'] for r in successful]
                f.write(f"Average CPU Usage (%):\n")
                f.write(f"  Min: {min(avg_cpus):.1f}\n")
                f.write(f"  Max: {max(avg_cpus):.1f}\n")
                f.write(f"  Mean: {statistics.mean(avg_cpus):.1f}\n")
                f.write(f"  Median: {statistics.median(avg_cpus):.1f}\n\n")
            
            if failed:
                f.write("Failed APIs:\n")
                f.write("-" * 20 + "\n")
                for result in failed:
                    f.write(f"  {result['api_name']}: {result['stderr'][:200]}...\n")
        
        print(f"Results saved to {category_dir}/")
    
    def calculate_category_statistics(self, category, results):
        """Calculate and save comprehensive statistics for a category"""
        successful = [r for r in results if r['success']]
        
        if not successful:
            print(f"No successful runs for category {category}")
            return
        
        # Extract metrics
        metrics = {
            'execution_time': [r['execution_time'] for r in successful],
            'avg_memory_mb': [r['avg_memory_mb'] for r in successful],
            'max_memory_mb': [r['max_memory_mb'] for r in successful],
            'avg_cpu': [r['avg_cpu'] for r in successful],
            'max_cpu': [r['max_cpu'] for r in successful],
            'violation_count': [r['violation_count'] for r in successful],
            'file_size_mb': [r['file_size_mb'] for r in successful],
            'number_paths': [r['number_paths'] for r in successful]
        }
        
        # Calculate statistics
        stats = {}
        for metric_name, values in metrics.items():
            stats[metric_name] = {
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'mean': statistics.mean(values),
                'median': statistics.median(values),
                'std_dev': statistics.stdev(values) if len(values) > 1 else 0
            }
        
        # Save statistics to CSV
        category_dir = os.path.join(self.results_dir, category.replace(' ', '_'))
        stats_file = os.path.join(category_dir, f"{category.replace(' ', '_')}_statistics.csv")
        
        with open(stats_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Count', 'Min', 'Max', 'Mean', 'Median', 'Std Dev'])
            
            for metric_name, stat in stats.items():
                writer.writerow([
                    metric_name,
                    stat['count'],
                    f"{stat['min']:.3f}",
                    f"{stat['max']:.3f}",
                    f"{stat['mean']:.3f}",
                    f"{stat['median']:.3f}",
                    f"{stat['std_dev']:.3f}"
                ])
        
        print(f"Statistics saved to {stats_file}")
    
    def generate_overall_report(self):
        """Generate overall benchmark report"""
        print(f"\n{'='*60}")
        print("Generating Overall Benchmark Report")
        print(f"{'='*60}")
        
        overall_stats = {}
        
        for category in self.categories:
            category_dir = os.path.join(self.results_dir, category.replace(' ', '_'))
            stats_file = os.path.join(category_dir, f"{category.replace(' ', '_')}_statistics.csv")
            
            if os.path.exists(stats_file):
                with open(stats_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    overall_stats[category] = {}
                    for row in reader:
                        metric = row['Metric']
                        overall_stats[category][metric] = {
                            'count': int(row['Count']),
                            'mean': float(row['Mean']),
                            'median': float(row['Median']),
                            'std_dev': float(row['Std Dev'])
                        }
        
        # Generate overall report
        report_file = os.path.join(self.results_dir, "overall_benchmark_report.md")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# REST-Ruler Performance Benchmark Report\n\n")
            f.write(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Summary by Category\n\n")
            f.write("| Category | APIs Tested | Avg Execution Time (s) | Avg Memory (MB) | Avg CPU (%) |\n")
            f.write("|----------|-------------|------------------------|----------------|-------------|\n")
            
            for category in self.categories:
                if category in overall_stats and 'execution_time' in overall_stats[category]:
                    exec_time = overall_stats[category]['execution_time']['mean']
                    memory = overall_stats[category]['avg_memory_mb']['mean'] if 'avg_memory_mb' in overall_stats[category] else 0
                    cpu = overall_stats[category]['avg_cpu']['mean'] if 'avg_cpu' in overall_stats[category] else 0
                    count = overall_stats[category]['execution_time']['count']
                    f.write(f"| {category} | {count} | {exec_time:.2f} | {memory:.1f} | {cpu:.1f} |\n")
            
            f.write("\n## Detailed Statistics\n\n")
            
            for category in self.categories:
                if category in overall_stats:
                    f.write(f"### {category.title()} APIs\n\n")
                    f.write("| Metric | Count | Mean | Median | Std Dev |\n")
                    f.write("|--------|-------|------|--------|---------|\n")
                    
                    for metric in ['execution_time', 'avg_memory_mb', 'avg_cpu', 'violation_count']:
                        if metric in overall_stats[category]:
                            stats = overall_stats[category][metric]
                            f.write(f"| {metric.replace('_', ' ').title()} | {stats['count']} | {stats['mean']:.3f} | {stats['median']:.3f} | {stats['std_dev']:.3f} |\n")
                    
                    f.write("\n")
        
        print(f"Overall report saved to {report_file}")
    
    def run_benchmark(self):
        """Run the complete benchmark across all categories"""
        print("REST-Ruler Comprehensive Performance Benchmark")
        print("=" * 60)
        print(f"Testing up to {self.max_apis_per_category} APIs per category")
        print(f"Categories: {', '.join(self.categories)}")
        print(f"Results will be saved to: {self.results_dir}")
        print()
        
        # Check if JAR file exists
        if not os.path.exists(self.jar_path):
            print(f"Error: {self.jar_path} not found!")
            return
        
        # Run benchmarks for each category
        for category in self.categories:
            self.benchmark_category(category)
        
        # Generate overall report
        self.generate_overall_report()
        
        print(f"\n{'='*60}")
        print("Benchmark completed!")
        print(f"Results saved to: {self.results_dir}")
        print(f"{'='*60}")


def main():
    """Main function"""
    benchmark = PerformanceBenchmark()
    benchmark.run_benchmark()


if __name__ == "__main__":
    main() 