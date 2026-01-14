"""
Conversation schemas for API requests and responses
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer, model_serializer

from app.models.conversation import ConversationType, ClassificationLevel
from app.models.message import MessageRole, MessageType


# ============================================================================
# Base Schemas
# ============================================================================

class ConversationBase(BaseModel):
    """Base conversation schema."""
    title: str = Field(..., min_length=1, max_length=255)
    type: ConversationType = ConversationType.GENERAL
    classification: ClassificationLevel = ClassificationLevel.UNCLASSIFIED
    mission_id: Optional[UUID] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class MessageBase(BaseModel):
    """Base message schema."""
    role: MessageRole
    content: str = Field(..., min_length=1)
    type: MessageType = MessageType.TEXT
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Request Schemas
# ============================================================================

class ConversationCreate(ConversationBase):
    """Schema for creating a conversation."""
    pass


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    summary: Optional[str] = None
    type: Optional[ConversationType] = None
    classification: Optional[ClassificationLevel] = None
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class MessageCreate(BaseModel):
    """Schema for creating a message."""
    content: str = Field(..., min_length=1)
    type: MessageType = MessageType.TEXT
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationSearch(BaseModel):
    """Schema for searching conversations."""
    query: str = Field(..., min_length=1)
    skip: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=100)


class MessageSearch(BaseModel):
    """Schema for searching messages."""
    query: str = Field(..., min_length=1)
    skip: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=100)


class ConversationExport(BaseModel):
    """Schema for exporting conversations."""
    format: str = Field("json", pattern="^(json|pdf|txt|csv)$")
    include_messages: bool = True
    include_metadata: bool = False


# ============================================================================
# Response Schemas
# ============================================================================

class MessageResponse(MessageBase):
    """Message response schema."""
    id: UUID
    conversation_id: UUID
    user_id: UUID
    tokens_used: Optional[int] = None
    processing_time_ms: Optional[float] = None
    confidence_score: Optional[float] = None
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    edited_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm to handle message_metadata -> metadata mapping."""
        data = {
            'id': obj.id,
            'conversation_id': obj.conversation_id,
            'user_id': obj.user_id,
            'role': obj.role,
            'content': obj.content,
            'type': obj.type,
            'metadata': obj.message_metadata,  # Map message_metadata to metadata
            'tokens_used': obj.tokens_used,
            'processing_time_ms': obj.processing_time_ms,
            'confidence_score': obj.confidence_score,
            'sources': obj.sources,
            'created_at': obj.created_at,
            'edited_at': obj.edited_at,
        }
        return cls(**data)


class ConversationResponse(ConversationBase):
    """Conversation response schema."""
    id: UUID
    user_id: UUID
    summary: Optional[str] = None
    message_count: int = 0
    last_message_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm to handle conversation_metadata -> metadata mapping."""
        # Create a dict from the ORM object
        data = {
            'id': obj.id,
            'user_id': obj.user_id,
            'title': obj.title,
            'type': obj.type,
            'classification': obj.classification,
            'mission_id': obj.mission_id,
            'context': obj.context,
            'metadata': obj.conversation_metadata,  # Map conversation_metadata to metadata
            'tags': obj.tags,
            'summary': obj.summary,
            'message_count': obj.message_count,
            'last_message_at': obj.last_message_at,
            'created_at': obj.created_at,
            'updated_at': obj.updated_at,
        }
        return cls(**data)


class ConversationWithMessages(ConversationResponse):
    """Conversation with messages response schema."""
    messages: List[MessageResponse] = Field(default_factory=list)


class ConversationListResponse(BaseModel):
    """Paginated conversation list response."""
    conversations: List[ConversationResponse]
    total: int
    skip: int
    limit: int


class MessageListResponse(BaseModel):
    """Paginated message list response."""
    messages: List[MessageResponse]
    total: int
    skip: int
    limit: int


class ConversationSummaryRequest(BaseModel):
    """Request for generating conversation summary."""
    max_messages: int = Field(50, ge=10, le=200)


class ConversationSummaryResponse(BaseModel):
    """Response for conversation summary."""
    conversation_id: UUID
    summary: str
    key_points: List[str]
    decisions: List[Dict[str, Any]]
    action_items: List[Dict[str, Any]]
    generated_at: datetime


class ConversationExportResponse(BaseModel):
    """Response for conversation export."""
    conversation_id: UUID
    format: str
    content: Optional[str] = None  # For JSON/TXT formats
    file_url: Optional[str] = None  # For PDF/CSV formats that generate files
    exported_at: datetime


class MessageStats(BaseModel):
    """Message statistics."""
    total_messages: int
    messages_by_type: Dict[str, int]
    avg_tokens_per_response: float
    avg_processing_time_ms: float


class ConversationStats(BaseModel):
    """Conversation statistics for a user."""
    total_conversations: int
    conversations_by_type: Dict[str, int]
    avg_messages_per_conversation: float
    recent_conversations: List[ConversationResponse]