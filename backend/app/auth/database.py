"""
Database configuration for authentication.

Uses SQLite with SQLAlchemy for user storage.
"""

from collections.abc import AsyncGenerator

from config import settings
from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Create async SQLite engine
DATABASE_URL = f"sqlite+aiosqlite:///{settings.upload_dir.parent}/users.db"

engine = create_async_engine(DATABASE_URL, echo=settings.debug)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def create_db_and_tables():
    """Create database tables."""
    # Import here to avoid circular dependency
    from auth.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    """Get user database manager."""
    # Import here to avoid circular dependency
    from auth.models import User

    yield SQLAlchemyUserDatabase(session, User)
