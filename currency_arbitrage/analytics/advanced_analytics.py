"""
Advanced analytics for filtering, scoring, ranking, and portfolio simulation.
"""

from typing import Dict, List, Optional

from currency_arbitrage.analytics.transaction_costs import TransactionCostModel


class OpportunityAnalyzer:
    """Analyze arbitrage opportunities beyond raw profit percentage."""

    def __init__(self, detector, cost_model: Optional[TransactionCostModel] = None):
        self.detector = detector
        self.cost_model = cost_model or TransactionCostModel()

    def filter_cycles(
        self,
        cycles: Optional[List[Dict]] = None,
        min_profit: float = 0.0,
        max_trades: Optional[int] = None,
        base_currency: Optional[str] = None,
        max_transaction_cost_pct: Optional[float] = None,
        investment: float = 10000.0,
    ) -> List[Dict]:
        cycles = cycles if cycles is not None else self.detector.get_profit_cycles()
        filtered = []

        for cycle in cycles:
            trade_count = len(cycle["cycle"])
            if cycle["profit_percent"] < min_profit:
                continue
            if max_trades is not None and trade_count > max_trades:
                continue
            if base_currency and base_currency not in cycle["cycle"]:
                continue

            cost_info = self.cost_model.calculate_total_cost(investment, trade_count)
            if max_transaction_cost_pct is not None and cost_info["cost_percentage"] > max_transaction_cost_pct:
                continue

            enriched = dict(cycle)
            enriched["trade_count"] = trade_count
            enriched["estimated_cost_percentage"] = cost_info["cost_percentage"]
            filtered.append(enriched)

        return filtered

    def score_cycle(
        self,
        cycle: Dict,
        investment: float = 10000.0,
        volatility: float = 0.0005,
        execution_delay_ms: int = 250,
        liquidity_score: Optional[float] = None,
    ) -> Dict:
        trade_count = len(cycle["cycle"])
        net_return, cost_details = self.cost_model.apply_costs_to_cycle(cycle["rates"], investment, trade_count)

        if liquidity_score is None:
            liquidity_score = max(0.35, 1.0 - (trade_count - 2) * 0.12)

        volatility_penalty = min(35.0, volatility * 100000)
        latency_penalty = min(20.0, execution_delay_ms / 75.0)
        cost_penalty = min(30.0, cost_details["costs"]["cost_percentage"] * 8.0)
        liquidity_bonus = liquidity_score * 20.0
        profitability_bonus = max(0.0, cost_details["net_profit_pct"] * 6.0)

        score = max(
            0.0,
            min(
                100.0,
                50.0 + profitability_bonus + liquidity_bonus - volatility_penalty - latency_penalty - cost_penalty,
            ),
        )

        scored = dict(cycle)
        scored.update(
            {
                "net_profit_pct": cost_details["net_profit_pct"],
                "risk_score": round(score, 2),
                "volatility_penalty": round(volatility_penalty, 2),
                "latency_penalty": round(latency_penalty, 2),
                "liquidity_score": round(liquidity_score * 100.0, 2),
                "cost_breakdown": cost_details["costs"],
                "net_return_multiple": net_return,
            }
        )
        return scored

    def rank_opportunities(
        self,
        min_profit: float = 0.0,
        max_trades: Optional[int] = None,
        base_currency: Optional[str] = None,
        max_transaction_cost_pct: Optional[float] = None,
        investment: float = 10000.0,
        limit: int = 10,
    ) -> List[Dict]:
        filtered = self.filter_cycles(
            min_profit=min_profit,
            max_trades=max_trades,
            base_currency=base_currency,
            max_transaction_cost_pct=max_transaction_cost_pct,
            investment=investment,
        )
        ranked = [self.score_cycle(cycle, investment=investment) for cycle in filtered]
        ranked.sort(key=lambda item: (item["risk_score"], item["net_profit_pct"]), reverse=True)
        return ranked[:limit]

    def simulate_portfolio(
        self,
        starting_capital: float = 10000.0,
        top_n: int = 3,
        rebalance_equal: bool = True,
        **ranking_filters,
    ) -> Dict:
        ranked = self.rank_opportunities(limit=top_n, investment=starting_capital, **ranking_filters)
        if not ranked:
            return {
                "starting_capital": starting_capital,
                "ending_capital": starting_capital,
                "net_profit": 0.0,
                "positions": [],
            }

        allocation = starting_capital / len(ranked) if rebalance_equal else starting_capital
        positions = []
        ending_capital = 0.0

        for cycle in ranked:
            invested_amount = allocation if rebalance_equal else starting_capital / len(ranked)
            final_amount = invested_amount * cycle["net_return_multiple"]
            positions.append(
                {
                    "cycle": cycle["cycle"],
                    "invested_amount": invested_amount,
                    "final_amount": final_amount,
                    "net_profit": final_amount - invested_amount,
                    "net_profit_pct": cycle["net_profit_pct"],
                    "risk_score": cycle["risk_score"],
                }
            )
            ending_capital += final_amount

        return {
            "starting_capital": starting_capital,
            "ending_capital": ending_capital,
            "net_profit": ending_capital - starting_capital,
            "positions": positions,
        }
