"""
Document admin API module for the FinMate AI Platform.

This module handles document upload and management.
"""

from fastapi import APIRouter

from .routes import router as document_router

router = APIRouter()
router.include_router(document_router) 