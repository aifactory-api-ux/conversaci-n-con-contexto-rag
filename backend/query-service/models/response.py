from pydantic import BaseModel, Field
from typing import Optional, List

from .query import SourceChunk


class QueryResponse(BaseModel):
    """Response model for query processing."""
    response: str = Field(..., description="Generated response from LLM")
    conversation_id: str = Field(..., description="ID of the conversation")
    message_id: str = Field(..., description="ID of the generated message")
    sources: Optional[List[SourceChunk]] = Field(default=None, description="Relevant source chunks")
    cached: bool = Field(default=False, description="Whether response was served from cache")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "response": "The capital of France is Paris.",
                "conversation_id": "conv_123",
                "message_id": "msg_456",
                "sources": [
                    {
                        "chunk_id": "chunk_789",
                        "document_id": "doc_012",
                        "content": "Paris is the capital and largest city of France.",
                        "score": 0.92,
                        "document_filename": "france_guide.pdf"
                    }
                ],
                "cached": False
            }
        }


class QueryHistoryResponse(BaseModel):
    """Response model for query history."""
    messages: List[dict] = Field(..., description="List of conversation messages")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "messages": [
                    {
                        "id": "msg_123",
                        "role": "user",
                        "content": "Hello",
                        "timestamp": "2024-01-01T12:00:00Z"
                    },
                    {
                        "id": "msg_456",
                        "role": "assistant",
                        "content": "Hi there!",
                        "timestamp": "2024-01-01T12:00:05Z"
                    }
                ]
            }
        }
