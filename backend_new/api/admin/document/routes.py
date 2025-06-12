"""
Document routes for the admin API.

This module defines the routes for handling document uploads and management.
"""
import logging
import os
from typing import Dict, Any, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from pydantic import BaseModel, Field

from agents.conductor import ConductorAgent
from agents.data_ingestion import DataIngestionAgent
from dependencies import get_conductor_agent, get_data_ingestion_agent
from services.storage import StorageService
from dependencies import get_storage_service

logger = logging.getLogger(__name__)

router = APIRouter()

class DocumentMetadata(BaseModel):
    """Document metadata model."""
    title: str = Field(..., description="Document title")
    description: Optional[str] = Field(None, description="Document description")
    source: Optional[str] = Field(None, description="Document source")
    tags: List[str] = Field(default_factory=list, description="Document tags")
    category: Optional[str] = Field(None, description="Document category")

class DocumentUploadResponse(BaseModel):
    """Document upload response model."""
    document_id: str = Field(..., description="Document identifier")
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File type")
    status: str = Field(..., description="Processing status")
    message: str = Field(..., description="Status message")

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    source: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    data_ingestion_agent: DataIngestionAgent = Depends(get_data_ingestion_agent),
    storage_service: StorageService = Depends(get_storage_service),
) -> Dict[str, Any]:
    """
    Upload a document for ingestion into the knowledge base.
    
    Args:
        file: Document file
        title: Document title
        description: Document description
        source: Document source
        tags: Comma-separated document tags
        category: Document category
        data_ingestion_agent: Data ingestion agent
        storage_service: Storage service
        
    Returns:
        Dict[str, Any]: Upload response
    """
    try:
        # Generate a unique document ID
        document_id = str(uuid4())
        
        # Get file extension
        _, file_extension = os.path.splitext(file.filename)
        file_extension = file_extension.lower().lstrip(".")
        
        # Determine file type
        file_type = file_extension
        if file_extension in ["jpg", "jpeg", "png", "gif", "bmp"]:
            file_type = "image"
        elif file_extension in ["pdf"]:
            file_type = "pdf"
        elif file_extension in ["doc", "docx"]:
            file_type = "docx"
        elif file_extension in ["xls", "xlsx"]:
            file_type = "xlsx"
        elif file_extension in ["txt"]:
            file_type = "txt"
        elif file_extension in ["json"]:
            file_type = "json"
        
        # Save the file
        file_path = await storage_service.save_uploaded_file(file, document_id, file_extension)
        
        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        # Prepare metadata
        metadata = {
            "document_id": document_id,
            "title": title,
            "description": description,
            "source": source,
            "tags": tag_list,
            "category": category,
            "filename": file.filename,
            "file_type": file_type,
        }
        
        # Process the document
        result = await data_ingestion_agent.process(
            input_data={
                "action": "ingest_document",
                "file_path": file_path,
                "metadata": metadata,
                "file_type": file_type,
            },
            context={},
        )
        
        # Check for errors
        if result.get("status") == "error":
            logger.error(f"Error processing document: {result.get('message')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Error processing document"),
            )
        
        # Return the response
        return {
            "document_id": document_id,
            "filename": file.filename,
            "file_type": file_type,
            "status": "success",
            "message": "Document uploaded and processed successfully",
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        # Log and convert other exceptions to HTTP exceptions
        logger.exception(f"Unexpected error uploading document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )

@router.post("/text", response_model=DocumentUploadResponse)
async def upload_text(
    title: str = Form(...),
    content: str = Form(...),
    description: Optional[str] = Form(None),
    source: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    data_ingestion_agent: DataIngestionAgent = Depends(get_data_ingestion_agent),
) -> Dict[str, Any]:
    """
    Upload text content for ingestion into the knowledge base.
    
    Args:
        title: Document title
        content: Text content
        description: Document description
        source: Document source
        tags: Comma-separated document tags
        category: Document category
        data_ingestion_agent: Data ingestion agent
        
    Returns:
        Dict[str, Any]: Upload response
    """
    try:
        # Generate a unique document ID
        document_id = str(uuid4())
        
        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        # Prepare metadata
        metadata = {
            "document_id": document_id,
            "title": title,
            "description": description,
            "source": source,
            "tags": tag_list,
            "category": category,
            "file_type": "text",
        }
        
        # Process the text
        result = await data_ingestion_agent.process(
            input_data={
                "action": "ingest_text",
                "content": content,
                "metadata": metadata,
            },
            context={},
        )
        
        # Check for errors
        if result.get("status") == "error":
            logger.error(f"Error processing text: {result.get('message')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Error processing text"),
            )
        
        # Return the response
        return {
            "document_id": document_id,
            "filename": f"{title}.txt",
            "file_type": "text",
            "status": "success",
            "message": "Text content processed successfully",
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        # Log and convert other exceptions to HTTP exceptions
        logger.exception(f"Unexpected error uploading text: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        ) 