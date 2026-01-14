"""
Conversation model
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class ConversationType(enum.Enum):
    """Conversation types."""

    TACTICAL = "tactical"
    STRATEGIC = "strategic"
    OPERATIONAL = "operational"
    INTELLIGENCE = "intelligence"
    LOGISTICS = "logistics"
    GENERAL = "general"


class ClassificationLevel(enum.Enum):
    """Classification levels."""

    UNCLASSIFIED = "unclassified"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"
    TOP_SECRET = "top_secret"


class Conversation(Base):
    """Conversation model for tracking chat sessions."""

    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    mission_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Link to mission if applicable

    title = Column(String(255), nullable=False)
    summary = Column(Text)  # AI-generated summary
    type = Column(Enum(ConversationType), default=ConversationType.GENERAL, nullable=False)
    classification = Column(Enum(ClassificationLevel), default=ClassificationLevel.UNCLASSIFIED, nullable=False)

    # Context and metadata
    context = Column(JSONB, default={})  # Mission context, operational parameters
    conversation_metadata = Column(JSONB, default={})  # Additional metadata
    tags = Column(JSONB, default=[])  # Searchable tags

    # Statistics
    message_count = Column(Integer, default=0)
    last_message_at = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    decisions = relationship("Decision", back_populates="conversation", cascade="all, delete-orphan")

    @property
    def metadata(self):
        """Property to maintain backward compatibility with API."""
        return self.conversation_metadata

    @metadata.setter
    def metadata(self, value):
        """Setter to maintain backward compatibility with API."""
        self.conversation_metadata = value

    def __repr__(self):
        return f"<Conversation(id={self.id}, title={self.title}, type={self.type})>"