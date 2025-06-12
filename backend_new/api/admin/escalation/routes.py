"""
Escalation routes for the admin API.

This module defines the routes for handling escalation management.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel, Field

from services.escalation import EscalationService
from dependencies import get_escalation_service

logger = logging.getLogger(__name__)

router = APIRouter()

class EscalationItem(BaseModel):
    """Escalation item model."""
    id: str = Field(..., description="Escalation identifier")
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    query: str = Field(..., description="User query that triggered the escalation")
    reason: str = Field(..., description="Reason for escalation")
    status: str = Field(..., description="Escalation status")
    created_at: str = Field(..., description="Creation timestamp")
    resolved_at: Optional[str] = Field(None, description="Resolution timestamp")
    resolution: Optional[str] = Field(None, description="Resolution details")

class EscalationListResponse(BaseModel):
    """Escalation list response model."""
    escalations: List[EscalationItem] = Field(..., description="List of escalations")
    total: int = Field(..., description="Total number of escalations")

class EscalationResolution(BaseModel):
    """Escalation resolution model."""
    resolution: str = Field(..., description="Resolution details")

@router.get("/", response_model=EscalationListResponse)
async def list_escalations(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    escalation_service: EscalationService = Depends(get_escalation_service),
) -> Dict[str, Any]:
    """
    List escalations.
    
    Args:
        skip: Number of items to skip
        limit: Maximum number of items to return
        status: Filter by status
        escalation_service: Escalation service
        
    Returns:
        Dict[str, Any]: Escalations list
    """
    try:
        # Get escalations
        escalations = await escalation_service.list_escalations(skip=skip, limit=limit, status=status)
        total = await escalation_service.count_escalations(status=status)
        
        return {
            "escalations": escalations,
            "total": total,
        }
        
    except Exception as e:
        logger.exception(f"Error listing escalations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing escalations: {str(e)}",
        )

@router.post("/{escalation_id}/resolve", status_code=status.HTTP_200_OK)
async def resolve_escalation(
    escalation_id: str,
    resolution_data: EscalationResolution = Body(...),
    escalation_service: EscalationService = Depends(get_escalation_service),
) -> Dict[str, Any]:
    """
    Resolve an escalation.
    
    Args:
        escalation_id: Escalation identifier
        resolution_data: Resolution details
        escalation_service: Escalation service
        
    Returns:
        Dict[str, Any]: Resolution result
    """
    try:
        # Resolve the escalation
        success = await escalation_service.resolve_escalation(
            escalation_id=escalation_id,
            resolution=resolution_data.resolution,
            resolved_at=datetime.now().isoformat(),
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Escalation not found: {escalation_id}",
            )
            
        return {
            "status": "success",
            "message": f"Escalation {escalation_id} resolved successfully",
        }
            
    except HTTPException:
        raise
        
    except Exception as e:
        logger.exception(f"Error resolving escalation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resolving escalation: {str(e)}",
        ) 