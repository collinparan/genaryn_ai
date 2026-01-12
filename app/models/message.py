"""
Message model
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class MessageRole(enum.Enum):
    """Message roles."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(enum.Enum):
    """Message types."""

    TEXT = "text"
    DECISION = "decision"
    ANALYSIS = "analysis"
    RECOMMENDATION = "recommendation"
    INTELLIGENCE = "intelligence"
    WARNING = "warning"


class Message(Base):
    """Message model for conversation messages."""

    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    role = Column(Enum(MessageRole), nullable=False)
    type = Column(Enum(MessageType), default=MessageType.TEXT, nullable=False)
    content = Column(Text, nullable=False)

    # Metadata
    metadata = Column(JSONB, default={})  # Attachments, references, etc.
    tokens_used = Column(Integer)  # Token count for LLM usage tracking
    processing_time_ms = Column(Float)  # Response time tracking

    # For decision/analysis messages
    confidence_score = Column(Float)  # AI confidence in response (0-1)
    sources = Column(JSONB, default=[])  # Referenced sources

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    edited_at = Column(DateTime(timezone=True))  # If message was edited

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    user = relationship("User", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role}, type={self.type})>"