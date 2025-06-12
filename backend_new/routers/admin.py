"""
Admin router for administrator-facing endpoints.

This module provides API endpoints for data ingestion, system monitoring,
and administrative functions.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Body, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
import json
import uuid
from enum import Enum

from ..config.dependencies import (
    get_conductor_agent, get_memory_service, get_cognee_client, get_storage_service
)
from ..agents.conductor import ConductorAgent
from ..agents.data_ingestion import DataIngestionAgent
from ..services.memory import MemoryService
from ..database.cognee_client import CogneeClient
from ..services.storage import StorageService

logger = logging.getLogger(__name__)

router = APIRouter()

# Enums
class DocumentType(str, Enum):
    FAQ = "faq"
    POLICY = "policy"
    GENERAL = "general"
    COMPANY = "company"
    OTHER = "other"

# Request/Response Models
class DocumentMetadata(BaseModel):
    """Model for document metadata."""
    title: str
    document_type: DocumentType
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    source: Optional[str] = None
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)

class UrlIngestionRequest(BaseModel):
    """Model for URL ingestion requests."""
    url: str
    document_type: DocumentType
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)

class TextIngestionRequest(BaseModel):
    """Model for text ingestion requests."""
    content: str
    document_type: DocumentType
    title: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)

class IngestionResponse(BaseModel):
    """Model for ingestion responses."""
    status: str
    message: str
    document_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

# File upload endpoint
@router.post("/upload", response_model=IngestionResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    document_type: DocumentType = Form(...),
    description: Optional[str] = Form(None),
    tags: str = Form("[]"),  # JSON array as string
    custom_metadata: str = Form("{}"),  # JSON object as string
    conductor: ConductorAgent = Depends(get_conductor_agent),
    storage_service: StorageService = Depends(get_storage_service),
):
    """
    Upload a document for processing.
    
    Args:
        file: Document file (PDF, DOCX, TXT, JSON)
        title: Document title
        document_type: Type of document
        description: Optional document description
        tags: Tags as JSON array string
        custom_metadata: Additional metadata as JSON object string
        conductor: Conductor agent for delegating to specialists
        storage_service: Service for storing uploaded files
        
    Returns:
        IngestionResponse: Result of the upload operation
    """
    try:
        # Parse tags and metadata from JSON strings
        try:
            tags_list = json.loads(tags)
            if not isinstance(tags_list, list):
                tags_list = []
        except json.JSONDecodeError:
            tags_list = []
            
        try:
            metadata_dict = json.loads(custom_metadata)
            if not isinstance(metadata_dict, dict):
                metadata_dict = {}
        except json.JSONDecodeError:
            metadata_dict = {}
        
        # Validate file type
        file_ext = file.filename.split(".")[-1].lower()
        supported_extensions = {"pdf", "docx", "txt", "json"}
        
        if file_ext not in supported_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. Supported types: {', '.join(supported_extensions)}"
            )
        
        # Save the file
        file_metadata = await storage_service.save_document(
            file.file, 
            filename=file.filename, 
            category="documents"
        )
        
        # Prepare document metadata
        document_metadata = {
            "title": title,
            "document_type": document_type,
            "description": description,
            "tags": tags_list,
            "file_path": file_metadata["path"],
            "filename": file_metadata["filename"],
            "file_id": file_metadata["id"],
            **metadata_dict
        }
        
        # Delegate to appropriate agent using conductor
        agent_input = {
            "action": "ingest_document",
            "file_path": file_metadata["path"],
            "metadata": document_metadata,
            "file_type": file_ext
        }
        
        result = await conductor.run(
            agent_input, 
            {"admin_action": True}  # Context flag to indicate admin action
        )
        
        if result.get("status") != "success":
            return IngestionResponse(
                status="error",
                message=result.get("message", "Document ingestion failed"),
                metadata=result.get("metadata", {})
            )
            
        return IngestionResponse(
            status="success",
            message="Document uploaded and processed successfully",
            document_id=result.get("document_id"),
            metadata=result.get("metadata", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# URL ingestion endpoint
@router.post("/ingest-url", response_model=IngestionResponse)
async def ingest_url(
    request: UrlIngestionRequest,
    conductor: ConductorAgent = Depends(get_conductor_agent),
):
    """
    Ingest content from a URL.
    
    Args:
        request: URL ingestion request
        conductor: Conductor agent for delegating to specialists
        
    Returns:
        IngestionResponse: Result of the URL ingestion
    """
    try:
        # Delegate to appropriate agent using conductor
        agent_input = {
            "action": "ingest_url",
            "url": request.url,
            "metadata": {
                "title": request.title or request.url,
                "document_type": request.document_type,
                "description": request.description,
                "tags": request.tags,
                "source": request.url,
                **request.custom_metadata
            }
        }
        
        result = await conductor.run(
            agent_input, 
            {"admin_action": True}  # Context flag to indicate admin action
        )
        
        if result.get("status") != "success":
            return IngestionResponse(
                status="error",
                message=result.get("message", "URL ingestion failed"),
                metadata=result.get("metadata", {})
            )
            
        return IngestionResponse(
            status="success",
            message="URL content ingested successfully",
            document_id=result.get("document_id"),
            metadata=result.get("metadata", {})
        )
        
    except Exception as e:
        logger.error(f"Error processing URL ingestion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Text ingestion endpoint
@router.post("/ingest-text", response_model=IngestionResponse)
async def ingest_text(
    request: TextIngestionRequest,
    conductor: ConductorAgent = Depends(get_conductor_agent),
):
    """
    Ingest raw text content.
    
    Args:
        request: Text ingestion request
        conductor: Conductor agent for delegating to specialists
        
    Returns:
        IngestionResponse: Result of the text ingestion
    """
    try:
        # Delegate to appropriate agent using conductor
        agent_input = {
            "action": "ingest_text",
            "content": request.content,
            "metadata": {
                "title": request.title,
                "document_type": request.document_type,
                "description": request.description,
                "tags": request.tags,
                **request.custom_metadata
            }
        }
        
        result = await conductor.run(
            agent_input, 
            {"admin_action": True}  # Context flag to indicate admin action
        )
        
        if result.get("status") != "success":
            return IngestionResponse(
                status="error",
                message=result.get("message", "Text ingestion failed"),
                metadata=result.get("metadata", {})
            )
            
        return IngestionResponse(
            status="success",
            message="Text content ingested successfully",
            document_id=result.get("document_id"),
            metadata=result.get("metadata", {})
        )
        
    except Exception as e:
        logger.error(f"Error processing text ingestion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Content search endpoint
@router.get("/search")
async def search_content(
    query: str = Query(..., min_length=2),
    document_type: Optional[DocumentType] = None,
    tags: Optional[str] = None,  # Comma-separated list
    limit: int = Query(10, ge=1, le=50),
    cognee_client: CogneeClient = Depends(get_cognee_client),
):
    """
    Search for content in the knowledge base.
    
    Args:
        query: Search query
        document_type: Optional type filter
        tags: Optional tags filter (comma-separated)
        limit: Maximum number of results
        cognee_client: Cognee client for knowledge retrieval
        
    Returns:
        Dict[str, Any]: Search results
    """
    try:
        # Build filters
        filters = {}
        if document_type:
            filters["document_type"] = document_type
            
        # Parse tags
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
            if tag_list:
                filters["tags"] = tag_list
                
        # Search in knowledge base
        results = await cognee_client.retrieve_knowledge(
            query=query,
            filters=filters,
            top_k=limit
        )
        
        return {
            "status": "success",
            "query": query,
            "filters": filters,
            "count": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error searching content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# DB status endpoint
@router.get("/status")
async def get_status(
    cognee_client: CogneeClient = Depends(get_cognee_client),
):
    """
    Get system status and statistics.
    
    Args:
        cognee_client: Cognee client for database queries
        
    Returns:
        Dict[str, Any]: System status
    """
    try:
        # Get document count by type
        counts = {}
        for doc_type in DocumentType:
            count_query = """
                MATCH (n)
                WHERE n.document_type = $type
                RETURN count(n) as count
            """
            results = await cognee_client.graph_db.run_query(count_query, {"type": doc_type})
            counts[doc_type] = results[0]["count"] if results else 0
            
        # Get total node count
        total_query = "MATCH (n) RETURN count(n) as count"
        total_results = await cognee_client.graph_db.run_query(total_query)
        total_count = total_results[0]["count"] if total_results else 0
        
        # Get relationship count
        rel_query = "MATCH ()-[r]->() RETURN count(r) as count"
        rel_results = await cognee_client.graph_db.run_query(rel_query)
        rel_count = rel_results[0]["count"] if rel_results else 0
        
        return {
            "status": "online",
            "database": {
                "total_nodes": total_count,
                "total_relationships": rel_count,
                "document_counts": counts
            },
            "system_info": {
                "version": "1.0.0",
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        } 