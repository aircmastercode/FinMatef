"""
API module for the FinMate AI Platform.

This module contains all API routes and endpoints.
"""

from .admin import router as admin_router
from .user import router as user_router

__all__ = ["admin_router", "user_router"] 