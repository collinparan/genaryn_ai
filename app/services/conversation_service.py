"""
Conversation service for business logic and LLM integration
"""

import json
import csv
import io
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.services.llm_service import LLMService, get_llm_service
from app.models.conversation import ConversationType, ClassificationLevel
from app.models.message import MessageRole, MessageType
from app.schemas.conversation import (
    ConversationSummaryResponse,
    ConversationExportResponse,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ConversationService:
    """Service for conversation business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.conversation_repo = ConversationRepository(db)
        self.message_repo = MessageRepository(db)

    async def generate_summary(
        self,
        conversation_id: UUID,
        max_messages: int = 50,
    ) -> ConversationSummaryResponse:
        """
        Generate AI summary of conversation.

        Args:
            conversation_id: ID of conversation to summarize
            max_messages: Maximum messages to include in context

        Returns:
            Summary response with key points and decisions
        """
        # Get conversation
        conversation = await self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise ValueError("Conversation not found")

        # Get message context
        messages = await self.message_repo.get_conversation_summary_context(
            conversation_id, max_messages
        )

        if not messages:
            return ConversationSummaryResponse(
                conversation_id=conversation_id,
                summary="No messages to summarize",
                key_points=[],
                decisions=[],
                action_items=[],
                generated_at=datetime.utcnow(),
            )

        # Prepare context for LLM
        message_text = "\n".join(
            [
                f"[{msg['created_at']}] {msg['role'].upper()}: {msg['content']}"
                for msg in messages
            ]
        )

        prompt = f"""Analyze this military/defense conversation and provide:

CONVERSATION TITLE: {conversation.title}
TYPE: {conversation.type.value}
CLASSIFICATION: {conversation.classification.value}

MESSAGES:
{message_text}

Generate:
1. Executive Summary (2-3 sentences)
2. Key Points (bullet list)
3. Decisions Made (with context)
4. Action Items (with assignees if mentioned)
5. Risk Factors Identified
6. Recommendations for Next Steps"""

        # Get LLM service
        llm_service = await get_llm_service()

        # Generate summary
        llm_messages = [{"role": "user", "content": prompt}]
        response = await llm_service.chat(
            llm_messages,
            temperature=0.3,  # Lower temperature for factual summarization
            max_tokens=1500,
            system_override="""You are a military intelligence analyst specializing in conversation analysis and summarization.
Focus on extracting actionable intelligence, decisions, and strategic insights.
Be concise, accurate, and maintain operational security."""
        )

        # Parse response to extract structured data
        summary_parts = self._parse_summary_response(response.content)

        # Update conversation with summary
        await self.conversation_repo.update(
            conversation_id,
            summary=summary_parts["summary"],
        )

        return ConversationSummaryResponse(
            conversation_id=conversation_id,
            summary=summary_parts["summary"],
            key_points=summary_parts["key_points"],
            decisions=summary_parts["decisions"],
            action_items=summary_parts["action_items"],
            generated_at=datetime.utcnow(),
        )

    def _parse_summary_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM response into structured format."""
        # Simple parsing logic - in production, use more robust parsing
        lines = content.split("\n")
        result = {
            "summary": "",
            "key_points": [],
            "decisions": [],
            "action_items": [],
        }

        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect sections
            if "Executive Summary" in line or "SUMMARY" in line.upper():
                current_section = "summary"
            elif "Key Points" in line or "KEY POINTS" in line.upper():
                current_section = "key_points"
            elif "Decisions" in line or "DECISIONS" in line.upper():
                current_section = "decisions"
            elif "Action Items" in line or "ACTION ITEMS" in line.upper():
                current_section = "action_items"
            elif current_section:
                # Process content based on section
                if current_section == "summary":
                    if result["summary"]:
                        result["summary"] += " " + line
                    else:
                        result["summary"] = line
                elif current_section == "key_points" and (line.startswith("-") or line.startswith("•")):
                    result["key_points"].append(line.lstrip("-•").strip())
                elif current_section == "decisions" and (line.startswith("-") or line.startswith("•")):
                    result["decisions"].append({
                        "description": line.lstrip("-•").strip(),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                elif current_section == "action_items" and (line.startswith("-") or line.startswith("•")):
                    result["action_items"].append({
                        "task": line.lstrip("-•").strip(),
                        "status": "pending"
                    })

        # Fallback if parsing fails
        if not result["summary"]:
            result["summary"] = content[:500] if len(content) > 500 else content

        return result

    async def export_conversation(
        self,
        conversation_id: UUID,
        format: str = "json",
        include_messages: bool = True,
        include_metadata: bool = False,
    ) -> ConversationExportResponse:
        """
        Export conversation in specified format.

        Args:
            conversation_id: ID of conversation to export
            format: Export format (json, pdf, txt, csv)
            include_messages: Whether to include messages
            include_metadata: Whether to include metadata

        Returns:
            Export response with content or file URL
        """
        # Get conversation with messages if needed
        conversation = await self.conversation_repo.get_by_id(
            conversation_id, with_messages=include_messages
        )

        if not conversation:
            raise ValueError("Conversation not found")

        # Get messages if needed
        messages = []
        if include_messages:
            messages_data, _ = await self.message_repo.get_conversation_messages(
                conversation_id, limit=10000  # Get all messages
            )
            messages = messages_data

        # Export based on format
        if format == "json":
            content = await self._export_json(conversation, messages, include_metadata)
        elif format == "txt":
            content = await self._export_text(conversation, messages)
        elif format == "csv":
            content = await self._export_csv(conversation, messages)
        elif format == "pdf":
            # PDF generation would require additional libraries (reportlab, weasyprint, etc.)
            # For now, return a placeholder
            content = None
            file_url = f"/api/conversations/{conversation_id}/export.pdf"
        else:
            raise ValueError(f"Unsupported export format: {format}")

        return ConversationExportResponse(
            conversation_id=conversation_id,
            format=format,
            content=content if format != "pdf" else None,
            file_url=file_url if format == "pdf" else None,
            exported_at=datetime.utcnow(),
        )

    async def _export_json(
        self,
        conversation,
        messages: List,
        include_metadata: bool,
    ) -> str:
        """Export conversation as JSON."""
        data = {
            "conversation": {
                "id": str(conversation.id),
                "title": conversation.title,
                "type": conversation.type.value,
                "classification": conversation.classification.value,
                "summary": conversation.summary,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
            },
            "messages": []
        }

        if include_metadata:
            data["conversation"]["metadata"] = conversation.conversation_metadata
            data["conversation"]["context"] = conversation.context
            data["conversation"]["tags"] = conversation.tags

        for msg in messages:
            msg_data = {
                "id": str(msg.id),
                "role": msg.role.value,
                "content": msg.content,
                "type": msg.type.value,
                "created_at": msg.created_at.isoformat(),
            }

            if include_metadata:
                msg_data["metadata"] = msg.message_metadata
                msg_data["tokens_used"] = msg.tokens_used
                msg_data["processing_time_ms"] = msg.processing_time_ms

            data["messages"].append(msg_data)

        return json.dumps(data, indent=2)

    async def _export_text(
        self,
        conversation,
        messages: List,
    ) -> str:
        """Export conversation as plain text."""
        lines = [
            f"CONVERSATION EXPORT",
            f"=" * 50,
            f"Title: {conversation.title}",
            f"Type: {conversation.type.value}",
            f"Classification: {conversation.classification.value}",
            f"Created: {conversation.created_at}",
            f"",
            f"SUMMARY:",
            f"{conversation.summary or 'No summary available'}",
            f"",
            f"=" * 50,
            f"MESSAGES:",
            f"",
        ]

        for msg in messages:
            lines.extend([
                f"[{msg.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {msg.role.value.upper()}:",
                f"{msg.content}",
                f"",
            ])

        return "\n".join(lines)

    async def _export_csv(
        self,
        conversation,
        messages: List,
    ) -> str:
        """Export conversation messages as CSV."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "Timestamp",
            "Role",
            "Type",
            "Content",
            "Tokens Used",
            "Processing Time (ms)",
        ])

        # Write messages
        for msg in messages:
            writer.writerow([
                msg.created_at.isoformat(),
                msg.role.value,
                msg.type.value,
                msg.content,
                msg.tokens_used or "",
                msg.processing_time_ms or "",
            ])

        return output.getvalue()

    async def search_conversations(
        self,
        user_id: UUID,
        query: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List, int]:
        """Search conversations for a user."""
        return await self.conversation_repo.search(user_id, query, skip, limit)

    async def search_messages(
        self,
        conversation_id: UUID,
        query: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List, int]:
        """Search messages within a conversation."""
        return await self.message_repo.search_messages(
            conversation_id, query, skip, limit
        )