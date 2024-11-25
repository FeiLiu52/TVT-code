import yaml

def expand_network(original_nodes, original_edges, compute_nodes, compute_capacities, Source_node, Dest_node):
    """
    Expand the original network into a three-layer network (C-UCL:BCL, C-CL:CL, C-DCL:ACL)
    
    :param original_nodes: List of nodes in the original network
    :param original_edges: List of edges in the original network, each edge is a tuple (source, destination, weight)
    :param compute_nodes: List of nodes with computing capabilities
    :param compute_capacities: Dictionary of computing capacities, where keys are node names and values are capacities
    :param Source_node: Source node
    :param Dest_node: Destination node
    :return: Expanded network nodes and edges
    """
    # Initialize nodes for three layers
    V_C_UCL = original_nodes.copy()
    V_C_CL = [f"{node}_2" for node in compute_nodes]
    V_C_DCL = [f"{node}_3" for node in original_nodes if node != Source_node]
    
    # Initialize expanded edge set
    expanded_edges = []
    
    # Add edges in C-UCL layer (similar to original network, but remove edges entering destination node)
    for u, v, weight in original_edges:
        if v != Dest_node:
            expanded_edges.append((u, v, weight, 'C-UCL'))
    
    # Add edges from C-UCL to C-CL, using compute node capacity as weight
    for node in compute_nodes:
        expanded_edges.append((node, f"{node}_2", {'capacity': compute_capacities[node]}, 'UCL-CL'))
    
    # Add edges from C-CL to C-DCL
    for node in compute_nodes:
        expanded_edges.append((f"{node}_2", f"{node}_3", 0, 'CL-DCL'))
    
    # Add edges in C-DCL layer
    for u, v, weight in original_edges:
        if u != Source_node and v != Source_node:
            expanded_edges.append((f"{u}_3", f"{v}_3", weight, 'C-DCL'))
    
    # Merge all nodes
    all_nodes = V_C_UCL + V_C_CL + V_C_DCL
    
    return all_nodes, expanded_edges
