from typing import Dict, List, Tuple

from currency_arbitrage.core.bellman_ford import BellmanFord
from currency_arbitrage.core.currency_graph import CurrencyGraph
from currency_arbitrage.utils import timer


class ArbitrageDetector:
    """Detect and analyze arbitrage opportunities."""

    def __init__(self, graph: CurrencyGraph):
        self.graph = graph
        self.bf = BellmanFord(graph.get_num_currencies())
        self.arbitrage_cycles: List[List[str]] = []

    @timer
    def detect_arbitrage(self, source_currency: str = None) -> bool:
        """
        Detect arbitrage opportunities in the graph.
        Returns: True if arbitrage exists.
        """
        if source_currency:
            source_idx = self.graph.currency_to_idx[source_currency]
            return self._check_from_source(source_idx)

        for i in range(min(3, self.graph.get_num_currencies())):
            if self._check_from_source(i):
                return True
        return False

    def _check_from_source(self, source_idx: int) -> bool:
        """Check for arbitrage starting from a specific source."""
        distances, predecessors = self.bf.find_shortest_paths(self.graph.edges, source_idx)

        if self.bf.has_negative_cycle:
            self.arbitrage_cycles = self.bf.get_negative_cycles(self.graph.edges, self.graph.currencies)
            return True
        return False

    def get_profit_cycles(self) -> List[Dict]:
        """Get detailed information about profitable cycles."""
        if not self.arbitrage_cycles:
            self._populate_simple_cycles()

        results = self._build_profit_cycle_results(self.arbitrage_cycles)
        if not results:
            results = self._find_profitable_triangles()
        return results

    def _build_profit_cycle_results(self, cycles: List[List[str]]) -> List[Dict]:
        """Convert cycle paths into detailed profit records."""
        results = []

        for cycle in cycles[:5]:
            if len(cycle) < 2:
                continue

            rates = []
            total_product = 1.0

            for i in range(len(cycle) - 1):
                from_c = cycle[i]
                to_c = cycle[i + 1]
                if from_c in self.graph.currency_to_idx and to_c in self.graph.currency_to_idx:
                    rate = self.graph.get_rate(
                        self.graph.currency_to_idx[from_c],
                        self.graph.currency_to_idx[to_c],
                    )
                    if rate:
                        rates.append(rate)
                        total_product *= rate

            if cycle:
                last_rate = self.graph.get_rate(
                    self.graph.currency_to_idx[cycle[-1]],
                    self.graph.currency_to_idx[cycle[0]],
                )
                if last_rate:
                    rates.append(last_rate)
                    total_product *= last_rate

            profit_percent = (total_product - 1) * 100

            if profit_percent > 0.01:
                results.append(
                    {
                        "cycle": cycle,
                        "rates": rates,
                        "total_product": total_product,
                        "profit_percent": profit_percent,
                        "is_profitable": profit_percent > 0,
                    }
                )

        return results

    def _find_profitable_triangles(self) -> List[Dict]:
        """Brute-force fallback for 3-currency cycles."""
        results = []
        currencies = self.graph.currencies

        for i in range(len(currencies)):
            for j in range(len(currencies)):
                if j == i:
                    continue
                for k in range(len(currencies)):
                    if k == i or k == j:
                        continue

                    rate1 = self.graph.get_rate(i, j)
                    rate2 = self.graph.get_rate(j, k)
                    rate3 = self.graph.get_rate(k, i)
                    if not (rate1 and rate2 and rate3):
                        continue

                    total_product = rate1 * rate2 * rate3
                    profit_percent = (total_product - 1) * 100
                    if profit_percent > 0.01:
                        results.append(
                            {
                                "cycle": [currencies[i], currencies[j], currencies[k]],
                                "rates": [rate1, rate2, rate3],
                                "total_product": total_product,
                                "profit_percent": profit_percent,
                                "is_profitable": True,
                            }
                        )

        results.sort(key=lambda item: item["profit_percent"], reverse=True)
        return results[:5]

    def _populate_simple_cycles(self):
        """Fallback search for simple triangular cycles when extraction is sparse."""
        currencies = self.graph.currencies
        found_cycles = []

        for i in range(len(currencies)):
            for j in range(len(currencies)):
                if j == i:
                    continue
                for k in range(len(currencies)):
                    if k == i or k == j:
                        continue

                    rate1 = self.graph.get_rate(i, j)
                    rate2 = self.graph.get_rate(j, k)
                    rate3 = self.graph.get_rate(k, i)

                    if rate1 and rate2 and rate3 and (rate1 * rate2 * rate3) > 1.0001:
                        cycle = [currencies[i], currencies[j], currencies[k]]
                        if cycle not in found_cycles:
                            found_cycles.append(cycle)

        if found_cycles:
            self.arbitrage_cycles = found_cycles[:5]

    def find_simple_arbitrage(self, max_length: int = 4, min_profit: float = 0.1):
        """
        Find simple arbitrage cycles (triangular arbitrage).

        Args:
            max_length: Maximum cycle length (3 or 4)
            min_profit: Minimum profit percentage to display
        """
        print("\nSEARCHING FOR SIMPLE ARBITRAGE CYCLES")
        print("-" * 50)

        currencies = self.graph.currencies
        found = False

        if max_length >= 3:
            print("\n  Checking Triangular Arbitrage (3-currency cycles)...")
            for i in range(len(currencies)):
                for j in range(len(currencies)):
                    if i == j:
                        continue
                    for k in range(len(currencies)):
                        if k == i or k == j:
                            continue

                        rate1 = self.graph.get_rate(i, j)
                        rate2 = self.graph.get_rate(j, k)
                        rate3 = self.graph.get_rate(k, i)

                        if rate1 and rate2 and rate3:
                            total = rate1 * rate2 * rate3
                            profit = (total - 1) * 100

                            if profit > min_profit:
                                found = True
                                print(f"\n  TRIANGULAR ARBITRAGE #{len(self.get_profit_cycles()) + 1}")
                                print(f"     Cycle: {currencies[i]} -> {currencies[j]} -> {currencies[k]} -> {currencies[i]}")
                                print(f"     Rates: {rate1:.6f} x {rate2:.6f} x {rate3:.6f} = {total:.8f}")
                                print(f"     PROFIT: {profit:.4f}%")
                                print(f"     Example: $1000 -> ${1000 * total:.2f} (${1000 * (total - 1):.2f} profit)")

        if max_length >= 4:
            print("\n  Checking 4-Currency Arbitrage Cycles...")
            count = 0
            for i in range(len(currencies)):
                for j in range(len(currencies)):
                    if j == i:
                        continue
                    for k in range(len(currencies)):
                        if k == i or k == j:
                            continue
                        for l in range(len(currencies)):
                            if l == i or l == j or l == k:
                                continue

                            rate1 = self.graph.get_rate(i, j)
                            rate2 = self.graph.get_rate(j, k)
                            rate3 = self.graph.get_rate(k, l)
                            rate4 = self.graph.get_rate(l, i)

                            if rate1 and rate2 and rate3 and rate4:
                                total = rate1 * rate2 * rate3 * rate4
                                profit = (total - 1) * 100

                                if profit > min_profit and count < 5:
                                    found = True
                                    count += 1
                                    print(f"\n  4-CURRENCY ARBITRAGE #{count}")
                                    print(
                                        f"     Cycle: {currencies[i]} -> {currencies[j]} -> "
                                        f"{currencies[k]} -> {currencies[l]} -> {currencies[i]}"
                                    )
                                    print(f"     Total Return: {total:.8f}")
                                    print(f"     PROFIT: {profit:.4f}%")

        if not found:
            print(f"\n  No simple arbitrage cycles found with >{min_profit}% profit")
            print("     (Try running with inject_arbitrage=True or lower min_profit)")

        return found

    def find_best_arbitrage(self, investment: float = 1000) -> Dict:
        """
        Find the most profitable arbitrage cycle.

        Args:
            investment: Amount to invest

        Returns:
            Dictionary with best arbitrage opportunity
        """
        print("\nFINDING BEST ARBITRAGE OPPORTUNITY")
        print("-" * 50)

        best_profit = 0
        best_cycle = None
        best_rates = None

        currencies = self.graph.currencies
        n = len(currencies)

        for i in range(n):
            for j in range(n):
                if j == i:
                    continue
                for k in range(n):
                    if k == i or k == j:
                        continue

                    rate1 = self.graph.get_rate(i, j)
                    rate2 = self.graph.get_rate(j, k)
                    rate3 = self.graph.get_rate(k, i)

                    if rate1 and rate2 and rate3:
                        total = rate1 * rate2 * rate3
                        profit_pct = (total - 1) * 100

                        if profit_pct > best_profit:
                            best_profit = profit_pct
                            best_cycle = [currencies[i], currencies[j], currencies[k]]
                            best_rates = [rate1, rate2, rate3]

        if best_cycle:
            final_amount = investment * (1 + best_profit / 100)
            print("\n  MOST PROFITABLE CYCLE FOUND:")
            print(f"     Cycle: {best_cycle[0]} -> {best_cycle[1]} -> {best_cycle[2]} -> {best_cycle[0]}")
            print(f"     Rates: {best_rates[0]:.6f} x {best_rates[1]:.6f} x {best_rates[2]:.6f}")
            print(f"     Total Return: {(1 + best_profit / 100):.8f}")
            print(f"     PROFIT: {best_profit:.4f}%")
            print(f"\n     Investment: ${investment:,.2f}")
            print(f"     Final amount: ${final_amount:,.2f}")
            print(f"     Net profit: ${final_amount - investment:,.2f}")

            return {
                "cycle": best_cycle,
                "rates": best_rates,
                "profit_percent": best_profit,
                "final_amount": final_amount,
                "profit_amount": final_amount - investment,
            }

        print("  No profitable cycles found")
        return None

    def get_shortest_paths(self, source_currency: str) -> Tuple[List[float], List[List[str]]]:
        """Get shortest paths from source to all currencies."""
        source_idx = self.graph.currency_to_idx[source_currency]
        distances, predecessors = self.bf.find_shortest_paths(self.graph.edges, source_idx)
        distances = [0.0 if abs(value) < 1e-12 else value for value in distances]

        paths = []
        for i in range(self.graph.get_num_currencies()):
            if distances[i] != float("inf"):
                path = self._reconstruct_path_safe(predecessors, source_idx, i)
                paths.append(
                    [
                        self.graph.get_currency_name(idx)
                        for idx in path
                        if idx < len(self.graph.currencies)
                    ]
                )
            else:
                paths.append([])

        return distances, paths

    def _reconstruct_path_safe(self, predecessors: List[int], source: int, target: int, max_length: int = 50) -> List[int]:
        """Reconstruct path from source to target safely without infinite loops."""
        path = []
        current = target
        visited = set()

        while current != -1 and current != source and len(path) < max_length:
            if current in visited:
                break
            visited.add(current)
            path.append(current)
            current = predecessors[current]

        if current == source:
            path.append(source)

        return path[::-1]
