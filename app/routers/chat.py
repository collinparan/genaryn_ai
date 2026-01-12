"""
Chat interaction endpoints
"""

from fastapi import APIRouter

router = APIRouter()

# Placeholder - will be implemented in US-004
@router.post("/")
async def chat():
    """Chat with AI Deputy Commander."""
    return {"message": "Chat endpoint - to be implemented"}