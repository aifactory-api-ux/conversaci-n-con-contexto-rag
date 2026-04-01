from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional

from shared.config import Settings as BaseSettings

class QueryServiceSettings(BaseSettings):
    """Query service specific settings."""
    
    # Query processing configuration
    MAX_QUERY_LENGTH: int = 5000
    MIN_QUERY_LENGTH: int = 1
    MAX_RETRIEVAL_CHUNKS: int = 5
    SIMILARITY_THRESHOLD: float = 0.7
    
    # LLM prompt configuration
    SYSTEM_PROMPT: str = "You are a helpful assistant that answers questions based on the provided context. If the context doesn't contain relevant information, say 'I don't have enough information to answer that question based on the provided documents.'"
    MAX_CONTEXT_TOKENS: int = 4000
    
    # Cache configuration
    QUERY_CACHE_TTL_SECONDS: int = 3600  # 1 hour
    EMBEDDING_CACHE_TTL_SECONDS: int = 86400  # 24 hours
    
    # Rate limiting
    MAX_REQUESTS_PER_MINUTE: int = 60
    MAX_REQUESTS_PER_HOUR: int = 1000
    
    # External service URLs
    CONVERSATION_SERVICE_URL: str = "http://localhost:8004"
    DOCUMENT_SERVICE_URL: str = "http://localhost:8003"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "QUERY_"
        case_sensitive = True

# Global settings instance
query_settings = QueryServiceSettings()

def get_settings() -> QueryServiceSettings:
    """Get query service settings instance."""
    return query_settings
