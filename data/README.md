# data/

This directory holds all persistent and input data used by the Currency Arbitrage Detector.

## Layout

| Path | Contents |
|---|---|
| `inputs/exchange_rates.csv` | 25-currency exchange rate matrix used as sample input data |
| `historical_snapshots/` | 12 timestamped CSV snapshots used by `HistoricalBacktester` for backtesting |
| `arbitrage_history.db` | SQLite database written by the live monitoring pipeline — **local only, not committed** |
| `test_history.db` | Temporary SQLite file created during test runs — **local only, not committed** |

## Notes

- Databases (`.db`) are excluded from Git via `.gitignore`.
- Historical snapshots are committed because they are required test fixtures.
- New snapshots are generated automatically by `HistoricalBacktester` if the directory is empty.
