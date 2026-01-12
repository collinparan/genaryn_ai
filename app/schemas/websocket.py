"""
WebSocket message schemas.
"""

from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """WebSocket message types."""

    # Connection management
    CONNECTION = "connection"
    DISCONNECT = "disconnect"
    PING = "ping"
    PONG = "pong"

    # User events
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    USER_UPDATE = "user_update"

    # Chat messages
    USER_MESSAGE = "user_message"
    AI_MESSAGE = "ai_message"
    SYSTEM_MESSAGE = "system_message"

    # Streaming
    LLM_STREAM = "llm_stream"
    LLM_COMPLETE = "llm_complete"

    # Typing indicators
    TYPING_START = "typing_start"
    TYPING_STOP = "typing_stop"
    TYPING_UPDATE = "typing_update"

    # Decision support
    DECISION_REQUEST = "decision_request"
    DECISION_RESPONSE = "decision_response"
    COA_ANALYSIS = "coa_analysis"
    RISK_ASSESSMENT = "risk_assessment"

    # Errors
    ERROR = "error"
    VALIDATION_ERROR = "validation_error"


class WebSocketMessage(BaseModel):
    """Base WebSocket message."""

    type: MessageType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[dict] = None


class ConnectionMessage(WebSocketMessage):
    """Connection establishment message."""

    type: MessageType = MessageType.CONNECTION
    session_id: str
    user: Optional[dict] = None


class UserMessage(WebSocketMessage):
    """User chat message."""

    type: MessageType = MessageType.USER_MESSAGE
    content: str
    user_id: Optional[UUID] = None
    username: Optional[str] = None
    message_id: Optional[str] = None


class AIMessage(WebSocketMessage):
    """AI response message."""

    type: MessageType = MessageType.AI_MESSAGE
    content: str
    message_id: str
    in_reply_to: Optional[str] = None
    confidence: Optional[float] = None
    sources: Optional[List[str]] = None


class StreamChunk(WebSocketMessage):
    """Streaming chunk message."""

    type: MessageType = MessageType.LLM_STREAM
    message_id: str
    chunk: str
    index: Optional[int] = None


class StreamComplete(WebSocketMessage):
    """Stream completion message."""

    type: MessageType = MessageType.LLM_COMPLETE
    message_id: str
    content: str
    token_count: Optional[int] = None
    duration_ms: Optional[int] = None


class TypingIndicator(WebSocketMessage):
    """Typing indicator message."""

    username: str
    is_typing: bool


class TypingUpdate(WebSocketMessage):
    """Typing users update."""

    type: MessageType = MessageType.TYPING_UPDATE
    typing_users: List[str]


class DecisionRequest(WebSocketMessage):
    """Decision support request."""

    type: MessageType = MessageType.DECISION_REQUEST
    scenario: str
    constraints: Optional[dict] = None
    priority: str = "normal"
    classification: str = "UNCLASSIFIED"


class DecisionResponse(WebSocketMessage):
    """Decision support response."""

    type: MessageType = MessageType.DECISION_RESPONSE
    recommendation: str
    courses_of_action: List[dict]
    risk_assessment: dict
    confidence: float
    supporting_data: Optional[dict] = None


class ErrorMessage(WebSocketMessage):
    """Error message."""

    type: MessageType = MessageType.ERROR
    error: str
    details: Optional[dict] = None
    recoverable: bool = True


class UserPresence(BaseModel):
    """User presence information."""

    user_id: UUID
    username: str
    role: str
    status: str = "online"
    last_activity: datetime


class SessionInfo(BaseModel):
    """Session information."""

    session_id: str
    created_at: datetime
    participant_count: int
    participants: List[UserPresence]
    message_count: int
    is_active: bool = True