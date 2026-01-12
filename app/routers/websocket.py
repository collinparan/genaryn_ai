"""
WebSocket endpoints for real-time communication
"""

from fastapi import APIRouter, WebSocket

router = APIRouter()

# Placeholder - will be implemented in US-006
@router.websocket("/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """WebSocket chat endpoint."""
    await websocket.accept()
    await websocket.send_json({"message": "WebSocket chat - to be implemented"})
    await websocket.close()