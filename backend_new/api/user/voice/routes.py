"""
Voice routes for the user API.

This module defines the routes for handling user voice queries.
"""
import logging
import os
from typing import Dict, Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from pydantic import BaseModel, Field

from agents.conductor import ConductorAgent
from dependencies import get_conductor_agent
from services.transcription import TranscriptionService
from dependencies import get_transcription_service
from services.storage import StorageService
from dependencies import get_storage_service

logger = logging.getLogger(__name__)

router = APIRouter()

class VoiceQueryResponse(BaseModel):
    """Voice query response model."""
    transcription: str = Field(..., description="Transcribed text")
    response: str = Field(..., description="Response text")
    sources: list = Field(default_factory=list, description="Knowledge sources")
    confidence: float = Field(..., description="Confidence score")
    needs_escalation: bool = Field(False, description="Whether the query needs escalation")
    escalation_reason: Optional[str] = Field(None, description="Reason for escalation")
    session_id: str = Field(..., description="Session identifier")

@router.post("/upload", response_model=VoiceQueryResponse)
async def upload_voice(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    session_id: Optional[str] = Form(None),
    language: Optional[str] = Form("en"),
    transcription_service: TranscriptionService = Depends(get_transcription_service),
    storage_service: StorageService = Depends(get_storage_service),
    conductor_agent: ConductorAgent = Depends(get_conductor_agent),
) -> Dict[str, Any]:
    """
    Upload a voice file and process it as a query.
    
    Args:
        file: Voice file
        user_id: User identifier
        session_id: Session identifier
        language: Voice language code
        transcription_service: Transcription service
        storage_service: Storage service
        conductor_agent: Conductor agent
        
    Returns:
        Dict[str, Any]: Voice query response
    """
    try:
        # Generate a unique file ID
        file_id = str(uuid4())
        
        # Get file extension
        _, file_extension = os.path.splitext(file.filename)
        file_extension = file_extension.lower().lstrip(".")
        
        # Validate audio format
        if file_extension not in ["mp3", "wav", "m4a", "ogg", "webm"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported audio format: {file_extension}. Supported formats: mp3, wav, m4a, ogg, webm",
            )
        
        # Save the file
        file_path = await storage_service.save_uploaded_file(file, file_id, file_extension)
        
        # Transcribe the audio
        transcription_result = await transcription_service.transcribe_audio(
            file_path=file_path,
            language=language,
        )
        
        # Check for transcription errors
        if transcription_result.get("status") == "error":
            logger.error(f"Error transcribing audio: {transcription_result.get('message')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=transcription_result.get("message", "Error transcribing audio"),
            )
        
        # Get the transcribed text
        transcribed_text = transcription_result.get("text", "")
        
        if not transcribed_text:
            logger.error("No speech detected in the audio")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No speech detected in the audio",
            )
        
        # Prepare context
        context = {
            "user_id": user_id,
            "session_id": session_id or f"session_{hash(user_id + transcribed_text) % 10000:04d}",
            "timestamp": None,  # Will be set by the conductor
            "voice_language": language,
        }
        
        # Process the query through the conductor agent
        result = await conductor_agent.process(
            input_data={
                "query": transcribed_text,
                "type": "voice",
                "audio_path": file_path,
            },
            context=context,
        )
        
        # Check for errors
        if result.get("status") == "error":
            logger.error(f"Error processing voice query: {result.get('message')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Error processing voice query"),
            )
        
        # Return the response
        return {
            "transcription": transcribed_text,
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
        logger.exception(f"Unexpected error processing voice query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        ) 