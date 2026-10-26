"""Async SQLAlchemy session for the *real* Home Assistant recorder database.

This module is only imported when ``DATA_SOURCE=database`` is enabled, which
requires installing the ``database`` extra::

    pip install -e ".[database]"

In ``mock`` mode it is never imported, so the prototype runs without
SQLAlchemy / a database driver installed.
"""

from __future__ import annotations

import ssl
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.engine import URL

from app.core.config import settings


def _build_url() -> URL:
    return URL.create(
        drivername="mysql+aiomysql",
        username=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
        query={"charset": "utf8mb4"},
    )


def _build_ssl_context() -> ssl.SSLContext | None:
    """TLS context for the DB connection, or ``None`` when ``DB_SSL`` is off.

    The UCLM server requires encrypted connections. Without a CA file the
    traffic is encrypted but the certificate is not verified, and the hostname
    is never checked because the server is reached by IP.
    """
    if not settings.DB_SSL:
        return None
    if settings.DB_SSL_CA:
        context = ssl.create_default_context(cafile=settings.DB_SSL_CA)
        context.check_hostname = False
        return context
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


_connect_args: dict[str, object] = {
    "connect_timeout": 5,
    # Home Assistant stores naive UTC datetimes; pinning the session timezone
    # makes UNIX_TIMESTAMP()/FROM_UNIXTIME() interpret them as UTC regardless of
    # the MariaDB server timezone.
    "init_command": "SET time_zone = '+00:00'",
}
_ssl_context = _build_ssl_context()
if _ssl_context is not None:
    _connect_args["ssl"] = _ssl_context

engine = create_async_engine(
    _build_url(),
    pool_pre_ping=True,
    pool_recycle=1800,
    connect_args=_connect_args,
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
