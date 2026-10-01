"""
SQLite persistence for snapshots, monitoring runs, and opportunities.
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

from currency_arbitrage.utils import ensure_directory


class ArbitragePersistence:
    """Persist runs and opportunities for later review."""

    def __init__(self, db_path: str = "data/arbitrage_history.db"):
        self.db_path = db_path
        self._uri = False
        ensure_directory("data")
        self._connection = self._create_connection(db_path)
        self._init_db()

    def _create_connection(self, db_path: str):
        try:
            return sqlite3.connect(db_path, check_same_thread=False)
        except sqlite3.OperationalError:
            self.db_path = "file:arbitrage_history?mode=memory&cache=shared"
            self._uri = True
            return sqlite3.connect(self.db_path, uri=True, check_same_thread=False)

    def _connect(self):
        return self._connection

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    base_currency TEXT NOT NULL,
                    rates_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS monitor_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    base_currency TEXT NOT NULL,
                    alert_threshold REAL NOT NULL,
                    opportunities_found INTEGER NOT NULL,
                    summary_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS opportunities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER,
                    created_at TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    cycle TEXT NOT NULL,
                    profit_percent REAL NOT NULL,
                    net_profit_pct REAL,
                    risk_score REAL,
                    details_json TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES monitor_runs(id)
                )
                """
            )

    def save_snapshot(self, provider: str, base_currency: str, rates: Dict) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO snapshots (created_at, provider, base_currency, rates_json)
                VALUES (?, ?, ?, ?)
                """,
                (datetime.utcnow().isoformat(), provider, base_currency, json.dumps(rates)),
            )
            return cursor.lastrowid

    def save_monitor_run(self, base_currency: str, alert_threshold: float, summary: Dict) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO monitor_runs (created_at, base_currency, alert_threshold, opportunities_found, summary_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    datetime.utcnow().isoformat(),
                    base_currency,
                    alert_threshold,
                    int(summary.get("opportunities_found", 0)),
                    json.dumps(summary),
                ),
            )
            return cursor.lastrowid

    def save_opportunities(self, run_id: Optional[int], provider: str, opportunities: List[Dict]):
        with self._connect() as conn:
            for item in opportunities:
                conn.execute(
                    """
                    INSERT INTO opportunities (
                        run_id, created_at, provider, cycle, profit_percent, net_profit_pct, risk_score, details_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        datetime.utcnow().isoformat(),
                        provider,
                        " -> ".join(item["cycle"]),
                        item.get("profit_percent", 0.0),
                        item.get("net_profit_pct"),
                        item.get("risk_score"),
                        json.dumps(item),
                    ),
                )

    def get_recent_runs(self, limit: int = 10) -> List[Dict]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM monitor_runs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            return [dict(row) for row in rows]

    def get_recent_opportunities(self, limit: int = 20) -> List[Dict]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM opportunities ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            return [dict(row) for row in rows]
