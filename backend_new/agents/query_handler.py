"""
Query Handler Agent - Process user queries and retrieve knowledge.

This agent handles natural language queries from users, retrieves relevant
information from the knowledge base, and generates responses.
"""
import logging
import json
from typing import Dict, Any, List, Optional, Union

from .base import Agent
from database.cognee_client import CogneeClient
from database.vector_db import VectorDBClient
from database.graph_db import GraphDBClient
from services.llm import LLMService
from services.memory import MemoryService

logger = logging.getLogger(__name__)

class QueryHandlerAgent(Agent):
    """
    Agent for handling user queries.
    
    This agent processes natural language questions from users,
    retrieves relevant information, and generates contextually relevant responses.
    """
    
    def __init__(
        self,
        cognee_client: CogneeClient,
        vector_db: VectorDBClient,
        graph_db: GraphDBClient,
        llm_service: LLMService,
        memory_service: MemoryService,
    ):
        """
        Initialize the query handler agent.
        
        Args:
            cognee_client: Client for interacting with cognee knowledge base
            vector_db: Client for vector database operations
            graph_db: Client for graph database operations
            llm_service: Service for language model processing
            memory_service: Service for handling conversation memory
        """
        super().__init__()
        self.cognee_client = cognee_client
        self.vector_db = vector_db
        self.graph_db = graph_db
        self.llm_service = llm_service
        self.memory_service = memory_service
    
    async def process(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a user query.
        
        Args:
            input_data: Input data containing user query
            context: Additional context including user_id, session_id
            
        Returns:
            Dict[str, Any]: Processing result with response
        """
        query = input_data.get("query")
        user_id = context.get("user_id")
        session_id = context.get("session_id")
        
        if not query:
            logger.error("No query provided")
            return {
                "status": "error",
                "message": "No query provided"
            }
        
        try:
            # Get conversation history
            conversation_memory = await self.memory_service.get_conversation_memory(
                user_id=user_id,
                session_id=session_id,
                limit=10  # Get last 10 messages for context
            )
            
            # Get relevant knowledge
            knowledge = await self._retrieve_knowledge(query, conversation_memory)
            
            # Generate response based on knowledge and conversation history
            response = await self._generate_response(query, knowledge, conversation_memory)
            
            # Save query and response to memory
            await self.memory_service.add_user_message(
                user_id=user_id,
                session_id=session_id,
                content=query
            )
            
            await self.memory_service.add_assistant_message(
                user_id=user_id,
                session_id=session_id,
                content=response["response"],
                metadata={
                    "knowledge_sources": response.get("sources", []),
                    "confidence": response.get("confidence", 0.0),
                }
            )
            
            return {
                "status": "success",
                "query": query,
                "response": response["response"],
                "sources": response.get("sources", []),
                "confidence": response.get("confidence", 0.0),
                "needs_escalation": response.get("needs_escalation", False),
                "escalation_reason": response.get("escalation_reason", ""),
                "metadata": {
                    "retrieved_knowledge_count": len(knowledge),
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing query '{query}': {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing query: {str(e)}",
                "query": query
            }
    
    async def _retrieve_knowledge(
        self, query: str, conversation_memory: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant knowledge for the user query.
        
        Args:
            query: User query
            conversation_memory: Recent conversation history
            
        Returns:
            List[Dict[str, Any]]: Retrieved knowledge items
        """
        try:
            # For context, extract relevant context from conversation history
            context_message = ""
            if conversation_memory:
                recent_messages = conversation_memory[-3:]  # Last 3 messages
                context_message = "\n".join([
                    f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                    for msg in recent_messages
                ])
            
            # Use cognee client to retrieve relevant knowledge
            search_query = query
            if context_message:
                search_query = f"{context_message}\n\nCurrent query: {query}"
            
            # Get knowledge from cognee
            knowledge_results = await self.cognee_client.search_knowledge(
                query=search_query,
                limit=5,  # Get top 5 results
                threshold=0.6  # Minimum similarity score
            )
            
            # Alternatively, use vector DB directly
            if not knowledge_results or len(knowledge_results) < 3:
                # Fallback to vector DB if no results from cognee or not enough results
                vector_results = await self.vector_db.search(
                    query=search_query,
                    limit=3,
                    filters={}  # No additional filters
                )
                
                if vector_results:
                    knowledge_results.extend(vector_results)
            
            # Deduplicate results
            seen_ids = set()
            unique_results = []
            for item in knowledge_results:
                item_id = item.get("id") or item.get("node_id")
                if item_id and item_id not in seen_ids:
                    seen_ids.add(item_id)
                    unique_results.append(item)
            
            return unique_results
            
        except Exception as e:
            logger.error(f"Error retrieving knowledge: {str(e)}")
            return []
    
    async def _generate_response(
        self, query: str, knowledge: List[Dict[str, Any]], conversation_memory: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a response based on the query, retrieved knowledge, and conversation history.
        
        Args:
            query: User query
            knowledge: Retrieved knowledge items
            conversation_memory: Recent conversation history
            
        Returns:
            Dict[str, Any]: Generated response
        """
        # Format knowledge for context
        knowledge_context = ""
        sources = []
        
        for i, item in enumerate(knowledge):
            content = item.get("content") or item.get("text") or ""
            source = item.get("source") or item.get("metadata", {}).get("source", f"Document {i+1}")
            
            if content:
                knowledge_context += f"\n\nSource {i+1} ({source}):\n{content}"
                sources.append(source)
        
        # Format conversation history
        conversation_context = ""
        if conversation_memory:
            # Get last few messages for immediate context
            recent_messages = conversation_memory[-5:]  # Last 5 messages
            conversation_context = "\n".join([
                f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                for msg in recent_messages
            ])
        
        # Create the prompt for the LLM
        system_prompt = {
            "role": "system",
            "content": """You are the AI assistant for LenDen Club, providing helpful, accurate information about financial products, services, and policies. Your responses should be:
1. Accurate and based on the provided knowledge sources
2. Clear and concise
3. Helpful and professional
4. Candid about limitations if you don't have enough information

When responding:
- Only reference information from the provided knowledge sources
- If the knowledge sources don't contain relevant information, acknowledge the limitations
- Cite sources when appropriate using the source identifier
- Never make up information or provide misleading responses
- If you need to escalate to a human, clearly indicate that in your response_metadata

For financial advice, always include appropriate disclaimers.
"""
        }
        
        user_prompt = {
            "role": "user", 
            "content": f"""Previous conversation:
{conversation_context}

User query: {query}

Relevant knowledge:
{knowledge_context}

Please provide a response based on the relevant knowledge sources. 
If you cannot answer the question based on the provided knowledge, acknowledge the limitations and suggest next steps.

For your internal assessment only (will not be shown to the user), include:
1. Confidence level (0-1) in your response
2. Whether this query needs human escalation (true/false)
3. Reason for escalation, if needed
"""
        }
        
        try:
            # Call the LLM for response generation
            completion_result = await self.llm_service.chat_completion(
                messages=[system_prompt, user_prompt],
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            response_text = completion_result.get("response") or completion_result.get("answer", "")
            confidence = float(completion_result.get("confidence", 0.7))
            needs_escalation = completion_result.get("needs_escalation", False)
            escalation_reason = completion_result.get("escalation_reason", "")
            
            return {
                "response": response_text,
                "sources": sources,
                "confidence": confidence,
                "needs_escalation": needs_escalation,
                "escalation_reason": escalation_reason
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                "response": "I apologize, but I encountered an error while generating a response. Please try asking your question again.",
                "sources": [],
                "confidence": 0.0,
                "needs_escalation": True,
                "escalation_reason": f"Error generating response: {str(e)}"
            }
