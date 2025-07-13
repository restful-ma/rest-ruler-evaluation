import subprocess
import csv
import re
import os
import pandas as pd
import time
from typing import Tuple, Dict

# Get the current script's directory
current_dir = os.path.dirname(os.path.abspath(__file__))
# Navigate to the 01-robustness directory for apis.csv
apis_csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), "rest-ruler-evaluation", "01-robustness", "apis.csv")
# Navigate to the root directory for file_size_apis_guru.csv
file_size_csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), "rest-ruler-evaluation", "file_size_apis_guru.csv")

# Path to the jar file
path_to_jar = "./rest-ruler.jar"

# Pattern to match the total violations output
pattern = re.compile(r"In total \d+ rule violations were found")

# Constants
REQUIRED_SUCCESSFUL_RUNS = 20  # Number of successful runs required

def file_size_smaller(name, mbs):
    df = pd.read_csv(
        file_size_csv_path,
        sep=",",
        encoding="utf8",
        names=["file_name", "file_size_in_mb"],
    )
    if (
        name in df["file_name"].values
        and float(df[df["file_name"] == name]["file_size_in_mb"].iloc[0]) < mbs
    ):
        print(
            f"File size is smaller than {mbs}MBs --> Value: "
            + df[df["file_name"] == name]["file_size_in_mb"].iloc[0]
            + " MB"
        )
        return True
    if name in df["file_name"].values:
        print(
            f"File size is bigger than {mbs}MBs --> Value: "
            + df[df["file_name"] == name]["file_size_in_mb"].iloc[0]
            + " MB"
        )
    else:
        print("File is not in the list")
    return False

def run_analysis(url: str) -> Tuple[Dict, bool]:
    """Run analysis on a single API specification."""
    try:
        # Setup environment for the jar
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Run the jar with report generation flag
        jar_path = os.path.join(current_dir, "rest-ruler.jar")
        cmd = ["java", "-jar", jar_path, "-n", "camelcase", "-p", url, "-r"]
            
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=current_dir
        )
        
        # Get the API name from the URL
        api_name = url.split("/")[-2] if "/" in url else url
        
        # Parse the output to extract violations
        output = result.stdout
        violations = 0
        violation_details = []
        
        # Look for the violations section in the output
        if "REST API Specification Report" in output:
            # Extract the violations count
            violations_match = re.search(r"In total (\d+) rule violations were found", output)
            if violations_match:
                violations = int(violations_match.group(1))
            
            # Extract violation details from the table format
            # The violations are in a table format between "REST API Specification Report" and "In total"
            report_section = output.split("REST API Specification Report")[1].split("In total")[0]
            
            # Each violation is in a table row with | separators
            for line in report_section.split('\n'):
                if '|' in line and not line.startswith('| Line No.') and not line.startswith('| --------'):
                    parts = [p.strip() for p in line.split('|') if p.strip()]
                    if len(parts) >= 2:  # We need at least line number and path
                        violation_details.append({
                            "line_no": parts[0],
                            "path": parts[1]
                        })
        
        # Print detailed output for debugging
        print(f"\nAnalyzing {url}:")
        print("Output from jar:")
        print(output)
        print(f"Found {violations} violations")
        if violation_details:
            print("Violation details:")
            for v in violation_details:
                print(f"  Line {v['line_no']}: {v['path']}")
        
        return {
            "title": api_name,
            "url": url,
            "violations": violations,
            "output": output,
            "violation_details": violation_details
        }, True
        
    except Exception as e:
        print(f"Error analyzing {url}: {str(e)}")
        return {
            "title": url.split("/")[-2] if "/" in url else url,
            "url": url,
            "violations": 0,
            "output": str(e),
            "violation_details": []
        }, False

# Track successful runs and results
successful_runs = 0
results = []
skipped_files = 0
failed_files = []

# Read and process APIs
with open(apis_csv_path, "r", encoding="utf8") as f:
    # Skip header
    f.readline()
    
    while successful_runs < REQUIRED_SUCCESSFUL_RUNS:
        line = f.readline()
        if not line:
            print(f"Reached end of file without getting {REQUIRED_SUCCESSFUL_RUNS} successful runs")
            break
            
        # Parse API info
        columns = line.strip().split(";")
        title = columns[0]
        url = columns[3]
        
        print(f"\nProcessing {title}...")
        
        # Check file size
        if not file_size_smaller(title, 1):
            print("File skipped because too large")
            skipped_files += 1
            continue
        
        # Run analysis
        print("Running analysis...")
        result = run_analysis(url)
        if result[1]:
            results.append({
                "title": title,
                "url": url,
                "violations": result[0]["violations"],
                "output": result[0]["output"],
                "violation_details": result[0]["violation_details"],
                "line_number": successful_runs + 1
            })
            successful_runs += 1
            print(f"Successfully processed analysis for {title} ({successful_runs}/{REQUIRED_SUCCESSFUL_RUNS})")
            if result[0]["violations"] > 0:
                print(f"Found {result[0]['violations']} violations:")
                for v in result[0]["violation_details"]:
                    print(f"  - Line {v['line_no']}: {v['path']}")
        else:
            failed_files.append((title, url, result[0]["output"]))
            print(f"Analysis failed for {title}: {result[0]['output']}")

# Write results to CSV file
with open("analysis_results.csv", "w", newline="", encoding="utf8") as f:
    writer = csv.DictWriter(f, fieldnames=["api_name", "api_url", "violation_line", "violation_path"])
    writer.writeheader()
    
    # Write each violation as a separate row
    for result in results:
        if result["violations"] > 0:
            for violation in result["violation_details"]:
                writer.writerow({
                    "api_name": result["title"],
                    "api_url": result["url"],
                    "violation_line": violation["line_no"],
                    "violation_path": violation["path"]
                })
        else:
            # If no violations, write one row with empty violation fields
            writer.writerow({
                "api_name": result["title"],
                "api_url": result["url"],
                "violation_line": "",
                "violation_path": ""
            })

# Write summary
with open("analysis_summary.txt", "w", encoding="utf8") as f:
    f.write("Analysis Summary\n")
    f.write("----------------\n")
    f.write(f"Total successful runs: {successful_runs}\n")
    f.write(f"Total skipped files: {skipped_files}\n")
    
    # Count total violations
    total_violations = sum(len(r["violation_details"]) for r in results)
    
    f.write(f"Total violations found: {total_violations}\n")
    f.write(f"Total failed runs: {len(failed_files)}\n\n")
    
    if failed_files:
        f.write("Failed Runs:\n")
        f.write("------------\n")
        for title, url, error in failed_files:
            f.write(f"Title: {title}\n")
            f.write(f"URL: {url}\n")
            f.write(f"Error: {error}\n")
            f.write("----------------\n")

print(f"\nAnalysis complete.")
print(f"Successful runs: {successful_runs}")
print(f"Total violations found: {total_violations}")
print(f"Skipped {skipped_files} files due to size.")
print(f"Failed runs: {len(failed_files)}")
print("Results written to analysis_results.csv")
print("Summary written to analysis_summary.txt")
print("Individual reports have been generated for each API in the current directory.") 