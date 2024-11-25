import yaml
import random
import os
from pathlib import Path

def read_nodes(lines):
    return [int(line.strip()) for line in lines if line.strip() and not line.startswith('#')]

def generate_random_network(num_nodes, num_edges):
    edges = []
    while len(edges) < num_edges:
        source = random.randint(1, num_nodes - 1)
        dest = random.randint(1, num_nodes - 1)
        if source != dest and (source, dest) not in edges:
            edges.append((source, dest))

    # Create lists of source and destination nodes (duplicates allowed)
    source_nodes = [edge[0] for edge in edges]
    destination_nodes = [edge[1] for edge in edges]

    return source_nodes, destination_nodes

def generate_network_parameters(num_nodes, num_edges):
    
    s, d = generate_random_network(num_nodes, num_edges)

    # Get all unique nodes
    all_nodes = list(set(s + d))
    total_nodes = len(all_nodes)

    # Calculate number of nodes to select (about 60%)
    num_selected_nodes = int(total_nodes * 0.6)

    # Randomly select compute nodes
    compute_nodes = random.sample(all_nodes, num_selected_nodes)

    # Select source and destination nodes (not in compute nodes)
    non_compute_nodes = list(set(all_nodes) - set(compute_nodes))
    if len(non_compute_nodes) < 2:
        raise ValueError("Not enough non-compute nodes to select source and destination nodes")
    
    source_node, destination_node = random.sample(non_compute_nodes, 2)

    # Create YAML data structure
    data = {
        'source_node': source_node,
        'destination_node': destination_node,
        'flow_size': random.randint(100, 1000),
        'gamma': 2,
        'omega': 10,
        'nodes': all_nodes,
        'compute_nodes': compute_nodes,
        'compute_node_capacity': [],
        'edges': [],
    }

    # Add properties for each edge
    for source, dest in zip(s, d):
        edge = {
            'source': source,
            'destination': dest,
            'bandwidth': random.randint(1000, 5000),  # Mbps
            'propagation_delay': round(random.uniform(1, 5), 2),  # ms
            'processing_delay': round(random.uniform(0.1,0.5), 2),  # ms
            'queuing_delay': round(random.uniform(0, 5), 2),  # ms
            'jitter': round(random.uniform(0, 2), 2),  # ms
            'loss': round(random.uniform(0.001, 0.01), 3)  # packet loss rate
        }
        data['edges'].append(edge)

    for computing_node in data['compute_nodes']:
        data['compute_node_capacity'].append(random.randint(10000, 100000))  

    # Get current file directory
    CURRENT_DIR = os.path.dirname(__file__)
    yaml_file_path = os.path.join(CURRENT_DIR, "random_network.yaml")

    with open(yaml_file_path, 'w') as file:
        yaml.dump(data, file, default_flow_style=False,sort_keys=False)

    print("YAML file has been generated with detailed edge properties, including s and d.")
    return yaml_file_path

if __name__ == "__main__":
    generate_network_parameters()
