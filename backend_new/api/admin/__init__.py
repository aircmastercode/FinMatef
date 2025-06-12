"""
Admin API module for the FinMate AI Platform.

This module contains all admin-related API routes and endpoints.
"""

from fastapi import APIRouter

from .document import router as document_router
from .knowledge import router as knowledge_router
from .escalation import router as escalation_router

router = APIRouter()

router.include_router(document_router, prefix="/document", tags=["admin-document"])
router.include_router(knowledge_router, prefix="/knowledge", tags=["admin-knowledge"])
router.include_router(escalation_router, prefix="/escalation", tags=["admin-escalation"]) 