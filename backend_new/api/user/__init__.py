"""
User API module for the FinMate AI Platform.

This module contains all user-related API routes and endpoints.
"""

from fastapi import APIRouter

from .query import router as query_router
from .voice import router as voice_router
from .history import router as history_router

router = APIRouter()

router.include_router(query_router, prefix="/query", tags=["user-query"])
router.include_router(voice_router, prefix="/voice", tags=["user-voice"])
router.include_router(history_router, prefix="/history", tags=["user-history"]) 