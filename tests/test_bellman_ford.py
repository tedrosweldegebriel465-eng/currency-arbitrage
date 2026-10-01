import unittest

from currency_arbitrage.core.bellman_ford import BellmanFord
from currency_arbitrage.core.currency_graph import CurrencyGraph
from currency_arbitrage.core.arbitrage_detector import ArbitrageDetector


class TestBellmanFord(unittest.TestCase):

    def setUp(self):
        self.graph = CurrencyGraph()
        self.graph.add_currency("USD")
        self.graph.add_currency("EUR")
        self.graph.add_currency("GBP")

        self.graph.add_rate("USD", "EUR", 0.85)
        self.graph.add_rate("EUR", "GBP", 0.86)
        self.graph.add_rate("GBP", "USD", 1.37)
        self.graph.add_rate("EUR", "USD", 1.176)
        self.graph.add_rate("GBP", "EUR", 1.163)
        self.graph.add_rate("USD", "GBP", 0.73)

    def test_initialization(self):
        bf = BellmanFord(3)
        self.assertEqual(bf.V, 3)
        self.assertFalse(bf.has_negative_cycle)

    def test_shortest_path_no_arbitrage(self):
        bf = BellmanFord(self.graph.get_num_currencies())
        distances, _ = bf.find_shortest_paths(self.graph.edges, 0)
        self.assertNotEqual(distances[0], float("inf"))
        self.assertNotEqual(distances[1], float("inf"))
        self.assertNotEqual(distances[2], float("inf"))

    def test_negative_cycle_detection(self):
        arb_graph = CurrencyGraph()
        arb_graph.add_currency("A")
        arb_graph.add_currency("B")
        arb_graph.add_currency("C")
        arb_graph.add_rate("A", "B", 2.0)
        arb_graph.add_rate("B", "C", 2.0)
        arb_graph.add_rate("C", "A", 0.3)  # product = 1.2 > 1

        bf = BellmanFord(3)
        bf.find_shortest_paths(arb_graph.edges, 0)
        self.assertTrue(bf.has_negative_cycle)

    def test_path_reconstruction(self):
        bf = BellmanFord(3)
        edges = [(0, 1, 1.0), (1, 2, 2.0)]
        bf.find_shortest_paths(edges, 0)
        self.assertEqual(bf.get_path_to(2), [0, 1, 2])

    def test_convergence_early_stop(self):
        bf = BellmanFord(4)
        edges = [(0, 1, 1.0), (1, 2, 1.0), (2, 3, 1.0)]
        bf.find_shortest_paths(edges, 0)
        self.assertEqual(bf.dist[3], 3.0)

    def test_infinity_distances(self):
        bf = BellmanFord(4)
        distances, _ = bf.find_shortest_paths([(0, 1, 1.0)], 0)
        self.assertEqual(distances[0], 0)
        self.assertEqual(distances[1], 1.0)
        self.assertEqual(distances[2], float("inf"))
        self.assertEqual(distances[3], float("inf"))


class TestArbitrageDetection(unittest.TestCase):

    def test_triangular_arbitrage(self):
        graph = CurrencyGraph()
        for c in ["USD", "EUR", "GBP"]:
            graph.add_currency(c)
        graph.add_rate("USD", "EUR", 0.86)
        graph.add_rate("EUR", "GBP", 0.88)
        graph.add_rate("GBP", "USD", 1.34)
        detector = ArbitrageDetector(graph)
        self.assertTrue(detector.detect_arbitrage("USD"))

    def test_no_arbitrage(self):
        graph = CurrencyGraph()
        graph.add_currency("USD")
        graph.add_currency("EUR")
        graph.add_rate("USD", "EUR", 0.85)
        graph.add_rate("EUR", "USD", 1.176)
        detector = ArbitrageDetector(graph)
        self.assertFalse(detector.detect_arbitrage("USD"))


if __name__ == "__main__":
    unittest.main()
