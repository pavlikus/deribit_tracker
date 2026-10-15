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

from .config import settings

async_engine = create_async_engine(settings.database_url_async, echo=False)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


sync_engine = create_engine(settings.database_url_sync)
SyncSessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False)


async def init_db() -> None:
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_async_db() -> AsyncGenerator[AsyncSession | Any]:
    async with AsyncSessionLocal() as session:
        yield session
