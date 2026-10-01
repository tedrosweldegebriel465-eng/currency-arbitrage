"""
Transaction Cost Modeling for Realistic Arbitrage
Models spreads, commissions, and slippage
"""

from typing import Dict, Tuple


class TransactionCostModel:
    """Realistic transaction cost modeling."""

    def __init__(self):
        self.bid_ask_spread = 0.0001
        self.commission_rate = 0.00005
        self.slippage_model = "linear"
        self.cost_tiers = [
            {"max": 10000, "spread": 0.0002, "commission": 0.0001},
            {"max": 100000, "spread": 0.0001, "commission": 0.00005},
            {"max": 1000000, "spread": 0.00005, "commission": 0.00002},
            {"max": float("inf"), "spread": 0.00003, "commission": 0.00001},
        ]

    def get_tier(self, amount: float) -> Dict:
        """Get cost tier based on trade amount."""
        for tier in self.cost_tiers:
            if amount <= tier["max"]:
                return tier
        return self.cost_tiers[-1]

    def calculate_spread_cost(self, rate: float, amount: float, is_buy: bool) -> float:
        """
        Calculate bid-ask spread cost.
        Buy: pay higher price (ask)
        Sell: receive lower price (bid)
        """
        tier = self.get_tier(amount)
        spread = tier["spread"]
        if is_buy:
            effective_rate = rate * (1 + spread)
        else:
            effective_rate = rate * (1 - spread)
        return effective_rate

    def calculate_commission(self, amount: float) -> float:
        """Calculate commission cost."""
        tier = self.get_tier(amount)
        return amount * tier["commission"]

    def calculate_slippage(self, amount: float, volatility: float = 0.0005) -> float:
        """
        Calculate slippage (price movement during execution).
        volatility: expected price movement during trade execution
        """
        if self.slippage_model == "linear":
            slippage = amount * volatility * (amount / 1000000)
        elif self.slippage_model == "percentage":
            slippage = amount * volatility
        else:
            slippage = amount * 0.0001

        return min(slippage, amount * 0.01)

    def calculate_total_cost(self, amount: float, num_trades: int, volatility: float = 0.0005) -> Dict:
        """Calculate total transaction costs for a cycle."""
        tier = self.get_tier(amount)
        commission = self.calculate_commission(amount) * num_trades
        slippage = self.calculate_slippage(amount, volatility) * num_trades
        spread_cost = amount * tier["spread"] * num_trades
        total_cost = commission + slippage + spread_cost

        return {
            "spread_cost": spread_cost,
            "commission": commission,
            "slippage": slippage,
            "total_cost": total_cost,
            "cost_percentage": (total_cost / amount) * 100,
            "tier": tier,
        }

    def apply_costs_to_cycle(self, cycle_rates: list, investment: float, num_trades: int) -> Tuple[float, Dict]:
        """Apply transaction costs to an arbitrage cycle."""
        gross_return = 1.0
        for rate in cycle_rates:
            gross_return *= rate

        gross_profit_pct = (gross_return - 1) * 100
        costs = self.calculate_total_cost(investment, num_trades)
        net_profit = (investment * (gross_return - 1)) - costs["total_cost"]
        net_return = (investment + net_profit) / investment

        return net_return, {
            "gross_profit_pct": gross_profit_pct,
            "net_profit_pct": (net_return - 1) * 100,
            "costs": costs,
            "is_profitable_after_costs": net_return > 1,
        }


class RealisticArbitrageAnalyzer:
    """Analyze arbitrage with realistic market conditions."""

    def __init__(self, detector, cost_model: TransactionCostModel):
        self.detector = detector
        self.cost_model = cost_model

    def analyze_with_costs(self, investment: float = 10000) -> Dict:
        """Analyze arbitrage opportunities with real costs."""
        results = {
            "profitable_cycles": [],
            "unprofitable_cycles": [],
            "best_net_profit": 0,
            "best_cycle": None,
            "summary": {},
        }

        cycles = self.detector.get_profit_cycles()
        for cycle in cycles[:50]:
            num_trades = len(cycle["cycle"])
            net_return, cost_details = self.cost_model.apply_costs_to_cycle(cycle["rates"], investment, num_trades)

            cycle_info = {
                "cycle": cycle["cycle"],
                "gross_profit_pct": cycle["profit_percent"],
                "net_profit_pct": cost_details["net_profit_pct"],
                "costs": cost_details["costs"],
                "net_return": net_return,
                "is_profitable": cost_details["is_profitable_after_costs"],
            }

            if cycle_info["is_profitable"]:
                results["profitable_cycles"].append(cycle_info)
                if cycle_info["net_profit_pct"] > results["best_net_profit"]:
                    results["best_net_profit"] = cycle_info["net_profit_pct"]
                    results["best_cycle"] = cycle_info
            else:
                results["unprofitable_cycles"].append(cycle_info)

        results["summary"] = {
            "total_cycles_analyzed": len(cycles[:50]),
            "profitable_after_costs": len(results["profitable_cycles"]),
            "unprofitable_after_costs": len(results["unprofitable_cycles"]),
            "best_net_profit_pct": results["best_net_profit"],
            "break_even_threshold": self._calculate_break_even(results),
        }
        return results

    def _calculate_break_even(self, results: Dict) -> float:
        """Calculate minimum gross profit needed to break even."""
        avg_cost_pct = 0.15
        return avg_cost_pct

    def print_cost_analysis(self, results: Dict):
        """Print detailed cost analysis."""
        print("\n" + "=" * 70)
        print("REALISTIC COST ANALYSIS")
        print("=" * 70)

        print("\nSUMMARY:")
        print(f"   Total cycles analyzed: {results['summary']['total_cycles_analyzed']}")
        print(f"   Profitable after costs: {results['summary']['profitable_after_costs']}")
        print(f"   Unprofitable after costs: {results['summary']['unprofitable_after_costs']}")
        print(f"   Best net profit: {results['summary']['best_net_profit_pct']:.4f}%")

        if results["best_cycle"]:
            best = results["best_cycle"]
            print("\nBEST CYCLE AFTER COSTS:")
            print(f"   Cycle: {' -> '.join(best['cycle'])} -> {best['cycle'][0]}")
            print(f"   Gross profit: {best['gross_profit_pct']:.4f}%")
            print(f"   Net profit: {best['net_profit_pct']:.4f}%")
            print("\n   Cost breakdown:")
            print(f"     Spread: ${best['costs']['spread_cost']:.2f}")
            print(f"     Commission: ${best['costs']['commission']:.2f}")
            print(f"     Slippage: ${best['costs']['slippage']:.2f}")
            print(f"     Total costs: ${best['costs']['total_cost']:.2f} ({best['costs']['cost_percentage']:.3f}%)")

        print("\nINSIGHT:")
        if results["summary"]["profitable_after_costs"] > 0:
            print("   [OK] Some cycles remain profitable after realistic costs!")
            print("   -> These are genuine arbitrage opportunities in theory")
        else:
            print("   [WARNING] No cycles profitable after costs")
            print("   -> Transaction costs eliminate theoretical profits")
            print("   -> Need lower costs or higher gross returns")
