"""
Decision model for military decision tracking
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class DecisionStatus(enum.Enum):
    """Decision status."""

    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"


class DecisionPriority(enum.Enum):
    """Decision priority levels."""

    ROUTINE = "routine"
    PRIORITY = "priority"
    IMMEDIATE = "immediate"
    FLASH = "flash"


class DecisionType(enum.Enum):
    """Types of military decisions."""

    TACTICAL = "tactical"
    OPERATIONAL = "operational"
    STRATEGIC = "strategic"
    ADMINISTRATIVE = "administrative"
    LOGISTICS = "logistics"


class Decision(Base):
    """Decision model for tracking military decisions and recommendations."""

    __tablename__ = "decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    mission_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    type = Column(Enum(DecisionType), nullable=False)
    status = Column(Enum(DecisionStatus), default=DecisionStatus.DRAFT, nullable=False)
    priority = Column(Enum(DecisionPriority), default=DecisionPriority.ROUTINE, nullable=False)

    # Decision details
    recommendation = Column(Text, nullable=False)  # AI recommendation
    rationale = Column(Text)  # Reasoning behind recommendation
    risk_assessment = Column(JSONB, default={})  # Risk matrix and analysis
    alternatives = Column(JSONB, default=[])  # Alternative courses of action

    # Courses of Action (COAs)
    selected_coa = Column(JSONB)  # Selected course of action
    coa_analysis = Column(JSONB, default=[])  # Analysis of all COAs

    # Confidence and metrics
    confidence_score = Column(Float)  # AI confidence (0-1)
    estimated_success_probability = Column(Float)  # Success probability (0-1)

    # MDMP (Military Decision Making Process) tracking
    mdmp_phase = Column(String(50))  # Current MDMP phase
    mdmp_data = Column(JSONB, default={})  # MDMP-specific data

    # Decision outcome tracking
    outcome = Column(Text)  # Actual outcome after execution
    lessons_learned = Column(Text)  # Post-decision analysis

    # Approval tracking
    approved_by = Column(UUID(as_uuid=True))  # User ID who approved
    approved_at = Column(DateTime(timezone=True))
    rejection_reason = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    executed_at = Column(DateTime(timezone=True))  # When decision was executed

    # Relationships
    conversation = relationship("Conversation", back_populates="decisions")
    user = relationship("User", back_populates="decisions")

    def __repr__(self):
        return f"<Decision(id={self.id}, title={self.title}, status={self.status}, priority={self.priority})>"