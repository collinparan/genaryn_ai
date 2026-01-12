"""
Conversation management endpoints
"""

from fastapi import APIRouter

router = APIRouter()

# Placeholder - will be implemented in US-007
@router.get("/")
async def list_conversations():
    """List conversations."""
    return {"message": "List conversations - to be implemented"}

@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get specific conversation."""
    return {"message": f"Get conversation {conversation_id} - to be implemented"}