'''
    Simulation the running time, end-to-end delay, memory usage, and expanded time of different algorithms (CPEG, CNE) over different network scales.
    Range of nodes: [200,2000].
    Range of edges: [2000,20000].
'''
import csv
import time
import subprocess
import sys
import statistics
import os
from network_parameters import generate_network_parameters
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

def parse_output(output, original_nodes, original_edges):
    """Parse performance metrics from algorithm output"""
    metrics = {
        'MEMORY_USAGE': None,
        'V_count': None,
        'E_count': None,
        'END_TO_END_DELAY': None,
        'RUNNING_TIME': None,
        'Network_Expansion_Time': None,
        'ORIGINAL_V_count': original_nodes,
        'ORIGINAL_E_count': original_edges
    }
    
    # Print original output
    print("Original output:")
    print(output)
    
    for line in output.split('\n'):
        line = line.strip()
        for key in metrics.keys():
            if key in line:
                try:
                    if key == 'MEMORY_USAGE':
                        parts = line.split(':')
                        if len(parts) >= 2:
                            value_str = parts[1].strip()
                            value = float(value_str.replace('MB', '').strip())
                            metrics[key] = value
                    else:
                        value = float(line.split(":")[-1].strip())
                        metrics[key] = value
                except (ValueError, IndexError) as e:
                    print(f"Failed to parse {key}: {line}, Error: {str(e)}")
                    continue
    
    # Output warning if parsing fails
    missing = [k for k, v in metrics.items() if v is None]
    if missing:
        print(f"Warning: Missing the following metrics: {missing}")
    
    return metrics

def save_detailed_results_to_csv(results, filename='expand_detailed_results.csv'):
    """Save detailed results to CSV file"""
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['Algorithm', 'Run', 'Original Nodes', 'Original Edges',
                     'Expanded Nodes', 'Expanded Edges', 'Memory Usage',
                     'End-to-End Delay', 'Running Time', 'Network Expansion Time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for name in results:
            for run, data in enumerate(results[name], 1):
                writer.writerow({
                    'Algorithm': name,
                    'Run': run,
                    'Original Nodes': data['ORIGINAL_V_count'],
                    'Original Edges': data['ORIGINAL_E_count'],
                    'Expanded Nodes': data['V_count'],
                    'Expanded Edges': data['E_count'],
                    'Memory Usage': f"{data['MEMORY_USAGE']:.2f}",
                    'End-to-End Delay': f"{data['END_TO_END_DELAY']:.4f}",
                    'Running Time': f"{data['RUNNING_TIME']:.4f}",
                    'Network Expansion Time': f"{data['Network_Expansion_Time']:.4f}"
                })

def save_summary_results_to_csv(results, network_scales, filename='expand_summary_results.csv'):
    """Save summary results to CSV file, statistics by network scale"""
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['Algorithm', 'Original Nodes', 'Original Edges',
                     'Avg Memory Usage', 'Avg Expanded Nodes', 'Avg Expanded Edges',
                     'Avg End-to-End Delay', 'Avg Running Time', 
                     'Avg Network Expansion Time', 'Valid Runs']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for name in results:
            # Organize data by network scale
            scale_results = {}
            for nodes, edges in network_scales:
                scale_results[(nodes, edges)] = {
                    'MEMORY_USAGE': [],
                    'V_count': [],
                    'E_count': [],
                    'END_TO_END_DELAY': [],
                    'RUNNING_TIME': [],
                    'Network_Expansion_Time': []
                }
            
            # Categorize results by scale
            for run_data in results[name]:
                original_nodes = run_data['ORIGINAL_V_count']
                original_edges = run_data['ORIGINAL_E_count']
                scale_key = (original_nodes, original_edges)
                
                if scale_key in scale_results:
                    for key in scale_results[scale_key]:
                        if run_data[key] is not None:
                            scale_results[scale_key][key].append(run_data[key])
            
            # Write one line of data for each scale
            for (nodes, edges), metrics in scale_results.items():
                if len(metrics['MEMORY_USAGE']) > 0:  # Only write if there are valid data
                    writer.writerow({
                        'Algorithm': name,
                        'Original Nodes': nodes,
                        'Original Edges': edges,
                        'Avg Memory Usage': f"{statistics.mean(metrics['MEMORY_USAGE']):.2f}",
                        'Avg Expanded Nodes': f"{statistics.mean(metrics['V_count']):.0f}",
                        'Avg Expanded Edges': f"{statistics.mean(metrics['E_count']):.0f}",
                        'Avg End-to-End Delay': f"{statistics.mean(metrics['END_TO_END_DELAY']):.4f}",
                        'Avg Running Time': f"{statistics.mean(metrics['RUNNING_TIME']):.4f}",
                        'Avg Network Expansion Time': f"{statistics.mean(metrics['Network_Expansion_Time']):.4f}",
                        'Valid Runs': len(metrics['MEMORY_USAGE'])
                    })

def main():
    num_runs = 500  # Number of runs for each scale
    
    # Get current file directory as base path
    BASE_PATH = Path(__file__).parent
    print(f"Current base path: {BASE_PATH}")  # Debug info

    algorithms = {
        "CPEG":  BASE_PATH / "CPEG algorithm.py",
        "CNE":   BASE_PATH / "CNE_algorithm.py",
    }

    # Verify all algorithm files exist
    for name, path in algorithms.items():
        if not path.exists():
            print(f"Warning: Algorithm file not found {name}: {path}")
        else:
            print(f"Found algorithm file {name}: {path}")
    
    network_scales = [
        (200, 2000),
        (400, 4000),
        (600, 6000),
        (800, 8000),
        (1000, 10000),
        (1200, 12000),
        (1400, 14000),
        (1600, 16000),
        (1800, 18000),
        (2000, 20000)   
    ]

    results = {name: [] for name in algorithms}
    
    for nodes, edges in network_scales:
        print(f"\nTesting network scale: Nodes {nodes}, Edges {edges}")
        
        for i in range(num_runs):
            print(f"   Executing run {i+1}...")
            
            # Generate network parameters for each test
            yaml_file_path = generate_network_parameters(nodes, edges)
            
            for name, path in algorithms.items():
                print(f"     Running {name} algorithm...")
                try:
                    output, _ = run_script(path, yaml_file_path)
                    if output is None:
                        continue
                
                    metrics = parse_output(output, nodes, edges)  # Pass the original network scale
                    if all(v is not None for v in metrics.values()):
                        print(f"     Successfully obtained all metrics")
                        results[name].append(metrics)
                    else:
                        missing = [k for k, v in metrics.items() if v is None]
                        print(f"     Warning: {name} algorithm missing the following metrics: {missing}")
                except Exception as e:
                    print(f"    {name} algorithm failed: {str(e)}")
            
            # Delete the generated network parameter file after each test
            os.remove(yaml_file_path)

    print("\nFinal comparison results:")
    for name in algorithms:
        print(f"\n{name} algorithm:")
        
        # Organize data by network scale
        scale_results = {}
        for nodes, edges in network_scales:
            scale_results[(nodes, edges)] = {
                'MEMORY_USAGE': [],
                'V_count': [],
                'E_count': [],
                'END_TO_END_DELAY': [],
                'RUNNING_TIME': [],
                'Network_Expansion_Time': [],
                'ORIGINAL_V_count': [],
                'ORIGINAL_E_count': []
            }
        
        # Categorize results by scale
        current_scale_index = 0
        for run_data in results[name]:
            nodes, edges = network_scales[current_scale_index // num_runs]
            for key in scale_results[(nodes, edges)]:
                if run_data[key] is not None:
                    scale_results[(nodes, edges)][key].append(run_data[key])
            current_scale_index += 1
        
        # Print results by scale
        for nodes, edges in network_scales:
            metrics = scale_results[(nodes, edges)]
            print(f"\n   Original network scale: Nodes {nodes}, Edges {edges}")
            print(f"     Average expanded nodes: {statistics.mean(metrics['V_count']):.0f}")
            print(f"     Average expanded edges: {statistics.mean(metrics['E_count']):.0f}")
            print(f"     Average memory usage: {statistics.mean(metrics['MEMORY_USAGE']):.2f} MB")
            print(f"     Average end-to-end delay: {statistics.mean(metrics['END_TO_END_DELAY']):.4f}")
            print(f"     Average running time: {statistics.mean(metrics['RUNNING_TIME']):.4f} seconds")
            print(f"     Average network expansion time: {statistics.mean(metrics['Network_Expansion_Time']):.4f} seconds")
            print(f"     Valid runs: {len(metrics['MEMORY_USAGE'])}/{num_runs}")

    # Save detailed results to CSV file
    save_detailed_results_to_csv(results)
    print("\nDetailed results saved to detailed_results.csv")

    # Save summary results to CSV file
    save_summary_results_to_csv(results, network_scales)
    print("Summary results saved to summary_results.csv")

if __name__ == "__main__":
    main() 