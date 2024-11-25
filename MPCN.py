import yaml
import networkx as nx
import matplotlib.pyplot as plt
import time
import os
from pathlib import Path

def load_network_from_yaml(file_path):
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    
    nodes = [str(node) for node in data['nodes']]
    edges = [(str(edge['source']), str(edge['destination']), {
        'bandwidth': edge['bandwidth'],
        'propagation_delay': edge['propagation_delay'],
        'processing_delay': edge['processing_delay'],
        'queuing_delay': edge['queuing_delay'],
        'jitter': edge['jitter']
    }) for edge in data['edges']]
    compute_nodes = [str(node) for node in data.get('compute_nodes', [])]
    
    compute_capacities = data.get('compute_node_capacity', {})
    if isinstance(compute_capacities, list):
        compute_capacities = {str(node): capacity for node, capacity in zip(compute_nodes, compute_capacities)}
    elif isinstance(compute_capacities, dict):
        compute_capacities = {str(node): capacity for node, capacity in compute_capacities.items()}
    else:
        compute_capacities = {node: 1 for node in compute_nodes}
    
    source_node = str(data['source_node'])
    destination_node = str(data['destination_node'])
    
    flow_size = data.get('flow_size', 1)
    gamma = data.get('gamma', 2)
    omega = data.get('omega', 10)
    
    return nodes, edges, compute_nodes, compute_capacities, source_node, destination_node, flow_size, gamma, omega

def find_max_capacity_compute_node(G, source_node, destination_node, compute_nodes, compute_capacities, flow_size, omega, gamma):
    # Find compute node with maximum capacity
    max_capacity_node = max(compute_capacities.items(), key=lambda x: x[1])[0]
    
    try:
        # Use Dijkstra's algorithm to find shortest path from source to compute node
        path_to_compute = nx.shortest_path(G, source_node, max_capacity_node, weight=lambda u, v, d: (
            d['propagation_delay'] + 
            d['processing_delay'] + 
            d['queuing_delay'] + 
            flow_size / d['bandwidth'] + 
            d['jitter']
        ))
        
        # Use Dijkstra's algorithm to find shortest path from compute node to destination
        path_to_dest = nx.shortest_path(G, max_capacity_node, destination_node, weight=lambda u, v, d: (
            d['propagation_delay'] + 
            d['processing_delay'] + 
            d['queuing_delay'] + 
            gamma * flow_size / d['bandwidth'] + 
            d['jitter']
        ))
        
        # Calculate total delay from source to compute node
        delay_to_compute = sum(
            G[path_to_compute[i]][path_to_compute[i+1]]['propagation_delay'] +
            G[path_to_compute[i]][path_to_compute[i+1]]['processing_delay'] +
            G[path_to_compute[i]][path_to_compute[i+1]]['queuing_delay'] +
            flow_size / G[path_to_compute[i]][path_to_compute[i+1]]['bandwidth'] +
            G[path_to_compute[i]][path_to_compute[i+1]]['jitter']
            for i in range(len(path_to_compute)-1))
        
        # Calculate delay from compute node to destination
        delay_to_dest = sum(
            G[path_to_dest[i]][path_to_dest[i+1]]['propagation_delay'] +
            G[path_to_dest[i]][path_to_dest[i+1]]['processing_delay'] +
            G[path_to_dest[i]][path_to_dest[i+1]]['queuing_delay'] +
            gamma * flow_size / G[path_to_dest[i]][path_to_dest[i+1]]['bandwidth'] +
            G[path_to_dest[i]][path_to_dest[i+1]]['jitter']
            for i in range(len(path_to_dest)-1))
        
        # Calculate processing delay at compute node
        compute_delay = omega * flow_size / compute_capacities[max_capacity_node]
        
        # Calculate total delay
        total_delay = delay_to_compute + delay_to_dest + compute_delay
        
        # Build complete path
        full_path = path_to_compute[:-1] + path_to_dest
        
        return max_capacity_node, total_delay, full_path
        
    except nx.NetworkXNoPath:
        return None, float('inf'), []

def main():
    # Get current file directory
    CURRENT_DIR = os.path.dirname(__file__)
    yaml_file_path = os.path.join(CURRENT_DIR, "random_network.yaml")

    nodes, edges, compute_nodes, compute_capacities, source_node, destination_node, flow_size, gamma,omega = load_network_from_yaml(yaml_file_path)

    G = nx.DiGraph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)
    
    # Start time
    the_closest_start_time = time.time()
    
    closest_node, total_delay, full_path = find_max_capacity_compute_node(G, source_node, destination_node, compute_nodes, compute_capacities, flow_size, omega, gamma)
    
    # End time
    the_closest_end_time = time.time()
    
    if closest_node:
        print(f"Closest compute node: {closest_node}")
        print(f"Shortest path: {' -> '.join(full_path)}")
    else:
        print("No reachable compute node found")
    
    end_to_end_delay = total_delay
    running_time = the_closest_end_time - the_closest_start_time

    print(f"END_TO_END_DELAY:{end_to_end_delay}")
    print(f"RUNNING_TIME:{running_time}")

if __name__ == "__main__":
    main()
