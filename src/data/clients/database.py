"""This module sets up the database connection and defines the base class for SQLAlchemy models. It includes an asynchronous engine and session maker for interacting with the database, as well as a function to initialize the database by applying any pending migrations. The `Base` class serves as a common base for all SQLAlchemy models, ensuring they are properly registered with the ORM system.    The `init_db` function should be called during application startup to prepare the database for use, ensuring that the schema is up to date with the application's requirements. The module also includes a dependency function `get_db` that provides an asynchronous database session for use in API route handlers, ensuring proper resource management by closing the session after use."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config.settings import settings
from src.data.migrations.runner import apply_migrations

engine = create_async_engine(settings.db_url)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models. All database models should inherit from this class to ensure they are properly registered with SQLAlchemy's ORM system. This class serves as a common base for all models, allowing for consistent behavior and easy integration with the database session."""

    pass


engine = create_async_engine(
    settings.db_url,
    pool_pre_ping=True,
)


async def init_db() -> None:
    """Initialize the database by applying any pending migrations. This function creates an asynchronous connection to the database and runs the migration scripts to ensure that the database schema is up to date with the application's requirements. It should be called during application startup to prepare the database for use."""
    async with engine.begin() as conn:
        await apply_migrations(conn)
