"""
User repository for database operations
"""

from typing import Optional, List
from datetime import datetime, timedelta
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.exc import IntegrityError

from app.models.user import User, UserRole
from app.utils.logger import get_logger

logger = get_logger(__name__)


class UserRepository:
    """Repository for user database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        email: str,
        username: str,
        hashed_password: str,
        full_name: Optional[str] = None,
        rank: Optional[str] = None,
        unit: Optional[str] = None,
        role: UserRole = UserRole.STAFF,
    ) -> User:
        """Create a new user."""
        user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            full_name=full_name,
            rank=rank,
            unit=unit,
            role=role,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        logger.info(f"Created user", user_id=str(user.id), username=username)
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def update(self, user: User, **kwargs) -> User:
        """Update user attributes."""
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)

        user.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_last_login(self, user: User) -> None:
        """Update last login timestamp."""
        user.last_login = datetime.utcnow()
        user.failed_login_attempts = 0
        await self.session.commit()

    async def increment_failed_login(self, user: User) -> None:
        """Increment failed login attempts and lock if necessary."""
        user.failed_login_attempts += 1

        # Lock account after max attempts
        if user.failed_login_attempts >= 5:  # Should use settings.MAX_LOGIN_ATTEMPTS
            user.locked_until = datetime.utcnow() + timedelta(minutes=15)  # Should use settings.LOCKOUT_DURATION_MINUTES
            logger.warning(f"User account locked", user_id=str(user.id))

        await self.session.commit()

    async def is_account_locked(self, user: User) -> bool:
        """Check if user account is locked."""
        if user.locked_until and user.locked_until > datetime.utcnow():
            return True
        return False

    async def unlock_account(self, user: User) -> None:
        """Unlock user account."""
        user.locked_until = None
        user.failed_login_attempts = 0
        await self.session.commit()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination."""
        result = await self.session.execute(
            select(User).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def delete(self, user: User) -> None:
        """Delete user."""
        await self.session.delete(user)
        await self.session.commit()
        logger.info(f"Deleted user", user_id=str(user.id))