"""
Query routes for the user API.

This module defines the routes for handling user text queries.
"""
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from agents.conductor import ConductorAgent
from dependencies import get_conductor_agent

logger = logging.getLogger(__name__)

router = APIRouter()

class QueryRequest(BaseModel):
    """Query request model."""
    query: str = Field(..., description="User query text")
    user_id: str = Field(..., description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")

class QueryResponse(BaseModel):
    """Query response model."""
    response: str = Field(..., description="Response text")
    sources: list = Field(default_factory=list, description="Knowledge sources")
    confidence: float = Field(..., description="Confidence score")
    needs_escalation: bool = Field(False, description="Whether the query needs escalation")
    escalation_reason: Optional[str] = Field(None, description="Reason for escalation")
    session_id: str = Field(..., description="Session identifier")

@router.post("/", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    conductor_agent: ConductorAgent = Depends(get_conductor_agent),
) -> Dict[str, Any]:
    """
    Process a user text query.
    
    Args:
        request: Query request containing user query and identifiers
        conductor_agent: Conductor agent for orchestrating the query processing
        
    Returns:
        Dict[str, Any]: Query response
    """
    try:
        # Prepare context
        context = {
            "user_id": request.user_id,
            "session_id": request.session_id or f"session_{hash(request.user_id + request.query) % 10000:04d}",
            "timestamp": None,  # Will be set by the conductor
        }
        
        # Process the query through the conductor agent
        result = await conductor_agent.process(
            input_data={
                "query": request.query,
                "type": "text",
            },
            context=context,
        )
        
        # Check for errors
        if result.get("status") == "error":
            logger.error(f"Error processing query: {result.get('message')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Error processing query"),
            )
        
        # Return the response
        return {
            "response": result.get("response", ""),
            "sources": result.get("sources", []),
            "confidence": result.get("confidence", 0.0),
            "needs_escalation": result.get("needs_escalation", False),
            "escalation_reason": result.get("escalation_reason"),
            "session_id": context["session_id"],
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        # Log and convert other exceptions to HTTP exceptions
        logger.exception(f"Unexpected error processing query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        ) 