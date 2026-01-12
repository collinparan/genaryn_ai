"""
Decision schemas for API requests and responses
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, validator

from app.models.decision import DecisionStatus, DecisionPriority, DecisionType


# ============================================================================
# Base Schemas
# ============================================================================

class RiskAssessment(BaseModel):
    """Risk assessment structure."""
    risk_level: str = Field(..., pattern="^(low|moderate|high|extreme)$")
    probability: float = Field(..., ge=0, le=1)
    impact: float = Field(..., ge=0, le=1)
    mitigation_strategies: List[str] = Field(default_factory=list)
    residual_risk: Optional[float] = Field(None, ge=0, le=1)


class CourseOfAction(BaseModel):
    """Course of Action (COA) structure."""
    id: str
    name: str
    description: str
    advantages: List[str]
    disadvantages: List[str]
    resources_required: List[str]
    estimated_timeline: str
    success_probability: float = Field(..., ge=0, le=1)
    risk_assessment: RiskAssessment


class MDMPPhase(BaseModel):
    """Military Decision Making Process phase data."""
    phase_name: str = Field(..., pattern="^(receipt_of_mission|mission_analysis|coa_development|coa_analysis|coa_comparison|coa_approval|orders_production)$")
    status: str = Field(..., pattern="^(not_started|in_progress|completed)$")
    findings: List[str]
    next_steps: List[str]
    completed_at: Optional[datetime] = None


# ============================================================================
# Request Schemas
# ============================================================================

class DecisionCreate(BaseModel):
    """Schema for creating a decision."""
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    type: DecisionType
    priority: DecisionPriority = DecisionPriority.ROUTINE
    conversation_id: Optional[UUID] = None
    mission_id: Optional[UUID] = None
    context: Dict[str, Any] = Field(default_factory=dict)


class DecisionUpdate(BaseModel):
    """Schema for updating a decision."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    type: Optional[DecisionType] = None
    priority: Optional[DecisionPriority] = None
    rationale: Optional[str] = None
    selected_coa: Optional[Dict[str, Any]] = None


class COAAnalysisRequest(BaseModel):
    """Request for COA analysis."""
    situation: str = Field(..., min_length=1)
    mission: str = Field(..., min_length=1)
    courses_of_action: List[str] = Field(..., min_items=2, max_items=10)
    constraints: Optional[str] = None
    available_resources: Optional[List[str]] = None
    time_constraints: Optional[str] = None


class RiskAssessmentRequest(BaseModel):
    """Request for risk assessment."""
    operation: str = Field(..., min_length=1)
    risk_factors: List[str] = Field(..., min_items=1)
    environment_factors: Optional[List[str]] = None
    force_capabilities: Optional[Dict[str, Any]] = None


class DecisionRecommendationRequest(BaseModel):
    """Request for decision recommendation."""
    decision_id: UUID
    coa_id: Optional[str] = None
    additional_context: Optional[str] = None


class DecisionApproval(BaseModel):
    """Schema for decision approval."""
    status: DecisionStatus = Field(..., pattern="^(approved|rejected)$")
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None


class DecisionOutcome(BaseModel):
    """Schema for recording decision outcome."""
    outcome: str = Field(..., min_length=1)
    lessons_learned: Optional[str] = None
    success_metrics: Optional[Dict[str, Any]] = None


# ============================================================================
# Response Schemas
# ============================================================================

class DecisionResponse(BaseModel):
    """Decision response schema."""
    id: UUID
    user_id: UUID
    conversation_id: Optional[UUID]
    mission_id: Optional[UUID]
    title: str
    description: str
    type: DecisionType
    status: DecisionStatus
    priority: DecisionPriority
    recommendation: str
    rationale: Optional[str]
    risk_assessment: Dict[str, Any]
    alternatives: List[Dict[str, Any]]
    selected_coa: Optional[Dict[str, Any]]
    coa_analysis: List[Dict[str, Any]]
    confidence_score: Optional[float]
    estimated_success_probability: Optional[float]
    mdmp_phase: Optional[str]
    mdmp_data: Dict[str, Any]
    outcome: Optional[str]
    lessons_learned: Optional[str]
    approved_by: Optional[UUID]
    approved_at: Optional[datetime]
    rejection_reason: Optional[str]
    created_at: datetime
    updated_at: datetime
    executed_at: Optional[datetime]

    class Config:
        from_attributes = True


class DecisionListResponse(BaseModel):
    """Paginated decision list response."""
    decisions: List[DecisionResponse]
    total: int
    skip: int
    limit: int


class COAAnalysisResponse(BaseModel):
    """COA analysis response."""
    decision_id: UUID
    recommended_coa: CourseOfAction
    all_coas: List[CourseOfAction]
    comparison_matrix: Dict[str, Any]
    rationale: str
    critical_factors: List[str]
    decision_points: List[Dict[str, Any]]
    generated_at: datetime


class RiskAssessmentResponse(BaseModel):
    """Risk assessment response."""
    decision_id: UUID
    overall_risk_level: str
    risk_factors: List[Dict[str, Any]]
    risk_matrix: Dict[str, Any]
    mitigation_plan: List[Dict[str, Any]]
    residual_risk_assessment: str
    confidence_level: float
    generated_at: datetime


class DecisionStatistics(BaseModel):
    """Decision statistics."""
    total_decisions: int
    decisions_by_status: Dict[str, int]
    decisions_by_type: Dict[str, int]
    average_confidence_score: float
    average_success_probability: float
    pending_decisions: int
    approved_decisions: int
    executed_decisions: int


class DecisionAuditLog(BaseModel):
    """Audit log entry for decision."""
    decision_id: UUID
    action: str
    user_id: UUID
    timestamp: datetime
    details: Dict[str, Any]


class DecisionTemplate(BaseModel):
    """Template for common decision types."""
    name: str
    type: DecisionType
    description: str
    default_priority: DecisionPriority
    required_fields: List[str]
    template_data: Dict[str, Any]


class HistoricalAnalysis(BaseModel):
    """Historical decision analysis."""
    similar_decisions: List[DecisionResponse]
    success_rate: float
    common_factors: List[str]
    lessons_learned: List[str]
    recommended_approach: str