"""
Authentication and authorization utilities.

Provides JWT token generation, validation, and user authentication.
"""

import os
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import User, get_db
from .schemas import TokenPayload


# Security configuration
# IMPORTANT: In production, SECRET_KEY must be set via environment variable.
# Use a strong, randomly generated key (e.g., `openssl rand -hex 32`).
# The default value is only for development purposes.
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Validate SECRET_KEY in production
if (
    os.getenv("UITESTFLOW_ENV") == "production"
    and SECRET_KEY == "dev-secret-key-change-in-production"
):
    raise RuntimeError(
        "CRITICAL SECURITY ERROR: SECRET_KEY environment variable must be set in production. "
        "Generate a secure key using: openssl rand -hex 32"
    )

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()


# ============================================================================
# Password Hashing
# ============================================================================


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


# ============================================================================
# JWT Token Management
# ============================================================================


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in token
        expires_delta: Token expiration time delta

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> TokenPayload:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        TokenPayload with decoded data

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
        return token_data
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================================================
# User Authentication
# ============================================================================


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """
    Authenticate a user by email and password.

    Args:
        db: Database session
        email: User email
        password: Plain text password

    Returns:
        User object if authentication succeeds, None otherwise
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        return None

    if not user.password_hash:
        return None

    if not verify_password(password, user.password_hash):
        return None

    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()

    return user


# ============================================================================
# Dependency Functions
# ============================================================================


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer credentials
        db: Database session

    Returns:
        User object

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    token_data = decode_token(token)

    # Get user from database
    try:
        user_id = UUID(token_data.sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current active user.

    Args:
        current_user: Current user from JWT token

    Returns:
        User object

    Raises:
        HTTPException: If user is inactive
    """
    # Add additional checks here (e.g., user.is_active)
    return current_user


def require_role(required_role: str):
    """
    Dependency factory to require a specific role.

    Args:
        required_role: Required role (e.g., "admin")

    Returns:
        Dependency function

    Example:
        @app.get("/admin/users")
        async def get_users(user: User = Depends(require_role("admin"))):
            ...
    """

    async def role_checker(user: User = Depends(get_current_active_user)) -> User:
        if user.role != required_role and user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}",
            )
        return user

    return role_checker


# ============================================================================
# Organization Access Control
# ============================================================================


async def verify_org_access(user: User, org_id: UUID) -> bool:
    """
    Verify that a user has access to an organization.

    Args:
        user: User object
        org_id: Organization ID to check

    Returns:
        True if user has access, False otherwise
    """
    return user.org_id == org_id


async def require_org_access(
    org_id: UUID,
    user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency to require organization access.

    Args:
        org_id: Organization ID
        user: Current user

    Returns:
        User object

    Raises:
        HTTPException: If user doesn't have access
    """
    if not await verify_org_access(user, org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization",
        )
    return user


# ============================================================================
# MCP API Key Authentication
# ============================================================================


from fastapi import Header


def get_api_key_from_header(
    x_api_key: str = Header(..., description="Anthropic API key"),
) -> str:
    """
    Extract Anthropic API key from X-API-Key header.

    This is used as a dependency for MCP endpoints that require
    an Anthropic API key for Claude interactions.

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        API key string

    Raises:
        HTTPException: If API key is missing

    Example:
        @router.post("/generate")
        async def generate(api_key: str = Depends(get_api_key_from_header)):
            generator = ClaudeTestGenerator(api_key=api_key)
            ...
    """
    return x_api_key
