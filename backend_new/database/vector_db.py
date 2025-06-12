"""
Vector database interface.

This module provides interfaces for interacting with vector databases,
including embedding storage, similarity search, and metadata operations.
"""
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
import numpy as np
from uuid import uuid4

logger = logging.getLogger(__name__)

class VectorDBClient:
    """
    Client for interacting with vector databases.
    
    This class provides a high-level interface for vector database operations
    like storing, retrieving, and searching vector embeddings.
    """
    
    def __init__(self, 
                 api_key: str = None,
                 api_url: str = None,
                 embedding_dim: int = 1536,
                 index_name: str = "default"):
        """
        Initialize the vector database client.
        
        Args:
            api_key: API key for the vector database service
            api_url: URL for the vector database service
            embedding_dim: Dimension of embeddings
            index_name: Name of the vector index
        """
        self.api_key = api_key
        self.api_url = api_url
        self.embedding_dim = embedding_dim
        self.index_name = index_name
        
        # Use in-memory database for development
        self.db = VectorDatabase(
            embedding_dim=embedding_dim,
            index_name=index_name
        )
        
        logger.info(f"Initialized vector database client for index {index_name}")
    
    async def store(
        self, 
        text: str, 
        embedding: List[float], 
        metadata: Dict[str, Any] = None,
        id: Optional[str] = None
    ) -> str:
        """
        Store text with its embedding and metadata.
        
        Args:
            text: Text content
            embedding: Vector embedding
            metadata: Associated metadata
            id: Optional vector ID
            
        Returns:
            str: Vector ID
        """
        if metadata is None:
            metadata = {}
        
        # Add text to metadata
        metadata["text"] = text
        
        # Store in vector database
        return await self.db.add_vector(
            vector=embedding,
            metadata=metadata,
            id=id
        )
    
    async def search(
        self, 
        query: str, 
        embedding: List[float] = None,
        limit: int = 5,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar content.
        
        Args:
            query: Query text
            embedding: Query embedding (if pre-computed)
            limit: Number of results to return
            filters: Metadata filters
            
        Returns:
            List[Dict[str, Any]]: Search results
        """
        # If embedding not provided, would typically generate it here
        # For now, we'll assume it's provided
        if embedding is None:
            logger.warning("No embedding provided for search, using zeros")
            embedding = [0.0] * self.embedding_dim
            
        # Search vector database
        results = await self.db.search(
            query_vector=embedding,
            top_k=limit,
            filter=filters
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "id": result["id"],
                "text": result["metadata"].get("text", ""),
                "metadata": {k: v for k, v in result["metadata"].items() if k != "text"},
                "score": result["score"]
            })
            
        return formatted_results
    
    async def delete(self, id: str) -> bool:
        """
        Delete content by ID.
        
        Args:
            id: Content ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        return await self.db.delete_vector(id)
    
    async def update_metadata(self, id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update metadata for content.
        
        Args:
            id: Content ID
            metadata: New metadata
            
        Returns:
            bool: True if updated, False if not found
        """
        return await self.db.update_metadata(id, metadata)

class VectorDatabase:
    """Vector database interface."""
    
    def __init__(self, 
                 embedding_dim: int = 1536, 
                 index_name: str = "default",
                 similarity_threshold: float = 0.75):
        """
        Initialize the vector database.
        
        Args:
            embedding_dim: Dimension of embeddings
            index_name: Name of the vector index
            similarity_threshold: Minimum similarity threshold for matches
        """
        self.embedding_dim = embedding_dim
        self.index_name = index_name
        self.similarity_threshold = similarity_threshold
        
        # In-memory storage for development - would be replaced with a proper vector DB
        # like Pinecone, Weaviate, Qdrant, etc. in production
        self._vectors = {}
        self._metadata = {}
        
        logger.info(f"Initialized vector database with dimension {embedding_dim}")
    
    async def add_vector(
        self, 
        vector: List[float], 
        metadata: Dict[str, Any] = None, 
        id: Optional[str] = None
    ) -> str:
        """
        Add a vector to the database.
        
        Args:
            vector: Vector embedding
            metadata: Associated metadata
            id: Optional vector ID
            
        Returns:
            str: Vector ID
        """
        # Generate ID if not provided
        if id is None:
            id = str(uuid4())
        
        # Validate vector dimension
        if len(vector) != self.embedding_dim:
            raise ValueError(f"Vector dimension {len(vector)} doesn't match expected {self.embedding_dim}")
        
        # Store vector and metadata
        self._vectors[id] = np.array(vector, dtype=np.float32)
        self._metadata[id] = metadata or {}
        
        logger.debug(f"Added vector with ID {id}")
        return id
    
    async def get_vector(self, id: str) -> Optional[Tuple[List[float], Dict[str, Any]]]:
        """
        Get a vector by ID.
        
        Args:
            id: Vector ID
            
        Returns:
            Optional[Tuple[List[float], Dict[str, Any]]]: (vector, metadata) tuple or None if not found
        """
        if id in self._vectors:
            vector = self._vectors[id].tolist()
            metadata = self._metadata[id]
            return vector, metadata
        return None
    
    async def delete_vector(self, id: str) -> bool:
        """
        Delete a vector by ID.
        
        Args:
            id: Vector ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        if id in self._vectors:
            del self._vectors[id]
            del self._metadata[id]
            logger.debug(f"Deleted vector with ID {id}")
            return True
        return False
    
    async def search(
        self, 
        query_vector: List[float], 
        top_k: int = 5, 
        filter: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: Query vector embedding
            top_k: Number of results to return
            filter: Metadata filter to apply
            
        Returns:
            List[Dict[str, Any]]: Search results with vectors, metadata, and scores
        """
        query_vector_np = np.array(query_vector, dtype=np.float32)
        
        # Calculate similarities and filter results
        results = []
        for id, vector in self._vectors.items():
            # Apply metadata filter if provided
            if filter and not self._matches_filter(self._metadata[id], filter):
                continue
                
            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_vector_np, vector)
            
            # Add to results if above threshold
            if similarity >= self.similarity_threshold:
                results.append({
                    "id": id,
                    "vector": vector.tolist(),
                    "metadata": self._metadata[id],
                    "score": float(similarity)
                })
        
        # Sort by similarity (descending) and limit to top_k
        results = sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]
        
        logger.debug(f"Found {len(results)} vector matches")
        return results
    
    async def update_metadata(self, id: str, metadata: Dict[str, Any], merge: bool = True) -> bool:
        """
        Update metadata for a vector.
        
        Args:
            id: Vector ID
            metadata: New metadata
            merge: Whether to merge with existing metadata or replace
            
        Returns:
            bool: True if updated, False if not found
        """
        if id in self._metadata:
            if merge:
                self._metadata[id].update(metadata)
            else:
                self._metadata[id] = metadata
            logger.debug(f"Updated metadata for vector {id}")
            return True
        return False
    
    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            v1: First vector
            v2: Second vector
            
        Returns:
            float: Cosine similarity
        """
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return float(np.dot(v1, v2) / (norm1 * norm2))
    
    def _matches_filter(self, metadata: Dict[str, Any], filter: Dict[str, Any]) -> bool:
        """
        Check if metadata matches a filter.
        
        Args:
            metadata: Metadata to check
            filter: Filter to apply
            
        Returns:
            bool: True if matches, False otherwise
        """
        for key, value in filter.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True 