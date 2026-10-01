import math
from typing import List, Tuple, Optional
from currency_arbitrage.utils import timer


class BellmanFord:
    """Bellman-Ford algorithm implementation"""

    def __init__(self, num_vertices: int):
        self.V = num_vertices
        self.dist: List[float] = []
        self.prev: List[int] = []
        self.has_negative_cycle = False
        self.cycle_nodes: List[int] = []

    @timer
    def find_shortest_paths(self, edges: List[Tuple[int, int, float]], source: int) -> Tuple[List[float], List[int]]:
        """
        Find shortest paths from source using Bellman-Ford
        Returns: (distances, predecessors)
        """
        self.dist = [float("inf")] * self.V
        self.prev = [-1] * self.V
        self.dist[source] = 0

        for i in range(self.V - 1):
            relaxed = False
            for u, v, w in edges:
                if self.dist[u] != float("inf") and self.dist[u] + w < self.dist[v]:
                    self.dist[v] = self.dist[u] + w
                    self.prev[v] = u
                    relaxed = True

            if not relaxed:
                print(f"   Converged after {i + 1} iterations")
                break

        self.has_negative_cycle = False
        self.cycle_nodes = set()

        for u, v, w in edges:
            if self.dist[u] != float("inf") and self.dist[u] + w < self.dist[v] - 0.000001:
                self.has_negative_cycle = True
                self.cycle_nodes.add(v)

        if self.has_negative_cycle:
            print(f"   [WARNING] Negative cycle detected! {len(self.cycle_nodes)} nodes affected")

        return self.dist, self.prev

    def get_path_to(self, target: int, max_length: int = 100) -> List[int]:
        """Reconstruct path to target node with safety limit"""
        if self.dist[target] == float("inf"):
            return []

        path = []
        current = target
        visited = set()

        while current != -1 and len(path) < max_length:
            if current in visited:
                break
            visited.add(current)
            path.append(current)
            current = self.prev[current]

        return path[::-1]

    def get_negative_cycles(self, edges: List[Tuple[int, int, float]], currency_names: List[str]) -> List[List[str]]:
        """Extract all negative cycles"""
        if not self.has_negative_cycle:
            return []

        cycles = []
        visited_nodes = set()

        for node in list(self.cycle_nodes)[:5]:
            if node in visited_nodes:
                continue

            cycle = self._find_cycle(node, currency_names)
            if cycle and len(cycle) <= 10:
                cycles.append(cycle)
                visited_nodes.update(cycle)

        return cycles

    def _find_cycle(self, start_node: int, currency_names: List[str]) -> List[str]:
        """Find cycle containing start_node with safety limits"""
        visited_in_path = {}
        current = start_node
        path = []
        max_steps = self.V * 2

        steps = 0
        while current not in visited_in_path and steps < max_steps:
            visited_in_path[current] = len(path)
            path.append(current)
            current = self.prev[current]
            if current == -1:
                return []
            steps += 1

        if current in visited_in_path:
            cycle_start_idx = visited_in_path[current]
            cycle_indices = path[cycle_start_idx:]
            return [currency_names[i] for i in cycle_indices if i < len(currency_names)]

        return []
