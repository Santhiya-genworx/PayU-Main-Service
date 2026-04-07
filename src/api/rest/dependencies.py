"""Module: dependencies.py"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.data.clients.database import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an asynchronous database session.   This function is an asynchronous generator that yields a database session. It ensures that the session is properly closed after use, preventing potential resource leaks. Route handlers that require database access can include this dependency to receive a session instance.    Yields:        An instance of AsyncSession for database operations."""
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()
