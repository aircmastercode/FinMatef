"""
Web Search Agent - Search the web for current information.

This agent handles web searches to retrieve current information
from the internet when knowledge base information is insufficient.
"""
import logging
import aiohttp
import json
from typing import Dict, Any, List, Optional

from .base import Agent
from services.llm import LLMService

logger = logging.getLogger(__name__)

class WebSearchAgent(Agent):
    """
    Agent for performing web searches to retrieve external information.
    
    This agent performs web searches using search APIs to retrieve
    current information not available in the internal knowledge base.
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        search_api_key: str,
        search_engine_id: str,
    ):
        """
        Initialize the web search agent.
        
        Args:
            llm_service: Service for language model processing
            search_api_key: API key for search provider
            search_engine_id: Custom search engine ID or configuration
        """
        super().__init__()
        self.llm_service = llm_service
        self.search_api_key = search_api_key
        self.search_engine_id = search_engine_id
        self.session = None
    
    async def _get_session(self):
        """Get or create an aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={"User-Agent": "LenDen Club AI Agent"}
            )
        return self.session
    
    async def process(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a web search request.
        
        Args:
            input_data: Input data containing search query
            context: Additional context
            
        Returns:
            Dict[str, Any]: Search results
        """
        query = input_data.get("query")
        
        if not query:
            logger.error("No search query provided")
            return {
                "status": "error",
                "message": "No search query provided"
            }
        
        try:
            # Generate optimized search queries based on the original query
            search_queries = await self._generate_search_queries(query)
            
            # Perform search for each generated query
            all_results = []
            for search_query in search_queries:
                results = await self._perform_search(search_query)
                if results:
                    all_results.extend(results)
            
            # Remove duplicates
            unique_results = []
            seen_urls = set()
            for result in all_results:
                url = result.get("url")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_results.append(result)
            
            # Limit to top results
            top_results = unique_results[:5]
            
            # Summarize search results with LLM
            summary = await self._summarize_results(query, top_results)
            
            return {
                "status": "success",
                "message": "Web search completed successfully",
                "original_query": query,
                "search_queries": search_queries,
                "results": top_results,
                "summary": summary,
                "result_count": len(top_results)
            }
            
        except Exception as e:
            logger.error(f"Error processing web search: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing web search: {str(e)}",
                "query": query
            }
    
    async def _generate_search_queries(self, original_query: str) -> List[str]:
        """
        Generate optimized search queries based on the original user query.
        
        Args:
            original_query: The original user query
            
        Returns:
            List[str]: List of optimized search queries
        """
        try:
            system_prompt = {
                "role": "system",
                "content": """You are a search query optimizer for LenDen Club's AI assistant.
Your task is to convert a user's natural language question into 1-3 effective web search queries.

Guidelines for creating search queries:
1. Focus on the core information need
2. Remove unnecessary words and phrases
3. Use keywords and specific terms
4. Include domain-specific terms for financial queries
5. For complex questions, create multiple queries focusing on different aspects
6. If the question is specific to LenDen Club, include "LenDen Club" in at least one query

Return an array of 1-3 effective search queries as a JSON object.
"""
            }
            
            user_prompt = {
                "role": "user",
                "content": f"""Original user query: {original_query}

Generate 1-3 effective search queries to find relevant information for this query.
Return only the search queries as a JSON array like this:
{{
    "search_queries": ["query 1", "query 2", "query 3"]
}}
"""
            }
            
            result = await self.llm_service.chat_completion(
                messages=[system_prompt, user_prompt],
                response_format={"type": "json_object"}
            )
            
            search_queries = result.get("search_queries", [])
            
            # Ensure we have at least the original query
            if not search_queries:
                search_queries = [original_query]
                
            return search_queries
            
        except Exception as e:
            logger.error(f"Error generating search queries: {str(e)}")
            # Fall back to the original query
            return [original_query]
    
    async def _perform_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Perform a web search using the search API.
        
        Args:
            query: Search query
            
        Returns:
            List[Dict[str, Any]]: Search results
        """
        # For demonstration, we'll use a mock response
        # In a real implementation, this would call a search API like Google Custom Search or Bing
        try:
            session = await self._get_session()
            
            # This is a placeholder for the actual API call
            # In a real implementation, you would use:
            # url = f"https://www.googleapis.com/customsearch/v1?key={self.search_api_key}&cx={self.search_engine_id}&q={query}"
            # async with session.get(url) as response:
            #     data = await response.json()
            
            # Mock response for demonstration
            mock_results = []
            words = query.split()
            
            for i in range(3):
                mock_results.append({
                    "title": f"Result {i+1} for {' '.join(words[:3])}",
                    "url": f"https://example.com/result{i+1}",
                    "snippet": f"This is a mock search result for the query '{query}'. It contains information about {' '.join(words[:3])} and related topics that would be relevant to the user's question.",
                    "source": "example.com"
                })
            
            return mock_results
            
        except Exception as e:
            logger.error(f"Error performing search: {str(e)}")
            return []
    
    async def _summarize_results(self, original_query: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Summarize search results using LLM.
        
        Args:
            original_query: Original search query
            results: List of search results
            
        Returns:
            Dict[str, Any]: Summary of search results
        """
        try:
            # Format results for the LLM
            formatted_results = "\n\n".join([
                f"Source {i+1}: {result.get('title')}\nURL: {result.get('url')}\nSnippet: {result.get('snippet')}"
                for i, result in enumerate(results)
            ])
            
            system_prompt = {
                "role": "system",
                "content": """You are a web search results analyzer for LenDen Club's AI assistant.
Your task is to analyze search results for a user query and provide:
1. A brief summary of the key information found
2. Key facts or points relevant to the query
3. An assessment of how well the search results answer the query

Be objective and factual. Focus on information relevant to the original query.
Note any areas where the search results might be insufficient or where more information is needed.
"""
            }
            
            user_prompt = {
                "role": "user",
                "content": f"""Original user query: {original_query}

Search results:
{formatted_results}

Please analyze these search results and provide:
1. A brief summary of the key information (2-3 sentences)
2. 3-5 key facts or points relevant to the query
3. An assessment of how well these results answer the original query (including any limitations)

Return your analysis as a JSON object with these fields:
{{
    "summary": "Brief summary of information",
    "key_facts": ["Fact 1", "Fact 2", "Fact 3"],
    "relevance_assessment": "Assessment of how well results answer the query",
    "confidence": 0.7 // Confidence score between 0 and 1
}}
"""
            }
            
            result = await self.llm_service.chat_completion(
                messages=[system_prompt, user_prompt],
                response_format={"type": "json_object"}
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error summarizing search results: {str(e)}")
            return {
                "summary": "Error summarizing search results",
                "key_facts": [],
                "relevance_assessment": "Unable to assess relevance due to an error",
                "confidence": 0.0
            }
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.debug("Closed web search session")
