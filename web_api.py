"""
Compatibility wrapper for the packaged FastAPI app.
"""

from advanced_features.web_api import app, create_app

__all__ = ["app", "create_app"]
