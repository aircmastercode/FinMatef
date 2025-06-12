"""
Multi-Intent Agent - Handles complex queries with multiple intents.

This agent breaks down complex queries into simpler sub-queries that can be
handled by specialist agents.
"""
from typing import Dict, Any, List
import logging
from .base import Agent
from services.llm import LLMService

logger = logging.getLogger(__name__)

class MultiIntentAgent(Agent):
    """
    Agent for handling queries with multiple intents.
    
    This agent breaks down complex queries into multiple sub-queries, each
    with a single intent, that can be processed separately by specialist agents.
    """
    
    def __init__(self, llm_service: LLMService):
        """
        Initialize the multi-intent agent.
        
        Args:
            llm_service: LLM service for query decomposition
        """
        super().__init__()
        self.llm_service = llm_service
    
    async def process(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a multi-intent query by breaking it down into sub-queries.
        
        Args:
            input_data: The input data including the user query and intent analysis
            context: Additional context information
            
        Returns:
            Dict[str, Any]: The processed result with sub-queries
        """
        query = input_data.get("query", "")
        intent_analysis = input_data.get("intent_analysis", {})
        
        logger.info(f"Breaking down multi-intent query: {query[:100]}...")
        
        # Use the intent analysis if available, or perform our own analysis
        if "intents" in intent_analysis and intent_analysis["intents"]:
            return await self._decompose_with_intent_analysis(query, intent_analysis)
        else:
            return await self._decompose_without_intent_analysis(query, context)
    
    async def _decompose_with_intent_analysis(self, query: str, intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decompose a query using existing intent analysis.
        
        Args:
            query: The original query
            intent_analysis: The intent analysis from the conductor agent
            
        Returns:
            Dict[str, Any]: The decomposed query with sub-queries
        """
        intents = intent_analysis.get("intents", [])
        agent_mapping = intent_analysis.get("agent_mapping", {})
        
        # Use LLM to decompose the query based on the identified intents
        decomposition_prompt = {
            "role": "system",
            "content": f"""Break down the following multi-intent query into {len(intents)} separate sub-queries.
Each sub-query should address exactly one intent from the list: {intents}.

Return your analysis as a JSON array of sub-queries, each with the following structure:
[
    {{
        "text": "the sub-query text",
        "intent": "the specific intent this sub-query addresses"
    }},
    ...
]

Make sure each sub-query stands on its own and can be understood without the context of the other sub-queries.
"""
        }
        
        result = await self.llm_service.chat_completion(
            messages=[
                decomposition_prompt,
                {"role": "user", "content": query}
            ],
            response_format={"type": "json_object"}
        )
        
        sub_queries = result.get("sub_queries", [])
        if not sub_queries:
            # Format the result properly if it's not in the expected format
            # This handles cases where the LLM returns a direct array instead of nested object
            if isinstance(result, list):
                sub_queries = result
        
        return {
            "original_query": query,
            "sub_queries": sub_queries,
        }
    
    async def _decompose_without_intent_analysis(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decompose a query without existing intent analysis.
        
        Args:
            query: The original query
            context: Additional context information
            
        Returns:
            Dict[str, Any]: The decomposed query with sub-queries
        """
        # Use LLM to both identify intents and decompose the query
        decomposition_prompt = {
            "role": "system",
            "content": """Analyze the following query and:
1. Determine if it contains multiple intents/questions
2. Break it down into separate sub-queries, each with a single intent
3. Identify the intent category for each sub-query

Return your analysis as a JSON object with the following structure:
{
    "is_multi_intent": boolean,
    "sub_queries": [
        {
            "text": "the sub-query text",
            "intent": "the intent category (knowledge_query, web_search, escalate, etc.)"
        },
        ...
    ]
}

Available intent categories:
- knowledge_query: For simple information retrieval
- web_search: For information that might require searching the web
- escalate: For queries requiring human assistance
- data_ingestion: For requests to ingest or process data
- url_scraping: For requests to extract information from URLs
"""
        }
        
        result = await self.llm_service.chat_completion(
            messages=[
                decomposition_prompt,
                {"role": "user", "content": query}
            ],
            response_format={"type": "json_object"}
        )
        
        # If LLM determines it's not multi-intent, create a single sub-query
        if not result.get("is_multi_intent", True):
            return {
                "original_query": query,
                "sub_queries": [
                    {
                        "text": query,
                        "intent": result.get("intent", "knowledge_query")
                    }
                ]
            }
        
        return {
            "original_query": query,
            "sub_queries": result.get("sub_queries", []),
        } 