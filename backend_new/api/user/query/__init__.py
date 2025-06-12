"""
Query user API module for the FinMate AI Platform.

This module handles user text queries.
"""

from fastapi import APIRouter

from .routes import router as query_router

router = APIRouter()
router.include_router(query_router) 