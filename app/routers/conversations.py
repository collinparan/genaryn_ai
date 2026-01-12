"""
Conversation management endpoints
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.conversation import ConversationType, ClassificationLevel
from app.models.message import MessageRole
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.services.conversation_service import ConversationService
from app.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationWithMessages,
    ConversationListResponse,
    MessageCreate,
    MessageResponse,
    MessageListResponse,
    ConversationSearch,
    MessageSearch,
    ConversationSummaryRequest,
    ConversationSummaryResponse,
    ConversationExport,
    ConversationExportResponse,
    ConversationStats,
    MessageStats,
)
from app.schemas.auth import UserResponse
from app.services.auth_service import get_current_user
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


# ============================================================================
# Conversation CRUD Endpoints
# ============================================================================

@router.post("/", response_model=ConversationResponse)
async def create_conversation(
    conversation: ConversationCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new conversation."""
    try:
        repo = ConversationRepository(db)
        new_conversation = await repo.create(
            user_id=UUID(current_user.id),
            title=conversation.title,
            type=conversation.type,
            classification=conversation.classification,
            mission_id=conversation.mission_id,
            context=conversation.context,
            metadata=conversation.metadata,
            tags=conversation.tags,
        )
        return ConversationResponse.from_orm(new_conversation)
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to create conversation")


@router.get("/", response_model=ConversationListResponse)
async def list_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    type_filter: Optional[ConversationType] = None,
    classification_filter: Optional[ClassificationLevel] = None,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's conversations with pagination."""
    try:
        repo = ConversationRepository(db)
        conversations, total = await repo.get_user_conversations(
            user_id=UUID(current_user.id),
            skip=skip,
            limit=limit,
            type_filter=type_filter,
            classification_filter=classification_filter,
        )

        return ConversationListResponse(
            conversations=[ConversationResponse.from_orm(c) for c in conversations],
            total=total,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to list conversations")


@router.get("/recent", response_model=List[ConversationResponse])
async def get_recent_conversations(
    limit: int = Query(10, ge=1, le=50),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's most recent conversations."""
    try:
        repo = ConversationRepository(db)
        conversations = await repo.get_recent_conversations(
            user_id=UUID(current_user.id),
            limit=limit,
        )
        return [ConversationResponse.from_orm(c) for c in conversations]
    except Exception as e:
        logger.error(f"Error getting recent conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recent conversations")


@router.get("/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: UUID,
    include_messages: bool = Query(False),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get specific conversation."""
    try:
        repo = ConversationRepository(db)
        conversation = await repo.get_by_id(conversation_id, with_messages=include_messages)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Verify user has access
        if str(conversation.user_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        response = ConversationWithMessages.from_orm(conversation)

        # If messages requested, get them
        if include_messages:
            message_repo = MessageRepository(db)
            messages, _ = await message_repo.get_conversation_messages(
                conversation_id, limit=100
            )
            response.messages = [MessageResponse.from_orm(m) for m in messages]

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversation")


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    update: ConversationUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update conversation details."""
    try:
        repo = ConversationRepository(db)

        # Verify conversation exists and user has access
        conversation = await repo.get_by_id(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        if str(conversation.user_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Update conversation
        updated = await repo.update(
            conversation_id,
            title=update.title,
            summary=update.summary,
            type=update.type,
            classification=update.classification,
            context=update.context,
            metadata=update.metadata,
            tags=update.tags,
        )

        return ConversationResponse.from_orm(updated)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to update conversation")


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a conversation."""
    try:
        repo = ConversationRepository(db)

        # Verify conversation exists and user has access
        conversation = await repo.get_by_id(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        if str(conversation.user_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Delete conversation
        success = await repo.delete(conversation_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete conversation")

        return {"message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete conversation")


# ============================================================================
# Message Management Endpoints
# ============================================================================

@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def add_message(
    conversation_id: UUID,
    message: MessageCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """Add a message to conversation."""
    try:
        # Verify conversation exists and user has access
        conv_repo = ConversationRepository(db)
        conversation = await conv_repo.get_by_id(conversation_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        if str(conversation.user_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Create message
        msg_repo = MessageRepository(db)
        new_message = await msg_repo.create(
            conversation_id=conversation_id,
            user_id=UUID(current_user.id),
            role=MessageRole.USER,  # User messages via API
            content=message.content,
            type=message.type,
            metadata=message.metadata,
        )

        # Update conversation message count in background
        background_tasks.add_task(
            conv_repo.update_message_count, conversation_id
        )

        return MessageResponse.from_orm(new_message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding message: {e}")
        raise HTTPException(status_code=500, detail="Failed to add message")


@router.get("/{conversation_id}/messages", response_model=MessageListResponse)
async def get_messages(
    conversation_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get messages from conversation with pagination."""
    try:
        # Verify conversation exists and user has access
        conv_repo = ConversationRepository(db)
        conversation = await conv_repo.get_by_id(conversation_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        if str(conversation.user_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get messages
        msg_repo = MessageRepository(db)
        messages, total = await msg_repo.get_conversation_messages(
            conversation_id, skip, limit, order
        )

        return MessageListResponse(
            messages=[MessageResponse.from_orm(m) for m in messages],
            total=total,
            skip=skip,
            limit=limit,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to get messages")


# ============================================================================
# Search Endpoints
# ============================================================================

@router.post("/search", response_model=ConversationListResponse)
async def search_conversations(
    search: ConversationSearch,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search user's conversations."""
    try:
        service = ConversationService(db)
        conversations, total = await service.search_conversations(
            user_id=UUID(current_user.id),
            query=search.query,
            skip=search.skip,
            limit=search.limit,
        )

        return ConversationListResponse(
            conversations=[ConversationResponse.from_orm(c) for c in conversations],
            total=total,
            skip=search.skip,
            limit=search.limit,
        )
    except Exception as e:
        logger.error(f"Error searching conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to search conversations")


@router.post("/{conversation_id}/messages/search", response_model=MessageListResponse)
async def search_messages(
    conversation_id: UUID,
    search: MessageSearch,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search messages within conversation."""
    try:
        # Verify conversation access
        conv_repo = ConversationRepository(db)
        conversation = await conv_repo.get_by_id(conversation_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        if str(conversation.user_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Search messages
        service = ConversationService(db)
        messages, total = await service.search_messages(
            conversation_id,
            search.query,
            search.skip,
            search.limit,
        )

        return MessageListResponse(
            messages=[MessageResponse.from_orm(m) for m in messages],
            total=total,
            skip=search.skip,
            limit=search.limit,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to search messages")


# ============================================================================
# Summarization and Export Endpoints
# ============================================================================

@router.post("/{conversation_id}/summarize", response_model=ConversationSummaryResponse)
async def generate_summary(
    conversation_id: UUID,
    request: ConversationSummaryRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate AI summary of conversation."""
    try:
        # Verify conversation access
        conv_repo = ConversationRepository(db)
        conversation = await conv_repo.get_by_id(conversation_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        if str(conversation.user_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Generate summary
        service = ConversationService(db)
        summary = await service.generate_summary(
            conversation_id,
            request.max_messages,
        )

        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate summary")


@router.post("/{conversation_id}/export", response_model=ConversationExportResponse)
async def export_conversation(
    conversation_id: UUID,
    export_config: ConversationExport,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export conversation in specified format."""
    try:
        # Verify conversation access
        conv_repo = ConversationRepository(db)
        conversation = await conv_repo.get_by_id(conversation_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        if str(conversation.user_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Export conversation
        service = ConversationService(db)
        export = await service.export_conversation(
            conversation_id,
            export_config.format,
            export_config.include_messages,
            export_config.include_metadata,
        )

        return export
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to export conversation")


# ============================================================================
# Statistics Endpoints
# ============================================================================

@router.get("/stats/messages", response_model=MessageStats)
async def get_message_stats(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get message statistics for current user."""
    try:
        msg_repo = MessageRepository(db)
        stats = await msg_repo.get_user_message_stats(UUID(current_user.id))
        return MessageStats(**stats)
    except Exception as e:
        logger.error(f"Error getting message stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get message statistics")


@router.get("/stats/overview", response_model=ConversationStats)
async def get_conversation_stats(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get conversation statistics for current user."""
    try:
        conv_repo = ConversationRepository(db)

        # Get total conversations
        all_convs, total = await conv_repo.get_user_conversations(
            UUID(current_user.id), skip=0, limit=1
        )

        # Get conversations by type
        type_stats = {}
        for conv_type in ConversationType:
            convs, count = await conv_repo.get_user_conversations(
                UUID(current_user.id),
                skip=0,
                limit=1,
                type_filter=conv_type,
            )
            type_stats[conv_type.value] = count

        # Get recent conversations
        recent = await conv_repo.get_recent_conversations(
            UUID(current_user.id), limit=5
        )

        # Calculate average messages per conversation
        msg_repo = MessageRepository(db)
        msg_stats = await msg_repo.get_user_message_stats(UUID(current_user.id))
        avg_messages = (
            msg_stats["total_messages"] / total if total > 0 else 0
        )

        return ConversationStats(
            total_conversations=total,
            conversations_by_type=type_stats,
            avg_messages_per_conversation=avg_messages,
            recent_conversations=[ConversationResponse.from_orm(c) for c in recent],
        )
    except Exception as e:
        logger.error(f"Error getting conversation stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversation statistics")