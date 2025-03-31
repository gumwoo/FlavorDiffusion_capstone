import json
import networkx as nx
from tqdm import tqdm

def load_graphs_from_json(filename):
    """
    Load NetworkX graphs from a JSON file.
    Each graph includes a 'type' field that distinguishes between 'ingr_comp' and 'ingr_ingr'.
    """
    with open(filename, 'r', encoding='utf-8') as f:
        subgraphs_data = json.load(f)
    
    loaded_subgraphs = []

    for subgraph_entry in tqdm(subgraphs_data, desc="Loading Subgraphs", unit="graph"):
        graph_type = subgraph_entry["type"]
        
        # Create a graph
        graph = nx.Graph()
        
        # Load nodes
        for node in subgraph_entry["nodes"]:
            graph.add_node(node["id"], **{k: v for k, v in node.items() if k != "id"})
        
        # Load edges
        for edge in subgraph_entry["edges"]:
            graph.add_edge(edge["source"], edge["target"], **{k: v for k, v in edge.items() if k not in ["source", "target"]})

        # Append as tuple (graph_type, graph)
        loaded_subgraphs.append((graph_type, graph))

    return loaded_subgraphs

input_file = "/workspace/FlavorGraph/Flavor_Diffusion/output_subgraphs/subgraphs_small.json"

subgraphs = load_graphs_from_json(input_file)

graph_type, graph = subgraphs[0]
print(f"Loaded Subgraph Type: {graph_type}")
print(f"# Nodes: {graph.number_of_nodes()}")
print(f"# Edges: {graph.number_of_edges()}")

graph_type, graph = subgraphs[1]
print(f"\nLoaded Subgraph Type: {graph_type}")
print(f"# Nodes: {graph.number_of_nodes()}")
print(f"# Edges: {graph.number_of_edges()}")
