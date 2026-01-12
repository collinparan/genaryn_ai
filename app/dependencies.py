"""
FastAPI dependencies for dependency injection.
"""

from typing import Optional, Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.services.auth_service import auth_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials

    user = await auth_service.verify_token(db, token)
    if not user:
        logger.warning("Invalid or expired authentication token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        logger.warning(f"Inactive user {current_user.username} attempted access")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_current_verified_user(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """Get current verified user."""
    if not current_user.is_verified:
        logger.warning(f"Unverified user {current_user.username} attempted access")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User email not verified"
        )
    return current_user


class RoleChecker:
    """Dependency class for role-based access control."""

    def __init__(self, allowed_roles: list[UserRole]):
        """Initialize role checker with allowed roles."""
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        current_user: Annotated[User, Depends(get_current_active_user)]
    ) -> User:
        """Check if user has required role."""
        if current_user.role not in self.allowed_roles:
            logger.warning(
                f"User {current_user.username} with role {current_user.role} "
                f"attempted access to resource requiring {self.allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {[r.value for r in self.allowed_roles]}"
            )
        return current_user


# Convenience role dependencies
def require_admin() -> RoleChecker:
    """Require admin role."""
    return RoleChecker([UserRole.ADMIN])


def require_commander() -> RoleChecker:
    """Require commander role or higher."""
    return RoleChecker([UserRole.COMMANDER, UserRole.ADMIN])


def require_staff() -> RoleChecker:
    """Require staff role or higher."""
    return RoleChecker([UserRole.STAFF, UserRole.COMMANDER, UserRole.ADMIN])


def require_observer() -> RoleChecker:
    """Require observer role or higher (any authenticated user)."""
    return RoleChecker([UserRole.OBSERVER, UserRole.STAFF, UserRole.COMMANDER, UserRole.ADMIN])


# Optional authentication
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise."""
    if not credentials:
        return None

    token = credentials.credentials
    user = await auth_service.verify_token(db, token)
    return user