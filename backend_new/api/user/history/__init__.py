"""
History user API module for the FinMate AI Platform.

This module handles user conversation history.
"""

from fastapi import APIRouter

from .routes import router as history_router

router = APIRouter()
router.include_router(history_router) 