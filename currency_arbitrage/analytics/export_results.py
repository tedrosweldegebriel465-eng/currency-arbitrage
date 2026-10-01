"""
Export arbitrage results to CSV and other formats
"""

import csv
import json
import math
import os
from datetime import datetime

import pandas as pd

from currency_arbitrage.utils import get_output_dir


class ResultsExporter:
    """Export arbitrage detection results to various formats."""

    def __init__(self, detector):
        self.detector = detector

    def export_to_csv(self, filename: str = None):
        """Export results to CSV file."""
        if not filename:
            filename = os.path.join(
                get_output_dir("csv"),
                f"arbitrage_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            )

        cycles = self.detector.get_profit_cycles()
        data = []
        for i, cycle in enumerate(cycles, 1):
            data.append(
                {
                    "cycle_id": i,
                    "cycle_currencies": " -> ".join(cycle["cycle"]) + " -> " + cycle["cycle"][0],
                    "num_currencies": len(cycle["cycle"]),
                    "gross_return": cycle["total_product"],
                    "profit_percent": cycle["profit_percent"],
                    "is_profitable": cycle["profit_percent"] > 0,
                    "rates_sequence": " | ".join([f"{r:.6f}" for r in cycle["rates"]]),
                }
            )

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

        print(f"[OK] Exported {len(data)} cycles to {filename}")
        return filename

    def export_shortest_paths(self, source: str = "USD", filename: str = None):
        """Export shortest paths to CSV."""
        if not filename:
            filename = os.path.join(
                get_output_dir("csv"),
                f"shortest_paths_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            )

        distances, paths = self.detector.get_shortest_paths(source)
        graph = self.detector.graph

        data = []
        for i, currency in enumerate(graph.currencies):
            if distances[i] != float("inf"):
                profit_pct = (math.exp(-distances[i]) - 1) * 100
                data.append(
                    {
                        "source": source,
                        "target": currency,
                        "distance": distances[i],
                        "profit_potential_percent": profit_pct,
                        "path": " -> ".join(paths[i]) if paths[i] else "",
                    }
                )

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

        print(f"[OK] Exported {len(data)} paths to {filename}")
        return filename

    def export_to_json(self, filename: str = None):
        """Export results to JSON format."""
        if not filename:
            filename = os.path.join(
                get_output_dir("json"),
                f"arbitrage_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            )

        cycles = self.detector.get_profit_cycles()
        output = {
            "timestamp": datetime.now().isoformat(),
            "total_cycles": len(cycles),
            "cycles": cycles,
            "summary": {
                "max_profit": max([c["profit_percent"] for c in cycles]) if cycles else 0,
                "avg_profit": sum([c["profit_percent"] for c in cycles]) / len(cycles) if cycles else 0,
            },
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)

        print(f"[OK] Exported results to {filename}")
        return filename

    def export_to_excel(self, filename: str = None):
        """Export to Excel format (requires pandas and openpyxl)."""
        if not filename:
            filename = os.path.join(
                get_output_dir("excel"),
                f"arbitrage_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            )

        try:
            cycles = self.detector.get_profit_cycles()
            pd.DataFrame(cycles).to_excel(filename, index=False)
            print(f"[OK] Exported to Excel: {filename}")
            return filename
        except ImportError:
            print("[WARNING] pandas or openpyxl not installed. Install with: pip install pandas openpyxl")
            return None

    def export_all(self, prefix: str = "arbitrage_analysis"):
        """Export all formats."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        files = {
            "csv_cycles": self.export_to_csv(
                os.path.join(get_output_dir("csv"), f"{prefix}_cycles_{timestamp}.csv")
            ),
            "csv_paths": self.export_shortest_paths(
                filename=os.path.join(get_output_dir("csv"), f"{prefix}_paths_{timestamp}.csv")
            ),
            "json": self.export_to_json(
                os.path.join(get_output_dir("json"), f"{prefix}_{timestamp}.json")
            ),
        }
        excel_file = self.export_to_excel(
            os.path.join(get_output_dir("excel"), f"{prefix}_{timestamp}.xlsx")
        )
        if excel_file:
            files["excel"] = excel_file
        return files
