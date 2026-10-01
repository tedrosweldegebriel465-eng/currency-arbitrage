"""
Historical backtesting for arbitrage detection over saved rate snapshots.
"""

import glob
import os
from datetime import datetime, timedelta
from typing import Dict, List

from .advanced_analytics import OpportunityAnalyzer
from currency_arbitrage.core.arbitrage_detector import ArbitrageDetector
from currency_arbitrage.core.currency_graph import CurrencyGraph
from currency_arbitrage.providers.data_generator import ExchangeRateGenerator
from currency_arbitrage.analytics.transaction_costs import TransactionCostModel
from currency_arbitrage.utils import ensure_directory


class HistoricalBacktester:
    """Run arbitrage analysis over historical snapshots stored as CSV matrices."""

    def __init__(self, snapshot_dir: str = "data/historical_snapshots"):
        self.snapshot_dir = ensure_directory(snapshot_dir)

    def generate_sample_snapshots(self, num_snapshots: int = 12, currencies: int = 20) -> List[str]:
        generator = ExchangeRateGenerator()
        generator.generate_currencies()
        generator.currencies = generator.currencies[:currencies]
        generator.generate_base_rates()

        created = []
        start_time = datetime.now() - timedelta(hours=num_snapshots)
        for index in range(num_snapshots):
            rates = generator.generate_complete_graph(inject_arbitrage=index % 3 == 0)
            timestamp = (start_time + timedelta(hours=index)).strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.snapshot_dir, f"snapshot_{timestamp}.csv")
            generator.save_to_csv(rates, filename)
            created.append(filename)
        return created

    def list_snapshots(self) -> List[str]:
        return sorted(glob.glob(os.path.join(self.snapshot_dir, "*.csv")))

    def _build_graph_from_snapshot(self, filename: str) -> CurrencyGraph:
        graph = CurrencyGraph()
        graph.load_from_csv(filename)
        return graph

    def run_backtest(
        self,
        source_currency: str = "USD",
        min_profit: float = 0.01,
        max_trades: int = 4,
        investment: float = 10000.0,
    ) -> Dict:
        snapshot_files = self.list_snapshots()
        if not snapshot_files:
            self.generate_sample_snapshots()
            snapshot_files = self.list_snapshots()

        cost_model = TransactionCostModel()
        timeline = []
        profitable_snapshot_count = 0
        total_ranked = 0

        for snapshot_file in snapshot_files:
            graph = self._build_graph_from_snapshot(snapshot_file)
            detector = ArbitrageDetector(graph)
            detector.detect_arbitrage(source_currency)
            analyzer = OpportunityAnalyzer(detector, cost_model)
            ranked = analyzer.rank_opportunities(
                min_profit=min_profit,
                max_trades=max_trades,
                base_currency=source_currency,
                investment=investment,
                limit=5,
            )

            profitable = len(ranked) > 0
            if profitable:
                profitable_snapshot_count += 1
            total_ranked += len(ranked)

            timeline.append(
                {
                    "snapshot": os.path.basename(snapshot_file),
                    "arbitrage_found": profitable,
                    "opportunity_count": len(ranked),
                    "best_profit_pct": ranked[0]["net_profit_pct"] if ranked else 0.0,
                    "best_risk_score": ranked[0]["risk_score"] if ranked else 0.0,
                }
            )

        frequency = profitable_snapshot_count / len(snapshot_files) if snapshot_files else 0.0
        return {
            "source_currency": source_currency,
            "snapshot_count": len(snapshot_files),
            "arbitrage_frequency": frequency,
            "profitable_snapshot_count": profitable_snapshot_count,
            "average_opportunities_per_snapshot": total_ranked / len(snapshot_files) if snapshot_files else 0.0,
            "timeline": timeline,
        }
