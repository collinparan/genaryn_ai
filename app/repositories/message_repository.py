"""
Message repository for data access operations
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, func, and_, or_, desc, asc, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message, MessageRole, MessageType


class MessageRepository:
    """Repository for message data operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        conversation_id: UUID,
        user_id: UUID,
        role: MessageRole,
        content: str,
        type: MessageType = MessageType.TEXT,
        metadata: Optional[Dict[str, Any]] = None,
        tokens_used: Optional[int] = None,
        processing_time_ms: Optional[float] = None,
        confidence_score: Optional[float] = None,
        sources: Optional[List[Dict[str, Any]]] = None,
    ) -> Message:
        """Create a new message."""
        message = Message(
            conversation_id=conversation_id,
            user_id=user_id,
            role=role,
            type=type,
            content=content,
            message_metadata=metadata or {},
            tokens_used=tokens_used,
            processing_time_ms=processing_time_ms,
            confidence_score=confidence_score,
            sources=sources or [],
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_by_id(self, message_id: UUID) -> Optional[Message]:
        """Get a message by ID."""
        query = select(Message).where(Message.id == message_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_conversation_messages(
        self,
        conversation_id: UUID,
        skip: int = 0,
        limit: int = 50,
        order: str = "asc",
    ) -> tuple[List[Message], int]:
        """Get messages for a conversation with pagination."""
        # Get total count
        count_query = select(func.count()).where(Message.conversation_id == conversation_id)
        total = await self.db.scalar(count_query)

        # Get paginated results
        query = select(Message).where(Message.conversation_id == conversation_id)

        if order == "desc":
            query = query.order_by(desc(Message.created_at))
        else:
            query = query.order_by(asc(Message.created_at))

        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        messages = result.scalars().all()

        return list(messages), total

    async def get_latest_messages(
        self,
        conversation_id: UUID,
        limit: int = 20,
    ) -> List[Message]:
        """Get the latest messages from a conversation."""
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(desc(Message.created_at))
            .limit(limit)
        )
        result = await self.db.execute(query)
        messages = list(result.scalars().all())
        # Reverse to get chronological order
        return messages[::-1]

    async def search_messages(
        self,
        conversation_id: UUID,
        query_text: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[Message], int]:
        """Search messages within a conversation."""
        search_pattern = f"%{query_text}%"

        base_query = select(Message).where(
            and_(
                Message.conversation_id == conversation_id,
                Message.content.ilike(search_pattern)
            )
        )

        # Get total count
        count_query = select(func.count()).select_from(base_query.subquery())
        total = await self.db.scalar(count_query)

        # Get paginated results
        query = base_query.order_by(desc(Message.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        messages = result.scalars().all()

        return list(messages), total

    async def update_content(
        self,
        message_id: UUID,
        content: str,
    ) -> Optional[Message]:
        """Update message content."""
        message = await self.get_by_id(message_id)
        if not message:
            return None

        message.content = content
        message.edited_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def delete(self, message_id: UUID) -> bool:
        """Delete a message."""
        message = await self.get_by_id(message_id)
        if not message:
            return False

        await self.db.delete(message)
        await self.db.commit()
        return True

    async def get_conversation_summary_context(
        self,
        conversation_id: UUID,
        max_messages: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get message context for generating conversation summary."""
        query = (
            select(
                Message.role,
                Message.content,
                Message.type,
                Message.created_at
            )
            .where(Message.conversation_id == conversation_id)
            .order_by(asc(Message.created_at))
            .limit(max_messages)
        )
        result = await self.db.execute(query)
        messages = []

        for row in result:
            messages.append({
                "role": row.role.value,
                "content": row.content,
                "type": row.type.value,
                "created_at": row.created_at.isoformat()
            })

        return messages

    async def get_user_message_stats(
        self,
        user_id: UUID,
    ) -> Dict[str, Any]:
        """Get message statistics for a user."""
        # Total message count
        total_query = select(func.count()).where(Message.user_id == user_id)
        total_messages = await self.db.scalar(total_query) or 0

        # Messages by type
        type_stats_query = (
            select(
                Message.type,
                func.count(Message.id).label("count")
            )
            .where(Message.user_id == user_id)
            .group_by(Message.type)
        )
        type_result = await self.db.execute(type_stats_query)

        type_stats = {}
        for row in type_result:
            type_stats[row.type.value] = row.count

        # Average tokens used (for assistant messages)
        avg_tokens_query = (
            select(func.avg(Message.tokens_used))
            .where(
                and_(
                    Message.user_id == user_id,
                    Message.role == MessageRole.ASSISTANT,
                    Message.tokens_used.isnot(None)
                )
            )
        )
        avg_tokens = await self.db.scalar(avg_tokens_query) or 0

        # Average processing time
        avg_time_query = (
            select(func.avg(Message.processing_time_ms))
            .where(
                and_(
                    Message.user_id == user_id,
                    Message.role == MessageRole.ASSISTANT,
                    Message.processing_time_ms.isnot(None)
                )
            )
        )
        avg_processing_time = await self.db.scalar(avg_time_query) or 0

        return {
            "total_messages": total_messages,
            "messages_by_type": type_stats,
            "avg_tokens_per_response": float(avg_tokens),
            "avg_processing_time_ms": float(avg_processing_time),
        }