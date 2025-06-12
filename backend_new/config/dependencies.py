"""
Dependency injection for FastAPI application components.
"""
from fastapi import Depends

from .settings import get_settings, Settings
from ..database.cognee_client import CogneeClient
from ..database.graph_db import GraphDatabase
from ..database.vector_db import VectorDatabase
from ..database.user_db import UserDatabase
from ..services.llm import LLMService
from ..services.memory import MemoryService
from ..services.transcription import TranscriptionService
from ..agents.conductor import ConductorAgent

# Database dependencies
def get_graph_db(settings: Settings = Depends(get_settings)) -> GraphDatabase:
    """Get GraphDatabase instance."""
    return GraphDatabase(
        uri=settings.NEO4J_URI,
        user=settings.NEO4J_USER,
        password=settings.NEO4J_PASSWORD
    )

def get_vector_db() -> VectorDatabase:
    """Get VectorDatabase instance."""
    return VectorDatabase()

def get_user_db() -> UserDatabase:
    """Get UserDatabase instance."""
    return UserDatabase()

def get_cognee_client(
    graph_db: GraphDatabase = Depends(get_graph_db),
    vector_db: VectorDatabase = Depends(get_vector_db)
) -> CogneeClient:
    """Get CogneeClient instance."""
    return CogneeClient(graph_db, vector_db)

# Service dependencies
def get_llm_service(settings: Settings = Depends(get_settings)) -> LLMService:
    """Get LLMService instance."""
    return LLMService(api_key=settings.OPENAI_API_KEY, model=settings.LLM_MODEL, temperature=settings.LLM_TEMPERATURE)

def get_memory_service(user_db: UserDatabase = Depends(get_user_db)) -> MemoryService:
    """Get MemoryService instance."""
    return MemoryService(user_db)

def get_transcription_service() -> TranscriptionService:
    """Get TranscriptionService instance."""
    return TranscriptionService()

# Agent dependencies
def get_conductor_agent() -> ConductorAgent:
    """Get ConductorAgent instance."""
    # Note: This is a placeholder. The actual conductor agent should be initialized
    # in the FastAPI application startup and stored in app.state.
    from ..main import app
    return app.state.conductor_agent 