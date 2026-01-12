"""
Military decision support endpoints
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.decision import DecisionStatus, DecisionPriority, DecisionType
from app.repositories.decision_repository import DecisionRepository
from app.services.decision_service import DecisionService
from app.services.llm_service import get_llm_service
from app.schemas.decision import (
    DecisionCreate,
    DecisionUpdate,
    DecisionResponse,
    DecisionListResponse,
    COAAnalysisRequest,
    COAAnalysisResponse,
    RiskAssessmentRequest,
    RiskAssessmentResponse,
    DecisionApproval,
    DecisionOutcome,
    DecisionStatistics,
    HistoricalAnalysis,
    DecisionTemplate,
    DecisionRecommendationRequest,
)
from app.schemas.auth import UserResponse
from app.services.auth_service import get_current_user
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/decisions", tags=["decisions"])


# ============================================================================
# Decision CRUD Endpoints
# ============================================================================

@router.post("/", response_model=DecisionResponse)
async def create_decision(
    decision: DecisionCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """Create a new decision for tracking and analysis."""
    try:
        repo = DecisionRepository(db)
        llm_service = await get_llm_service()

        # Generate initial recommendation using AI
        prompt = f"""Provide initial military decision recommendation:

TITLE: {decision.title}
DESCRIPTION: {decision.description}
TYPE: {decision.type.value}
PRIORITY: {decision.priority.value}
CONTEXT: {decision.context}

Generate:
1. Clear recommendation
2. Rationale
3. Initial risk assessment
4. Alternative approaches"""

        messages = [{"role": "user", "content": prompt}]
        ai_response = await llm_service.chat(messages, temperature=0.5, max_tokens=1500)

        # Create decision with AI recommendation
        new_decision = await repo.create(
            user_id=UUID(current_user.id),
            title=decision.title,
            description=decision.description,
            type=decision.type,
            priority=decision.priority,
            recommendation=ai_response.content,
            conversation_id=decision.conversation_id,
            mission_id=decision.mission_id,
            confidence_score=0.75,  # Initial confidence
        )

        # Trigger background analysis if high priority
        if decision.priority in [DecisionPriority.IMMEDIATE, DecisionPriority.FLASH]:
            background_tasks.add_task(
                _perform_automatic_analysis,
                new_decision.id,
                db,
            )

        return DecisionResponse.from_orm(new_decision)
    except Exception as e:
        logger.error(f"Error creating decision: {e}")
        raise HTTPException(status_code=500, detail="Failed to create decision")


@router.get("/", response_model=DecisionListResponse)
async def list_decisions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[DecisionStatus] = None,
    type_filter: Optional[DecisionType] = None,
    priority_filter: Optional[DecisionPriority] = None,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's decisions with filtering and pagination."""
    try:
        repo = DecisionRepository(db)
        decisions, total = await repo.get_user_decisions(
            user_id=UUID(current_user.id),
            skip=skip,
            limit=limit,
            status_filter=status_filter,
            type_filter=type_filter,
            priority_filter=priority_filter,
        )

        return DecisionListResponse(
            decisions=[DecisionResponse.from_orm(d) for d in decisions],
            total=total,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"Error listing decisions: {e}")
        raise HTTPException(status_code=500, detail="Failed to list decisions")


@router.get("/pending", response_model=List[DecisionResponse])
async def get_pending_decisions(
    limit: int = Query(10, ge=1, le=50),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get pending decisions requiring immediate attention."""
    try:
        repo = DecisionRepository(db)

        # Check if user is a commander
        if current_user.role == "commander":
            # Commanders see all pending decisions
            decisions = await repo.get_pending_decisions(limit=limit)
        else:
            # Others see only their pending decisions
            decisions = await repo.get_pending_decisions(
                user_id=UUID(current_user.id),
                limit=limit,
            )

        return [DecisionResponse.from_orm(d) for d in decisions]
    except Exception as e:
        logger.error(f"Error getting pending decisions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pending decisions")


@router.get("/{decision_id}", response_model=DecisionResponse)
async def get_decision(
    decision_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get specific decision details."""
    try:
        repo = DecisionRepository(db)
        decision = await repo.get_by_id(decision_id)

        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")

        # Verify user has access
        if str(decision.user_id) != current_user.id and current_user.role != "commander":
            raise HTTPException(status_code=403, detail="Access denied")

        return DecisionResponse.from_orm(decision)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting decision: {e}")
        raise HTTPException(status_code=500, detail="Failed to get decision")


@router.patch("/{decision_id}", response_model=DecisionResponse)
async def update_decision(
    decision_id: UUID,
    update: DecisionUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update decision details."""
    try:
        repo = DecisionRepository(db)

        # Get decision
        decision = await repo.get_by_id(decision_id)
        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")

        # Verify user has access
        if str(decision.user_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Update fields
        if update.title:
            decision.title = update.title
        if update.description:
            decision.description = update.description
        if update.type:
            decision.type = update.type
        if update.priority:
            decision.priority = update.priority
        if update.rationale:
            decision.rationale = update.rationale
        if update.selected_coa:
            decision.selected_coa = update.selected_coa

        decision.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(decision)

        return DecisionResponse.from_orm(decision)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating decision: {e}")
        raise HTTPException(status_code=500, detail="Failed to update decision")


# ============================================================================
# COA Analysis Endpoints
# ============================================================================

@router.post("/{decision_id}/analyze-coa", response_model=COAAnalysisResponse)
async def analyze_courses_of_action(
    decision_id: UUID,
    request: COAAnalysisRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Perform comprehensive COA analysis for a decision."""
    try:
        # Verify decision access
        repo = DecisionRepository(db)
        decision = await repo.get_by_id(decision_id)

        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")

        if str(decision.user_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Perform COA analysis
        service = DecisionService(db)
        analysis = await service.analyze_courses_of_action(
            decision_id=decision_id,
            situation=request.situation,
            mission=request.mission,
            courses_of_action=request.courses_of_action,
            constraints=request.constraints,
            available_resources=request.available_resources,
            time_constraints=request.time_constraints,
        )

        return analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing COAs: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze courses of action")


# ============================================================================
# Risk Assessment Endpoints
# ============================================================================

@router.post("/{decision_id}/assess-risk", response_model=RiskAssessmentResponse)
async def assess_decision_risk(
    decision_id: UUID,
    request: RiskAssessmentRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Perform comprehensive risk assessment for a decision."""
    try:
        # Verify decision access
        repo = DecisionRepository(db)
        decision = await repo.get_by_id(decision_id)

        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")

        if str(decision.user_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Perform risk assessment
        service = DecisionService(db)
        assessment = await service.assess_risk(
            decision_id=decision_id,
            operation=request.operation,
            risk_factors=request.risk_factors,
            environment_factors=request.environment_factors,
            force_capabilities=request.force_capabilities,
        )

        return assessment
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assessing risk: {e}")
        raise HTTPException(status_code=500, detail="Failed to assess risk")


# ============================================================================
# Decision Approval and Tracking
# ============================================================================

@router.post("/{decision_id}/approve")
async def approve_decision(
    decision_id: UUID,
    approval: DecisionApproval,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject a decision."""
    try:
        # Check if user has approval authority (commander role)
        if current_user.role != "commander":
            raise HTTPException(status_code=403, detail="Only commanders can approve decisions")

        repo = DecisionRepository(db)
        decision = await repo.get_by_id(decision_id)

        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")

        # Update decision status
        updated = await repo.update_status(
            decision_id=decision_id,
            status=approval.status,
            approved_by=UUID(current_user.id) if approval.status == DecisionStatus.APPROVED else None,
            rejection_reason=approval.rejection_reason,
        )

        return {"message": f"Decision {approval.status.value}", "decision_id": str(decision_id)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving decision: {e}")
        raise HTTPException(status_code=500, detail="Failed to process decision approval")


@router.post("/{decision_id}/outcome")
async def record_decision_outcome(
    decision_id: UUID,
    outcome: DecisionOutcome,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record the outcome of an executed decision."""
    try:
        repo = DecisionRepository(db)
        decision = await repo.get_by_id(decision_id)

        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")

        # Verify user has access
        if str(decision.user_id) != current_user.id and current_user.role != "commander":
            raise HTTPException(status_code=403, detail="Access denied")

        # Update outcome
        updated = await repo.update_outcome(
            decision_id=decision_id,
            outcome=outcome.outcome,
            lessons_learned=outcome.lessons_learned,
        )

        # Update status to executed if not already
        if decision.status != DecisionStatus.EXECUTED:
            await repo.update_status(decision_id, DecisionStatus.EXECUTED)

        return {"message": "Outcome recorded successfully", "decision_id": str(decision_id)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording outcome: {e}")
        raise HTTPException(status_code=500, detail="Failed to record decision outcome")


# ============================================================================
# MDMP Support Endpoints
# ============================================================================

@router.post("/{decision_id}/mdmp/{phase}")
async def support_mdmp_phase(
    decision_id: UUID,
    phase: str,
    phase_inputs: Dict[str, Any],
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Support specific MDMP phase for a decision."""
    try:
        # Verify decision access
        repo = DecisionRepository(db)
        decision = await repo.get_by_id(decision_id)

        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")

        if str(decision.user_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Process MDMP phase
        service = DecisionService(db)
        result = await service.support_mdmp(
            decision_id=decision_id,
            phase=phase,
            phase_inputs=phase_inputs,
        )

        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing MDMP phase: {e}")
        raise HTTPException(status_code=500, detail="Failed to process MDMP phase")


# ============================================================================
# Historical Analysis
# ============================================================================

@router.get("/historical/analysis", response_model=HistoricalAnalysis)
async def analyze_historical_decisions(
    decision_type: DecisionType,
    context: str = Query(..., min_length=1),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Analyze historical decisions for patterns and lessons learned."""
    try:
        service = DecisionService(db)
        analysis = await service.analyze_historical_decisions(
            decision_type=decision_type,
            context=context,
            user_id=UUID(current_user.id),
        )

        return analysis
    except Exception as e:
        logger.error(f"Error analyzing historical decisions: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze historical decisions")


# ============================================================================
# Statistics Endpoints
# ============================================================================

@router.get("/stats", response_model=DecisionStatistics)
async def get_decision_statistics(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get decision statistics for the current user."""
    try:
        repo = DecisionRepository(db)
        stats = await repo.get_decision_statistics(user_id=UUID(current_user.id))

        # Add computed statistics
        stats["pending_decisions"] = stats["decisions_by_status"].get("pending", 0)
        stats["approved_decisions"] = stats["decisions_by_status"].get("approved", 0)
        stats["executed_decisions"] = stats["decisions_by_status"].get("executed", 0)

        return DecisionStatistics(**stats)
    except Exception as e:
        logger.error(f"Error getting decision statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get decision statistics")


# ============================================================================
# Decision Templates
# ============================================================================

@router.get("/templates", response_model=List[DecisionTemplate])
async def get_decision_templates(
    type_filter: Optional[DecisionType] = None,
    current_user: UserResponse = Depends(get_current_user),
):
    """Get available decision templates."""
    templates = [
        DecisionTemplate(
            name="Tactical Movement",
            type=DecisionType.TACTICAL,
            description="Template for tactical movement decisions",
            default_priority=DecisionPriority.PRIORITY,
            required_fields=["unit", "destination", "timeline"],
            template_data={
                "checklist": ["Route recon", "Security measures", "Comms plan"],
                "risk_factors": ["Enemy contact", "Terrain", "Weather"],
            },
        ),
        DecisionTemplate(
            name="Logistics Support",
            type=DecisionType.LOGISTICS,
            description="Template for logistics support decisions",
            default_priority=DecisionPriority.ROUTINE,
            required_fields=["supplies", "location", "timeline"],
            template_data={
                "checklist": ["Inventory check", "Transport", "Distribution"],
                "risk_factors": ["Supply chain", "Transport security"],
            },
        ),
        DecisionTemplate(
            name="Strategic Planning",
            type=DecisionType.STRATEGIC,
            description="Template for strategic planning decisions",
            default_priority=DecisionPriority.PRIORITY,
            required_fields=["objective", "resources", "timeline"],
            template_data={
                "checklist": ["Objective analysis", "Resource allocation", "Risk assessment"],
                "risk_factors": ["Political", "Economic", "Military"],
            },
        ),
    ]

    if type_filter:
        templates = [t for t in templates if t.type == type_filter]

    return templates


# ============================================================================
# Helper Functions
# ============================================================================

async def _perform_automatic_analysis(
    decision_id: UUID,
    db: AsyncSession,
):
    """Perform automatic analysis for high-priority decisions."""
    try:
        service = DecisionService(db)
        repo = DecisionRepository(db)

        # Get decision
        decision = await repo.get_by_id(decision_id)
        if not decision:
            return

        # Auto-generate COAs if not present
        if not decision.coa_analysis:
            # Generate default COAs based on decision type
            default_coas = [
                "Immediate action with available resources",
                "Delayed action with additional preparation",
                "Alternative approach with minimal resources",
            ]

            await service.analyze_courses_of_action(
                decision_id=decision_id,
                situation=decision.description,
                mission=decision.title,
                courses_of_action=default_coas,
            )

        logger.info(f"Automatic analysis completed for decision {decision_id}")
    except Exception as e:
        logger.error(f"Error in automatic analysis: {e}")


# Import at the end to avoid circular dependencies
from typing import Dict, Any