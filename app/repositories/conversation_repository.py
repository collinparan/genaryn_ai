"""
Conversation repository for data access operations
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, func, and_, or_, desc, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation, ConversationType, ClassificationLevel
from app.models.message import Message, MessageRole


class ConversationRepository:
    """Repository for conversation data operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: UUID,
        title: str,
        type: ConversationType = ConversationType.GENERAL,
        classification: ClassificationLevel = ClassificationLevel.UNCLASSIFIED,
        mission_id: Optional[UUID] = None,
        context: Optional[Dict[str, Any]] = None,
        conversation_metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(
            user_id=user_id,
            title=title,
            type=type,
            classification=classification,
            mission_id=mission_id,
            context=context or {},
            conversation_metadata=conversation_metadata or {},
            tags=tags or [],
        )
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation

    async def get_by_id(
        self, conversation_id: UUID, with_messages: bool = False
    ) -> Optional[Conversation]:
        """Get a conversation by ID."""
        query = select(Conversation).where(Conversation.id == conversation_id)

        if with_messages:
            query = query.options(selectinload(Conversation.messages))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_conversations(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        type_filter: Optional[ConversationType] = None,
        classification_filter: Optional[ClassificationLevel] = None,
    ) -> tuple[List[Conversation], int]:
        """Get conversations for a user with pagination."""
        # Build base query
        base_query = select(Conversation).where(Conversation.user_id == user_id)

        # Apply filters
        if type_filter:
            base_query = base_query.where(Conversation.type == type_filter)
        if classification_filter:
            base_query = base_query.where(Conversation.classification == classification_filter)

        # Get total count
        count_query = select(func.count()).select_from(base_query.subquery())
        total = await self.db.scalar(count_query)

        # Get paginated results
        query = base_query.order_by(desc(Conversation.updated_at)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        conversations = result.scalars().all()

        return list(conversations), total

    async def update(
        self,
        conversation_id: UUID,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        type: Optional[ConversationType] = None,
        classification: Optional[ClassificationLevel] = None,
        context: Optional[Dict[str, Any]] = None,
        conversation_metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> Optional[Conversation]:
        """Update a conversation."""
        conversation = await self.get_by_id(conversation_id)
        if not conversation:
            return None

        if title is not None:
            conversation.title = title
        if summary is not None:
            conversation.summary = summary
        if type is not None:
            conversation.type = type
        if classification is not None:
            conversation.classification = classification
        if context is not None:
            conversation.context = context
        if conversation_metadata is not None:
            conversation.conversation_metadata = conversation_metadata
        if tags is not None:
            conversation.tags = tags

        conversation.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation

    async def delete(self, conversation_id: UUID) -> bool:
        """Delete a conversation."""
        conversation = await self.get_by_id(conversation_id)
        if not conversation:
            return False

        await self.db.delete(conversation)
        await self.db.commit()
        return True

    async def search(
        self,
        user_id: UUID,
        query: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[Conversation], int]:
        """Search conversations by title, tags, or summary."""
        search_pattern = f"%{query}%"

        base_query = select(Conversation).where(
            and_(
                Conversation.user_id == user_id,
                or_(
                    Conversation.title.ilike(search_pattern),
                    Conversation.summary.ilike(search_pattern),
                    # For tags, we'd need to use PostgreSQL JSON operators
                    func.cast(Conversation.tags, String).ilike(search_pattern)
                )
            )
        )

        # Get total count
        count_query = select(func.count()).select_from(base_query.subquery())
        total = await self.db.scalar(count_query)

        # Get paginated results
        query = base_query.order_by(desc(Conversation.updated_at)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        conversations = result.scalars().all()

        return list(conversations), total

    async def update_message_count(self, conversation_id: UUID) -> None:
        """Update the message count and last message timestamp."""
        # Get message count
        count_query = select(func.count()).where(Message.conversation_id == conversation_id)
        message_count = await self.db.scalar(count_query)

        # Get last message timestamp
        last_msg_query = (
            select(Message.created_at)
            .where(Message.conversation_id == conversation_id)
            .order_by(desc(Message.created_at))
            .limit(1)
        )
        last_message_at = await self.db.scalar(last_msg_query)

        # Update conversation
        conversation = await self.get_by_id(conversation_id)
        if conversation:
            conversation.message_count = message_count
            conversation.last_message_at = last_message_at
            conversation.updated_at = datetime.utcnow()
            await self.db.commit()

    async def get_recent_conversations(
        self,
        user_id: UUID,
        limit: int = 10,
    ) -> List[Conversation]:
        """Get the most recent conversations for a user."""
        query = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(desc(Conversation.last_message_at))
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())