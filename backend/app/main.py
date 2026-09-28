"""Compatibility entry point. Use `uvicorn app.api:app --reload`."""
from .api import app

__all__ = ["app"]
