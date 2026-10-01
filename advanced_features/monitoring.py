"""
Real-time monitoring loop for arbitrage opportunities.
"""

import time
from statistics import median
from typing import Dict, List, Optional

from .advanced_analytics import OpportunityAnalyzer
from currency_arbitrage.core.arbitrage_detector import ArbitrageDetector
from currency_arbitrage.core.currency_graph import CurrencyGraph
from .persistence import ArbitragePersistence
from currency_arbitrage.analytics.transaction_costs import TransactionCostModel


class RealTimeArbitrageMonitor:
    """Continuously poll providers and alert when profitable opportunities appear."""

    def __init__(self, comparator, persistence: Optional[ArbitragePersistence] = None):
        self.comparator = comparator
        self.persistence = persistence or ArbitragePersistence()

    def _aggregate_rates(self, provider_rates: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        merged = {}
        all_symbols = set()
        for rates in provider_rates.values():
            all_symbols.update(rates.keys())

        for symbol in all_symbols:
            values = [rates[symbol] for rates in provider_rates.values() if symbol in rates]
            if values:
                merged[symbol] = median(values)
        return merged

    def _build_graph(self, base_currency: str, rates: Dict[str, float]) -> CurrencyGraph:
        graph = CurrencyGraph()
        graph.add_currency(base_currency)
        for to_currency, rate in rates.items():
            if rate <= 0:
                continue
            graph.add_rate(base_currency, to_currency, rate)
            graph.add_rate(to_currency, base_currency, 1.0 / rate)

        currencies = list(graph.currencies)
        for from_curr in currencies:
            if from_curr == base_currency:
                continue
            for to_curr in currencies:
                if to_curr in (base_currency, from_curr):
                    continue
                from_rate = rates.get(from_curr)
                to_rate = rates.get(to_curr)
                if from_rate and to_rate:
                    graph.add_rate(from_curr, to_curr, to_rate / from_rate)
        return graph

    def run_monitoring(
        self,
        base_currency: str = "USD",
        providers: Optional[List[str]] = None,
        iterations: int = 3,
        interval_seconds: int = 2,
        alert_profit_threshold: float = 0.1,
        investment: float = 10000.0,
    ) -> Dict:
        providers = providers or ["exchangerate-api", "frankfurter"]
        events = []
        opportunities_found = 0

        for _ in range(iterations):
            comparison = self.comparator.compare_provider_rates(base_currency=base_currency, providers=providers)
            provider_rates = comparison["provider_rates"]
            aggregated_rates = self._aggregate_rates(provider_rates)

            for provider, rates in provider_rates.items():
                self.persistence.save_snapshot(provider, base_currency, rates)

            graph = self._build_graph(base_currency, aggregated_rates)
            detector = ArbitrageDetector(graph)
            detector.detect_arbitrage(base_currency)
            analyzer = OpportunityAnalyzer(detector, TransactionCostModel())
            ranked = analyzer.rank_opportunities(
                min_profit=alert_profit_threshold,
                base_currency=base_currency,
                investment=investment,
                limit=5,
            )

            alert = len(ranked) > 0
            if alert:
                opportunities_found += len(ranked)

            events.append(
                {
                    "timestamp": time.time(),
                    "alert": alert,
                    "top_opportunities": ranked,
                    "provider_mismatches": comparison["mismatches"][:5],
                }
            )

            if interval_seconds > 0:
                time.sleep(interval_seconds)

        summary = {
            "base_currency": base_currency,
            "iterations": iterations,
            "providers": providers,
            "opportunities_found": opportunities_found,
            "events": events,
        }
        run_id = self.persistence.save_monitor_run(base_currency, alert_profit_threshold, summary)
        latest_opportunities = events[-1]["top_opportunities"] if events else []
        self.persistence.save_opportunities(run_id, "aggregated", latest_opportunities)
        return summary
