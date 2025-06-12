"""
Voice user API module for the FinMate AI Platform.

This module handles user voice queries.
"""

from fastapi import APIRouter

from .routes import router as voice_router

router = APIRouter()
router.include_router(voice_router) 