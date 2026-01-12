"""
Decision repository for military decision tracking
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.decision import Decision, DecisionStatus, DecisionPriority, DecisionType


class DecisionRepository:
    """Repository for decision data operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: UUID,
        title: str,
        description: str,
        type: DecisionType,
        recommendation: str,
        priority: DecisionPriority = DecisionPriority.ROUTINE,
        conversation_id: Optional[UUID] = None,
        mission_id: Optional[UUID] = None,
        rationale: Optional[str] = None,
        risk_assessment: Optional[Dict[str, Any]] = None,
        alternatives: Optional[List[Dict[str, Any]]] = None,
        coa_analysis: Optional[List[Dict[str, Any]]] = None,
        confidence_score: Optional[float] = None,
        estimated_success_probability: Optional[float] = None,
        mdmp_phase: Optional[str] = None,
        mdmp_data: Optional[Dict[str, Any]] = None,
    ) -> Decision:
        """Create a new decision."""
        decision = Decision(
            user_id=user_id,
            conversation_id=conversation_id,
            mission_id=mission_id,
            title=title,
            description=description,
            type=type,
            status=DecisionStatus.DRAFT,
            priority=priority,
            recommendation=recommendation,
            rationale=rationale,
            risk_assessment=risk_assessment or {},
            alternatives=alternatives or [],
            coa_analysis=coa_analysis or [],
            confidence_score=confidence_score,
            estimated_success_probability=estimated_success_probability,
            mdmp_phase=mdmp_phase,
            mdmp_data=mdmp_data or {},
        )
        self.db.add(decision)
        await self.db.commit()
        await self.db.refresh(decision)
        return decision

    async def get_by_id(self, decision_id: UUID) -> Optional[Decision]:
        """Get a decision by ID."""
        query = select(Decision).where(Decision.id == decision_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_decisions(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        status_filter: Optional[DecisionStatus] = None,
        type_filter: Optional[DecisionType] = None,
        priority_filter: Optional[DecisionPriority] = None,
    ) -> tuple[List[Decision], int]:
        """Get decisions for a user with pagination and filters."""
        # Build base query
        base_query = select(Decision).where(Decision.user_id == user_id)

        # Apply filters
        if status_filter:
            base_query = base_query.where(Decision.status == status_filter)
        if type_filter:
            base_query = base_query.where(Decision.type == type_filter)
        if priority_filter:
            base_query = base_query.where(Decision.priority == priority_filter)

        # Get total count
        count_query = select(func.count()).select_from(base_query.subquery())
        total = await self.db.scalar(count_query)

        # Get paginated results
        query = base_query.order_by(desc(Decision.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        decisions = result.scalars().all()

        return list(decisions), total

    async def get_conversation_decisions(
        self,
        conversation_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[Decision], int]:
        """Get decisions associated with a conversation."""
        base_query = select(Decision).where(Decision.conversation_id == conversation_id)

        # Get total count
        count_query = select(func.count()).select_from(base_query.subquery())
        total = await self.db.scalar(count_query)

        # Get paginated results
        query = base_query.order_by(desc(Decision.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        decisions = result.scalars().all()

        return list(decisions), total

    async def get_pending_decisions(
        self,
        user_id: Optional[UUID] = None,
        limit: int = 10,
    ) -> List[Decision]:
        """Get pending decisions requiring action."""
        query = select(Decision).where(Decision.status == DecisionStatus.PENDING)

        if user_id:
            query = query.where(Decision.user_id == user_id)

        query = query.order_by(
            desc(Decision.priority == DecisionPriority.FLASH),
            desc(Decision.priority == DecisionPriority.IMMEDIATE),
            desc(Decision.priority == DecisionPriority.PRIORITY),
            desc(Decision.created_at),
        ).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_status(
        self,
        decision_id: UUID,
        status: DecisionStatus,
        approved_by: Optional[UUID] = None,
        rejection_reason: Optional[str] = None,
    ) -> Optional[Decision]:
        """Update decision status."""
        decision = await self.get_by_id(decision_id)
        if not decision:
            return None

        decision.status = status
        decision.updated_at = datetime.utcnow()

        if status == DecisionStatus.APPROVED and approved_by:
            decision.approved_by = approved_by
            decision.approved_at = datetime.utcnow()
        elif status == DecisionStatus.REJECTED and rejection_reason:
            decision.rejection_reason = rejection_reason
        elif status == DecisionStatus.EXECUTED:
            decision.executed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(decision)
        return decision

    async def update_coa(
        self,
        decision_id: UUID,
        selected_coa: Dict[str, Any],
        coa_analysis: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[Decision]:
        """Update selected course of action."""
        decision = await self.get_by_id(decision_id)
        if not decision:
            return None

        decision.selected_coa = selected_coa
        if coa_analysis:
            decision.coa_analysis = coa_analysis
        decision.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(decision)
        return decision

    async def update_outcome(
        self,
        decision_id: UUID,
        outcome: str,
        lessons_learned: Optional[str] = None,
    ) -> Optional[Decision]:
        """Update decision outcome after execution."""
        decision = await self.get_by_id(decision_id)
        if not decision:
            return None

        decision.outcome = outcome
        if lessons_learned:
            decision.lessons_learned = lessons_learned
        decision.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(decision)
        return decision

    async def get_decision_statistics(
        self,
        user_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """Get decision statistics."""
        base_query = select(Decision)
        if user_id:
            base_query = base_query.where(Decision.user_id == user_id)

        # Total decisions
        total_query = select(func.count()).select_from(base_query.subquery())
        total = await self.db.scalar(total_query) or 0

        # Decisions by status
        status_stats = {}
        for status in DecisionStatus:
            query = select(func.count()).where(
                and_(
                    Decision.user_id == user_id if user_id else True,
                    Decision.status == status
                )
            )
            count = await self.db.scalar(query) or 0
            status_stats[status.value] = count

        # Decisions by type
        type_stats = {}
        for dec_type in DecisionType:
            query = select(func.count()).where(
                and_(
                    Decision.user_id == user_id if user_id else True,
                    Decision.type == dec_type
                )
            )
            count = await self.db.scalar(query) or 0
            type_stats[dec_type.value] = count

        # Average confidence score
        confidence_query = select(func.avg(Decision.confidence_score)).where(
            and_(
                Decision.user_id == user_id if user_id else True,
                Decision.confidence_score.isnot(None)
            )
        )
        avg_confidence = await self.db.scalar(confidence_query) or 0

        # Success probability average
        success_query = select(func.avg(Decision.estimated_success_probability)).where(
            and_(
                Decision.user_id == user_id if user_id else True,
                Decision.estimated_success_probability.isnot(None)
            )
        )
        avg_success_probability = await self.db.scalar(success_query) or 0

        return {
            "total_decisions": total,
            "decisions_by_status": status_stats,
            "decisions_by_type": type_stats,
            "average_confidence_score": float(avg_confidence),
            "average_success_probability": float(avg_success_probability),
        }

    async def search_decisions(
        self,
        query: str,
        user_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[Decision], int]:
        """Search decisions by title, description, or recommendation."""
        search_pattern = f"%{query}%"

        base_query = select(Decision).where(
            or_(
                Decision.title.ilike(search_pattern),
                Decision.description.ilike(search_pattern),
                Decision.recommendation.ilike(search_pattern),
            )
        )

        if user_id:
            base_query = base_query.where(Decision.user_id == user_id)

        # Get total count
        count_query = select(func.count()).select_from(base_query.subquery())
        total = await self.db.scalar(count_query)

        # Get paginated results
        query = base_query.order_by(desc(Decision.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        decisions = result.scalars().all()

        return list(decisions), total