import os
import networkx as nx
import matplotlib.pyplot as plt
from typing import List, Optional
import numpy as np
from currency_arbitrage.utils import ensure_directory

class GraphVisualizer:
    """Visualize currency graph and arbitrage cycles"""
    
    def __init__(self, graph):
        self.graph = graph
        self.G = nx.DiGraph()
        
    def build_networkx_graph(self):
        """Convert to NetworkX graph"""
        self.G.clear()
        
        # Add nodes
        for currency in self.graph.currencies:
            self.G.add_node(currency)
        
        # Add edges with weights
        for from_idx, to_idx, weight in self.graph.edges:
            from_curr = self.graph.get_currency_name(from_idx)
            to_curr = self.graph.get_currency_name(to_idx)
            rate = self.graph.get_rate(from_idx, to_idx)
            self.G.add_edge(from_curr, to_curr, weight=rate)
    
    def draw_graph(self, highlight_cycles: Optional[List[List[str]]] = None,
                   title: str = "Currency Exchange Graph"):
        """Draw the currency graph"""
        self.build_networkx_graph()
        
        plt.figure(figsize=(14, 10))
        
        # Layout
        pos = nx.spring_layout(self.G, k=2, iterations=50)
        
        # Draw nodes
        nx.draw_networkx_nodes(self.G, pos, node_color='lightblue', 
                               node_size=2000, alpha=0.7)
        
        # Draw edges
        nx.draw_networkx_edges(self.G, pos, edge_color='gray', 
                               arrows=True, arrowsize=15, alpha=0.5)
        
        # Draw labels
        nx.draw_networkx_labels(self.G, pos, font_size=10, font_weight='bold')
        
        # Highlight arbitrage cycles if provided
        if highlight_cycles:
            for cycle in highlight_cycles:
                cycle_edges = [(cycle[i], cycle[i+1]) for i in range(len(cycle)-1)]
                cycle_edges.append((cycle[-1], cycle[0]))
                nx.draw_networkx_edges(self.G, pos, edgelist=cycle_edges,
                                       edge_color='red', width=3, arrows=True)
        
        plt.title(title, fontsize=16, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()
        plt.show()
    
    def draw_arbitrage_cycle(self, cycle: List[str], rates: List[float]):
        """Draw a specific arbitrage cycle"""
        plt.figure(figsize=(10, 8))
        
        # Create cycle subgraph
        cycle_graph = nx.DiGraph()
        for i in range(len(cycle) - 1):
            cycle_graph.add_edge(cycle[i], cycle[i+1], rate=rates[i])
        cycle_graph.add_edge(cycle[-1], cycle[0], rate=rates[-1])
        
        # Layout in a circle
        pos = nx.circular_layout(cycle_graph)
        
        # Draw
        nx.draw_networkx_nodes(cycle_graph, pos, node_color='lightgreen',
                               node_size=3000, alpha=0.8)
        nx.draw_networkx_edges(cycle_graph, pos, edge_color='blue',
                               width=2, arrows=True, arrowsize=20)
        nx.draw_networkx_labels(cycle_graph, pos, font_size=12, font_weight='bold')
        
        # Add edge labels (exchange rates)
        edge_labels = {(u, v): f"{d['rate']:.4f}" for u, v, d in cycle_graph.edges(data=True)}
        nx.draw_networkx_edge_labels(cycle_graph, pos, edge_labels, font_size=9)
        
        # Calculate total profit
        total = np.prod(rates)
        profit = (total - 1) * 100
        
        plt.title(f"Arbitrage Cycle - Profit: {profit:.2f}%", 
                  fontsize=14, fontweight='bold', color='green' if profit > 0 else 'red')
        plt.axis('off')
        plt.show()

    def save_graph(self, highlight_cycles: Optional[List[List[str]]] = None,
                   title: str = "Currency Exchange Graph",
                   output_path: str = "output/network_graph.png"):
        """Save a graph/network image for reports and dashboards."""
        self.build_networkx_graph()
        output_dir = os.path.dirname(output_path) or "output"
        ensure_directory(output_dir)

        plt.figure(figsize=(14, 10))
        pos = nx.spring_layout(self.G, k=2, iterations=50)
        nx.draw_networkx_nodes(self.G, pos, node_color='lightblue', node_size=2000, alpha=0.7)
        nx.draw_networkx_edges(self.G, pos, edge_color='gray', arrows=True, arrowsize=15, alpha=0.5)
        nx.draw_networkx_labels(self.G, pos, font_size=10, font_weight='bold')

        if highlight_cycles:
            for cycle in highlight_cycles:
                cycle_edges = [(cycle[i], cycle[i + 1]) for i in range(len(cycle) - 1)]
                if cycle:
                    cycle_edges.append((cycle[-1], cycle[0]))
                nx.draw_networkx_edges(
                    self.G,
                    pos,
                    edgelist=cycle_edges,
                    edge_color='red',
                    width=3,
                    arrows=True
                )

        plt.title(title, fontsize=16, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        return output_path
