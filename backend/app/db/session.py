"""Async SQLAlchemy session for the *real* Home Assistant recorder database.

This module is only imported when ``DATA_SOURCE=database`` is enabled, which
requires installing the ``database`` extra::

    pip install -e ".[database]"

In the default ``mock`` mode it is never imported, so the prototype runs without
SQLAlchemy / a database driver installed.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.engine import URL

from app.core.config import settings


def _build_url() -> URL:
    query = {"charset": "utf8mb4"}
    if settings.DB_SSL:
        query["ssl"] = "true"
        if settings.DB_SSL_CA:
            query["ssl_ca"] = settings.DB_SSL_CA

    return URL.create(
        drivername="mysql+aiomysql",
        username=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
        query=query,
    )


engine = create_async_engine(_build_url(), pool_pre_ping=True, pool_recycle=1800)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
