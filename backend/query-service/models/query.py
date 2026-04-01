from pydantic import BaseModel, Field
from typing import Optional


class QueryRequest(BaseModel):
    """Request model for query processing."""
    conversation_id: str = Field(..., min_length=1, description="ID of the conversation")
    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    include_sources: bool = Field(default=True, description="Whether to include source chunks in response")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "conversation_id": "conv_123",
                "message": "What is the capital of France?",
                "include_sources": True
            }
        }


class SourceChunk(BaseModel):
    """Model for a source document chunk."""
    chunk_id: str = Field(..., description="Unique identifier for the chunk")
    document_id: str = Field(..., description="ID of the source document")
    content: str = Field(..., description="Content of the chunk")
    score: float = Field(..., ge=0.0, le=1.0, description="Similarity score (0-1)")
    document_filename: str = Field(..., description="Name of the source document")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "chunk_id": "chunk_456",
                "document_id": "doc_789",
                "content": "Paris is the capital of France.",
                "score": 0.95,
                "document_filename": "france_info.pdf"
            }
        }
