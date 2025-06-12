"""
Dependency injection for the FinMate AI Platform.

This module provides dependency injection functions for FastAPI endpoints.
"""
import logging
from typing import Dict, Any

from fastapi import Depends, HTTPException, status

from agents.conductor import ConductorAgent
from agents.data_ingestion import DataIngestionAgent
from agents.url_scraper import URLScraperAgent
from agents.query_handler import QueryHandlerAgent
from agents.multi_intent import MultiIntentAgent
from agents.response_combiner import ResponseCombinerAgent
from agents.escalation import EscalationAgent
from agents.web_search import WebSearchAgent

from database.cognee_client import CogneeClient
from database.graph_db import GraphDBClient
from database.vector_db import VectorDBClient
from database.user_db import UserDBClient

from services.llm import LLMService
from services.memory import MemoryService
from services.transcription import TranscriptionService
from services.storage import StorageService
from services.knowledge import KnowledgeService
from services.escalation import EscalationService

from config import settings

logger = logging.getLogger(__name__)

# Services
def get_llm_service() -> LLMService:
    """Get LLM service instance."""
    return LLMService(
        api_key=settings.openai_api_key,
        model=settings.model_name,
        temperature=settings.temperature,
        max_retries=3,
        timeout=30
    )

# Database clients
def get_user_db() -> UserDBClient:
    """Get user database client instance."""
    return UserDBClient(
        data_dir=settings.user_data_dir,
    )

def get_memory_service(user_db: UserDBClient = Depends(get_user_db)) -> MemoryService:
    """Get memory service instance."""
    return MemoryService(
        user_db=user_db,
        redis_host=settings.redis_host,
        redis_port=settings.redis_port,
        redis_password=settings.redis_password,
        redis_db=settings.redis_db,
    )

def get_transcription_service() -> TranscriptionService:
    """Get transcription service instance."""
    return TranscriptionService(
        api_key=settings.openai_api_key,
    )

def get_storage_service() -> StorageService:
    """Get storage service instance."""
    return StorageService(
        upload_dir=settings.upload_dir,
        processed_dir=settings.processed_dir,
        temp_dir=settings.temp_dir,
    )

# Database clients
def get_graph_db() -> GraphDBClient:
    """Get graph database client instance."""
    return GraphDBClient(
        uri=settings.neo4j_uri,
        user=settings.neo4j_username,
        password=settings.neo4j_password,
    )

def get_vector_db() -> VectorDBClient:
    """Get vector database client instance."""
    return VectorDBClient(
        api_key=settings.vector_db_api_key,
        api_url=settings.vector_db_uri,
    )

def get_cognee_client(
    graph_db: GraphDBClient = Depends(get_graph_db),
    vector_db: VectorDBClient = Depends(get_vector_db),
) -> CogneeClient:
    """Get Cognee client instance."""
    return CogneeClient(
        graph_db=graph_db,
        vector_db=vector_db,
    )

# Admin services
def get_knowledge_service(vector_db: VectorDBClient = Depends(get_vector_db)) -> KnowledgeService:
    """Get knowledge service instance."""
    return KnowledgeService(vector_db_client=vector_db)

def get_escalation_service(user_db: UserDBClient = Depends(get_user_db)) -> EscalationService:
    """Get escalation service instance."""
    return EscalationService(user_db_client=user_db)

# Agents
def get_data_ingestion_agent(
    llm_service: LLMService = Depends(get_llm_service),
) -> DataIngestionAgent:
    """Get data ingestion agent instance."""
    return DataIngestionAgent(llm_service=llm_service)

def get_url_scraper_agent(
    llm_service: LLMService = Depends(get_llm_service),
) -> URLScraperAgent:
    """Get URL scraper agent instance."""
    return URLScraperAgent(
        llm_service=llm_service,
    )

def get_query_handler_agent(
    cognee_client: CogneeClient = Depends(get_cognee_client),
    vector_db: VectorDBClient = Depends(get_vector_db),
    graph_db: GraphDBClient = Depends(get_graph_db),
    llm_service: LLMService = Depends(get_llm_service),
    memory_service: MemoryService = Depends(get_memory_service),
) -> QueryHandlerAgent:
    """Get query handler agent instance."""
    return QueryHandlerAgent(
        cognee_client=cognee_client,
        vector_db=vector_db,
        graph_db=graph_db,
        llm_service=llm_service,
        memory_service=memory_service,
    )

def get_multi_intent_agent(
    llm_service: LLMService = Depends(get_llm_service),
) -> MultiIntentAgent:
    """Get multi-intent agent instance."""
    return MultiIntentAgent(
        llm_service=llm_service,
    )

def get_response_combiner_agent(
    llm_service: LLMService = Depends(get_llm_service),
) -> ResponseCombinerAgent:
    """Get response combiner agent instance."""
    return ResponseCombinerAgent(
        llm_service=llm_service,
    )

def get_escalation_agent(
    llm_service: LLMService = Depends(get_llm_service),
    memory_service: MemoryService = Depends(get_memory_service),
) -> EscalationAgent:
    """Get escalation agent instance."""
    return EscalationAgent(
        llm_service=llm_service,
        memory_service=memory_service,
    )

def get_web_search_agent(
    llm_service: LLMService = Depends(get_llm_service),
) -> WebSearchAgent:
    """Get web search agent instance."""
    return WebSearchAgent(
        llm_service=llm_service,
        search_api_key=settings.search_api_key,
        search_engine_id=settings.search_engine_id,
    )

def get_conductor_agent(
    data_ingestion_agent: DataIngestionAgent = Depends(get_data_ingestion_agent),
    url_scraper_agent: URLScraperAgent = Depends(get_url_scraper_agent),
    query_handler_agent: QueryHandlerAgent = Depends(get_query_handler_agent),
    multi_intent_agent: MultiIntentAgent = Depends(get_multi_intent_agent),
    response_combiner_agent: ResponseCombinerAgent = Depends(get_response_combiner_agent),
    escalation_agent: EscalationAgent = Depends(get_escalation_agent),
    web_search_agent: WebSearchAgent = Depends(get_web_search_agent),
    llm_service: LLMService = Depends(get_llm_service),
) -> ConductorAgent:
    """Get conductor agent instance."""
    return ConductorAgent(
        agents={
            "data_ingestion": data_ingestion_agent,
            "url_scraper": url_scraper_agent,
            "query_handler": query_handler_agent,
            "multi_intent": multi_intent_agent,
            "response_combiner": response_combiner_agent,
            "escalation": escalation_agent,
            "web_search": web_search_agent,
        },
        llm_service=llm_service,
    ) 