"""
Authentication and authorization endpoints.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user, get_current_active_user
from app.models.user import User, UserRole
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    TokenResponse,
    TokenRefresh,
    PasswordChange,
    PasswordReset,
    PasswordResetConfirm
)
from app.services.auth_service import auth_service
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user account."""
    # Check if username already exists
    query = select(User).where(
        (User.username == user_data.username) | (User.email == user_data.email)
    )
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        if existing_user.username == user_data.username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )

    # Create new user
    user = await auth_service.create_user(
        db=db,
        email=user_data.email,
        username=user_data.username,
        password=user_data.password,
        full_name=user_data.full_name,
        rank=user_data.rank,
        unit=user_data.unit,
        role=user_data.role
    )

    logger.info(f"New user registered: {user.username}")
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    user_credentials: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return JWT tokens."""
    user = await auth_service.authenticate_user(
        db=db,
        username=user_credentials.username,
        password=user_credentials.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create token pair
    tokens = auth_service.create_token_pair(user)

    # Set refresh token as HTTP-only cookie
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="strict",
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )

    logger.info(f"User {user.username} logged in successfully")

    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRefresh,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token."""
    tokens = await auth_service.refresh_access_token(
        db=db,
        refresh_token=token_data.refresh_token
    )

    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Set new refresh token as HTTP-only cookie
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="strict",
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )

    logger.info("Access token refreshed successfully")

    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Logout user by clearing refresh token cookie."""
    # Clear refresh token cookie
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="strict"
    )

    logger.info(f"User {current_user.username} logged out")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get current user information."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db)
):
    """Update current user information."""
    # Update user fields
    if user_update.email is not None:
        # Check if email is already taken
        query = select(User).where(User.email == user_update.email)
        result = await db.execute(query)
        existing_user = result.scalar_one_or_none()
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already in use"
            )
        current_user.email = user_update.email
        current_user.is_verified = False  # Require re-verification

    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name

    if user_update.rank is not None:
        current_user.rank = user_update.rank

    if user_update.unit is not None:
        current_user.unit = user_update.unit

    await db.commit()
    await db.refresh(current_user)

    logger.info(f"User {current_user.username} updated their profile")
    return current_user


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    password_data: PasswordChange,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db)
):
    """Change user password."""
    # Verify current password
    if not auth_service.verify_password(
        password_data.current_password,
        current_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Update password
    current_user.hashed_password = auth_service.hash_password(password_data.new_password)
    current_user.last_password_change = datetime.utcnow()

    await db.commit()

    logger.info(f"User {current_user.username} changed their password")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/password-reset", status_code=status.HTTP_204_NO_CONTENT)
async def request_password_reset(
    reset_data: PasswordReset,
    db: AsyncSession = Depends(get_db)
):
    """Request password reset email."""
    # Find user by email
    query = select(User).where(User.email == reset_data.email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    # Always return success to prevent user enumeration
    if user:
        # In production, send password reset email
        # For now, just log
        logger.info(f"Password reset requested for user {user.username}")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_password_reset(
    reset_confirm: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """Confirm password reset with token."""
    # Decode reset token
    payload = auth_service.decode_token(reset_confirm.token)

    if not payload or payload.get("type") != "password_reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Get user
    user_id = UUID(payload["sub"])
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update password
    user.hashed_password = auth_service.hash_password(reset_confirm.new_password)
    user.last_password_change = datetime.utcnow()

    await db.commit()

    logger.info(f"Password reset completed for user {user.username}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Import datetime and UUID for password reset
from datetime import datetime
from uuid import UUID