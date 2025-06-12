"""
Escalation admin API module for the FinMate AI Platform.

This module handles escalation management.
"""

from fastapi import APIRouter

from .routes import router as escalation_router

router = APIRouter()
router.include_router(escalation_router) 