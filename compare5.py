'''
    Simulation the running time and end-to-end delay of different algorithms (MINLP, CPEG, CNE, CCN, MPCN) over different network densities.
    Range of nodes: 1000.
    Range of edges: [5000,50000].
'''
import csv
import time
import subprocess
import sys
from network_parameters import generate_network_parameters
import statistics
import os
import shutil
from pathlib import Path
    
def generate_network_parameters_with_scale(nodes, edges):
    yaml_file_path = generate_network_parameters(nodes, edges)
    yaml_copy_path = f'network_parameters_n{nodes}_e{edges}.yaml'
    shutil.copy2(yaml_file_path, yaml_copy_path)
    os.remove(yaml_file_path)
    return yaml_copy_path

def run_script(script_path, yaml_file_path):
    start_time = time.time()
    result = subprocess.run([sys.executable, script_path, yaml_file_path], capture_output=True, text=True)
    end_time = time.time()
    return result.stdout, end_time - start_time

def parse_output(output):
    delay = None
    running_time = None
    
    for line in output.split('\n'):
        if line.startswith("END_TO_END_DELAY:"):
            try:
                delay = float(line.split(":")[-1].strip())
            except ValueError:
                print(f"Unable to parse end-to-end delay: {line}")
        
        if line.startswith("RUNNING_TIME:"):
            try:
                running_time = float(line.split(":")[-1].strip())
            except ValueError:
                print(f"Unable to parse running time: {line}")
    
    if delay is None:
        print("End-to-end delay not found")
    if running_time is None:
        print("Running time not found")
    
    if delay is None or running_time is None:
        print("Complete output:")
        print(output)
    
    return delay, running_time

def save_detailed_results_to_csv(results, filename='detailed_results.csv'):
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['Algorithm', 'Nodes', 'Edges', 'Run', 'Run Time', 'Delay']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for name in results:
            for (nodes, edges), data in results[name].items():
                for run, (run_time, delay) in enumerate(zip(data["run_times"], data["delays"]), 1):
                    writer.writerow({
                        'Algorithm': name,
                        'Nodes': nodes,
                        'Edges': edges,
                        'Run': run,
                        'Run Time': f"{run_time:.4f}",
                        'Delay': f"{delay:.4f}"
                    })

def save_summary_results_to_csv(results, filename='density8i_results.csv'):
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['Algorithm', 'Nodes', 'Edges', 'Avg Run Time', 'Avg Delay', 'Valid Runs']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for name in results:
            for (nodes, edges), data in results[name].items():
                avg_run_time = statistics.mean(data["run_times"]) if data["run_times"] else 0
                avg_delay = statistics.mean(data["delays"]) if data["delays"] else 0
                valid_runs = len(data["run_times"])
                
                writer.writerow({
                    'Algorithm': name,
                    'Nodes': nodes,
                    'Edges': edges,
                    'Avg Run Time': f"{avg_run_time:.4f}",
                    'Avg Delay': f"{avg_delay:.4f}",
                    'Valid Runs': valid_runs
                })

def main():
    num_runs = 500  # Number of runs for each scale
    
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

    network_scales = [
        (1000, 5000),
        (1000, 10000),
        (1000, 15000),
        (1000, 20000),
        (1000, 25000),
        (1000, 30000),
        (1000, 35000),
        (1000, 40000),
        (1000, 45000),
        (1000, 50000)
    ]

    results = {name: {scale: {"run_times": [], "delays": []} for scale in network_scales} for name in algorithms}

    for nodes, edges in network_scales:
        print(f"\nTesting network scale: Nodes {nodes}, Edges {edges}")
        
        yaml_file_path = generate_network_parameters(nodes, edges)
        
        for i in range(num_runs):
            print(f"   Executing test {i+1}...")
            
            for name, path in algorithms.items():
                print(f"     Running {name} algorithm...")
                try:
                    output, _ = run_script(path, yaml_file_path)
                    delay, running_time = parse_output(output)
                    if delay is not None and running_time is not None:
                        results[name][(nodes, edges)]["run_times"].append(running_time)
                        results[name][(nodes, edges)]["delays"].append(delay)
                    else:
                        print(f"      {name} algorithm did not return valid delay or running time")
                except Exception as e:
                    print(f"      {name} algorithm failed: {str(e)}")
        
        os.remove(yaml_file_path)

    print("\nFinal comparison results:")
    for name in algorithms:
        print(f"\n{name} algorithm:")
        for nodes, edges in network_scales:
            avg_run_time = statistics.mean(results[name][(nodes, edges)]["run_times"]) if results[name][(nodes, edges)]["run_times"] else 0
            avg_delay = statistics.mean(results[name][(nodes, edges)]["delays"]) if results[name][(nodes, edges)]["delays"] else 0
            print(f"  Network scale (Nodes: {nodes}, Edges: {edges}):")
            print(f"    Average running time = {avg_run_time:.4f} seconds")
            print(f"    Average end-to-end delay = {avg_delay:.4f}")
            print(f"    Valid runs: {len(results[name][(nodes, edges)]['run_times'])}/{num_runs}")

    # Save detailed results to CSV file
    save_detailed_results_to_csv(results)
    print("\nDetailed results saved to detailed_results.csv")

    # Save summary results to CSV file
    save_summary_results_to_csv(results)
    print("Summary results saved to summary_results.csv")

if __name__ == "__main__":
    main()
