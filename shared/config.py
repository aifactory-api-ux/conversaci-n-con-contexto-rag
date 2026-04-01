from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings
from typing import Optional
import secrets


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Conversación con Contexto / RAG"
    PROJECT_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "rag_conversation"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[PostgresDsn] = None
    
    # Vector Database
    VECTOR_DB_SCHEMA: str = "public"
    VECTOR_DIMENSION: int = 384  # Default for sentence-transformers/all-MiniLM-L6-v2
    SIMILARITY_THRESHOLD: float = 0.7
    MAX_CHUNKS_PER_QUERY: int = 5
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: Optional[RedisDsn] = None
    
    # LLM Configuration
    LLM_PROVIDER: str = "openai"  # openai, anthropic, local
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-3.5-turbo"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 1000
    
    # Embedding Configuration
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DEVICE: str = "cpu"  # cpu or cuda
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # Service Ports
    AUTH_SERVICE_PORT: int = 8001
    QUERY_SERVICE_PORT: int = 8002
    DOCUMENT_SERVICE_PORT: int = 8003
    CONVERSATION_SERVICE_PORT: int = 8004
    FRONTEND_PORT: int = 3000
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_FILE_TYPES: list[str] = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"]
    UPLOAD_DIR: str = "./uploads"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_and_set_urls()
    
    def _validate_and_set_urls(self):
        """Validate required settings and construct URLs."""
        # Construct DATABASE_URL if not provided
        if not self.DATABASE_URL:
            self.DATABASE_URL = PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_SERVER,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            )
        
        # Construct REDIS_URL if not provided
        if not self.REDIS_URL:
            auth_part = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
            self.REDIS_URL = RedisDsn.build(
                scheme="redis",
                host=self.REDIS_HOST,
                port=self.REDIS_PORT,
                path=f"/{self.REDIS_DB}",
                username=auth_part if auth_part else None,
            )
        
        # Validate LLM configuration
        if self.LLM_PROVIDER in ["openai", "anthropic"] and not self.LLM_API_KEY:
            raise ValueError(f"LLM_API_KEY is required for provider: {self.LLM_PROVIDER}")
        
        # Validate vector dimension
        if self.VECTOR_DIMENSION <= 0:
            raise ValueError("VECTOR_DIMENSION must be positive")
        
        # Validate similarity threshold
        if not 0.0 <= self.SIMILARITY_THRESHOLD <= 1.0:
            raise ValueError("SIMILARITY_THRESHOLD must be between 0.0 and 1.0")
        
        # Validate chunk sizes
        if self.CHUNK_SIZE <= 0:
            raise ValueError("CHUNK_SIZE must be positive")
        if self.CHUNK_OVERLAP < 0 or self.CHUNK_OVERLAP >= self.CHUNK_SIZE:
            raise ValueError("CHUNK_OVERLAP must be non-negative and less than CHUNK_SIZE")
    
    def get_service_url(self, service_name: str) -> str:
        """Get the base URL for a service."""
        port_map = {
            "auth": self.AUTH_SERVICE_PORT,
            "query": self.QUERY_SERVICE_PORT,
            "document": self.DOCUMENT_SERVICE_PORT,
            "conversation": self.CONVERSATION_SERVICE_PORT,
        }
        
        if service_name not in port_map:
            raise ValueError(f"Unknown service: {service_name}")
        
        return f"http://localhost:{port_map[service_name]}"
    
    def get_database_config(self) -> dict:
        """Get database configuration as dict."""
        return {
            "url": str(self.DATABASE_URL),
            "pool_size": 20,
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_recycle": 3600,
            "echo": self.DEBUG,
        }
    
    def get_redis_config(self) -> dict:
        """Get Redis configuration as dict."""
        return {
            "url": str(self.REDIS_URL),
            "encoding": "utf-8",
            "decode_responses": True,
            "socket_connect_timeout": 5,
            "socket_timeout": 5,
            "retry_on_timeout": True,
        }


# Global settings instance
settings = Settings()
