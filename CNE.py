# Computing Node Extended algorithm
def expand_network(original_nodes, original_edges, compute_nodes, compute_capacities, Source_node, Dest_node):
    num_copies = len(compute_nodes)
    expanded_nodes = original_nodes.copy()
    expanded_edges = []
    
    # Add original edges
    for u, v, weight in original_edges:
        expanded_edges.append((u, v, weight, 'original'))
    
    # Create copied networks
    for i in range(1, num_copies + 1):
        for node in original_nodes:
            if node != Source_node:
                expanded_nodes.append(f"{node}_{i}")
        
        for u, v, weight in original_edges:
            if u != Source_node and v != Source_node:
                expanded_edges.append((f"{u}_{i}", f"{v}_{i}", weight, 'copied'))
    
    # Add computing edges (virtual edges)
    for i, compute_node in enumerate(compute_nodes, 1):
        expanded_edges.append((compute_node, f"{compute_node}_{i}", {'capacity': compute_capacities[compute_node]}, 'compute'))
    
    # Create super destination node
    super_dest = f"{Dest_node}_Super_Dest"
    expanded_nodes.append(super_dest)
    
    # Connect all destination nodes in copied networks to super destination node
    for i in range(1, num_copies + 1):
        expanded_edges.append((f"{Dest_node}_{i}", super_dest, 0, 'aggregate'))
    
    return expanded_nodes, expanded_edges, super_dest