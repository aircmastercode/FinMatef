"""
History routes for the user API.

This module defines the routes for handling user conversation history.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from services.memory import MemoryService
from dependencies import get_memory_service

logger = logging.getLogger(__name__)

router = APIRouter()

class MessageModel(BaseModel):
    """Message model."""
    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(None, description="Message timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Message metadata")

class SessionModel(BaseModel):
    """Session model."""
    id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    created_at: str = Field(..., description="Creation timestamp")
    last_active: str = Field(..., description="Last activity timestamp")
    message_count: int = Field(..., description="Number of messages in the session")
    title: str = Field(..., description="Session title")

class ConversationHistoryResponse(BaseModel):
    """Conversation history response model."""
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    messages: List[MessageModel] = Field(default_factory=list, description="Conversation messages")
    total_messages: int = Field(..., description="Total number of messages")

@router.get("/", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    user_id: str,
    session_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    memory_service: MemoryService = Depends(get_memory_service),
) -> Dict[str, Any]:
    """
    Get conversation history for a user session.
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        limit: Maximum number of messages to return
        offset: Number of messages to skip
        memory_service: Memory service
        
    Returns:
        Dict[str, Any]: Conversation history
    """
    try:
        # Get conversation history
        history = await memory_service.get_conversation_memory(
            user_id=user_id,
            session_id=session_id,
            limit=limit,
            offset=offset,
        )
        
        # Get total message count
        total_count = await memory_service.get_conversation_message_count(
            user_id=user_id,
            session_id=session_id,
        )
        
        # Return the response
        return {
            "user_id": user_id,
            "session_id": session_id,
            "messages": history,
            "total_messages": total_count,
        }
        
    except Exception as e:
        # Log and convert exceptions to HTTP exceptions
        logger.exception(f"Error retrieving conversation history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving conversation history: {str(e)}",
        )

@router.get("/sessions", response_model=List[SessionModel])
async def get_user_sessions(
    user_id: str,
    memory_service: MemoryService = Depends(get_memory_service),
) -> List[Dict[str, Any]]:
    """
    Get all sessions for a user.
    
    Args:
        user_id: User identifier
        memory_service: Memory service
        
    Returns:
        List[Dict[str, Any]]: List of session data
    """
    try:
        # Get user sessions
        sessions = await memory_service.get_user_sessions(
            user_id=user_id,
        )
        
        return sessions
        
    except Exception as e:
        # Log and convert exceptions to HTTP exceptions
        logger.exception(f"Error retrieving user sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user sessions: {str(e)}",
        )

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation_history(
    user_id: str,
    session_id: str,
    memory_service: MemoryService = Depends(get_memory_service),
) -> None:
    """
    Delete conversation history for a user session.
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        memory_service: Memory service
    """
    try:
        # Delete conversation history
        await memory_service.delete_conversation_memory(
            user_id=user_id,
            session_id=session_id,
        )
        
    except Exception as e:
        # Log and convert exceptions to HTTP exceptions
        logger.exception(f"Error deleting conversation history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting conversation history: {str(e)}",
        ) 