"""
Server-Sent Events streaming endpoints
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()

# Placeholder - will be implemented with LLM integration
@router.get("/chat/{session_id}")
async def stream_chat(session_id: str):
    """SSE streaming chat endpoint."""
    async def event_generator():
        yield f"data: {{'message': 'SSE streaming - to be implemented'}}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )