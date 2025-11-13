"""
User manager for fastapi-users.

Handles user lifecycle events and email notifications.
"""

import logging
import uuid

import resend
from config import settings
from fastapi import Depends, Request
from fastapi_users import BaseUserManager, UUIDIDMixin

from auth.database import get_user_db
from auth.models import User

logger = logging.getLogger(__name__)

# Secret key for JWT tokens (should be set via environment variable in production)
SECRET = (
    settings.secret_key
    if hasattr(settings, "secret_key")
    else "changeme-secret-key-in-production"
)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    """
    Custom user manager with Resend email integration.

    Handles magic link email sending for passwordless authentication.
    """

    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Request | None = None):
        """Called after user registration."""
        logger.info(f"User {user.id} ({user.email}) registered")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Request | None = None
    ):
        """Send magic link email after forgot password request."""
        if not settings.resend_api_key:
            logger.warning(
                f"Magic link requested for {user.email} but Resend not configured. Token: {token}"
            )
            return

        try:
            # Get the base URL from request or config
            base_url = (
                settings.frontend_url
                if hasattr(settings, "frontend_url")
                else "http://localhost:5173"
            )
            magic_link = f"{base_url}/auth/verify?token={token}"

            # Send email via Resend
            resend.api_key = settings.resend_api_key
            resend.Emails.send(
                {
                    "from": settings.resend_from_email,
                    "to": [user.email],
                    "subject": "Sign in to Photo Vectorizer",
                    "html": f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <h2>Sign in to Photo Vectorizer</h2>
                        <p>Click the button below to sign in to your account:</p>
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{magic_link}"
                               style="background-color: #4F46E5; color: white; padding: 12px 24px;
                                      text-decoration: none; border-radius: 6px; display: inline-block;">
                                Sign In
                            </a>
                        </div>
                        <p style="color: #666; font-size: 14px;">
                            This link will expire in 1 hour.<br>
                            If you didn't request this, you can safely ignore this email.
                        </p>
                    </div>
                    """,
                }
            )
            logger.info(f"Magic link sent to {user.email}")
        except Exception as e:
            logger.exception(f"Failed to send magic link to {user.email}: {e}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Request | None = None
    ):
        """Send verification email with magic link."""
        await self.on_after_forgot_password(user, token, request)


async def get_user_manager(user_db=Depends(get_user_db)):
    """Dependency to get user manager instance."""
    yield UserManager(user_db)
