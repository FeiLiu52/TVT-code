'''
    Simulation the running time and end-to-end delay of different algorithms (MINLP, CPEG, CNE, CCN, MPCN) over different network densities.
    Range of nodes: 1000.
    Range of edges: from minimum connection to full connection.
'''
import time
import subprocess
import sys
import random
from network_parameters import generate_network_parameters
import statistics
import os
import shutil
import numpy as np
import csv
from pathlib import Path

def generate_new_parameters(num_nodes, num_edges):
    yaml_file_path = generate_network_parameters(num_nodes, num_edges)
    yaml_copy_path = yaml_file_path.replace('.yaml', '_copy.yaml')
    shutil.copy2(yaml_file_path, yaml_copy_path)
    return yaml_file_path

def run_script(script_path, yaml_file_path):
    start_time = time.time()
    result = subprocess.run([sys.executable, script_path, yaml_file_path], capture_output=True, text=True)
    end_time = time.time()
    return result.stdout, end_time - start_time

def parse_output(output):
    delay = None
    running_time = None
    
    if not output or output.isspace():
        return None, None
    
    for line in output.split('\n'):
        line = line.strip()
        if "END_TO_END_DELAY:" in line:
            try:
                delay = float(line.split(":")[-1].strip())
            except ValueError:
                pass
        
        if "RUNNING_TIME:" in line:
            try:
                running_time = float(line.split(":")[-1].strip())
            except ValueError:
                pass
    
    return delay, running_time

def save_data_to_csv(results, avg_runtimes, avg_delay_diffs):
    algorithms = list(results.keys())  # Including all algorithms, including NLP
    with open('algorithm_comparison.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Algorithm', 'Average Running Time', 'Average Delay Difference from NLP'])
        
        # First write NLP data
        nlp_runtime = statistics.mean(results['NLP']['run_times'])
        writer.writerow(['NLP', nlp_runtime, 0])  # NLP's delay difference is 0
        
        # Write other algorithms' data
        for alg, runtime, delay_diff in zip(algorithms[1:], avg_runtimes, avg_delay_diffs):
            writer.writerow([alg, runtime, delay_diff])

def main():
    num_runs = 500  # Number of runs for each scale
    num_nodes = 1000  # Fixed number of nodes
    
    # Define the sequence of edges to test
    min_edges = num_nodes - 1  # Minimum number of edges (to ensure connectivity)
    max_edges = num_nodes * (num_nodes - 1) // 2  # Maximum possible number of edges
    edge_steps = [
        # min_edges,  # Minimum connectivity
        min_edges * 2,  # Sparse network
        min_edges * 4,  # Medium density
        min_edges * 8,  # Dense
        max_edges // 2,  # High density
        max_edges  # Complete graph
    ]
    
    # Get current file directory as base path
    BASE_PATH = Path(__file__).parent
    print(f"Current base path: {BASE_PATH}")  # Debug info

    algorithms = {
        "MINLP": BASE_PATH / "MINLP.py",
        # "LP":    BASE_PATH / "LP_in_CPEG.py",
        "CPEG":  BASE_PATH / "CPEG algorithm.py",
        "CNE":   BASE_PATH / "CNE_algorithm.py",
        "CCN":   BASE_PATH / "CCN.py",
        "MPCN":  BASE_PATH / "MPCN.py"
    }

    # Verify all algorithm files exist
    for name, path in algorithms.items():
        if not path.exists():
            print(f"Warning: Algorithm file not found {name}: {path}")
        else:
            print(f"Found algorithm file {name}: {path}")
            
    results = {edges: {alg: {"run_times": [], "delays": []} for alg in algorithms} 
              for edges in edge_steps}

    for num_edges in edge_steps:
        density = round(2 * num_edges / (num_nodes * (num_nodes - 1)), 3)
        print(f"\nTesting network density: {density} (Number of edges: {num_edges})")
        
        for i in range(num_runs):
            print(f"Executing test {i+1}/{num_runs}")
            yaml_file_path = generate_new_parameters(num_nodes, num_edges)
            
            for name, path in algorithms.items():
                print(f"Running {name} algorithm...")
                try:
                    output, runtime = run_script(path, yaml_file_path)
                    if output is not None:
                        delay, _ = parse_output(output)
                        if delay is not None:
                            results[num_edges][name]["run_times"].append(runtime)
                            results[num_edges][name]["delays"].append(delay)
                    else:
                        if runtime is not None:
                            results[num_edges][name]["run_times"].append(runtime)
                except Exception as e:
                    print(f"{name} algorithm failed: {str(e)}")
            
            os.remove(yaml_file_path)

    # Save results to CSV
    with open('density_comparison.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        header = ['Network density', 'Number of edges', 'Algorithm', 'Average Running Time', 'End-to-end delay', 'Average Delay Difference from NLP', 'Successful runs']
        writer.writerow(header)
        
        for num_edges in edge_steps:
            density = round(2 * num_edges / (num_nodes * (num_nodes - 1)), 3)
            nlp_delays = results[num_edges]["NLP"]["delays"]
            
            for name in algorithms:
                run_times = results[num_edges][name]["run_times"]
                delays = results[num_edges][name]["delays"]
                success_runs = len(run_times)
                
                if success_runs > 0:
                    avg_runtime = statistics.mean(run_times)
                    if delays:  # If there are delay data
                        avg_delay = statistics.mean(delays)
                    else:
                        avg_delay = None
                        
                    if name == "NLP":
                        avg_delay_diff = 0
                    else:
                        delay_diffs = [d - n for d, n in zip(delays, nlp_delays) if d is not None and n is not None]
                        avg_delay_diff = statistics.mean(delay_diffs) if delay_diffs else float('inf')
                    
                    writer.writerow([
                        density, 
                        num_edges, 
                        name, 
                        avg_runtime, 
                        avg_delay,  # New: Add end-to-end delay
                        avg_delay_diff, 
                        success_runs
                    ])

    print("\nResults saved to density_comparison.csv")

if __name__ == "__main__":
    main()
