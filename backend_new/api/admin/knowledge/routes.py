"""
Knowledge routes for the admin API.

This module defines the routes for handling knowledge base management.
"""
import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from services.knowledge import KnowledgeService
from dependencies import get_knowledge_service

logger = logging.getLogger(__name__)

router = APIRouter()

class KnowledgeItem(BaseModel):
    """Knowledge item model."""
    id: str = Field(..., description="Knowledge item identifier")
    title: str = Field(..., description="Knowledge item title")
    source: Optional[str] = Field(None, description="Knowledge item source")
    category: Optional[str] = Field(None, description="Knowledge item category")
    tags: List[str] = Field(default_factory=list, description="Knowledge item tags")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

class KnowledgeListResponse(BaseModel):
    """Knowledge list response model."""
    items: List[KnowledgeItem] = Field(..., description="List of knowledge items")
    total: int = Field(..., description="Total number of items")

@router.get("/", response_model=KnowledgeListResponse)
async def list_knowledge_items(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
) -> Dict[str, Any]:
    """
    List knowledge items in the knowledge base.
    
    Args:
        skip: Number of items to skip
        limit: Maximum number of items to return
        category: Filter by category
        tag: Filter by tag
        knowledge_service: Knowledge service
        
    Returns:
        Dict[str, Any]: Knowledge items list
    """
    try:
        # Get knowledge items
        items = await knowledge_service.list_items(skip=skip, limit=limit, category=category, tag=tag)
        total = await knowledge_service.count_items(category=category, tag=tag)
        
        return {
            "items": items,
            "total": total,
        }
        
    except Exception as e:
        logger.exception(f"Error listing knowledge items: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing knowledge items: {str(e)}",
        )

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_item(
    item_id: str,
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
) -> None:
    """
    Delete a knowledge item from the knowledge base.
    
    Args:
        item_id: Knowledge item identifier
        knowledge_service: Knowledge service
    """
    try:
        # Delete the knowledge item
        success = await knowledge_service.delete_item(item_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge item not found: {item_id}",
            )
            
    except HTTPException:
        raise
        
    except Exception as e:
        logger.exception(f"Error deleting knowledge item: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting knowledge item: {str(e)}",
        ) 