#!/usr/bin/env python3
"""
Currency Arbitrage Detector — main entry point.
Imports exclusively from the canonical currency_arbitrage package.
"""

import sys
import warnings

warnings.filterwarnings("ignore")

# ── Canonical package imports ─────────────────────────────────────────────────
from currency_arbitrage.core.currency_graph import CurrencyGraph
from currency_arbitrage.core.arbitrage_detector import ArbitrageDetector
from currency_arbitrage.providers.data_generator import ExchangeRateGenerator
from currency_arbitrage.providers.live_rates_api import (
    LiveExchangeRateAPI,
    SimulatedLiveRates,
    MultiProviderRateComparator,
)
from currency_arbitrage.analytics.transaction_costs import (
    TransactionCostModel,
    RealisticArbitrageAnalyzer,
)
from currency_arbitrage.analytics.export_results import ResultsExporter
from currency_arbitrage.analytics.advanced_analytics import OpportunityAnalyzer
from currency_arbitrage.analytics.historical_backtesting import HistoricalBacktester
from currency_arbitrage.analytics.report_generator import ReportGenerator
from currency_arbitrage.analytics.visualizer import GraphVisualizer
from currency_arbitrage.persistence.arbitrage_persistence import ArbitragePersistence
from currency_arbitrage.config import Config


def print_header():
    print("\n" + "=" * 70)
    print(" " * 15 + "CURRENCY ARBITRAGE DETECTOR")
    print(" " * 10 + "Bellman-Ford Algorithm | Negative Cycle Detection")
    print("=" * 70)


def quick_analysis():
    """Quick analysis with generated data."""
    print("\nRunning Quick Analysis...")
    print("-" * 50)

    try:
        generator = ExchangeRateGenerator()
        currencies = generator.generate_currencies()
        generator.generate_base_rates()

        print(f"   [OK] Generated {len(currencies)} currencies")

        rates = generator.generate_complete_graph(inject_arbitrage=True)
        print(f"   [OK] Generated {len(rates)} exchange rate pairs")
        print("   [OK] Injected synthetic arbitrage opportunities")

        print("\nBuilding Currency Graph...")
        graph = CurrencyGraph()
        for from_curr, to_curr in rates:
            graph.add_rate(from_curr, to_curr, rates[(from_curr, to_curr)])

        print(f"   [OK] Graph built: {graph}")

        print("\nRunning Bellman-Ford Algorithm...")
        detector = ArbitrageDetector(graph)
        detector.detect_arbitrage("USD")

        cycles = detector.get_profit_cycles()
        print(f"\n[OK] Found {len(cycles)} arbitrage cycles")

        if cycles:
            print("\nTOP 5 PROFITABLE CYCLES:")
            print("-" * 50)
            for i, cycle in enumerate(cycles[:5], 1):
                cycle_path = cycle["cycle"]
                if len(cycle_path) >= 3:
                    display_path = f"{cycle_path[0]} -> {cycle_path[1]} -> {cycle_path[2]}"
                    display_path += f" -> ... -> {cycle_path[0]}" if len(cycle_path) > 3 else f" -> {cycle_path[0]}"
                else:
                    display_path = " -> ".join(cycle_path) + f" -> {cycle_path[0]}"

                print(f"\n  {i}. {display_path}")
                print(f"     Gross Return: {cycle['total_product']:.6f}")
                print(f"     Profit: {cycle['profit_percent']:.4f}%")

                investment = 1000
                profit = investment * cycle["profit_percent"] / 100
                print(f"     Example: ${investment} -> ${investment + profit:.2f}")
        else:
            print("   No arbitrage cycles found with >0.01% profit")

        return detector, graph

    except Exception as e:
        print(f"\n[ERROR] in quick_analysis: {e}")
        return None, None


def live_rates_analysis():
    """Fetch and analyze live exchange rates."""
    print("\nLive Exchange Rates Analysis")
    print("-" * 50)

    try:
        print("   Fetching live exchange rates...")
        api = LiveExchangeRateAPI()
        live_rates = api.fetch_live_rates("USD")

        if not live_rates:
            print("   [WARNING] Live API failed, using simulated rates...")
            generator = ExchangeRateGenerator()
            generator.generate_currencies()
            generator.generate_base_rates()
            sim = SimulatedLiveRates(generator)
            rates = sim.get_simulated_live_rates()

            graph = CurrencyGraph()
            for from_curr, to_curr in rates:
                graph.add_rate(from_curr, to_curr, rates[(from_curr, to_curr)])
        else:
            print(f"   [OK] Fetched {len(live_rates)} live rates")
            graph = CurrencyGraph()

            for currency in list(live_rates.keys())[:25]:
                graph.add_currency(currency)

            for to_curr, rate in list(live_rates.items())[:25]:
                if rate > 0:
                    graph.add_rate("USD", to_curr, rate)
                    graph.add_rate(to_curr, "USD", 1.0 / rate)

        detector = ArbitrageDetector(graph)
        detector.detect_arbitrage("USD")

        cycles = detector.get_profit_cycles()
        print(f"\n[OK] Found {len(cycles)} arbitrage opportunities in live data")
        return detector, graph

    except Exception as e:
        print(f"   [WARNING] Error: {e}")
        print("   Falling back to quick analysis...")
        return quick_analysis()


def cost_analysis():
    """Run analysis with transaction costs."""
    print("\nRealistic Cost Analysis")
    print("-" * 50)

    detector, graph = quick_analysis()
    if detector is None:
        print("   [ERROR] Failed to initialize detector")
        return None

    cost_model = TransactionCostModel()
    analyzer = RealisticArbitrageAnalyzer(detector, cost_model)

    try:
        investment = float(input("   Enter investment amount ($) [default: 10000]: ") or "10000")
    except Exception:
        investment = 10000

    results = analyzer.analyze_with_costs(investment)
    analyzer.print_cost_analysis(results)
    return results


def gui_interface():
    """Launch GUI interface."""
    print("\nLaunching GUI Interface...")
    print("-" * 50)

    try:
        from currency_arbitrage.ui.gui_arbitrage import ArbitrageGUI

        detector, graph = quick_analysis()
        if detector is None or graph is None:
            print("   [ERROR] Failed to initialize detector for GUI")
            return

        print("   Starting GUI...")
        gui = ArbitrageGUI(detector, graph)
        gui.run()

    except ImportError as e:
        print(f"   [WARNING] GUI module not available: {e}")
        print("   Tkinter is usually pre-installed with Python")
        choice = input("\n   Run quick analysis instead? (y/n): ")
        if choice.lower() == "y":
            quick_analysis()
    except Exception as e:
        print(f"   [WARNING] GUI error: {e}")


def export_results_menu(detector):
    """Export results to various formats."""
    if detector is None:
        print("\n[ERROR] No detector available. Run quick analysis first.")
        return

    print("\nExport Results")
    print("-" * 50)
    print("  1. Export to CSV (Arbitrage Cycles)")
    print("  2. Export to CSV (Shortest Paths)")
    print("  3. Export to JSON")
    print("  4. Export to Excel (if available)")
    print("  5. Export All Formats")
    print("  6. Back to Main Menu")

    choice = input("\n   Choose export format (1-6): ")

    try:
        exporter = ResultsExporter(detector)

        if choice == "1":
            print(f"   [OK] Exported to {exporter.export_to_csv()}")
        elif choice == "2":
            print(f"   [OK] Exported to {exporter.export_shortest_paths()}")
        elif choice == "3":
            print(f"   [OK] Exported to {exporter.export_to_json()}")
        elif choice == "4":
            f = exporter.export_to_excel()
            if f:
                print(f"   [OK] Exported to {f}")
        elif choice == "5":
            files = exporter.export_all()
            print(f"   [OK] Exported {len(files)} files")
        elif choice == "6":
            return
        else:
            print("   Invalid choice")

    except Exception as e:
        print(f"   [WARNING] Export error: {e}")


def complete_analysis():
    """Run complete analysis with all features."""
    print("\nComplete Analysis (All Features)")
    print("=" * 70)

    detector, graph = quick_analysis()
    if detector is None:
        print("[ERROR] Analysis failed - cannot proceed")
        return

    print("\n" + "=" * 70)
    print("TRANSACTION COST ANALYSIS")
    print("=" * 70)

    cost_model = TransactionCostModel()
    analyzer = RealisticArbitrageAnalyzer(detector, cost_model)
    analyzer.print_cost_analysis(analyzer.analyze_with_costs(10000))

    print("\n" + "=" * 70)
    print("EXPORTING RESULTS")
    print("=" * 70)

    exporter = ResultsExporter(detector)
    files = exporter.export_all("complete_analysis")
    print(f"\n   [OK] Exported {len(files)} files:")
    for name, path in files.items():
        if path:
            print(f"     - {name}: {path}")

    print("\n" + "=" * 70)
    print("COMPLEXITY SUMMARY")
    print("=" * 70)
    print(f"   Vertices (V): {graph.get_num_currencies()}")
    print(f"   Edges (E): {graph.get_num_edges()}")
    print(f"   Time Complexity: O(V x E) = {graph.get_num_currencies() * graph.get_num_edges():,} operations")
    print(f"   Space Complexity: O(V) = {graph.get_num_currencies()} units")

    print("\n" + "=" * 70)
    print("COMPLETE ANALYSIS FINISHED!")
    print("=" * 70)


def advanced_analysis():
    """Run advanced analytics: ranking, backtesting, monitoring, reports, persistence."""
    print("\nAdvanced Arbitrage Analysis")
    print("=" * 70)

    detector, graph = quick_analysis()
    if detector is None or graph is None:
        print("[ERROR] Could not build the baseline graph.")
        return

    analyzer = OpportunityAnalyzer(detector, TransactionCostModel())
    ranked = analyzer.rank_opportunities(
        min_profit=0.01, max_trades=4, base_currency="USD",
        max_transaction_cost_pct=1.0, investment=10000, limit=5,
    )
    portfolio = analyzer.simulate_portfolio(
        starting_capital=10000, top_n=3, min_profit=0.01,
        max_trades=4, base_currency="USD", max_transaction_cost_pct=1.0,
    )

    print("\nTOP RANKED OPPORTUNITIES")
    print("-" * 50)
    if ranked:
        for index, item in enumerate(ranked, 1):
            print(f"  {index}. {' -> '.join(item['cycle'])} -> {item['cycle'][0]}")
            print(f"     Gross Profit: {item['profit_percent']:.4f}%")
            print(f"     Net Profit: {item['net_profit_pct']:.4f}%")
            print(f"     Risk Score: {item['risk_score']:.2f}")
    else:
        print("  No ranked opportunities met the filters.")

    print("\nPORTFOLIO SIMULATION")
    print("-" * 50)
    print(f"   Starting Capital: ${portfolio['starting_capital']:,.2f}")
    print(f"   Ending Capital:   ${portfolio['ending_capital']:,.2f}")
    print(f"   Net Profit:       ${portfolio['net_profit']:,.2f}")

    print("\nHISTORICAL BACKTEST")
    print("-" * 50)
    backtester = HistoricalBacktester()
    backtest_summary = backtester.run_backtest(source_currency="USD", min_profit=0.01)
    print(f"   Snapshots Analyzed: {backtest_summary['snapshot_count']}")
    print(f"   Arbitrage Frequency: {backtest_summary['arbitrage_frequency']:.2%}")
    print(f"   Avg Opportunities/Snapshot: {backtest_summary['average_opportunities_per_snapshot']:.2f}")

    provider_comparison = {"provider_rates": {}, "mismatches": []}
    try:
        comparator = MultiProviderRateComparator()
        provider_comparison = comparator.compare_provider_rates(base_currency="USD")
        from currency_arbitrage.analytics.monitoring import RealTimeArbitrageMonitor

        monitor = RealTimeArbitrageMonitor(comparator, ArbitragePersistence())
        monitor_summary = monitor.run_monitoring(
            base_currency="USD", iterations=1, interval_seconds=0,
            alert_profit_threshold=0.01, investment=10000,
        )
        print("\nMULTI-PROVIDER COMPARISON")
        print("-" * 50)
        print(f"   Providers compared: {len(provider_comparison['provider_rates'])}")
        print(f"   Mismatches found: {len(provider_comparison['mismatches'])}")
        print(f"   Monitoring alerts: {monitor_summary['opportunities_found']}")
    except Exception as e:
        print(f"\n[WARNING] Live monitoring skipped: {e}")

    graph_image = None
    try:
        vis = GraphVisualizer(graph)
        graph_image = vis.save_graph(
            highlight_cycles=[item["cycle"] for item in ranked[:3]],
            title="Ranked Arbitrage Opportunities",
        )
        print(f"\n   Saved graph visualization to {graph_image}")
    except Exception as e:
        print(f"\n[WARNING] Visualization export skipped: {e}")

    reporter = ReportGenerator()
    html_report = reporter.generate_html_report(
        backtest_summary=backtest_summary, ranked_opportunities=ranked,
        portfolio_summary=portfolio, provider_comparison=provider_comparison,
        graph_image_path=graph_image,
    )
    pdf_report = reporter.generate_pdf_report(
        backtest_summary=backtest_summary, ranked_opportunities=ranked,
        portfolio_summary=portfolio,
    )
    print("\nREPORTS")
    print("-" * 50)
    print(f"   HTML Report: {html_report}")
    print(f"   PDF Report:  {pdf_report}")


def main_menu():
    print_header()
    print("\nSelect Mode:")
    print("  1. Quick Analysis (Generated Data)")
    print("  2. Live Exchange Rates (API)")
    print("  3. Realistic Cost Analysis")
    print("  4. GUI Interface")
    print("  5. Export Results to CSV/JSON")
    print("  6. Complete Analysis (All Features)")
    print("  7. Advanced Analytics, Backtesting, and Reports")
    print("  8. Exit")
    return input("\nEnter your choice (1-8): ").strip()


def main():
    detector = None
    graph = None

    while True:
        choice = main_menu()

        if choice == "1":
            detector, graph = quick_analysis()
            input("\nPress Enter to continue...")
        elif choice == "2":
            detector, graph = live_rates_analysis()
            input("\nPress Enter to continue...")
        elif choice == "3":
            cost_analysis()
            input("\nPress Enter to continue...")
        elif choice == "4":
            gui_interface()
        elif choice == "5":
            if detector is None:
                print("\n[WARNING] No analysis data available. Running quick analysis first...")
                detector, graph = quick_analysis()
            export_results_menu(detector)
            input("\nPress Enter to continue...")
        elif choice == "6":
            complete_analysis()
            input("\nPress Enter to continue...")
        elif choice == "7":
            advanced_analysis()
            input("\nPress Enter to continue...")
        elif choice == "8":
            print("\n" + "=" * 70)
            print("Thank you for using Currency Arbitrage Detector!")
            print("   Based on Bellman-Ford Algorithm | O(VE) Complexity")
            print("=" * 70 + "\n")
            sys.exit(0)
        else:
            print("\n[ERROR] Invalid choice. Please enter 1-8")
            input("Press Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Unexpected Error: {e}")
        sys.exit(1)
