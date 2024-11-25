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

def find_closest_compute_node(G, source_node, destination_node, compute_nodes, compute_capacities, flow_size, omega, gamma):
    valid_compute_nodes = []
    
    # First, filter compute nodes that are reachable from both source and destination
    for compute_node in compute_nodes:
        try:
            # Check path from source to compute node
            path_to_compute = nx.shortest_path(G, source_node, compute_node, weight='propagation_delay')
            # Check path from compute node to destination
            path_to_dest = nx.shortest_path(G, compute_node, destination_node, weight='propagation_delay')
            
            # Calculate propagation delay from source to compute node
            delay_to_compute = sum(G[path_to_compute[i]][path_to_compute[i+1]]['propagation_delay'] 
                                 for i in range(len(path_to_compute)-1))
            
            valid_compute_nodes.append((compute_node, delay_to_compute, path_to_compute, path_to_dest))
        except nx.NetworkXNoPath:
            continue
    
    if not valid_compute_nodes:
        return None, float('inf'), []
    
    # Sort by propagation delay to source node
    valid_compute_nodes.sort(key=lambda x: x[1])
    
    # Select node with minimum propagation delay
    closest_node, _, shortest_path, path_compute_to_destination = valid_compute_nodes[0]
    
    # Calculate total delay from source to compute node
    transmission_delay = sum(flow_size / G[shortest_path[i]][shortest_path[i+1]]['bandwidth'] 
                           for i in range(len(shortest_path)-1))
    processing_delay = sum(G[shortest_path[i]][shortest_path[i+1]]['processing_delay'] 
                          for i in range(len(shortest_path)-1))
    queuing_delay = sum(G[shortest_path[i]][shortest_path[i+1]]['queuing_delay'] 
                       for i in range(len(shortest_path)-1))
    jitter = sum(G[shortest_path[i]][shortest_path[i+1]]['jitter'] 
                for i in range(len(shortest_path)-1))
    propagation_delay = sum(G[shortest_path[i]][shortest_path[i+1]]['propagation_delay'] 
                          for i in range(len(shortest_path)-1))
    
    delay_to_compute_node = propagation_delay + transmission_delay + processing_delay + queuing_delay + jitter
    
    # Calculate delay from compute node to destination
    delay_compute_to_destination = sum(
        G[path_compute_to_destination[i]][path_compute_to_destination[i+1]]['propagation_delay'] +
        G[path_compute_to_destination[i]][path_compute_to_destination[i+1]]['processing_delay'] +
        G[path_compute_to_destination[i]][path_compute_to_destination[i+1]]['queuing_delay'] +
        gamma * flow_size / G[path_compute_to_destination[i]][path_compute_to_destination[i+1]]['bandwidth'] +
        G[path_compute_to_destination[i]][path_compute_to_destination[i+1]]['jitter']
        for i in range(len(path_compute_to_destination)-1))
    
    compute_delay = omega * flow_size / compute_capacities[closest_node]
    total_delay = delay_to_compute_node + delay_compute_to_destination + compute_delay
    
    # Build complete path
    full_path = shortest_path[:-1] + path_compute_to_destination
    
    return closest_node, total_delay, full_path

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
    
    closest_node, total_delay, full_path = find_closest_compute_node(G, source_node, destination_node, compute_nodes, compute_capacities, flow_size, omega, gamma)
    
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
