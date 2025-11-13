"""
Authentication routes.

Provides login, logout, register, and magic link endpoints.
"""

from config import settings
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi_users import exceptions
from pydantic import BaseModel, EmailStr

from auth import UserCreate, UserRead, UserUpdate, auth_backend, fastapi_users
from auth.manager import UserManager, get_user_manager

router = APIRouter()

# Include FastAPI-Users auth routes
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth",
    tags=["auth"],
)

# Include register route (optional - can be disabled in production)
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

# Include users routes for profile management
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)


class MagicLinkRequest(BaseModel):
    """Request model for magic link."""

    email: EmailStr


@router.post("/auth/magic-link", tags=["auth"])
async def request_magic_link(
    body: MagicLinkRequest,
    request: Request,
    user_manager: UserManager = Depends(get_user_manager),
):
    """
    Request a magic link for passwordless login.

    Sends an email with a magic link that logs the user in.
    """
    if not settings.resend_api_key:
        raise HTTPException(
            status_code=503,
            detail="Email service not configured. Please set RESEND_API_KEY.",
        )

    try:
        # Get user by email
        user = await user_manager.get_by_email(body.email)
        if not user:
            # Don't reveal if user exists or not for security
            return {
                "message": "If an account exists with this email, you will receive a magic link."
            }

        # Generate magic link token
        token = await user_manager.forgot_password(user, request)

        return {
            "message": "If an account exists with this email, you will receive a magic link."
        }

    except exceptions.UserNotExists:
        # Don't reveal if user exists or not
        return {
            "message": "If an account exists with this email, you will receive a magic link."
        }
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to send magic link")
