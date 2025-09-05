"""
API module for the Intelligent Model Routing System.

This module provides FastAPI endpoints for query routing,
model management, and system monitoring.
"""

from .realtime_routing_api import create_app
from .error_handlers import setup_error_handlers

__all__ = [
    "create_app",
    "setup_error_handlers"
]
