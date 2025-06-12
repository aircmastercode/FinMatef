"""
Cognee client for interfacing with knowledge graphs.

This module provides interfaces for using Cognee to interact with
both graph and vector databases in a unified way.
"""
import logging
from typing import Dict, Any, List, Optional, Union
from .graph_db import GraphDatabase
from .vector_db import VectorDatabase

logger = logging.getLogger(__name__)

class CogneeClient:
    """Client for Cognee knowledge graph framework."""
    
    def __init__(
        self, 
        graph_db: GraphDatabase,
        vector_db: VectorDatabase,
    ):
        """
        Initialize the Cognee client.
        
        Args:
            graph_db: Graph database interface
            vector_db: Vector database interface
        """
        self.graph_db = graph_db
        self.vector_db = vector_db
        logger.info("Initialized Cognee client")
    
    async def store_knowledge(
        self, content: str, metadata: Dict[str, Any], embedding: List[float] = None
    ) -> Dict[str, Any]:
        """
        Store knowledge in the graph and vector databases.
        
        Args:
            content: Content to store
            metadata: Metadata for the content
            embedding: Vector embedding for the content
            
        Returns:
            Dict[str, Any]: Node information
        """
        try:
            # Store in graph database
            node_props = {
                "content": content,
                **metadata
            }
            node_type = metadata.get("type", "Knowledge")
            graph_result = await self.graph_db.create_node(node_type, node_props)
            
            # If embedding provided, store in vector database
            vector_id = None
            if embedding:
                vector_metadata = {
                    "content": content[:200] + "..." if len(content) > 200 else content,
                    "graph_id": graph_result.get("id"),
                    **metadata
                }
                vector_id = await self.vector_db.add_vector(embedding, vector_metadata)
                
                # Update graph node with vector ID
                if "id" in graph_result:
                    await self.graph_db.run_query(
                        "MATCH (n) WHERE id(n) = $id SET n.vector_id = $vector_id",
                        {"id": graph_result["id"], "vector_id": vector_id}
                    )
            
            return {
                "graph_id": graph_result.get("id"),
                "vector_id": vector_id,
                "content": content,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error storing knowledge: {str(e)}")
            raise
    
    async def retrieve_knowledge(
        self, query: str, embedding: List[float] = None, filters: Dict[str, Any] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve knowledge using vector similarity and/or graph queries.
        
        Args:
            query: Query string
            embedding: Query vector embedding
            filters: Metadata filters
            top_k: Number of results to return
            
        Returns:
            List[Dict[str, Any]]: Retrieved knowledge
        """
        results = []
        
        try:
            # Vector search if embedding provided
            if embedding:
                vector_results = await self.vector_db.search(
                    embedding, top_k=top_k, filter=filters
                )
                
                for result in vector_results:
                    # Fetch full content from graph if needed
                    graph_id = result["metadata"].get("graph_id")
                    if graph_id:
                        node = await self.graph_db.get_node_by_id(graph_id)
                        if node:
                            results.append({
                                "content": node.get("content", ""),
                                "similarity": result["score"],
                                "metadata": {
                                    **node,
                                    "vector_id": result["id"]
                                }
                            })
                    else:
                        # Use vector metadata if no graph ID
                        results.append({
                            "content": result["metadata"].get("content", ""),
                            "similarity": result["score"],
                            "metadata": result["metadata"]
                        })
            else:
                # Graph-only search using text matching
                # Convert filters to Cypher conditions
                conditions = []
                params = {"query": f"%{query}%"}
                
                if filters:
                    for i, (key, value) in enumerate(filters.items()):
                        conditions.append(f"n.{key} = $filter_{i}")
                        params[f"filter_{i}"] = value
                
                where_clause = "WHERE n.content CONTAINS $query"
                if conditions:
                    where_clause += " AND " + " AND ".join(conditions)
                
                cypher_query = f"""
                    MATCH (n)
                    {where_clause}
                    RETURN n
                    LIMIT {top_k}
                """
                
                graph_results = await self.graph_db.run_query(cypher_query, params)
                
                for result in graph_results:
                    node = result["n"]
                    results.append({
                        "content": node.get("content", ""),
                        "similarity": 1.0,  # No similarity score for graph-only search
                        "metadata": node
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving knowledge: {str(e)}")
            return []
    
    async def create_relationship(
        self, source_id: Union[str, int], target_id: Union[str, int], 
        relation_type: str, properties: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create a relationship between knowledge nodes.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            relation_type: Type of relationship
            properties: Relationship properties
            
        Returns:
            Dict[str, Any]: Created relationship
        """
        try:
            return await self.graph_db.create_relationship(
                source_id, target_id, relation_type, properties
            )
        except Exception as e:
            logger.error(f"Error creating relationship: {str(e)}")
            raise
    
    async def run_graph_query(
        self, query: str, params: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Run a custom graph query.
        
        Args:
            query: Cypher query
            params: Query parameters
            
        Returns:
            List[Dict[str, Any]]: Query results
        """
        try:
            return await self.graph_db.run_query(query, params)
        except Exception as e:
            logger.error(f"Error running graph query: {str(e)}")
            raise 