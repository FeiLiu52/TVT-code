import yaml
import networkx as nx
import matplotlib.pyplot as plt
from CPEG import expand_network
import time
from pympler import asizeof
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
    
    # Handle the case where compute_node_capacity is a list
    compute_node_capacity = data.get('compute_node_capacity', [])
    if isinstance(compute_node_capacity, list):
        if len(compute_node_capacity) == len(compute_nodes):
            compute_capacities = {str(node): capacity for node, capacity in zip(compute_nodes, compute_node_capacity)}
        else:
            print("Warning: compute_node_capacity list length doesn't match compute_nodes. Using default capacity 1.")
            compute_capacities = {node: 1 for node in compute_nodes}
    elif isinstance(compute_node_capacity, dict):
        compute_capacities = {str(node): capacity for node, capacity in compute_node_capacity.items()}
    else:
        print("Warning: Invalid compute_node_capacity format. Using default capacity 1.")
        compute_capacities = {node: 1 for node in compute_nodes}
    
    source_node = str(data['source_node'])
    destination_node = str(data['destination_node'])
    
    flow_size = data.get('flow_size', 1)
    gamma = data.get('gamma', 2)
    omega = data.get('omega', 10)
    
    return nodes, edges, compute_nodes, compute_capacities, source_node, destination_node, flow_size, gamma, omega

def d_uv(u, v, layer, edge_data):
    # Check if edge_data is a dictionary
    if not isinstance(edge_data, dict):
        # print(f"Warning: edge_data is not a dictionary. u={u}, v={v}, layer={layer}, edge_data={edge_data}")
        return 0  # or return a default value
    
    if layer == 'C-UCL':
        transmission_delay = flow_size / edge_data.get('bandwidth', 1)
        non_transmission_delay = (edge_data.get('propagation_delay', 0) + 
                                  edge_data.get('processing_delay', 0) + 
                                  edge_data.get('queuing_delay', 0) + 
                                  edge_data.get('jitter', 0))
        return transmission_delay + non_transmission_delay
    elif layer == 'C-DCL':
        transmission_delay = gamma * flow_size / edge_data.get('bandwidth', 1)
        non_transmission_delay = (edge_data.get('propagation_delay', 0) + 
                                  edge_data.get('processing_delay', 0) + 
                                  edge_data.get('queuing_delay', 0) + 
                                  edge_data.get('jitter', 0))
        return transmission_delay + non_transmission_delay
    elif layer == 'UCL-CL':
        compute_node = v.split('_')[0]  # Get the original name of compute node
        compute_capacity = compute_capacities.get(compute_node, 1)  # Get the computing capacity of the node
        computing_delay = omega * flow_size / compute_capacity
        return computing_delay
    elif layer == 'CL-DCL':
        return 0
    else:
        return 0  # Other cases

# Get current file directory
CURRENT_DIR = os.path.dirname(__file__)
yaml_file_path = os.path.join(CURRENT_DIR, "random_network.yaml")

original_nodes, original_edges, compute_nodes, compute_capacities, source_node, destination_node, flow_size, gamma, omega = load_network_from_yaml(yaml_file_path)

# Expand network
expansion_start_time = time.time()
V, E = expand_network(original_nodes, original_edges, compute_nodes, compute_capacities, source_node, destination_node)

# Create NetworkX graph
G = nx.DiGraph()

# Add nodes and edges, using d_uv as weight
for u, v, edge_data, layer in E:
    weight = d_uv(u, v, layer, edge_data)
    G.add_edge(u, v, weight=weight, layer=layer)
expansion_end_time = time.time()

# Calculate and output key metrics immediately
total_size = asizeof.asizeof(G)
print(f"MEMORY_USAGE:{total_size/(1024*1024) :.2f} MB")  # Convert to MB
print(f"V_count:{len(G.nodes())}")
print(f"E_count:{len(G.edges())}")

                    
# Find shortest path
dest_node_dcl = destination_node + '_3'  # Destination node in DCL layer

# Start timing
EGCAN_start_time = time.time()

shortest_path = nx.dijkstra_path(G, source_node, dest_node_dcl, weight='weight')

# End timing
EGCAN_end_time = time.time()

# Calculate total path weight
path_weight = sum(G[shortest_path[i]][shortest_path[i+1]]['weight'] for i in range(len(shortest_path)-1))

# Print results
print(f"Shortest path: {' -> '.join(shortest_path)}")

end_to_end_delay = path_weight
running_time = EGCAN_end_time - EGCAN_start_time

print(f"END_TO_END_DELAY:{end_to_end_delay}")
print(f"RUNNING_TIME:{running_time}")
print(f"Network_Expansion_Time: {expansion_end_time - expansion_start_time}")
