"""
FastAPI surface for dashboard and JSON API access.
"""

try:
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
except ImportError:  # pragma: no cover
    FastAPI = None
    HTMLResponse = None

from currency_arbitrage.analytics.historical_backtesting import HistoricalBacktester
from currency_arbitrage.analytics.monitoring import RealTimeArbitrageMonitor
from currency_arbitrage.persistence.arbitrage_persistence import ArbitragePersistence
from currency_arbitrage.providers.live_rates_api import MultiProviderRateComparator


def create_app():
    if FastAPI is None:
        raise RuntimeError("FastAPI is not installed. Install dependencies from requirements.txt first.")

    app = FastAPI(title="Currency Arbitrage API", version="1.0.0")
    persistence = ArbitragePersistence()
    comparator = MultiProviderRateComparator()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/providers/compare")
    def compare(base_currency: str = "USD"):
        return comparator.compare_provider_rates(base_currency=base_currency)

    @app.get("/backtest")
    def backtest(base_currency: str = "USD"):
        backtester = HistoricalBacktester()
        return backtester.run_backtest(source_currency=base_currency)

    @app.get("/monitor/run")
    def monitor(base_currency: str = "USD", threshold: float = 0.1):
        monitor_service = RealTimeArbitrageMonitor(comparator, persistence)
        return monitor_service.run_monitoring(
            base_currency=base_currency,
            alert_profit_threshold=threshold,
            iterations=1,
            interval_seconds=0,
        )

    @app.get("/dashboard", response_class=HTMLResponse)
    def dashboard():
        runs = persistence.get_recent_runs(limit=5)
        opportunities = persistence.get_recent_opportunities(limit=10)
        total_runs = len(runs)
        total_opportunities = len(opportunities)
        latest_base = runs[0]["base_currency"] if runs else "USD"
        best_profit = max([row["profit_percent"] for row in opportunities], default=0.0)
        best_risk = max([(row["risk_score"] or 0) for row in opportunities], default=0.0)
        avg_threshold = (
            sum(float(row["alert_threshold"]) for row in runs) / len(runs)
            if runs else 0.0
        )
        strongest_cycle = opportunities[0]["cycle"] if opportunities else "No stored cycle yet"

        max_profit_width = max(best_profit, 0.0001)
        spotlight_cards = "".join(
            [
                f"""
                <article class="spotlight">
                  <div class="spotlight-top">
                    <span class="pill">{row['provider']}</span>
                    <span class="risk">Risk {(row['risk_score'] or 0):.2f}</span>
                  </div>
                  <h3>{row['cycle']}</h3>
                  <div class="metric-row">
                    <div>
                      <span class="mini-label">Gross Profit</span>
                      <strong>{row['profit_percent']:.4f}%</strong>
                    </div>
                    <div>
                      <span class="mini-label">Net Profit</span>
                      <strong>{(row['net_profit_pct'] or 0):.4f}%</strong>
                    </div>
                  </div>
                  <div class="bar-track"><div class="bar-fill" style="width:{(row['profit_percent'] / max_profit_width) * 100:.2f}%"></div></div>
                </article>
                """
                for row in opportunities[:3]
            ]
        )

        run_rows = "".join(
            [
                f"<tr><td>{row['created_at']}</td><td>{row['base_currency']}</td><td>{row['alert_threshold']}</td><td>{row['opportunities_found']}</td></tr>"
                for row in runs
            ]
        )
        opportunity_rows = "".join(
            [
                f"<tr><td>{row['provider']}</td><td>{row['cycle']}</td><td>{row['profit_percent']:.4f}%</td><td>{(row['net_profit_pct'] or 0):.4f}%</td><td>{(row['risk_score'] or 0):.2f}</td></tr>"
                for row in opportunities
            ]
        )
        return f"""
        <html lang="en">
          <head>
            <title>Arbitrage Dashboard</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
              :root {{
                --ink: #132238;
                --muted: #6b7b8f;
                --panel: #ffffff;
                --line: rgba(19, 34, 56, 0.09);
                --sky: #ddf1ff;
                --mint: #dff7e6;
                --gold: #fff0c7;
                --rose: #ffe2df;
                --navy: #102a43;
                --accent: #1b76d1;
                --accent-2: #0d5cab;
                --bg: radial-gradient(circle at top left, #fdfefe 0%, #eef6fb 40%, #fff8ef 100%);
              }}
              * {{ box-sizing: border-box; }}
              body {{
                font-family: "Segoe UI", Arial, sans-serif;
                margin: 0;
                color: var(--ink);
                background: var(--bg);
              }}
              a {{ color: inherit; }}
              .shell {{ max-width: 1240px; margin: 0 auto; padding: 28px 20px 52px; }}
              .hero {{
                position: relative;
                overflow: hidden;
                background:
                  radial-gradient(circle at top left, rgba(255,255,255,0.95) 0%, rgba(226,240,255,0.92) 34%, rgba(255,248,236,0.95) 100%);
                border: 1px solid var(--line);
                padding: 30px;
                border-radius: 28px;
                margin-bottom: 20px;
                box-shadow: 0 24px 55px rgba(16, 42, 67, 0.10);
              }}
              .hero::after {{
                content: "";
                position: absolute;
                right: -60px;
                top: -60px;
                width: 220px;
                height: 220px;
                border-radius: 50%;
                background: radial-gradient(circle, rgba(27,118,209,0.12), rgba(27,118,209,0));
              }}
              .eyebrow {{
                display: inline-flex;
                align-items: center;
                gap: 8px;
                border-radius: 999px;
                background: rgba(255,255,255,0.75);
                border: 1px solid var(--line);
                padding: 8px 12px;
                font-size: 0.82rem;
                text-transform: uppercase;
                letter-spacing: 0.09em;
                color: var(--muted);
              }}
              .hero h1 {{ margin: 16px 0 10px; font-size: clamp(2rem, 4vw, 3.3rem); line-height: 0.95; max-width: 780px; }}
              .hero p {{ margin: 0; color: var(--muted); max-width: 760px; line-height: 1.7; font-size: 1rem; }}
              .hero-links {{ margin-top: 22px; display: flex; gap: 12px; flex-wrap: wrap; }}
              .hero-links a {{
                text-decoration: none;
                color: var(--navy);
                background: rgba(255,255,255,0.95);
                border: 1px solid var(--line);
                padding: 12px 16px;
                border-radius: 999px;
                font-weight: 700;
                transition: transform 140ms ease, box-shadow 140ms ease, border-color 140ms ease;
              }}
              .hero-links a:hover {{
                transform: translateY(-1px);
                box-shadow: 0 12px 20px rgba(16,42,67,0.08);
                border-color: rgba(27,118,209,0.18);
              }}
              .metrics {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 16px;
                margin-bottom: 20px;
              }}
              .metric {{
                background: var(--panel);
                border-radius: 22px;
                padding: 20px;
                box-shadow: 0 18px 34px rgba(16, 42, 67, 0.07);
                border: 1px solid var(--line);
              }}
              .metric:nth-child(1) {{ background: linear-gradient(180deg, #ffffff 0%, var(--sky) 100%); }}
              .metric:nth-child(2) {{ background: linear-gradient(180deg, #ffffff 0%, var(--mint) 100%); }}
              .metric:nth-child(3) {{ background: linear-gradient(180deg, #ffffff 0%, #eef2ff 100%); }}
              .metric:nth-child(4) {{ background: linear-gradient(180deg, #ffffff 0%, var(--rose) 100%); }}
              .metric .label {{ font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); }}
              .metric .value {{ font-size: 2rem; font-weight: 800; margin-top: 10px; }}
              .metric .subvalue {{ margin-top: 10px; color: var(--muted); font-size: 0.92rem; }}
              .grid {{
                display: grid;
                grid-template-columns: 1.15fr 0.95fr;
                gap: 20px;
              }}
              .card {{
                background: white;
                padding: 22px;
                border-radius: 24px;
                margin-bottom: 18px;
                box-shadow: 0 16px 36px rgba(16,42,67,0.08);
                border: 1px solid var(--line);
              }}
              h2 {{ margin: 0 0 8px; font-size: 1.15rem; }}
              .subtle {{ color: var(--muted); margin-top: 0; margin-bottom: 18px; line-height: 1.55; }}
              .stack {{ display: grid; gap: 18px; }}
              .mini-grid {{
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 14px;
              }}
              .mini-stat {{
                padding: 16px;
                border-radius: 18px;
                background: #f7fbff;
                border: 1px solid var(--line);
              }}
              .mini-stat strong {{
                display: block;
                margin-top: 8px;
                font-size: 1.25rem;
              }}
              table {{ width: 100%; border-collapse: collapse; }}
              th, td {{ padding: 12px 10px; border-bottom: 1px solid #e5e7eb; text-align: left; vertical-align: top; }}
              th {{
                background: #f0f7ff;
                color: #17324d;
                font-size: 0.85rem;
                text-transform: uppercase;
                letter-spacing: 0.06em;
              }}
              .badge {{
                display: inline-block;
                padding: 6px 10px;
                border-radius: 999px;
                background: #eef6ff;
                color: #174a7c;
                font-weight: 700;
                font-size: 0.8rem;
              }}
              .risk {{
                color: var(--muted);
                font-size: 0.85rem;
                font-weight: 700;
              }}
              .spotlights {{
                display: grid;
                gap: 14px;
              }}
              .spotlight {{
                border: 1px solid var(--line);
                background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
                border-radius: 20px;
                padding: 18px;
              }}
              .spotlight-top {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 12px;
                margin-bottom: 12px;
              }}
              .spotlight h3 {{
                margin: 0 0 14px;
                font-size: 1rem;
                line-height: 1.45;
              }}
              .metric-row {{
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 12px;
                margin-bottom: 12px;
              }}
              .mini-label {{
                display: block;
                color: var(--muted);
                font-size: 0.8rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 6px;
              }}
              .bar-track {{
                width: 100%;
                height: 10px;
                background: #edf3f9;
                border-radius: 999px;
                overflow: hidden;
              }}
              .bar-fill {{
                height: 100%;
                border-radius: 999px;
                background: linear-gradient(90deg, var(--accent), #6eb9ff);
              }}
              .callout {{
                display: grid;
                gap: 12px;
                padding: 18px;
                border-radius: 22px;
                background: linear-gradient(145deg, #fffef9 0%, #fff6e0 100%);
                border: 1px solid rgba(179, 105, 18, 0.14);
              }}
              .callout p {{
                margin: 0;
                line-height: 1.6;
                color: #70511d;
              }}
              .empty {{
                color: var(--muted);
                padding: 16px 0 4px;
              }}
              @media (max-width: 980px) {{
                .grid {{ grid-template-columns: 1fr; }}
                .hero h1 {{ font-size: 1.8rem; }}
              }}
              @media (max-width: 640px) {{
                .shell {{ padding: 18px 14px 36px; }}
                .hero {{ padding: 22px; border-radius: 22px; }}
                .mini-grid,
                .metric-row {{ grid-template-columns: 1fr; }}
              }}
            </style>
          </head>
          <body>
            <div class="shell">
              <section class="hero">
                <div class="eyebrow">Live Monitoring + Bellman-Ford Research</div>
                <h1>Currency Arbitrage Dashboard</h1>
                <p>Track monitoring runs, compare provider mismatches, and review the strongest arbitrage opportunities discovered by the Bellman-Ford analysis pipeline. This frontend is designed as a cleaner control room for your research output, not just a raw API view.</p>
                <div class="hero-links">
                  <a href="/health">Health</a>
                  <a href="/providers/compare">Compare Providers</a>
                  <a href="/backtest">Run Backtest</a>
                  <a href="/monitor/run">Run Monitor</a>
                </div>
              </section>

              <section class="metrics">
                <div class="metric">
                  <div class="label">Recent Runs</div>
                  <div class="value">{total_runs}</div>
                  <div class="subvalue">Stored monitoring sessions ready for review</div>
                </div>
                <div class="metric">
                  <div class="label">Saved Opportunities</div>
                  <div class="value">{total_opportunities}</div>
                  <div class="subvalue">Cycles persisted from recent monitoring passes</div>
                </div>
                <div class="metric">
                  <div class="label">Latest Base Currency</div>
                  <div class="value">{latest_base}</div>
                  <div class="subvalue">Current source for shortest path evaluation</div>
                </div>
                <div class="metric">
                  <div class="label">Best Gross Profit</div>
                  <div class="value">{best_profit:.4f}%</div>
                  <div class="subvalue">Best risk score: {best_risk:.2f}</div>
                </div>
              </section>

              <section class="grid">
                <div>
                  <div class="card">
                    <h2>Recent Monitoring Runs</h2>
                    <p class="subtle">Each run stores its base currency, alert threshold, and detected opportunity count.</p>
                    {f"<table><thead><tr><th>Created</th><th>Base</th><th>Threshold</th><th>Opportunities</th></tr></thead><tbody>{run_rows}</tbody></table>" if run_rows else "<div class='empty'>No monitoring runs have been stored yet.</div>"}
                  </div>
                  <div class="card">
                    <h2>Opportunity Spotlight</h2>
                    <p class="subtle">The strongest stored opportunities rendered as compact cards so the most important signals stand out quickly.</p>
                    {f"<div class='spotlights'>{spotlight_cards}</div>" if spotlight_cards else "<div class='empty'>Run the monitor first to populate spotlight cards.</div>"}
                  </div>
                </div>
                <div>
                  <div class="card stack">
                    <h2>Recent Opportunities</h2>
                    <p class="subtle">Stored cycles ranked after monitoring runs. Gross profit reflects pre-cost return.</p>
                    {f"<table><thead><tr><th>Provider</th><th>Cycle</th><th>Gross</th><th>Net</th><th>Risk</th></tr></thead><tbody>{opportunity_rows}</tbody></table>" if opportunity_rows else "<div class='empty'>No opportunities have been stored yet.</div>"}
                    <div class="mini-grid">
                      <div class="mini-stat">
                        <span class="mini-label">Average Alert Threshold</span>
                        <strong>{avg_threshold:.4f}</strong>
                      </div>
                      <div class="mini-stat">
                        <span class="mini-label">Strongest Cycle</span>
                        <strong style="font-size:1rem; line-height:1.45;">{strongest_cycle}</strong>
                      </div>
                    </div>
                  </div>
                  <div class="card">
                    <h2>System Summary</h2>
                    <p><span class="badge">Bellman-Ford</span> Negative cycles correspond to arbitrage opportunities after rates are converted to `-log(rate)` weights.</p>
                    <p><span class="badge">Research Mode</span> Use `/backtest` to analyze snapshot frequency and `/providers/compare` to inspect rate mismatches across data sources.</p>
                  </div>
                  <div class="callout">
                    <p><strong>Why this layout helps:</strong> it surfaces the most valuable research signals first, gives the stored run history context, and keeps the API actions one click away.</p>
                    <p><strong>Next step:</strong> if you want, we can make this fully interactive with filters, live refresh, and small SVG charts fed by the API endpoints.</p>
                  </div>
                </div>
              </section>
            </div>
          </body>
        </html>
        """

    return app


app = create_app() if FastAPI is not None else None
