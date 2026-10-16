from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.config import settings

# Async engine and session factory for high-performance FastAPI interactions
async_engine = create_async_engine(settings.database_url_async, echo=False)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


# Sync engine and session factory for background Celery tasks
sync_engine = create_engine(settings.database_url_sync)
SyncSessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False)


async def init_db() -> None:
    """Initializes the database and generates all missing schemas."""
    async with async_engine.begin() as conn:
        # Create tables safely inside the current async transaction
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_async_db() -> AsyncGenerator[AsyncSession | Any]:
    """Dependency injection provider for FastAPI async DB sessions."""
    async with AsyncSessionLocal() as session:
        yield session
