import subprocess
import re
import pandas as pd
import time
import csv
import os

def file_size_smaller(name, mbs):
    df = pd.read_csv(
        "../file_size_apis_guru.csv",
        sep=",",
        encoding="utf8",
        names=["file_name", "file_size_in_mb"],
    )
    if (
        name in df["file_name"].values
        and float(df[df["file_name"] == name]["file_size_in_mb"].iloc[0]) < mbs
    ):
        print(
            "File size is smaller than 4MBs --> Value: "
            + df[df["file_name"] == name]["file_size_in_mb"].iloc[0]
            + " MB"
        )
        return True
    if name in df["file_name"].values:
        print(
            "File size is bigger than 4MBs --> Value: "
            + df[df["file_name"] == name]["file_size_in_mb"].iloc[0]
            + " MB"
        )
    else:
        print("File is not in the list")
    return False


statistic = {}
totalViolations = 0
failed = []
pattern = re.compile(r"In total \d+ rule violations were found")
skip_files = 0

# Load path counts for rate limiting
path_counts = {}
try:
    with open('../02-performance/api_information_categorisation_test.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Remove .json extension from filename to match API titles
            api_name = row['file_name'].replace('.json', '')
            path_counts[api_name] = int(row['number_paths'])
    print(f"Loaded path counts for {len(path_counts)} APIs")
    
    # Calculate total GPT requests for estimation
    total_paths = sum(path_counts.values())
    total_gpt_requests = total_paths * 2  # 2 AI rules per path
    total_tokens = len(path_counts) * 15000  # 15k tokens per API (all paths combined)
    print(f"Total paths: {total_paths:,}")
    print(f"Estimated total GPT requests: {total_gpt_requests:,}")
    print(f"Estimated total tokens: {total_tokens:,}")
    print(f"At 4000 RPM (conservative): {total_gpt_requests / 4000:.1f} minutes minimum")
    print(f"At 5000 RPM (full speed): {total_gpt_requests / 5000:.1f} minutes minimum")
    print(f"At 1.8M TPM (conservative): {total_tokens / 1800000:.1f} minutes minimum")
    
except FileNotFoundError:
    print("Warning: ../02-performance/api_information_categorisation_test.csv not found. Using default rate limiting.")
    path_counts = {}

# '~/rest-ruler/cli/'
process_cwd = ""

with open("apis_v2.csv", "r", encoding="utf8") as f:
    if f.readable():
        # ignore first line with column descriptions
        f.readline()
        line = f.readline()

        # for displaying current line number
        count = 1
        # start_index = 1206

        while line:
            # if count <= start_index:
            #     count += 1
            #     line = f.readline()
            #     continue
            
            # prepare data
            columns = line.split(";")
            title = columns[0]
            categories = columns[1]
            version = columns[2]
            url = columns[3]

            print(str(count) + " title: " + title)
            smaller = file_size_smaller(title, 4)
            count += 1
            if not smaller:
                print("File skipped because too large")
                skip_files += 1
                line = f.readline()
                continue

            current_dir = os.path.dirname(os.path.abspath(__file__))
            jar_path = os.path.join(current_dir, "rest-ruler.jar")
            process = subprocess.run(
                ["java", "-jar", jar_path, "-p", url, "-r", "-rn", title, "-llm", "-n", "camelcase"],
                cwd=current_dir,
                input=b"no",
                capture_output=True,
            )
            # process failed to finish
            if process.returncode != 0:
                failed.append((title, url, process.stderr))
                line = f.readline()
                print("Analysis FAILED for: " + title + " |" + url + "\n")
                print(process.stderr)
                print("\n")
                continue

            for outputline in process.stdout.split(b"\n"):
                if pattern.search(str(outputline)):
                    for content in outputline.split():
                        if re.search(r"\d+", str(content)):
                            statistic[title] = int(content)
                            totalViolations += int(content)

            # Calculate adaptive delay based on path count
            path_count = path_counts.get(title, 10)  # Default to 10 if not found
            gpt_requests = path_count * 2  # 2 AI rules per path
            
            # New GPT-4.1 Mini limits: 5000 RPM, 2,000,000 TPM
            # We can be much more aggressive now
            if gpt_requests > 0:
                # Conservative approach: ensure we don't exceed 4000 RPM (leaving buffer)
                delay_per_request = 60.0 / 4000  # seconds per request
                total_delay_needed = gpt_requests * delay_per_request
                
                # Add token-based delay (15k tokens per API)
                token_delay = (15000 * 60) / 1800000  # seconds for 15k tokens at 1.8M TPM
                
                # Use the longer delay (more restrictive limit)
                delay = max(0.5, total_delay_needed + 0.1, token_delay)
                
                print(f"  Paths: {path_count}, GPT requests: {gpt_requests}, Delay: {delay:.1f}s")
                time.sleep(delay)
            else:
                # No paths, minimal delay
                time.sleep(0.5)
            
            line = f.readline()


with open("ai_robustness_results.csv", "w", encoding="utf8") as outputFile:
    outputFile.write("title | number of Violations found\n")
    for key, value in statistic.items():
        outputFile.write(key + " | " + str(value) + "\n")
    # failed APIs
    outputFile.write("---------------------------------------------------\n")
    outputFile.write("failed to read following OpenAPI definitions\n")
    outputFile.write("title | url | print trace \n")
    for item in failed:
        outputFile.write(str(item[0]) + " | " + str(item[1]) + " | " + str(item[2]) + "\n")
    outputFile.write("---------------------------------------------------\n")
    outputFile.write("total APIs failed to read: " + str(len(failed)) + "\n")
    outputFile.write("---------------------------------------------------\n")
    outputFile.write(
        "total APIs skipped because of file size: " + str(skip_files) + "\n"
    )
    outputFile.write("---------------------------------------------------\n")
    outputFile.write("total Violations found: " + str(totalViolations))
