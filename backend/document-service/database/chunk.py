from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from shared.database import Base


class Chunk(Base):
    """SQLAlchemy model for document chunks with vector embeddings."""
    __tablename__ = "chunks"
    __table_args__ = {
        "schema": "document_service",
        "comment": "Stores document chunks with vector embeddings for semantic search"
    }
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, comment="Unique identifier for the chunk")
    
    # Foreign keys
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("document_service.documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the parent document"
    )
    
    # Content fields
    content = Column(Text, nullable=False, comment="The actual text content of the chunk")
    chunk_index = Column(Integer, nullable=False, comment="Position of this chunk within the document (0-based)")
    
    # Vector embedding
    embedding = Column(
        Vector(384),  # Dimension matches EMBEDDING_DIMENSION from constants
        nullable=False,
        comment="Vector embedding of the chunk content for semantic search"
    )
    
    # Metadata
    metadata = Column(
        Text,
        nullable=True,
        comment="JSON metadata about the chunk (page number, section, etc.)"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="When the chunk was created"
    )
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self) -> str:
        return f"<Chunk(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"
    
    def to_dict(self) -> dict:
        """Convert chunk to dictionary representation."""
        return {
            "id": str(self.id),
            "document_id": str(self.document_id),
            "content": self.content,
            "chunk_index": self.chunk_index,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Document(Base):
    """SQLAlchemy model for uploaded documents."""
    __tablename__ = "documents"
    __table_args__ = {
        "schema": "document_service",
        "comment": "Stores metadata about uploaded documents"
    }
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, comment="Unique identifier for the document")
    
    # Foreign keys
    user_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="ID of the user who uploaded the document"
    )
    
    # File metadata
    filename = Column(String(500), nullable=False, comment="Original filename")
    content_type = Column(String(100), nullable=False, comment="MIME type of the file")
    file_size = Column(Integer, nullable=False, comment="Size of the file in bytes")
    file_path = Column(String(1000), nullable=True, comment="Path to the stored file on disk")
    
    # Processing status
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        comment="Processing status: pending, processing, completed, failed"
    )
    
    # Processing metadata
    chunks_count = Column(Integer, nullable=True, default=0, comment="Number of chunks generated from this document")
    error_message = Column(Text, nullable=True, comment="Error message if processing failed")
    
    # Timestamps
    uploaded_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="When the document was uploaded"
    )
    processed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the document processing was completed"
    )
    
    # Relationships
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"
    
    def to_dict(self) -> dict:
        """Convert document to dictionary representation."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "filename": self.filename,
            "content_type": self.content_type,
            "file_size": self.file_size,
            "status": self.status,
            "chunks_count": self.chunks_count,
            "error_message": self.error_message,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None
        }