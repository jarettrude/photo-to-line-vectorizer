"""
Authentication module.

Provides fastapi-users integration with Resend email for magic links.
"""

from auth.config import (
    auth_backend,
    current_active_user,
    current_user_optional,
    fastapi_users,
)
from auth.database import create_db_and_tables
from auth.models import User
from auth.schemas import UserCreate, UserRead, UserUpdate

__all__ = [
    "auth_backend",
    "create_db_and_tables",
    "current_active_user",
    "current_user_optional",
    "fastapi_users",
    "User",
    "UserCreate",
    "UserRead",
    "UserUpdate",
]
