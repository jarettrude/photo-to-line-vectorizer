"""
User models for authentication.

Extends fastapi-users SQLAlchemyBaseUserTable.
"""

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""



class User(SQLAlchemyBaseUserTableUUID, Base):
    """
    User model with email-based authentication.

    Inherits from fastapi-users base with UUID primary key.
    """

    __tablename__ = "users"

    # Additional fields (beyond fastapi-users defaults)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
