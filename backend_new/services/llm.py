"""
LLM Service for interfacing with OpenAI's language models.

This service provides a clean interface for making LLM API calls with
proper error handling, retries, and response parsing.
"""
import os
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional, Union
import openai
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

class LLMService:
    """Service for interacting with OpenAI's language models."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.2,
        max_retries: int = 3,
        timeout: int = 30
    ):
        """
        Initialize the LLM service.
        
        Args:
            api_key: OpenAI API key. If not provided, will use OPENAI_API_KEY environment variable
            model: Model to use for completions
            temperature: Temperature parameter for completions
            max_retries: Maximum number of retry attempts for failed API calls
            timeout: Timeout in seconds for API calls
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided and OPENAI_API_KEY environment variable not set")
            
        self.client = AsyncOpenAI(api_key=self.api_key, timeout=timeout)
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self.timeout = timeout
    
    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((openai.APITimeoutError, openai.APIConnectionError))
    )
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        response_format: Optional[Dict[str, str]] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a chat completion using OpenAI's API.
        
        Args:
            messages: List of message objects with role and content
            temperature: Temperature for randomness (0-1)
            model: Override the default model
            response_format: Format for the response (e.g., {"type": "json_object"})
            max_tokens: Maximum tokens in the response
            
        Returns:
            Dict[str, Any]: Parsed response
        """
        try:
            kwargs = {
                "model": model or self.model,
                "messages": messages,
                "temperature": temperature if temperature is not None else self.temperature,
            }
            
            if response_format:
                kwargs["response_format"] = response_format
                
            if max_tokens:
                kwargs["max_tokens"] = max_tokens
            
            logger.debug(f"Making chat completion request with parameters: {kwargs}")
            
            response = await self.client.chat.completions.create(**kwargs)
            
            content = response.choices[0].message.content
            
            # If response is expected to be JSON, parse it
            if response_format and response_format.get("type") == "json_object":
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON response: {content}")
                    return {"error": "Invalid JSON response", "raw_content": content}
            
            return {"content": content}
            
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in chat completion: {str(e)}")
            raise
    
    async def analyze_intent(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the intent of a query.
        
        Args:
            query: User query
            context: Additional context information
            
        Returns:
            Dict[str, Any]: Intent analysis
        """
        intent_prompt = {
            "role": "system",
            "content": """Analyze the user's query to determine the intent.
Return your analysis as a JSON object with the following structure:
{
    "is_multi_intent": boolean,
    "intent": "primary intent category",
    "intents": [list of intent categories if multi-intent],
    "agent_mapping": {"intent": "agent_type"}
}

Available intent categories and corresponding agents:
- knowledge_query -> query_handler: For simple information retrieval
- web_search -> web_search: For information that might require searching the web
- escalate -> escalation: For queries requiring human assistance
- data_ingestion -> data_ingestion: For requests to ingest or process data
- url_scraping -> url_scraper: For requests to extract information from URLs
"""
        }
        
        chat_history_context = ""
        if "chat_history" in context:
            chat_history = context["chat_history"]
            if chat_history:
                chat_history_context = "\n\nChat history context:\n" + "\n".join([
                    f"User: {msg['query']}\nAssistant: {msg['response']}"
                    for msg in chat_history[-3:]  # Last 3 messages for context
                ])
        
        user_message = query
        if chat_history_context:
            user_message = f"{query}\n\n{chat_history_context}"
        
        return await self.chat_completion(
            messages=[
                intent_prompt,
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"}
        )
    
    async def generate_response(self, query: str, context: List[str], user_context: Dict[str, Any] = None) -> str:
        """
        Generate a natural language response to a query.
        
        Args:
            query: User query
            context: Relevant context information (passages, data)
            user_context: User-specific context information
            
        Returns:
            str: Generated response
        """
        context_str = "\n".join([f"- {ctx}" for ctx in context])
        
        chat_history = ""
        if user_context and "chat_history" in user_context:
            history = user_context["chat_history"]
            if history:
                chat_history = "\nRecent conversation history:\n" + "\n".join([
                    f"User: {msg['query']}\nAssistant: {msg['response']}"
                    for msg in history[-3:]  # Last 3 messages
                ])
        
        system_prompt = {
            "role": "system",
            "content": f"""You are an AI assistant for LenDen Club. Provide helpful, accurate, and concise answers.
            
Use the following information to answer the user's question:

{context_str}

{chat_history}

If you don't know the answer or don't have enough information, say so clearly and suggest what additional information might help."""
        }
        
        result = await self.chat_completion(
            messages=[
                system_prompt,
                {"role": "user", "content": query}
            ]
        )
        
        return result.get("content", "I'm sorry, I couldn't generate a response at this time.") 