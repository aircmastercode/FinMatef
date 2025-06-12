"""
Neo4j graph database interface.

This module provides interfaces for interacting with the Neo4j graph database,
including connection management, querying, and schema operations.
"""
import logging
from typing import Dict, Any, List, Optional, Union
import json
from neo4j import AsyncGraphDatabase

logger = logging.getLogger(__name__)

class GraphDBClient:
    """
    Client for interacting with the Neo4j graph database.
    
    This class provides a high-level interface for graph database operations,
    including knowledge graph traversal, relationship management, and querying.
    """
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "password",
        database: str = "neo4j"
    ):
        """
        Initialize the graph database client.
        
        Args:
            uri: Neo4j URI
            user: Neo4j username
            password: Neo4j password
            database: Neo4j database name
        """
        self.db = GraphDatabase(uri, user, password, database)
        logger.info("Initialized graph database client")
    
    async def close(self):
        """Close the database connection."""
        await self.db.close()
    
    async def create_entity(
        self, entity_type: str, properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create an entity node in the knowledge graph.
        
        Args:
            entity_type: Type of entity
            properties: Entity properties
            
        Returns:
            Dict[str, Any]: Created entity
        """
        return await self.db.create_node(entity_type, properties)
    
    async def create_relationship(
        self, source_id: Union[str, int], target_id: Union[str, int],
        relation_type: str, properties: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create a relationship between entities.
        
        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            relation_type: Type of relationship
            properties: Relationship properties
            
        Returns:
            Dict[str, Any]: Created relationship
        """
        return await self.db.create_relationship(
            source_id, target_id, relation_type, properties
        )
    
    async def get_entity(self, entity_id: Union[str, int]) -> Optional[Dict[str, Any]]:
        """
        Get an entity by ID.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            Optional[Dict[str, Any]]: Entity properties or None if not found
        """
        return await self.db.get_node_by_id(entity_id)
    
    async def search_entities(
        self, entity_type: str = None, properties: Dict[str, Any] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for entities.
        
        Args:
            entity_type: Type of entity to search for
            properties: Properties to match
            limit: Maximum number of results
            
        Returns:
            List[Dict[str, Any]]: Matching entities
        """
        return await self.db.search_nodes(entity_type, properties, limit)
    
    async def query(
        self, query: str, params: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Run a custom Cypher query.
        
        Args:
            query: Cypher query
            params: Query parameters
            
        Returns:
            List[Dict[str, Any]]: Query results
        """
        return await self.db.run_query(query, params)
    
    async def get_related_entities(
        self, entity_id: Union[str, int], relation_type: str = None,
        direction: str = "outgoing", limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get entities related to the given entity.
        
        Args:
            entity_id: Entity ID
            relation_type: Type of relationship (optional)
            direction: Relationship direction ("outgoing", "incoming", or "both")
            limit: Maximum number of results
            
        Returns:
            List[Dict[str, Any]]: Related entities
        """
        # Build relationship pattern based on direction
        if direction == "outgoing":
            rel_pattern = "-[r]->"
        elif direction == "incoming":
            rel_pattern = "<-[r]-"
        else:  # both
            rel_pattern = "-[r]-"
        
        # Add relationship type if specified
        if relation_type:
            rel_pattern = rel_pattern.replace("r", f"r:{relation_type}")
        
        query = f"""
            MATCH (n){rel_pattern}(related)
            WHERE id(n) = $entity_id
            RETURN related, type(r) as relationship_type
            LIMIT {limit}
        """
        
        results = await self.db.run_query(query, {"entity_id": entity_id})
        
        # Format results
        formatted_results = []
        for result in results:
            entity = result["related"]
            entity["relationship_type"] = result["relationship_type"]
            formatted_results.append(entity)
            
        return formatted_results

class GraphDatabase:
    """Neo4j graph database interface."""
    
    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        database: str = "neo4j"
    ):
        """
        Initialize the Neo4j graph database connection.
        
        Args:
            uri: Neo4j URI
            user: Neo4j username
            password: Neo4j password
            database: Neo4j database name
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        logger.info(f"Initialized Neo4j connection to {uri}")
    
    async def close(self):
        """Close the Neo4j driver connection."""
        if self.driver:
            await self.driver.close()
            logger.info("Closed Neo4j connection")
    
    async def run_query(
        self, query: str, params: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Run a Cypher query against the Neo4j database.
        
        Args:
            query: Cypher query
            params: Query parameters
            
        Returns:
            List[Dict[str, Any]]: Query results
        """
        try:
            params = params or {}
            async with self.driver.session(database=self.database) as session:
                result = await session.run(query, params)
                records = await result.values()
                
                # Convert Neo4j objects to Python native types
                records = [
                    dict(zip(result.keys(), [self._convert_neo4j_value(v) for v in values]))
                    for values in records
                ]
                
                return records
        except Exception as e:
            logger.error(f"Neo4j query error: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
    
    async def create_node(
        self, label: str, properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a node in the graph.
        
        Args:
            label: Node label
            properties: Node properties
            
        Returns:
            Dict[str, Any]: Created node properties
        """
        query = f"CREATE (n:{label} $props) RETURN n"
        params = {"props": properties}
        
        results = await self.run_query(query, params)
        return results[0]["n"] if results else {}
    
    async def get_node_by_id(
        self, node_id: Union[str, int]
    ) -> Optional[Dict[str, Any]]:
        """
        Get a node by its ID.
        
        Args:
            node_id: Node ID (neo4j internal ID)
            
        Returns:
            Optional[Dict[str, Any]]: Node properties or None if not found
        """
        query = "MATCH (n) WHERE id(n) = $id RETURN n"
        params = {"id": node_id}
        
        results = await self.run_query(query, params)
        return results[0]["n"] if results else None
    
    async def create_relationship(
        self, from_id: Union[str, int], to_id: Union[str, int], 
        rel_type: str, properties: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create a relationship between nodes.
        
        Args:
            from_id: Source node ID
            to_id: Target node ID
            rel_type: Relationship type
            properties: Relationship properties
            
        Returns:
            Dict[str, Any]: Created relationship properties
        """
        properties = properties or {}
        query = f"""
            MATCH (from) WHERE id(from) = $from_id
            MATCH (to) WHERE id(to) = $to_id
            CREATE (from)-[r:{rel_type} $props]->(to)
            RETURN r
        """
        params = {
            "from_id": from_id,
            "to_id": to_id,
            "props": properties
        }
        
        results = await self.run_query(query, params)
        return results[0]["r"] if results else {}
    
    async def search_nodes(
        self, labels: Union[str, List[str]] = None, properties: Dict[str, Any] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for nodes matching labels and properties.
        
        Args:
            labels: Node label(s)
            properties: Node properties to match
            limit: Maximum number of results
            
        Returns:
            List[Dict[str, Any]]: Matching nodes
        """
        properties = properties or {}
        
        # Build label part of query
        if labels:
            if isinstance(labels, list):
                label_str = ":".join(labels)
            else:
                label_str = labels
            node_pattern = f"(n:{label_str})"
        else:
            node_pattern = "(n)"
        
        # Build property conditions
        property_conditions = []
        params = {}
        
        for i, (key, value) in enumerate(properties.items()):
            param_name = f"prop_{i}"
            property_conditions.append(f"n.{key} = ${param_name}")
            params[param_name] = value
        
        # Build query
        query = f"MATCH {node_pattern}"
        
        if property_conditions:
            query += " WHERE " + " AND ".join(property_conditions)
        
        query += f" RETURN n LIMIT {limit}"
        
        results = await self.run_query(query, params)
        return [result["n"] for result in results]
    
    def _convert_neo4j_value(self, value):
        """
        Convert Neo4j values to Python native types.
        
        Args:
            value: Value to convert
            
        Returns:
            Converted value
        """
        # Handle specific Neo4j types here as needed
        # This is a placeholder for custom type conversion logic
        # For many simple cases, Neo4j driver already handles conversion
        return value 