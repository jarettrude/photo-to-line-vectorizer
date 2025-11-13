"""
Pydantic schemas for authentication.

Request/response models for user operations.
"""

import uuid
from typing import Optional
from fastapi_users import schemas
from pydantic import Field


class UserRead(schemas.BaseUser[uuid.UUID]):
    """User response schema."""

    name: Optional[str] = None


class UserCreate(schemas.BaseUserCreate):
    """User creation schema."""

    name: Optional[str] = Field(None, max_length=255)


class UserUpdate(schemas.BaseUserUpdate):
    """User update schema."""

    name: Optional[str] = Field(None, max_length=255)
