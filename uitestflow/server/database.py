"""
Database setup and models for UITestFlow server.

Provides SQLAlchemy async setup, database models, and session management.
"""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, DateTime, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# Database configuration from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://uitest:uitest@localhost:5432/uitestflow"
)


class Base(DeclarativeBase):
    """Base class for all database models."""


# ============================================================================
# Database Models
# ============================================================================


class Organization(Base):
    """Organization/tenant model."""

    __tablename__ = "organizations"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    plan: Mapped[str] = mapped_column(String(50), nullable=False, default="free")
    monthly_test_runs: Mapped[int] = mapped_column(Integer, default=100)
    storage_gb: Mapped[int] = mapped_column(Integer, default=1)
    retention_days: Mapped[int] = mapped_column(Integer, default=7)
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("NOW()")
    )


class User(Base):
    """User model."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    org_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="member")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("NOW()")
    )
    last_login: Mapped[datetime] = mapped_column(DateTime, nullable=True)


class Profile(Base):
    """Profile model for environment configurations."""

    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    org_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    profile_type: Mapped[str] = mapped_column(
        String(50), default="environment"
    )  # environment, workflow, custom
    execution_mode: Mapped[str] = mapped_column(
        String(50), default="automated"
    )  # automated, manual, hybrid
    base_url: Mapped[str] = mapped_column(String(500), nullable=True)
    init_steps: Mapped[list] = mapped_column(JSON, default=list)  # Initialization steps
    auth_config: Mapped[dict] = mapped_column(JSON, default=dict)
    browser_config: Mapped[dict] = mapped_column(JSON, default=dict)
    llm_config: Mapped[dict] = mapped_column(JSON, default=dict)  # LLM configuration
    notification_config: Mapped[dict] = mapped_column(JSON, default=dict)
    tags: Mapped[list] = mapped_column(JSON, default=list)  # Profile tags for categorization
    environment_status: Mapped[str] = mapped_column(
        String(50), nullable=True
    )  # running, stopped, error, etc.

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("NOW()"), onupdate=text("NOW()")
    )


class TestDefinitionModel(Base):
    """Test definition model."""

    __tablename__ = "test_definitions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    org_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(20), default="1.0")
    url: Mapped[str] = mapped_column(String(500), nullable=True)
    steps: Mapped[dict] = mapped_column(JSON, nullable=False)
    evaluators: Mapped[dict] = mapped_column(JSON, default=dict)
    browser_config: Mapped[dict] = mapped_column(JSON, default=dict)
    auth_config: Mapped[dict] = mapped_column(JSON, default=dict)
    timeout: Mapped[int] = mapped_column(Integer, default=30000)
    retry_config: Mapped[dict] = mapped_column(JSON, default=dict)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("NOW()"), onupdate=text("NOW()")
    )
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=True)


class TestRunModel(Base):
    """Test run model."""

    __tablename__ = "test_runs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    test_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    org_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    test_name: Mapped[str] = mapped_column(String(255), nullable=False)
    profile: Mapped[str] = mapped_column(String(100), nullable=True)
    triggered_by: Mapped[str] = mapped_column(String(50), nullable=False)
    context: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    result: Mapped[dict] = mapped_column(JSON, nullable=True)
    video_url: Mapped[str] = mapped_column(String(500), nullable=True)
    trace_url: Mapped[str] = mapped_column(String(500), nullable=True)
    har_url: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("NOW()")
    )


class ScreenshotModel(Base):
    """Screenshot model."""

    __tablename__ = "screenshots"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    test_run_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    step_name: Mapped[str] = mapped_column(String(255), nullable=True)
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_url: Mapped[str] = mapped_column(String(500), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=True)


class LogModel(Base):
    """Log entry model."""

    __tablename__ = "logs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    test_run_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    log_metadata: Mapped[dict] = mapped_column(JSON, default=dict)


class APIKey(Base):
    """API key model."""

    __tablename__ = "api_keys"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    org_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    last_used: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("NOW()")
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)


# ============================================================================
# Database Engine and Session Management
# ============================================================================

# Create async engine
# Note: SQLite doesn't support pool_size or max_overflow parameters
if DATABASE_URL.startswith("sqlite"):
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,  # Set to True for SQL query logging
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    )
else:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,  # Set to True for SQL query logging
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.

    Yields:
        AsyncSession: Database session

    Example:
        @app.get("/tests")
        async def get_tests(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(TestDefinitionModel))
            return result.scalars().all()
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context():
    """
    Context manager to get database session.

    Yields:
        AsyncSession: Database session

    Example:
        async with get_db_context() as db:
            result = await db.execute(select(TestDefinitionModel))
            tests = result.scalars().all()
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database by creating all tables.

    This should be called on application startup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    """
    Drop all database tables.

    WARNING: This will delete all data. Use only for testing.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def close_db():
    """
    Close database connections.

    This should be called on application shutdown.
    """
    await engine.dispose()


# ============================================================================
# Migration Helpers
# ============================================================================


async def get_table_names() -> list[str]:
    """
    Get list of all table names in the database.

    Returns:
        List of table names
    """
    async with engine.begin() as conn:
        result = await conn.run_sync(lambda sync_conn: sync_conn.dialect.get_table_names(sync_conn))
        return result


async def table_exists(table_name: str) -> bool:
    """
    Check if a table exists in the database.

    Args:
        table_name: Name of the table to check

    Returns:
        True if table exists, False otherwise
    """
    tables = await get_table_names()
    return table_name in tables
