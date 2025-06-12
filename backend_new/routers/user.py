"""
User router for user-facing endpoints.

This module provides API endpoints for user interactions with the AI assistant.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Body, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
import json
import uuid

from ..config.dependencies import (
    get_conductor_agent, get_memory_service, get_llm_service, get_transcription_service
)
from ..agents.conductor import ConductorAgent
from ..services.memory import MemoryService
from ..services.llm import LLMService
from ..services.transcription import TranscriptionService

logger = logging.getLogger(__name__)

router = APIRouter()

# Request/Response Models
class QueryRequest(BaseModel):
    """Model for text query requests."""
    query: str
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)

class AudioQueryRequest(BaseModel):
    """Model for audio query metadata."""
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: Optional[str] = None
    language: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)

class QueryResponse(BaseModel):
    """Model for query responses."""
    response: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

# Text query endpoint
@router.post("/query", response_model=QueryResponse)
async def text_query(
    request: QueryRequest,
    conductor: ConductorAgent = Depends(get_conductor_agent),
    memory_service: MemoryService = Depends(get_memory_service),
):
    """
    Process a text query from a user.
    
    Args:
        request: The query request
        conductor: The conductor agent for processing the query
        memory_service: Memory service for retrieving and storing chat history
        
    Returns:
        QueryResponse: The response to the query
    """
    try:
        user_id = request.user_id
        query = request.query
        
        # Get user context
        user_context = await memory_service.get_memory_context(user_id)
        
        # Prepare input for agent
        agent_input = {
            "query": query, 
            "user_id": user_id,
            "session_id": request.session_id,
        }
        
        # Add custom context from request if present
        if request.context:
            agent_input["custom_context"] = request.context
        
        # Process query with the conductor agent
        result = await conductor.run(agent_input, user_context)
        
        # Save the exchange to the user's chat history
        await memory_service.add_exchange(
            user_id=user_id,
            query=query,
            response=result.get("response", ""),
            metadata={
                "session_id": request.session_id,
                "sources": result.get("sources", []),
                "metadata": result.get("metadata", {})
            }
        )
        
        return QueryResponse(
            response=result.get("response", "I couldn't generate a response."),
            sources=result.get("sources", []),
            metadata=result.get("metadata", {})
        )
    
    except Exception as e:
        logger.error(f"Error processing text query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Audio query endpoint
@router.post("/audio-query", response_model=QueryResponse)
async def audio_query(
    audio_file: UploadFile = File(...),
    user_id: str = Form(default_factory=lambda: str(uuid.uuid4())),
    session_id: Optional[str] = Form(None),
    language: Optional[str] = Form(None),
    context: str = Form("{}"),
    conductor: ConductorAgent = Depends(get_conductor_agent),
    memory_service: MemoryService = Depends(get_memory_service),
    transcription_service: TranscriptionService = Depends(get_transcription_service),
):
    """
    Process an audio query from a user.
    
    Args:
        audio_file: The audio file containing the user's query
        user_id: ID of the user
        session_id: Optional session ID
        language: Optional language code
        context: Additional context as JSON string
        conductor: The conductor agent for processing the query
        memory_service: Memory service for retrieving and storing chat history
        transcription_service: Service for transcribing audio to text
        
    Returns:
        QueryResponse: The response to the query
    """
    try:
        # Parse context
        try:
            context_dict = json.loads(context)
        except json.JSONDecodeError:
            context_dict = {}
        
        # Transcribe audio
        transcription = await transcription_service.transcribe_file(
            audio_file.file, language=language
        )
        
        if "error" in transcription:
            raise HTTPException(status_code=400, detail=transcription["error"])
        
        query_text = transcription.get("text", "")
        if not query_text:
            raise HTTPException(status_code=400, detail="Could not transcribe audio")
        
        # Get user context
        user_context = await memory_service.get_memory_context(user_id)
        
        # Prepare input for agent
        agent_input = {
            "query": query_text, 
            "user_id": user_id,
            "session_id": session_id,
            "transcription": transcription,
        }
        
        # Add custom context if present
        if context_dict:
            agent_input["custom_context"] = context_dict
        
        # Process query with the conductor agent
        result = await conductor.run(agent_input, user_context)
        
        # Save the exchange to the user's chat history
        await memory_service.add_exchange(
            user_id=user_id,
            query=query_text,
            response=result.get("response", ""),
            metadata={
                "session_id": session_id,
                "audio_transcription": transcription,
                "sources": result.get("sources", []),
                "metadata": result.get("metadata", {})
            }
        )
        
        return QueryResponse(
            response=result.get("response", "I couldn't generate a response."),
            sources=result.get("sources", []),
            metadata={
                **result.get("metadata", {}),
                "transcription": transcription.get("text")
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing audio query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Chat history endpoint
@router.get("/history/{user_id}")
async def get_chat_history(
    user_id: str,
    limit: int = Query(10, ge=1, le=50),
    skip: int = Query(0, ge=0),
    memory_service: MemoryService = Depends(get_memory_service),
):
    """
    Get chat history for a user.
    
    Args:
        user_id: ID of the user
        limit: Maximum number of history entries to retrieve
        skip: Number of entries to skip
        memory_service: Memory service for retrieving chat history
        
    Returns:
        List[Dict[str, Any]]: Chat history entries
    """
    try:
        history = await memory_service.get_chat_history(user_id, limit, skip)
        return history
    except Exception as e:
        logger.error(f"Error retrieving chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Clear history endpoint
@router.delete("/history/{user_id}")
async def clear_chat_history(
    user_id: str,
    memory_service: MemoryService = Depends(get_memory_service),
):
    """
    Clear chat history for a user.
    
    Args:
        user_id: ID of the user
        memory_service: Memory service for clearing chat history
        
    Returns:
        Dict[str, Any]: Result of the operation
    """
    try:
        success = await memory_service.clear_chat_history(user_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to clear chat history")
        return {"status": "success", "message": "Chat history cleared"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 