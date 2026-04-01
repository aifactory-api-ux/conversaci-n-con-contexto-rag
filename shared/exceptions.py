"""
Custom exceptions for the RAG conversation system.

All exceptions inherit from a base ApplicationException for consistent error handling.
"""

from typing import Any, Optional


class ApplicationException(Exception):
    """Base exception for all application-specific errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


class AuthenticationException(ApplicationException):
    """Raised when authentication fails."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(message, status_code=401, details=details)


class UnauthorizedException(ApplicationException):
    """Raised when user lacks required permissions."""
    
    def __init__(
        self,
        message: str = "Unauthorized access",
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(message, status_code=403, details=details)


class NotFoundException(ApplicationException):
    """Raised when a requested resource is not found."""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        details: Optional[Any] = None,
    ) -> None:
        message = f"{resource_type} with ID '{resource_id}' not found"
        super().__init__(message, status_code=404, details=details)


class ValidationException(ApplicationException):
    """Raised when input validation fails."""
    
    def __init__(
        self,
        message: str = "Validation error",
        field_errors: Optional[dict[str, list[str]]] = None,
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(message, status_code=422, details=details)
        self.field_errors = field_errors or {}


class DatabaseException(ApplicationException):
    """Raised when database operations fail."""
    
    def __init__(
        self,
        message: str = "Database operation failed",
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(message, status_code=500, details=details)


class ExternalServiceException(ApplicationException):
    """Raised when external service calls fail."""
    
    def __init__(
        self,
        service_name: str,
        message: str = "External service error",
        details: Optional[Any] = None,
    ) -> None:
        full_message = f"{service_name}: {message}"
        super().__init__(full_message, status_code=502, details=details)


class RateLimitException(ApplicationException):
    """Raised when rate limits are exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(message, status_code=429, details=details)
        self.retry_after = retry_after


class ConfigurationException(ApplicationException):
    """Raised when configuration is invalid or missing."""
    
    def __init__(
        self,
        message: str = "Configuration error",
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(message, status_code=500, details=details)


class DocumentProcessingException(ApplicationException):
    """Raised when document processing fails."""
    
    def __init__(
        self,
        document_id: Optional[str] = None,
        message: str = "Document processing failed",
        details: Optional[Any] = None,
    ) -> None:
        if document_id:
            message = f"Document {document_id}: {message}"
        super().__init__(message, status_code=500, details=details)


class EmbeddingException(ApplicationException):
    """Raised when embedding generation fails."""
    
    def __init__(
        self,
        message: str = "Embedding generation failed",
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(message, status_code=500, details=details)


class LLMException(ApplicationException):
    """Raised when LLM operations fail."""
    
    def __init__(
        self,
        message: str = "LLM operation failed",
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(message, status_code=500, details=details)


class CacheException(ApplicationException):
    """Raised when cache operations fail."""
    
    def __init__(
        self,
        message: str = "Cache operation failed",
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(message, status_code=500, details=details)


class ConversationException(ApplicationException):
    """Raised when conversation operations fail."""
    
    def __init__(
        self,
        message: str = "Conversation operation failed",
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(message, status_code=500, details=details)
