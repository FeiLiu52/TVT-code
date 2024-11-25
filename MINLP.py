import gurobipy as gp
from gurobipy import GRB
import yaml
from collections import defaultdict
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
    
    # Handle the case where compute_node_capacity is a list
    compute_node_capacity = data.get('compute_node_capacity', [])
    if isinstance(compute_node_capacity, list):
        if len(compute_node_capacity) == len(compute_nodes):
            compute_capacities = {str(node): capacity for node, capacity in zip(compute_nodes, compute_node_capacity)}
    if isinstance(compute_node_capacity, dict):
        compute_capacities = {str(node): capacity for node, capacity in compute_node_capacity.items()}

    source_node = str(data['source_node'])
    destination_node = str(data['destination_node'])
    
    flow_size = data.get('flow_size', 1)
    gamma = data.get('gamma', 2)
    omega = data.get('omega', 10)
    
    return nodes, edges, compute_nodes, compute_capacities, source_node, destination_node, flow_size, gamma, omega

def build_directed_graph(nodes, edges):
    graph = {node: {'in': [], 'out': []} for node in nodes}
    for u, v, edge_data in edges:
        graph[u]['out'].append((v, edge_data))
        graph[v]['in'].append((u, edge_data))
    return graph

# Get current file directory
CURRENT_DIR = os.path.dirname(__file__)
yaml_file_path = os.path.join(CURRENT_DIR, "random_network.yaml")

original_nodes, original_edges, compute_nodes, compute_capacities, source_node, destination_node, flow_size, gamma, omega = load_network_from_yaml(yaml_file_path)
M = 1000000

# Build directed graph
graph = build_directed_graph(original_nodes, original_edges)

# Create mathematical model
model = gp.Model("Network_Optimization")

# Define decision variables
f = model.addVars([(u, v) for u in graph for v, _ in graph[u]['out']], lb=0, ub=gamma * flow_size, name="f")
x = model.addVars([(u, v) for u in graph for v, _ in graph[u]['out']], vtype=GRB.BINARY, name="x")
y = model.addVars(original_nodes, vtype=GRB.BINARY, name="y")

# Set objective function
L = gp.quicksum(
    f[u,v] * x[u, v] / edge_data['bandwidth'] +
    (edge_data['propagation_delay'] + edge_data['queuing_delay'] + edge_data['processing_delay'] + edge_data['jitter']) * x[u, v]
    for u in graph for v, edge_data in graph[u]['out']
) + gp.quicksum(
    (flow_size * omega / compute_capacities[v]) * y[v]
    for v in compute_nodes
)
model.setObjective(L, GRB.MINIMIZE)

# Add constraints
# Flow out of source node equals flow_size
model.addConstr(gp.quicksum(f[source_node, v] for v, _ in graph[source_node]['out']) == flow_size)

# Flow into destination node equals gamma * flow_size
model.addConstr(gp.quicksum(f[u, destination_node] for u, _ in graph[destination_node]['in']) == gamma * flow_size)

# Flow constraints for other nodes
for v in original_nodes:
    if v != source_node and v != destination_node:        
        model.addConstr(gp.quicksum(f[v, u] for u, _ in graph[v]['out']) ==
                        y[v]*gamma*gp.quicksum(f[u, v] for u, _ in graph[v]['in']) + (1-y[v])*gp.quicksum(f[u, v] for u, _ in graph[v]['in']))

for u in graph:
    for v, _ in graph[u]['out']:
        model.addConstr(f[u, v] <= M * x[u, v])

# Compute node selection constraints
model.addConstr(gp.quicksum(y[v] for v in compute_nodes) == 1)

for v in original_nodes:
    if v not in compute_nodes:
        model.addConstr(y[v] == 0)
        
# Start time
NLP_start_time = time.time()

# Solve model
model.optimize()

# End time
NLP_end_time = time.time()

# Output results
if model.status == GRB.OPTIMAL:
    print("Optimal solution found:")
    for v in compute_nodes:
        if y[v].x > 0.5:
            processing_delay = flow_size * omega / compute_capacities[v]
            print(f"Selected compute node: {v}, Processing delay: {processing_delay:.2f}")

    path = []
    current_node = source_node
    visited = set()  # Track visited nodes
    while current_node != destination_node:
        if current_node in visited:
            print("Error: Loop detected in path")
            break
        visited.add(current_node)
        next_node = None
        for v, _ in graph[current_node]['out']:
            if x[current_node, v].x > 0.5:
                path.append((current_node, v))
                print(f"Selected link: {current_node} -> {v}, Flow: {f[current_node, v].x:.2f}")
                next_node = v
                break
        if next_node is None:
            print("Error: Cannot find next node")
            break
        current_node = next_node
    
    if current_node == destination_node:
        print(f"Path: {' -> '.join([source_node] + [p[1] for p in path])}")
    else:
        print("Valid path not found")

    print(f"Total delay: {model.objVal}")
else:
    print("Optimal solution not found")

end_to_end_delay = model.objVal
running_time = NLP_end_time - NLP_start_time

print(f"END_TO_END_DELAY:{end_to_end_delay}")
print(f"RUNNING_TIME:{running_time}")
