"""
Authentication service for JWT token management and user authentication.
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from uuid import UUID

import bcrypt
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models.user import User, UserRole
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AuthService:
    """Service for authentication and authorization operations."""

    def __init__(self):
        """Initialize authentication service."""
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        self.bcrypt_rounds = settings.BCRYPT_ROUNDS
        self.max_login_attempts = settings.MAX_LOGIN_ATTEMPTS
        self.lockout_duration = settings.LOCKOUT_DURATION_MINUTES

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt(rounds=self.bcrypt_rounds)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )

    def create_access_token(
        self,
        user_id: UUID,
        username: str,
        role: UserRole,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT access token."""
        expire = datetime.utcnow() + (
            expires_delta or timedelta(minutes=self.access_token_expire)
        )

        payload = {
            "sub": str(user_id),
            "username": username,
            "role": role.value,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.info(f"Created access token for user {username}")
        return token

    def create_refresh_token(
        self,
        user_id: UUID,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT refresh token."""
        expire = datetime.utcnow() + (
            expires_delta or timedelta(days=self.refresh_token_expire)
        )

        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def decode_token(self, token: str) -> Optional[dict]:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {e}")
            return None

    async def authenticate_user(
        self,
        db: AsyncSession,
        username: str,
        password: str
    ) -> Optional[User]:
        """Authenticate a user with username and password."""
        # Find user by username or email
        query = select(User).where(
            (User.username == username) | (User.email == username)
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"Authentication failed: User {username} not found")
            return None

        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            logger.warning(f"Authentication failed: User {username} is locked until {user.locked_until}")
            return None

        # Verify password
        if not self.verify_password(password, user.hashed_password):
            # Increment failed login attempts
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1

            # Lock account if max attempts exceeded
            if user.failed_login_attempts >= self.max_login_attempts:
                user.locked_until = datetime.utcnow() + timedelta(minutes=self.lockout_duration)
                logger.warning(f"User {username} locked due to {user.failed_login_attempts} failed attempts")

            await db.commit()
            logger.warning(f"Authentication failed: Invalid password for user {username}")
            return None

        # Check if user is active
        if not user.is_active:
            logger.warning(f"Authentication failed: User {username} is inactive")
            return None

        # Reset failed attempts and update last login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        await db.commit()

        logger.info(f"User {username} authenticated successfully")
        return user

    async def create_user(
        self,
        db: AsyncSession,
        email: str,
        username: str,
        password: str,
        full_name: Optional[str] = None,
        rank: Optional[str] = None,
        unit: Optional[str] = None,
        role: UserRole = UserRole.STAFF
    ) -> User:
        """Create a new user with hashed password."""
        hashed_password = self.hash_password(password)

        user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            full_name=full_name,
            rank=rank,
            unit=unit,
            role=role,
            is_active=True,
            is_verified=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info(f"Created new user: {username} with role {role.value}")
        return user

    async def get_user_by_id(
        self,
        db: AsyncSession,
        user_id: UUID
    ) -> Optional[User]:
        """Get user by ID."""
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    def create_token_pair(self, user: User) -> dict:
        """Create access and refresh token pair."""
        access_token = self.create_access_token(
            user_id=user.id,
            username=user.username,
            role=user.role
        )
        refresh_token = self.create_refresh_token(user_id=user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    async def refresh_access_token(
        self,
        db: AsyncSession,
        refresh_token: str
    ) -> Optional[dict]:
        """Refresh an access token using a refresh token."""
        payload = self.decode_token(refresh_token)

        if not payload or payload.get("type") != "refresh":
            logger.warning("Invalid refresh token")
            return None

        user_id = UUID(payload["sub"])
        user = await self.get_user_by_id(db, user_id)

        if not user or not user.is_active:
            logger.warning(f"User {user_id} not found or inactive")
            return None

        # Create new token pair
        return self.create_token_pair(user)

    async def verify_token(
        self,
        db: AsyncSession,
        token: str
    ) -> Optional[User]:
        """Verify an access token and return the user."""
        payload = self.decode_token(token)

        if not payload or payload.get("type") != "access":
            return None

        user_id = UUID(payload["sub"])
        user = await self.get_user_by_id(db, user_id)

        if not user or not user.is_active:
            return None

        return user


# Global auth service instance
auth_service = AuthService()