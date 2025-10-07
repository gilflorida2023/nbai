# llmbench.py - Simplified to always use REPEATED flag
import argparse
import csv
import time
import numpy as np
import subprocess
import os
import hashlib
from pathlib import Path

def parse_list(arg, file_path):
    if file_path:
        with open(file_path, "r") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return arg.split(",")

def run_article3_script(host, url, model, summary_length):
    """Run the article3.sh script with REPEATED flag and capture its output"""
    
    # Build the command - ALWAYS pass REPEATED as the 5th parameter
    cmd = [
        "./article3.sh",
        host,
        url,
        model,
        str(summary_length),
        "REPEATED"  # Always force processing of cached content
    ]
    
    start_time = time.time()
    
    try:
        # Run the shell script
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        if result.returncode == 0:
            summary = result.stdout.strip()
            return {
                'success': True,
                'summary': summary,
                'time': elapsed_time,
                'error': None,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        else:
            return {
                'success': False,
                'summary': None,
                'time': elapsed_time,
                'error': f"Script failed with return code {result.returncode}",
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'summary': None,
            'time': 300,
            'error': "Timeout after 300 seconds",
            'stdout': '',
            'stderr': 'Timeout expired'
        }
    except Exception as e:
        return {
            'success': False,
            'summary': None,
            'time': time.time() - start_time,
            'error': f"Execution error: {str(e)}",
            'stdout': '',
            'stderr': str(e)
        }

def get_cache_info(url):
    """Get cache file information for a URL"""
    script_name = "article3"
    cache_dir = Path.home() / ".cache" / script_name
    url_hash = hashlib.md5(url.encode()).hexdigest()
    cache_file = cache_dir / f"{url_hash}.txt"
    
    cache_exists = cache_file.exists()
    cache_age = None
    
    if cache_exists:
        cache_mtime = cache_file.stat().st_mtime
        cache_age = (time.time() - cache_mtime) / 3600  # Age in hours
    
    return {
        'cache_file': str(cache_file),
        'cache_exists': cache_exists,
        'cache_age_hours': cache_age
    }

def main():
    parser = argparse.ArgumentParser(description="Benchmark Ollama models on article summarization using article3.sh")
    parser.add_argument("host", help="Ollama server host (e.g., 192.168.0.10:11434)")
    parser.add_argument("max_length", type=int, help="Summary length in characters")
    parser.add_argument("-m", "--models", help="Comma-separated list of models")
    parser.add_argument("-mf", "--model_file", help="File with model names")
    parser.add_argument("-u", "--urls", help="Comma-separated list of URLs")
    parser.add_argument("-uf", "--urls_file", help="File with URLs")
    parser.add_argument("-r", "--runs", type=int, default=3, help="Number of runs per test (default: 3)")
    args = parser.parse_args()

    # Verify article3.sh exists and is executable
    if not os.path.exists("./article3.sh"):
        print("Error: article3.sh not found in current directory")
        return 1
    
    if not os.access("./article3.sh", os.X_OK):
        print("Error: article3.sh is not executable. Run: chmod +x article3.sh")
        return 1

    models = [m for m in parse_list(args.models, args.model_file) if m and '-embedding' not in m]
    urls = parse_list(args.urls, args.urls_file)
    
    if not models:
        print("Error: No valid models provided after filtering out embedding models.")
        return 1
    
    if not urls:
        print("Error: No URLs provided.")
        return 1

    csv_file = f"article3_bench_{int(time.time())}.csv"
    
    print(f"Starting benchmark with:")
    print(f"  Host: {args.host}")
    print(f"  Models: {', '.join(models)}")
    print(f"  URLs: {', '.join(urls)}")
    print(f"  Summary length: {args.max_length} chars")
    print(f"  Runs per test: {args.runs}")
    print(f"  Output: {csv_file}")
    print()

    with open(csv_file, "w", newline="", encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "URL", "Model", "Run", "Time (s)", "Success", 
            "Summary Length", "Target Length", "Length Match", "Cache Used", 
            "Cache Age (hours)", "Error", "Summary"
        ])
        
        total_tests = len(urls) * len(models) * args.runs
        current_test = 0
        
        for url in urls:
            cache_info = get_cache_info(url)
            print(f"Testing URL: {url}")
            print(f"  Cache: {'Exists' if cache_info['cache_exists'] else 'None'}")
            if cache_info['cache_age_hours']:
                print(f"  Cache age: {cache_info['cache_age_hours']:.1f} hours")
            
            for model in models:
                print(f"  Model: {model}")
                times = []
                summaries = []
                successful_runs = 0
                
                for run in range(args.runs):
                    current_test += 1
                    print(f"    Run {run + 1}/{args.runs}...", end=" ")
                    
                    result = run_article3_script(
                        args.host, 
                        url, 
                        model, 
                        args.max_length
                    )
                    
                    times.append(result['time'])
                    
                    if result['success']:
                        summary_length = len(result['summary']) if result['summary'] else 0
                        length_match = (summary_length <= args.max_length)
                        summaries.append(result['summary'])
                        successful_runs += 1
                        status_symbol = "✓" if length_match else "⚠"
                        print(f"{status_symbol} {result['time']:.2f}s, {summary_length}/{args.max_length} chars")
                    else:
                        print(f"✗ {result['time']:.2f}s - {result['error']}")
                        summary_length = 0
                        length_match = False
                    
                    # Write individual run results
                    writer.writerow([
                        url,
                        model,
                        run + 1,
                        f"{result['time']:.2f}",
                        result['success'],
                        summary_length,
                        args.max_length,
                        length_match,
                        cache_info['cache_exists'],
                        cache_info['cache_age_hours'] or 0,
                        result['error'] or "",
                        (result['summary'] or "")[:100] + "..." if result['summary'] and len(result['summary']) > 100 else (result['summary'] or "")
                    ])
                    f.flush()  # Ensure data is written after each test
                
                # Calculate statistics for this model/url combination
                if successful_runs > 0:
                    successful_times = [times[i] for i in range(len(times)) if result['success']]
                    if successful_times:
                        mean_time = np.mean(successful_times)
                        std_time = np.std(successful_times) if len(successful_times) > 1 else 0
                        print(f"    Stats: {mean_time:.2f}s ± {std_time:.2f}s ({successful_runs}/{args.runs} successful)")
                
                print()
    
    print(f"Benchmark completed! Results saved to {csv_file}")
    
    # Print summary
    print("\n=== SUMMARY ===")
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        if rows:
            # Group by model and URL
            from collections import defaultdict
            model_stats = defaultdict(list)
            
            for row in rows:
                if row['Success'].lower() == 'true':
                    key = (row['Model'], row['URL'])
                    model_stats[key].append(float(row['Time (s)']))
            
            print("\nPerformance by Model and URL (successful runs only):")
            for (model, url), times in model_stats.items():
                if times:
                    avg_time = np.mean(times)
                    print(f"  {model:20} {url:40} {avg_time:6.2f}s avg ({len(times)} runs)")

if __name__ == "__main__":
    main()
