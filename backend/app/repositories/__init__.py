"""
Repository pattern for data access abstraction.

Provides clean separation between business logic and data storage.
"""

from repositories.job_repository import (
    JobRepository,
    InMemoryJobRepository,
    RedisJobRepository,
)

__all__ = [
    "JobRepository",
    "InMemoryJobRepository",
    "RedisJobRepository",
]
