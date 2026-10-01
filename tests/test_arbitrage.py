import unittest

from currency_arbitrage.core.arbitrage_detector import ArbitrageDetector
from currency_arbitrage.core.currency_graph import CurrencyGraph
from currency_arbitrage.providers.data_generator import ExchangeRateGenerator


class TestArbitrageDetector(unittest.TestCase):

    def setUp(self):
        self.graph_no_arbitrage = self._create_fair_graph()
        self.graph_with_arbitrage = self._create_arbitrage_graph()

    def _create_fair_graph(self):
        graph = CurrencyGraph()
        graph.add_currency("USD")
        graph.add_currency("EUR")
        graph.add_currency("GBP")
        graph.add_currency("JPY")

        rates_usd = {"EUR": 0.85, "GBP": 0.73, "JPY": 110.5}
        for curr, rate in rates_usd.items():
            graph.add_rate("USD", curr, rate)
            graph.add_rate(curr, "USD", 1 / rate)

        graph.add_rate("EUR", "GBP", rates_usd["GBP"] / rates_usd["EUR"])
        graph.add_rate("GBP", "EUR", rates_usd["EUR"] / rates_usd["GBP"])
        graph.add_rate("EUR", "JPY", rates_usd["JPY"] / rates_usd["EUR"])
        graph.add_rate("JPY", "EUR", rates_usd["EUR"] / rates_usd["JPY"])
        graph.add_rate("GBP", "JPY", rates_usd["JPY"] / rates_usd["GBP"])
        graph.add_rate("JPY", "GBP", rates_usd["GBP"] / rates_usd["JPY"])
        return graph

    def _create_arbitrage_graph(self):
        graph = self._create_fair_graph()
        graph.add_rate("USD", "EUR", 0.86)
        graph.add_rate("EUR", "GBP", 0.88)
        graph.add_rate("GBP", "USD", 1.34)
        return graph

    def test_detect_arbitrage_true(self):
        detector = ArbitrageDetector(self.graph_with_arbitrage)
        self.assertTrue(detector.detect_arbitrage("USD"))

    def test_detect_arbitrage_false(self):
        detector = ArbitrageDetector(self.graph_no_arbitrage)
        self.assertFalse(detector.detect_arbitrage("USD"))

    def test_get_profit_cycles(self):
        detector = ArbitrageDetector(self.graph_with_arbitrage)
        detector.detect_arbitrage("USD")
        cycles = detector.get_profit_cycles()
        self.assertGreater(len(cycles), 0)
        for cycle in cycles:
            self.assertIn("cycle", cycle)
            self.assertIn("profit_percent", cycle)
            self.assertGreater(cycle["profit_percent"], 0)

    def test_shortest_paths(self):
        detector = ArbitrageDetector(self.graph_no_arbitrage)
        distances, paths = detector.get_shortest_paths("USD")
        self.assertEqual(len(distances), self.graph_no_arbitrage.get_num_currencies())
        usd_idx = self.graph_no_arbitrage.currency_to_idx["USD"]
        self.assertEqual(distances[usd_idx], 0)

    def test_profit_calculation_accuracy(self):
        detector = ArbitrageDetector(self.graph_with_arbitrage)
        detector.detect_arbitrage("USD")
        for cycle_info in detector.get_profit_cycles():
            self.assertGreater(cycle_info["total_product"], 1.0)
            self.assertGreater(cycle_info["profit_percent"], 0)
            product = 1.0
            for rate in cycle_info["rates"]:
                product *= rate
            self.assertAlmostEqual(product, cycle_info["total_product"], places=6)


class TestDataGenerator(unittest.TestCase):

    def test_currency_generation(self):
        gen = ExchangeRateGenerator()
        currencies = gen.generate_currencies()
        self.assertIsNotNone(currencies)
        self.assertGreater(len(currencies), 0)

    def test_rate_generation(self):
        gen = ExchangeRateGenerator()
        gen.generate_currencies()
        gen.generate_base_rates()
        self.assertGreater(gen.generate_rate("USD", "EUR"), 0)

    def test_arbitrage_injection(self):
        gen = ExchangeRateGenerator()
        gen.generate_currencies()
        gen.generate_base_rates()
        cycle, modifications = gen.inject_arbitrage_cycle(3)
        self.assertEqual(len(cycle), 4)
        self.assertEqual(len(modifications), 1)

    def test_complete_graph_generation(self):
        gen = ExchangeRateGenerator()
        gen.generate_currencies()
        rates = gen.generate_complete_graph(inject_arbitrage=True)
        n = len(gen.currencies)
        self.assertEqual(len(rates), n * (n - 1))


if __name__ == "__main__":
    unittest.main()
