"""
Application constants for the RAG system.
Contains JWT settings, roles, status values, and other application-wide constants.
"""

from enum import Enum
from typing import Final

# JWT Configuration
JWT_ALGORITHM: Final[str] = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: Final[int] = 30
REFRESH_TOKEN_EXPIRE_DAYS: Final[int] = 7

# Roles
class UserRole(str, Enum):
    """User roles in the system."""
    ADMIN: str = "admin"
    USER: str = "user"
    GUEST: str = "guest"

# Document Status
class DocumentStatus(str, Enum):
    """Status values for document processing."""
    PENDING: str = "pending"
    PROCESSING: str = "processing"
    COMPLETED: str = "completed"
    FAILED: str = "failed"

# Conversation Status
class ConversationStatus(str, Enum):
    """Status values for conversations."""
    ACTIVE: str = "active"
    ARCHIVED: str = "archived"

# Message Roles
class MessageRole(str, Enum):
    """Role values for messages in a conversation."""
    USER: str = "user"
    ASSISTANT: str = "assistant"
    SYSTEM: str = "system"

# Document Content Types
SUPPORTED_CONTENT_TYPES: Final[list[str]] = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
]

ALLOWED_EXTENSIONS: Final[list[str]] = [
    ".pdf",
    ".docx",
    ".txt",
]

# Embedding Configuration
EMBEDDING_MODEL_NAME: Final[str] = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION: Final[int] = 384

# Vector Search Configuration
TOP_K_CHUNKS: Final[int] = 5
SIMILARITY_THRESHOLD: Final[float] = 0.7

# Chunk Configuration
CHUNK_SIZE: Final[int] = 1000
CHUNK_OVERLAP: Final[int] = 200

# LLM Configuration
DEFAULT_LLM_MODEL: Final[str] = "gpt-3.5-turbo"
LLM_TEMPERATURE: Final[float] = 0.7
LLM_MAX_TOKENS: Final[int] = 2000

# Pagination
DEFAULT_PAGE_SIZE: Final[int] = 20
MAX_PAGE_SIZE: Final[int] = 100

# Cache Configuration
CACHE_TTL_SECONDS: Final[int] = 3600  # 1 hour
CACHE_PREFIX: Final[str] = "rag:"

# Database Configuration
MAX_CONNECTION_POOL_SIZE: Final[int] = 20
MIN_CONNECTION_POOL_SIZE: Final[int] = 5
CONNECTION_POOL_TIMEOUT: Final[int] = 30

# API Configuration
API_VERSION: Final[str] = "1.0.0"
API_TITLE: Final[str] = "RAG System API"
API_DESCRIPTION: Final[str] = "Conversational RAG system for code and documentation understanding"

# Rate Limiting
RATE_LIMIT_PER_MINUTE: Final[int] = 60
RATE_LIMIT_BURST: Final[int] = 10

# File Upload Limits
MAX_FILE_SIZE_MB: Final[int] = 50
MAX_FILE_SIZE_BYTES: Final[int] = MAX_FILE_SIZE_MB * 1024 * 1024

# Error Messages
ERROR_INVALID_CREDENTIALS: Final[str] = "Invalid username or password"
ERROR_USER_EXISTS: Final[str] = "User already exists"
ERROR_UNAUTHORIZED: Final[str] = "Unauthorized access"
ERROR_NOT_FOUND: Final[str] = "Resource not found"
ERROR_INVALID_TOKEN: Final[str] = "Invalid or expired token"
ERROR_INVALID_FILE_TYPE: Final[str] = "File type not supported"
ERROR_FILE_TOO_LARGE: Final[str] = "File exceeds maximum size limit"

# Success Messages
SUCCESS_USER_REGISTERED: Final[str] = "User registered successfully"
SUCCESS_LOGIN: Final[str] = "Login successful"
SUCCESS_DOCUMENT_UPLOADED: Final[str] = "Document uploaded successfully"
SUCCESS_DOCUMENT_DELETED: Final[str] = "Document deleted successfully"
SUCCESS_CONVERSATION_CREATED: Final[str] = "Conversation created successfully"
SUCCESS_CONVERSATION_DELETED: Final[str] = "Conversation deleted successfully"
