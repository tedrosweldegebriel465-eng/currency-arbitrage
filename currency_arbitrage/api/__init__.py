"""HTTP API and dashboard (FastAPI)."""

from currency_arbitrage.api.web_api import app, create_app

__all__ = ["app", "create_app"]
