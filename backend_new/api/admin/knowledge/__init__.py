"""
Knowledge admin API module for the FinMate AI Platform.

This module handles knowledge base management.
"""

from fastapi import APIRouter

from .routes import router as knowledge_router

router = APIRouter()
router.include_router(knowledge_router) 