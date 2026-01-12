"""
Decision service for military decision analysis and support
"""

import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.repositories.decision_repository import DecisionRepository
from app.models.decision import Decision, DecisionStatus, DecisionPriority, DecisionType
from app.services.llm_service import LLMService, get_llm_service
from app.schemas.decision import (
    CourseOfAction,
    RiskAssessment,
    COAAnalysisResponse,
    RiskAssessmentResponse,
    HistoricalAnalysis,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DecisionService:
    """Service for military decision analysis and support."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.decision_repo = DecisionRepository(db)

    async def analyze_courses_of_action(
        self,
        decision_id: UUID,
        situation: str,
        mission: str,
        courses_of_action: List[str],
        constraints: Optional[str] = None,
        available_resources: Optional[List[str]] = None,
        time_constraints: Optional[str] = None,
    ) -> COAAnalysisResponse:
        """
        Perform comprehensive COA analysis using AI.

        Args:
            decision_id: Decision ID for tracking
            situation: Current situation description
            mission: Mission statement
            courses_of_action: List of possible COAs
            constraints: Operational constraints
            available_resources: Available resources
            time_constraints: Time limitations

        Returns:
            Comprehensive COA analysis with recommendations
        """
        # Get LLM service
        llm_service = await get_llm_service()

        # Build analysis prompt
        prompt = f"""Perform a comprehensive military Courses of Action (COA) analysis:

SITUATION: {situation}

MISSION: {mission}

COURSES OF ACTION:
{chr(10).join(f'{i+1}. {coa}' for i, coa in enumerate(courses_of_action))}

{'CONSTRAINTS: ' + constraints if constraints else ''}
{'AVAILABLE RESOURCES: ' + ', '.join(available_resources) if available_resources else ''}
{'TIME CONSTRAINTS: ' + time_constraints if time_constraints else ''}

For EACH Course of Action, provide:
1. Detailed advantages and disadvantages
2. Resource requirements
3. Estimated timeline for execution
4. Success probability (0-1 scale)
5. Risk assessment (probability and impact)
6. Mitigation strategies

Then provide:
- COA comparison matrix
- Recommended COA with detailed rationale
- Critical success factors
- Key decision points and triggers
- Contingency planning recommendations

Use military doctrinal analysis methods and be specific."""

        # Get AI analysis
        messages = [{"role": "user", "content": prompt}]
        response = await llm_service.chat(
            messages,
            temperature=0.3,  # Low temperature for analytical consistency
            max_tokens=3000,
        )

        # Parse response into structured COAs
        coas = await self._parse_coa_analysis(response.content, courses_of_action)

        # Identify recommended COA
        recommended_coa = max(coas, key=lambda x: x.success_probability)

        # Create comparison matrix
        comparison_matrix = self._create_comparison_matrix(coas)

        # Extract key insights
        insights = self._extract_coa_insights(response.content)

        # Update decision with COA analysis
        await self.decision_repo.update_coa(
            decision_id,
            selected_coa=recommended_coa.dict(),
            coa_analysis=[coa.dict() for coa in coas],
        )

        return COAAnalysisResponse(
            decision_id=decision_id,
            recommended_coa=recommended_coa,
            all_coas=coas,
            comparison_matrix=comparison_matrix,
            rationale=insights["rationale"],
            critical_factors=insights["critical_factors"],
            decision_points=insights["decision_points"],
            generated_at=datetime.utcnow(),
        )

    async def assess_risk(
        self,
        decision_id: UUID,
        operation: str,
        risk_factors: List[str],
        environment_factors: Optional[List[str]] = None,
        force_capabilities: Optional[Dict[str, Any]] = None,
    ) -> RiskAssessmentResponse:
        """
        Perform comprehensive risk assessment.

        Args:
            decision_id: Decision ID for tracking
            operation: Operation description
            risk_factors: Identified risk factors
            environment_factors: Environmental considerations
            force_capabilities: Force capability assessment

        Returns:
            Comprehensive risk assessment with mitigation strategies
        """
        # Get LLM service
        llm_service = await get_llm_service()

        # Build risk assessment prompt
        prompt = f"""Conduct a comprehensive military risk assessment:

OPERATION: {operation}

IDENTIFIED RISK FACTORS:
{chr(10).join(f'- {factor}' for factor in risk_factors)}

{'ENVIRONMENTAL FACTORS:' + chr(10) + chr(10).join(f'- {factor}' for factor in environment_factors) if environment_factors else ''}

{'FORCE CAPABILITIES:' + chr(10) + json.dumps(force_capabilities, indent=2) if force_capabilities else ''}

Provide:
1. Overall risk level (LOW/MODERATE/HIGH/EXTREME) with justification
2. For EACH risk factor:
   - Probability of occurrence (0-1)
   - Potential impact (0-1)
   - Specific mitigation strategies
3. Risk matrix visualization data
4. Comprehensive mitigation plan with:
   - Primary mitigation measures
   - Contingency actions
   - Resource requirements
5. Residual risk assessment after mitigation
6. Confidence level in assessment (0-1)

Use military risk assessment doctrine (ATP 5-19) methodology."""

        # Get AI analysis
        messages = [{"role": "user", "content": prompt}]
        response = await llm_service.chat(
            messages,
            temperature=0.2,  # Very low temperature for consistent risk assessment
            max_tokens=2500,
        )

        # Parse risk assessment
        risk_data = await self._parse_risk_assessment(response.content, risk_factors)

        # Update decision with risk assessment
        decision = await self.decision_repo.get_by_id(decision_id)
        if decision:
            decision.risk_assessment = risk_data["risk_matrix"]
            await self.db.commit()

        return RiskAssessmentResponse(
            decision_id=decision_id,
            overall_risk_level=risk_data["overall_risk_level"],
            risk_factors=risk_data["risk_factors"],
            risk_matrix=risk_data["risk_matrix"],
            mitigation_plan=risk_data["mitigation_plan"],
            residual_risk_assessment=risk_data["residual_risk"],
            confidence_level=risk_data["confidence_level"],
            generated_at=datetime.utcnow(),
        )

    async def support_mdmp(
        self,
        decision_id: UUID,
        phase: str,
        phase_inputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Support Military Decision Making Process (MDMP) phases.

        Args:
            decision_id: Decision ID for tracking
            phase: Current MDMP phase
            phase_inputs: Phase-specific inputs

        Returns:
            Phase-specific analysis and outputs
        """
        # MDMP phases and their specific processing
        mdmp_phases = {
            "receipt_of_mission": self._mdmp_receipt_of_mission,
            "mission_analysis": self._mdmp_mission_analysis,
            "coa_development": self._mdmp_coa_development,
            "coa_analysis": self._mdmp_coa_analysis,
            "coa_comparison": self._mdmp_coa_comparison,
            "coa_approval": self._mdmp_coa_approval,
            "orders_production": self._mdmp_orders_production,
        }

        if phase not in mdmp_phases:
            raise ValueError(f"Invalid MDMP phase: {phase}")

        # Process phase
        phase_handler = mdmp_phases[phase]
        result = await phase_handler(phase_inputs)

        # Update decision with MDMP data
        decision = await self.decision_repo.get_by_id(decision_id)
        if decision:
            decision.mdmp_phase = phase
            if not decision.mdmp_data:
                decision.mdmp_data = {}
            decision.mdmp_data[phase] = result
            await self.db.commit()

        return result

    async def analyze_historical_decisions(
        self,
        decision_type: DecisionType,
        context: str,
        user_id: Optional[UUID] = None,
    ) -> HistoricalAnalysis:
        """
        Analyze historical decisions for patterns and lessons learned.

        Args:
            decision_type: Type of decision
            context: Current decision context
            user_id: User ID for personalized analysis

        Returns:
            Historical analysis with recommendations
        """
        # Query similar historical decisions
        query = select(Decision).where(
            and_(
                Decision.type == decision_type,
                Decision.status == DecisionStatus.EXECUTED,
                Decision.outcome.isnot(None),
            )
        )

        if user_id:
            query = query.where(Decision.user_id == user_id)

        query = query.limit(20)  # Limit to recent decisions
        result = await self.db.execute(query)
        historical_decisions = list(result.scalars().all())

        if not historical_decisions:
            return HistoricalAnalysis(
                similar_decisions=[],
                success_rate=0.0,
                common_factors=[],
                lessons_learned=[],
                recommended_approach="No historical data available for analysis",
            )

        # Calculate success rate
        successful = sum(
            1 for d in historical_decisions
            if d.estimated_success_probability and d.estimated_success_probability > 0.7
        )
        success_rate = successful / len(historical_decisions) if historical_decisions else 0

        # Extract patterns using AI
        llm_service = await get_llm_service()

        decisions_summary = "\n".join([
            f"- {d.title}: {d.outcome} (Confidence: {d.confidence_score})"
            for d in historical_decisions[:10]
        ])

        prompt = f"""Analyze these historical military decisions for patterns:

DECISION TYPE: {decision_type.value}
CURRENT CONTEXT: {context}

HISTORICAL DECISIONS:
{decisions_summary}

Extract:
1. Common success factors
2. Common failure patterns
3. Key lessons learned
4. Recommended approach based on historical patterns
5. Specific tactics that worked well"""

        messages = [{"role": "user", "content": prompt}]
        response = await llm_service.chat(messages, temperature=0.3, max_tokens=1500)

        # Parse insights
        insights = self._parse_historical_insights(response.content)

        return HistoricalAnalysis(
            similar_decisions=[
                DecisionResponse.from_orm(d) for d in historical_decisions[:5]
            ],
            success_rate=success_rate,
            common_factors=insights["common_factors"],
            lessons_learned=insights["lessons_learned"],
            recommended_approach=insights["recommended_approach"],
        )

    # ============================================================================
    # Helper Methods
    # ============================================================================

    async def _parse_coa_analysis(
        self, content: str, coa_names: List[str]
    ) -> List[CourseOfAction]:
        """Parse LLM response into structured COAs."""
        coas = []

        for i, coa_name in enumerate(coa_names):
            # Default COA structure
            coa = CourseOfAction(
                id=f"coa_{i+1}",
                name=f"COA {i+1}: {coa_name}",
                description=coa_name,
                advantages=self._extract_list_from_text(content, f"COA {i+1}", "advantages"),
                disadvantages=self._extract_list_from_text(content, f"COA {i+1}", "disadvantages"),
                resources_required=self._extract_list_from_text(content, f"COA {i+1}", "resources"),
                estimated_timeline="To be determined",
                success_probability=self._extract_probability(content, f"COA {i+1}"),
                risk_assessment=RiskAssessment(
                    risk_level="moderate",
                    probability=0.5,
                    impact=0.5,
                    mitigation_strategies=[],
                    residual_risk=0.3,
                ),
            )
            coas.append(coa)

        return coas

    async def _parse_risk_assessment(
        self, content: str, risk_factors: List[str]
    ) -> Dict[str, Any]:
        """Parse LLM risk assessment response."""
        # Extract overall risk level
        overall_risk = "moderate"  # Default
        for level in ["extreme", "high", "moderate", "low"]:
            if level.upper() in content.upper():
                overall_risk = level
                break

        # Parse individual risk factors
        parsed_factors = []
        for factor in risk_factors:
            parsed_factors.append({
                "factor": factor,
                "probability": self._extract_probability(content, factor),
                "impact": 0.5,  # Default if not found
                "mitigation": "See mitigation plan",
            })

        return {
            "overall_risk_level": overall_risk,
            "risk_factors": parsed_factors,
            "risk_matrix": {
                "high_probability_high_impact": [],
                "high_probability_low_impact": [],
                "low_probability_high_impact": [],
                "low_probability_low_impact": [],
            },
            "mitigation_plan": self._extract_list_from_text(content, "mitigation", ""),
            "residual_risk": "Moderate after mitigation",
            "confidence_level": 0.75,
        }

    def _create_comparison_matrix(self, coas: List[CourseOfAction]) -> Dict[str, Any]:
        """Create COA comparison matrix."""
        matrix = {
            "criteria": [
                "Success Probability",
                "Resource Requirements",
                "Risk Level",
                "Timeline",
            ],
            "scores": {},
        }

        for coa in coas:
            matrix["scores"][coa.id] = {
                "success_probability": coa.success_probability,
                "resource_score": 0.5,  # Would need more complex calculation
                "risk_score": 1 - coa.risk_assessment.probability,
                "timeline_score": 0.5,  # Would need timeline parsing
                "total": coa.success_probability * 0.4 + 0.3 + 0.3,
            }

        return matrix

    def _extract_coa_insights(self, content: str) -> Dict[str, Any]:
        """Extract key insights from COA analysis."""
        return {
            "rationale": self._extract_section(content, "rationale", "recommended"),
            "critical_factors": self._extract_list_from_text(content, "critical", "factors"),
            "decision_points": [
                {"point": "Initial assessment", "trigger": "Mission receipt"},
                {"point": "Resource allocation", "trigger": "COA selection"},
                {"point": "Execution start", "trigger": "Conditions met"},
            ],
        }

    def _extract_list_from_text(
        self, text: str, section: str, keyword: str
    ) -> List[str]:
        """Extract list items from text based on section/keyword."""
        items = []
        lines = text.split("\n")
        in_section = False

        for line in lines:
            if section.lower() in line.lower() and (
                not keyword or keyword.lower() in line.lower()
            ):
                in_section = True
            elif in_section and (line.startswith("-") or line.startswith("•")):
                items.append(line.lstrip("-•").strip())
            elif in_section and line and not line[0].isspace():
                in_section = False

        return items if items else ["Analysis in progress"]

    def _extract_probability(self, text: str, context: str) -> float:
        """Extract probability value from text."""
        # Simple extraction - would need more sophisticated parsing
        import re

        pattern = rf"{context}.*?(\d+\.?\d*)%"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1)) / 100
        return 0.5  # Default

    def _extract_section(self, text: str, start_keyword: str, end_keyword: str) -> str:
        """Extract text section between keywords."""
        lines = text.split("\n")
        capturing = False
        section = []

        for line in lines:
            if start_keyword.lower() in line.lower():
                capturing = True
            elif end_keyword and end_keyword.lower() in line.lower():
                break
            elif capturing:
                section.append(line)

        return " ".join(section) if section else "See detailed analysis"

    def _parse_historical_insights(self, content: str) -> Dict[str, Any]:
        """Parse historical analysis insights."""
        return {
            "common_factors": self._extract_list_from_text(content, "success", "factors"),
            "lessons_learned": self._extract_list_from_text(content, "lessons", "learned"),
            "recommended_approach": self._extract_section(content, "recommended", ""),
        }

    # ============================================================================
    # MDMP Phase Handlers
    # ============================================================================

    async def _mdmp_receipt_of_mission(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process Receipt of Mission phase."""
        return {
            "phase": "receipt_of_mission",
            "status": "completed",
            "outputs": {
                "mission_received": inputs.get("mission", ""),
                "initial_guidance": inputs.get("guidance", ""),
                "timeline": inputs.get("timeline", ""),
            },
            "next_steps": ["Initiate mission analysis", "Alert staff", "Gather intel"],
        }

    async def _mdmp_mission_analysis(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process Mission Analysis phase."""
        llm_service = await get_llm_service()

        prompt = f"""Conduct military mission analysis:

MISSION: {inputs.get('mission', '')}
ENEMY SITUATION: {inputs.get('enemy_situation', '')}
FRIENDLY FORCES: {inputs.get('friendly_forces', '')}
TERRAIN: {inputs.get('terrain', '')}

Provide:
1. Mission statement (Who, What, When, Where, Why)
2. Commander's intent
3. Specified, implied, and essential tasks
4. Constraints and limitations
5. Risk assessment
6. Initial CCIR (Commander's Critical Information Requirements)"""

        messages = [{"role": "user", "content": prompt}]
        response = await llm_service.chat(messages, temperature=0.3)

        return {
            "phase": "mission_analysis",
            "status": "completed",
            "analysis": response.content,
            "outputs": {
                "mission_statement": "Extracted from analysis",
                "tasks": ["specified", "implied", "essential"],
                "constraints": [],
                "ccir": [],
            },
        }

    async def _mdmp_coa_development(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process COA Development phase."""
        return {
            "phase": "coa_development",
            "status": "completed",
            "developed_coas": inputs.get("coas", []),
            "screening_criteria": ["feasible", "acceptable", "suitable", "distinguishable"],
        }

    async def _mdmp_coa_analysis(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process COA Analysis (Wargaming) phase."""
        return {
            "phase": "coa_analysis",
            "status": "completed",
            "wargaming_results": inputs.get("wargaming", {}),
            "refined_coas": inputs.get("refined_coas", []),
        }

    async def _mdmp_coa_comparison(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process COA Comparison phase."""
        return {
            "phase": "coa_comparison",
            "status": "completed",
            "comparison_matrix": inputs.get("matrix", {}),
            "recommended_coa": inputs.get("recommended", ""),
        }

    async def _mdmp_coa_approval(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process COA Approval phase."""
        return {
            "phase": "coa_approval",
            "status": "completed",
            "approved_coa": inputs.get("approved_coa", ""),
            "commander_guidance": inputs.get("guidance", ""),
        }

    async def _mdmp_orders_production(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process Orders Production phase."""
        return {
            "phase": "orders_production",
            "status": "completed",
            "opord": inputs.get("opord", ""),
            "fragos": inputs.get("fragos", []),
            "dissemination": inputs.get("dissemination", ""),
        }

# Ensure proper imports are available
from app.schemas.decision import DecisionResponse