"""
Generate HTML and PDF reports with charts and opportunity summaries.
"""

import os
from datetime import datetime
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from currency_arbitrage.utils import ensure_directory


class ReportGenerator:
    """Render compact reports for advanced arbitrage analysis."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = ensure_directory(output_dir)

    def _timeline_chart(self, backtest_summary: Dict) -> str:
        timeline = backtest_summary.get("timeline", [])
        labels = [item["snapshot"][-10:-4] for item in timeline]
        values = [item["best_profit_pct"] for item in timeline]

        chart_path = os.path.join(self.output_dir, "backtest_timeline.png")
        plt.figure(figsize=(10, 4))
        plt.plot(labels, values, marker="o", color="#1f77b4")
        plt.title("Best Net Profit by Snapshot")
        plt.xlabel("Snapshot")
        plt.ylabel("Net Profit %")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(chart_path)
        plt.close()
        return chart_path

    def generate_html_report(
        self,
        backtest_summary: Dict,
        ranked_opportunities: List[Dict],
        portfolio_summary: Dict,
        provider_comparison: Dict,
        graph_image_path: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> str:
        filename = filename or f"arbitrage_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        path = os.path.join(self.output_dir, filename)
        chart_path = self._timeline_chart(backtest_summary)

        rows = "".join(
            [
                "<tr>"
                f"<td>{' -> '.join(item['cycle'])}</td>"
                f"<td>{item['profit_percent']:.4f}%</td>"
                f"<td>{item['net_profit_pct']:.4f}%</td>"
                f"<td>{item['risk_score']:.2f}</td>"
                "</tr>"
                for item in ranked_opportunities
            ]
        )

        mismatch_rows = "".join(
            [
                "<tr>"
                f"<td>{item['currency']}</td>"
                f"<td>{item['lowest_provider']}</td>"
                f"<td>{item['highest_provider']}</td>"
                f"<td>{item['spread_percent']:.4f}%</td>"
                "</tr>"
                for item in provider_comparison.get("mismatches", [])[:10]
            ]
        )

        graph_section = ""
        if graph_image_path:
            graph_section = f"<div class='card'><h2>Graph View</h2><img src='{os.path.basename(graph_image_path)}' alt='Graph view'></div>"

        html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Arbitrage Report</title>
  <style>
    body {{ font-family: Georgia, serif; margin: 32px; color: #1b1b1b; background: #f8f5ef; }}
    h1, h2 {{ color: #0f4c5c; }}
    .card {{ background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 8px 24px rgba(0,0,0,0.08); }}
    .metrics {{ display: flex; gap: 18px; flex-wrap: wrap; }}
    .metric {{ background: #edf6f9; padding: 12px 16px; border-radius: 10px; min-width: 180px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border-bottom: 1px solid #ddd; padding: 10px; text-align: left; }}
    th {{ background: #e6f1f3; }}
    img {{ max-width: 100%; border-radius: 10px; }}
  </style>
</head>
<body>
  <h1>Currency Arbitrage Research Report</h1>
  <div class="card">
    <div class="metrics">
      <div class="metric"><strong>Snapshots</strong><br>{backtest_summary.get('snapshot_count', 0)}</div>
      <div class="metric"><strong>Arbitrage Frequency</strong><br>{backtest_summary.get('arbitrage_frequency', 0.0):.2%}</div>
      <div class="metric"><strong>Portfolio End Value</strong><br>${portfolio_summary.get('ending_capital', 0.0):,.2f}</div>
      <div class="metric"><strong>Provider Mismatches</strong><br>{len(provider_comparison.get('mismatches', []))}</div>
    </div>
  </div>
  <div class="card">
    <h2>Historical Backtesting</h2>
    <img src="{os.path.basename(chart_path)}" alt="Backtest timeline">
  </div>
  <div class="card">
    <h2>Top Opportunities</h2>
    <table>
      <thead><tr><th>Cycle</th><th>Gross Profit</th><th>Net Profit</th><th>Risk Score</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
  <div class="card">
    <h2>Provider Comparison</h2>
    <table>
      <thead><tr><th>Currency</th><th>Lowest Provider</th><th>Highest Provider</th><th>Spread</th></tr></thead>
      <tbody>{mismatch_rows}</tbody>
    </table>
  </div>
  <div class="card">
    <h2>Portfolio Simulation</h2>
    <p>Starting capital: ${portfolio_summary.get('starting_capital', 0.0):,.2f}</p>
    <p>Ending capital: ${portfolio_summary.get('ending_capital', 0.0):,.2f}</p>
    <p>Net profit: ${portfolio_summary.get('net_profit', 0.0):,.2f}</p>
  </div>
  {graph_section}
</body>
</html>"""

        with open(path, "w", encoding="utf-8") as handle:
            handle.write(html)
        return path

    def generate_pdf_report(
        self,
        backtest_summary: Dict,
        ranked_opportunities: List[Dict],
        portfolio_summary: Dict,
        filename: Optional[str] = None,
    ) -> str:
        filename = filename or f"arbitrage_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        path = os.path.join(self.output_dir, filename)

        with PdfPages(path) as pdf:
            fig = plt.figure(figsize=(8.27, 11.69))
            fig.text(0.08, 0.95, "Currency Arbitrage Report", fontsize=20, weight="bold")
            fig.text(0.08, 0.90, f"Snapshots analyzed: {backtest_summary.get('snapshot_count', 0)}")
            fig.text(0.08, 0.87, f"Arbitrage frequency: {backtest_summary.get('arbitrage_frequency', 0.0):.2%}")
            fig.text(0.08, 0.84, f"Ending capital: ${portfolio_summary.get('ending_capital', 0.0):,.2f}")
            y = 0.78
            fig.text(0.08, y, "Top opportunities", fontsize=14, weight="bold")
            y -= 0.04
            for item in ranked_opportunities[:8]:
                fig.text(
                    0.08,
                    y,
                    f"{' -> '.join(item['cycle'])} | gross {item['profit_percent']:.4f}% | net {item['net_profit_pct']:.4f}% | score {item['risk_score']:.2f}",
                    fontsize=9,
                )
                y -= 0.03
            pdf.savefig(fig)
            plt.close(fig)
        return path
