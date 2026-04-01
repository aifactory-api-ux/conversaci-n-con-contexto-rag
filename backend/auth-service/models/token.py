from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from shared.database import Base


class Token(Base):
    """Database model for authentication tokens."""
    __tablename__ = "tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(512), nullable=False, unique=True)
    token_type = Column(String(20), nullable=False)  # 'access', 'refresh', 'reset'
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="tokens")
    
    def __repr__(self) -> str:
        return f"<Token(id={self.id}, user_id={self.user_id}, type={self.token_type})>"
    
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not revoked)."""
        return not self.is_expired() and not self.is_revoked
    
    def revoke(self) -> None:
        """Revoke the token."""
        self.is_revoked = True
        self.revoked_at = datetime.utcnow()