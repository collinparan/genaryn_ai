"""
Chat interaction endpoints
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

from app.services.llm_service import get_llm_service, LLMService
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class ChatRequest(BaseModel):
    """Chat request model."""

    messages: List[Dict[str, str]]
    temperature: float = 0.7
    max_tokens: int = 2000
    stream: bool = False


class ChatResponse(BaseModel):
    """Chat response model."""

    content: str
    tokens_used: int
    model: str


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    llm_service: LLMService = Depends(get_llm_service),
):
    """Chat with AI Deputy Commander."""
    try:
        response = await llm_service.chat(
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=False,
        )

        return ChatResponse(
            content=response.content,
            tokens_used=response.tokens_used,
            model=response.model,
        )
    except Exception as e:
        logger.error(f"Chat error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to process chat request")


@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    llm_service: LLMService = Depends(get_llm_service),
):
    """Stream chat response from AI Deputy Commander."""

    async def generate():
        try:
            async for chunk in llm_service.stream_chat(
                messages=request.messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            ):
                # Format as SSE
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Stream chat error", error=str(e))
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


class DecisionAnalysisRequest(BaseModel):
    """Decision analysis request."""

    context: str
    options: List[str]
    constraints: str = None


@router.post("/analyze-decision")
async def analyze_decision(
    request: DecisionAnalysisRequest,
    llm_service: LLMService = Depends(get_llm_service),
):
    """Analyze a military decision with COA analysis."""
    try:
        analysis = await llm_service.analyze_decision(
            context=request.context,
            options=request.options,
            constraints=request.constraints,
        )
        return {"analysis": analysis}
    except Exception as e:
        logger.error(f"Decision analysis error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to analyze decision")


class RiskAssessmentRequest(BaseModel):
    """Risk assessment request."""

    operation: str
    factors: List[str]


@router.post("/assess-risk")
async def assess_risk(
    request: RiskAssessmentRequest,
    llm_service: LLMService = Depends(get_llm_service),
):
    """Assess operational risk."""
    try:
        assessment = await llm_service.assess_risk(
            operation=request.operation,
            factors=request.factors,
        )
        return {"assessment": assessment}
    except Exception as e:
        logger.error(f"Risk assessment error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to assess risk")