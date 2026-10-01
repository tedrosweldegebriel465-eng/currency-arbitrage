import os
import unittest

from currency_arbitrage.core.arbitrage_detector import ArbitrageDetector
from currency_arbitrage.core.currency_graph import CurrencyGraph
from currency_arbitrage.analytics.advanced_analytics import OpportunityAnalyzer
from currency_arbitrage.analytics.historical_backtesting import HistoricalBacktester
from currency_arbitrage.analytics.monitoring import RealTimeArbitrageMonitor
from currency_arbitrage.analytics.transaction_costs import TransactionCostModel
from currency_arbitrage.persistence.arbitrage_persistence import ArbitragePersistence


class StubComparator:
    def compare_provider_rates(self, base_currency="USD", providers=None):
        return {
            "base_currency": base_currency,
            "provider_rates": {
                "provider_a": {"EUR": 0.91, "GBP": 0.81, "JPY": 150.0},
                "provider_b": {"EUR": 0.89, "GBP": 0.79, "JPY": 149.0},
            },
            "mismatches": [
                {
                    "currency": "EUR",
                    "lowest_provider": "provider_b",
                    "highest_provider": "provider_a",
                    "spread_percent": 2.24,
                }
            ],
        }


class TestAdvancedFeatures(unittest.TestCase):

    def _workspace_temp_dir(self, name):
        return "data/historical_snapshots"

    def setUp(self):
        self.graph = CurrencyGraph()
        self.graph.add_rate("USD", "EUR", 0.91)
        self.graph.add_rate("EUR", "GBP", 0.92)
        self.graph.add_rate("GBP", "USD", 1.22)
        self.graph.add_rate("USD", "GBP", 0.82)
        self.graph.add_rate("GBP", "EUR", 1.07)
        self.graph.add_rate("EUR", "USD", 1.12)

        self.detector = ArbitrageDetector(self.graph)
        self.detector.detect_arbitrage("USD")

    def test_ranking_and_portfolio(self):
        analyzer = OpportunityAnalyzer(self.detector, TransactionCostModel())
        ranked = analyzer.rank_opportunities(
            min_profit=0.01, max_trades=4, base_currency="USD", limit=3
        )
        self.assertGreaterEqual(len(ranked), 1)
        self.assertIn("risk_score", ranked[0])

        portfolio = analyzer.simulate_portfolio(
            starting_capital=10000,
            top_n=2,
            min_profit=0.01,
            max_trades=4,
            base_currency="USD",
        )
        self.assertIn("ending_capital", portfolio)

    def test_backtesting_generates_snapshots(self):
        temp_dir = self._workspace_temp_dir("backtest")
        backtester = HistoricalBacktester(snapshot_dir=temp_dir)
        summary = backtester.run_backtest(source_currency="USD", min_profit=0.01)
        self.assertGreater(summary["snapshot_count"], 0)
        self.assertIn("timeline", summary)

    def test_persistence_and_monitoring(self):
        temp_dir = self._workspace_temp_dir("persistence")
        db_path = os.path.join(temp_dir, "test_history.db")
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except PermissionError:
                pass

        persistence = ArbitragePersistence(db_path=db_path)
        monitor = RealTimeArbitrageMonitor(StubComparator(), persistence)
        summary = monitor.run_monitoring(
            base_currency="USD",
            iterations=1,
            interval_seconds=0,
            alert_profit_threshold=0.01,
        )
        self.assertIn("events", summary)
        self.assertGreaterEqual(len(persistence.get_recent_runs()), 1)

        # Close the connection before attempting removal (Windows file-lock fix)
        try:
            persistence._connection.close()
        except Exception:
            pass

        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except PermissionError:
                pass  # File still locked — not a test logic failure


if __name__ == "__main__":
    unittest.main()
