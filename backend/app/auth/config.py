"""
FastAPI-Users configuration.

Sets up authentication backends and strategies.
"""

import uuid

from config import settings
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)

from auth.manager import get_user_manager
from auth.models import User

# Bearer token transport
bearer_transport = BearerTransport(tokenUrl="auth/login")


def get_jwt_strategy() -> JWTStrategy:
    """Get JWT strategy for authentication."""
    return JWTStrategy(
        secret=settings.secret_key,
        lifetime_seconds=3600 * 24 * 7,  # 7 days
    )


# Authentication backend
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# FastAPI Users instance
fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

# Dependency for requiring authentication
current_active_user = fastapi_users.current_user(active=True)
# Optional authentication (returns None if not authenticated)
current_user_optional = fastapi_users.current_user(active=True, optional=True)
