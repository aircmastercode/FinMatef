"""
Configuration settings for the FinMate AI Platform.

This module loads configuration from environment variables and
provides default values for development.
"""
import os
from typing import List, Optional

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    # API Settings
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS Settings
    cors_origins: List[str] = ["*"]  # In production, specify actual origins
    
    # OpenAI Settings
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    model_name: str = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
    max_tokens: int = int(os.getenv("MAX_TOKENS", "4096"))
    temperature: float = float(os.getenv("TEMPERATURE", "0.2"))
    
    # Cognee Settings
    cognee_api_key: str = os.getenv("COGNEE_API_KEY", "")
    cognee_api_url: str = os.getenv("COGNEE_API_URL", "https://api.cognee.com/v1")
    
    # Neo4j Settings
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    neo4j_username: str = os.getenv("NEO4J_USERNAME", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "password")
    
    # Vector DB Settings
    vector_db_uri: str = os.getenv("VECTOR_DB_URI", "")
    vector_db_api_key: str = os.getenv("VECTOR_DB_API_KEY", "")
    
    # Redis Settings
    redis_host: str = os.getenv("REDIS_HOST", "redis")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_password: Optional[str] = os.getenv("REDIS_PASSWORD", None)
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    
    # Search Settings
    search_api_key: str = os.getenv("SEARCH_API_KEY", "")
    search_engine_id: str = os.getenv("SEARCH_ENGINE_ID", "")
    
    # Storage Settings
    upload_dir: str = os.getenv("UPLOAD_DIR", "./data/uploads")
    processed_dir: str = os.getenv("PROCESSED_DIR", "./data/processed")
    temp_dir: str = os.getenv("TEMP_DIR", "./data/temp")
    user_data_dir: str = os.getenv("USER_DATA_DIR", "./data/users")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create settings instance
settings = Settings()

# Ensure required directories exist
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.processed_dir, exist_ok=True)
os.makedirs(settings.temp_dir, exist_ok=True)
os.makedirs(settings.user_data_dir, exist_ok=True) 