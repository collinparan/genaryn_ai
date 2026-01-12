"""
WebSocket connection manager for real-time chat.
"""

from typing import Dict, List, Optional, Set
from uuid import UUID
import json
import asyncio

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.utils.logger import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """Manage WebSocket connections for real-time communication."""

    def __init__(self):
        """Initialize connection manager."""
        # Map session_id to list of connected WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Map WebSocket to user info
        self.connection_users: Dict[WebSocket, dict] = {}
        # Typing indicators
        self.typing_users: Dict[str, Set[str]] = {}
        # Lock for thread safety
        self.lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        session_id: str,
        user_info: Optional[dict] = None
    ):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()

        async with self.lock:
            if session_id not in self.active_connections:
                self.active_connections[session_id] = []

            self.active_connections[session_id].append(websocket)

            if user_info:
                self.connection_users[websocket] = user_info

            # Initialize typing set for session
            if session_id not in self.typing_users:
                self.typing_users[session_id] = set()

        logger.info(
            f"WebSocket connected to session {session_id}",
            user=user_info.get("username") if user_info else "anonymous"
        )

        # Send connection confirmation
        await self.send_personal_message(
            websocket,
            {
                "type": "connection",
                "content": "Connected to chat session",
                "session_id": session_id,
                "user": user_info
            }
        )

        # Notify others in session about new user
        if user_info:
            await self.broadcast_to_session(
                session_id,
                {
                    "type": "user_joined",
                    "user": user_info,
                    "content": f"{user_info.get('username', 'User')} joined the session"
                },
                exclude=websocket
            )

    async def disconnect(self, websocket: WebSocket, session_id: str):
        """Remove a WebSocket connection."""
        async with self.lock:
            if session_id in self.active_connections:
                if websocket in self.active_connections[session_id]:
                    self.active_connections[session_id].remove(websocket)

                # Remove session if no connections left
                if not self.active_connections[session_id]:
                    del self.active_connections[session_id]
                    if session_id in self.typing_users:
                        del self.typing_users[session_id]

            # Get user info before removing
            user_info = self.connection_users.pop(websocket, None)

            # Remove from typing users
            if session_id in self.typing_users and user_info:
                username = user_info.get("username")
                if username in self.typing_users[session_id]:
                    self.typing_users[session_id].remove(username)

        logger.info(
            f"WebSocket disconnected from session {session_id}",
            user=user_info.get("username") if user_info else "anonymous"
        )

        # Notify others in session about user leaving
        if user_info:
            await self.broadcast_to_session(
                session_id,
                {
                    "type": "user_left",
                    "user": user_info,
                    "content": f"{user_info.get('username', 'User')} left the session"
                }
            )

    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """Send a message to a specific WebSocket connection."""
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending personal message: {e}")

    async def broadcast_to_session(
        self,
        session_id: str,
        message: dict,
        exclude: Optional[WebSocket] = None
    ):
        """Broadcast a message to all connections in a session."""
        if session_id not in self.active_connections:
            return

        disconnected = []
        for connection in self.active_connections[session_id]:
            if exclude and connection == exclude:
                continue

            if connection.client_state == WebSocketState.CONNECTED:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting message: {e}")
                    disconnected.append(connection)
            else:
                disconnected.append(connection)

        # Clean up disconnected connections
        async with self.lock:
            for conn in disconnected:
                if conn in self.active_connections.get(session_id, []):
                    self.active_connections[session_id].remove(conn)
                self.connection_users.pop(conn, None)

    async def handle_typing(
        self,
        session_id: str,
        username: str,
        is_typing: bool
    ):
        """Handle typing indicator updates."""
        async with self.lock:
            if session_id not in self.typing_users:
                self.typing_users[session_id] = set()

            if is_typing:
                self.typing_users[session_id].add(username)
            else:
                self.typing_users[session_id].discard(username)

            typing_list = list(self.typing_users[session_id])

        # Broadcast typing status
        await self.broadcast_to_session(
            session_id,
            {
                "type": "typing_update",
                "typing_users": typing_list
            }
        )

    async def stream_llm_response(
        self,
        session_id: str,
        message_id: str,
        content_generator,
        metadata: Optional[dict] = None
    ):
        """Stream LLM response tokens to session."""
        full_content = ""

        try:
            async for chunk in content_generator:
                full_content += chunk

                # Send streaming chunk
                await self.broadcast_to_session(
                    session_id,
                    {
                        "type": "llm_stream",
                        "message_id": message_id,
                        "chunk": chunk,
                        "metadata": metadata
                    }
                )

            # Send completion message
            await self.broadcast_to_session(
                session_id,
                {
                    "type": "llm_complete",
                    "message_id": message_id,
                    "content": full_content,
                    "metadata": metadata
                }
            )

        except Exception as e:
            logger.error(f"Error streaming LLM response: {e}")
            await self.broadcast_to_session(
                session_id,
                {
                    "type": "error",
                    "message_id": message_id,
                    "error": str(e)
                }
            )

    def get_session_users(self, session_id: str) -> List[dict]:
        """Get list of users in a session."""
        if session_id not in self.active_connections:
            return []

        users = []
        for conn in self.active_connections[session_id]:
            if conn in self.connection_users:
                users.append(self.connection_users[conn])

        return users

    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs."""
        return list(self.active_connections.keys())

    def get_connection_count(self, session_id: str) -> int:
        """Get number of connections in a session."""
        return len(self.active_connections.get(session_id, []))


# Global connection manager instance
manager = ConnectionManager()