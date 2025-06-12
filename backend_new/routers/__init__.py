"""
Routers module for the LenDen Club AI Platform.

This module contains the API routers for different endpoints.
"""

from .admin import router as admin_router
from .user import router as user_router

__all__ = [
    "admin_router",
    "user_router",
] 