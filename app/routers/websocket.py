"""
WebSocket endpoints for real-time communication.
"""

import json
import uuid
from typing import Optional
import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.services.websocket_manager import manager
from app.services.llm_service import llm_service
from app.services.auth_service import auth_service
from app.schemas.websocket import (
    MessageType,
    UserMessage,
    ErrorMessage
)
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.models.user import User
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


async def authenticate_websocket(
    token: Optional[str],
    db: AsyncSession
) -> Optional[User]:
    """Authenticate WebSocket connection via JWT token."""
    if not token:
        return None

    user = await auth_service.verify_token(db, token)
    return user


@router.websocket("/chat/{session_id}")
async def websocket_chat(
    websocket: WebSocket,
    session_id: str,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time chat.

    Protocol:
    - Send messages as JSON with 'type' field
    - Supported types: user_message, typing_start, typing_stop, decision_request
    - Receives: ai_message, llm_stream, llm_complete, typing_update, error
    """
    db_gen = get_db()
    db = await anext(db_gen)

    try:
        # Authenticate user
        user = await authenticate_websocket(token, db)

        user_info = {
            "user_id": str(user.id) if user else None,
            "username": user.username if user else "Anonymous",
            "role": user.role.value if user else "observer"
        }

        # Connect to manager
        await manager.connect(websocket, session_id, user_info)

        try:
            # Get or create conversation
            conversation = await get_or_create_conversation(db, session_id, user)

            # Main message loop
            while True:
                # Receive message from client
                try:
                    data = await websocket.receive_json()
                except json.JSONDecodeError:
                    await manager.send_personal_message(
                        websocket,
                        ErrorMessage(
                            error="Invalid JSON format",
                            details={"message": "Message must be valid JSON"}
                        ).dict()
                    )
                    continue

                message_type = data.get("type")

                if message_type == MessageType.USER_MESSAGE:
                    await handle_user_message(
                        db, websocket, session_id, conversation, user, data
                    )

                elif message_type == MessageType.TYPING_START:
                    await manager.handle_typing(
                        session_id, user_info["username"], True
                    )

                elif message_type == MessageType.TYPING_STOP:
                    await manager.handle_typing(
                        session_id, user_info["username"], False
                    )

                elif message_type == MessageType.DECISION_REQUEST:
                    await handle_decision_request(
                        db, websocket, session_id, conversation, user, data
                    )

                elif message_type == MessageType.PING:
                    await manager.send_personal_message(
                        websocket,
                        {"type": MessageType.PONG}
                    )

                else:
                    await manager.send_personal_message(
                        websocket,
                        ErrorMessage(
                            error="Unknown message type",
                            details={"type": message_type}
                        ).dict()
                    )

        except WebSocketDisconnect:
            await manager.disconnect(websocket, session_id)
            logger.info(f"Client disconnected from session {session_id}")

        except Exception as e:
            logger.error(f"WebSocket error in session {session_id}: {e}")
            await manager.send_personal_message(
                websocket,
                ErrorMessage(
                    error="Internal server error",
                    details={"error": str(e)},
                    recoverable=False
                ).dict()
            )
            await manager.disconnect(websocket, session_id)

    finally:
        # Ensure database session is closed
        await db.close()
        try:
            await anext(db_gen)
        except StopAsyncIteration:
            pass


async def get_or_create_conversation(
    db: AsyncSession,
    session_id: str,
    user: Optional[User]
) -> Conversation:
    """Get existing conversation or create new one."""
    try:
        conv_id = uuid.UUID(session_id)
    except ValueError:
        # Generate new UUID if session_id is not valid UUID
        conv_id = uuid.uuid4()

    query = select(Conversation).where(Conversation.id == conv_id)
    result = await db.execute(query)
    conversation = result.scalar_one_or_none()

    if not conversation:
        # Create new conversation
        conversation = Conversation(
            id=conv_id,
            user_id=user.id if user else None,
            title=f"Chat Session {session_id[:8]}",
            context={
                "session_type": "websocket",
                "created_via": "websocket_chat"
            }
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)

        logger.info(f"Created new conversation {conv_id}")

    return conversation


async def handle_user_message(
    db: AsyncSession,
    websocket: WebSocket,
    session_id: str,
    conversation: Conversation,
    user: Optional[User],
    data: dict
):
    """Handle incoming user message."""
    content = data.get("content", "").strip()

    if not content:
        await manager.send_personal_message(
            websocket,
            ErrorMessage(
                error="Empty message",
                details={"message": "Message content cannot be empty"}
            ).dict()
        )
        return

    # Generate message ID
    message_id = str(uuid.uuid4())

    # Store user message in database
    user_message = Message(
        conversation_id=conversation.id,
        user_id=user.id if user else None,
        role=MessageRole.USER,
        content=content,
        metadata={"message_id": message_id}
    )
    db.add(user_message)
    await db.commit()

    # Broadcast user message to session
    await manager.broadcast_to_session(
        session_id,
        UserMessage(
            content=content,
            user_id=user.id if user else None,
            username=user.username if user else "Anonymous",
            message_id=message_id
        ).dict()
    )

    # Generate AI response
    ai_message_id = str(uuid.uuid4())

    try:
        # Get conversation history
        history = await get_conversation_history(db, conversation.id)

        # Stream AI response
        async def stream_generator():
            async for chunk in llm_service.stream_chat(history + [{"role": "user", "content": content}]):
                yield chunk

        await manager.stream_llm_response(
            session_id,
            ai_message_id,
            stream_generator(),
            metadata={
                "in_reply_to": message_id,
                "model": llm_service.model
            }
        )

        # Store AI response in database
        ai_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content="[Response streamed]",  # Placeholder
            metadata={
                "message_id": ai_message_id,
                "in_reply_to": message_id
            }
        )
        db.add(ai_message)
        await db.commit()

    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        await manager.send_personal_message(
            websocket,
            ErrorMessage(
                error="Failed to generate AI response",
                details={"error": str(e)}
            ).dict()
        )


async def handle_decision_request(
    db: AsyncSession,
    websocket: WebSocket,
    session_id: str,
    conversation: Conversation,
    user: Optional[User],
    data: dict
):
    """Handle military decision support request."""
    scenario = data.get("scenario", "").strip()

    if not scenario:
        await manager.send_personal_message(
            websocket,
            ErrorMessage(
                error="Empty scenario",
                details={"message": "Scenario description required"}
            ).dict()
        )
        return

    # Generate decision analysis
    decision_id = str(uuid.uuid4())

    try:
        # Analyze decision with specialized prompt
        analysis = await llm_service.analyze_decision(
            scenario,
            data.get("constraints", {}),
            data.get("priority", "normal")
        )

        # Broadcast decision response
        await manager.broadcast_to_session(
            session_id,
            {
                "type": MessageType.DECISION_RESPONSE,
                "decision_id": decision_id,
                "recommendation": analysis.get("recommendation"),
                "courses_of_action": analysis.get("courses_of_action", []),
                "risk_assessment": analysis.get("risk_assessment", {}),
                "confidence": analysis.get("confidence", 0.7)
            }
        )

        # Store decision in database
        from app.models.decision import Decision, DecisionStatus

        decision = Decision(
            user_id=user.id if user else None,
            conversation_id=conversation.id,
            scenario=scenario,
            recommendation=analysis.get("recommendation"),
            risk_assessment=analysis.get("risk_assessment"),
            courses_of_action=analysis.get("courses_of_action"),
            confidence_score=analysis.get("confidence", 0.7),
            status=DecisionStatus.DRAFT,
            metadata={
                "decision_id": decision_id,
                "constraints": data.get("constraints", {}),
                "priority": data.get("priority", "normal")
            }
        )
        db.add(decision)
        await db.commit()

    except Exception as e:
        logger.error(f"Error analyzing decision: {e}")
        await manager.send_personal_message(
            websocket,
            ErrorMessage(
                error="Failed to analyze decision",
                details={"error": str(e)}
            ).dict()
        )


async def get_conversation_history(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    limit: int = 20
) -> list:
    """Get recent conversation history."""
    query = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )

    result = await db.execute(query)
    messages = result.scalars().all()

    # Convert to LLM format
    history = []
    for msg in reversed(messages):
        history.append({
            "role": msg.role.value,
            "content": msg.content
        })

    return history


@router.websocket("/presence/{session_id}")
async def websocket_presence(
    websocket: WebSocket,
    session_id: str,
    token: Optional[str] = Query(None)
):
    """WebSocket endpoint for user presence and status updates."""
    await websocket.accept()

    try:
        while True:
            # Send periodic presence updates
            users = manager.get_session_users(session_id)
            await websocket.send_json({
                "type": "presence_update",
                "session_id": session_id,
                "users": users,
                "count": len(users)
            })

            # Wait before next update
            await asyncio.sleep(5)

    except WebSocketDisconnect:
        logger.info(f"Presence connection closed for session {session_id}")

    except Exception as e:
        logger.error(f"Presence WebSocket error: {e}")