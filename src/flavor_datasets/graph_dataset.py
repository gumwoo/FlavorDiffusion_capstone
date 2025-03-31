import os
import torch
import numpy as np
from torch.utils.data import Dataset
from torch_geometric.data import Data as GraphData
from torch_geometric.data import DataLoader as GraphDataLoader
import networkx as nx
from tqdm import tqdm
import json

def load_graphs_from_json(filename):
    """
    Load NetworkX graphs from a JSON file.
    """
    with open(filename, 'r', encoding='utf-8') as f:
        subgraphs_data = json.load(f)
    
    loaded_subgraphs = []

    for subgraph_entry in tqdm(subgraphs_data, desc="Loading Subgraphs", unit="graph"):
        graph_type = subgraph_entry["type"]
        graph = nx.Graph()
        
        # Load nodes
        for node in subgraph_entry["nodes"]:
            graph.add_node(node["id"], **{k: v for k, v in node.items() if k != "id"})
        
        # Load edges
        for edge in subgraph_entry["edges"]:
            weight = edge.get("weight", 1.0)  # Default weight = 1.0 if not provided
            graph.add_edge(edge["source"], edge["target"], weight=weight)

        loaded_subgraphs.append((graph_type, graph))

    return loaded_subgraphs

class GraphDataset(Dataset):
    def __init__(self, data_file):
        """
        Graph dataset that can return adjacency matrices in dense format.

        :param data_file: Path to the JSON file containing graphs.
        """
        
        self.data_file = data_file
        self.subgraphs = load_graphs_from_json(self.data_file)

    def __len__(self):
        return len(self.subgraphs)

    def __getitem__(self, idx):
        graph_type, graph = self.subgraphs[idx]

        # **Extract node features (Node ID directly used)**
        node_list = list(graph.nodes())
        node_features = torch.tensor(node_list, dtype=torch.long)

        # Extract edges
        node_id_to_idx = {node_id: i for i, node_id in enumerate(node_list)}

        edge_list = list(graph.edges(data=True))
        num_nodes = node_features.shape[0]

        adj_matrix = torch.zeros((num_nodes, num_nodes), dtype=torch.float32)
        for e in edge_list:
            node_i, node_j = node_id_to_idx[e[0]], node_id_to_idx[e[1]]
            weight = e[2].get("weight", 1.0)
            adj_matrix[node_i, node_j] = weight
            adj_matrix[node_j, node_i] = weight  # Since it's undirected

        return (
            torch.LongTensor([idx]),  # Graph Index (real_batch_idx)
            node_features,  # Node features (IDs)
            adj_matrix  # Dense Adjacency Matrix
        )
