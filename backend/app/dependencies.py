"""
Dependency injection for FastAPI.

Provides factory functions for services, repositories, and other dependencies.
Enables clean architecture with proper dependency inversion.
"""

import logging
from functools import lru_cache

from fastapi import Depends
from repositories.job_repository import (
    InMemoryJobRepository,
    JobRepository,
    RedisJobRepository,
)
from services.job_service import JobService
from pipeline.processor import PhotoToLineProcessor
from config import settings

logger = logging.getLogger(__name__)


@lru_cache
def get_processor() -> PhotoToLineProcessor:
    """
    Get or create the global processor instance.

    Uses LRU cache to ensure singleton behavior - processor is expensive to create
    due to model loading, so we want one instance per application.

    Returns:
        PhotoToLineProcessor instance
    """
    logger.info("Initializing PhotoToLineProcessor")

    return PhotoToLineProcessor(
        u2net_model_path=settings.u2net_model_path
        if settings.u2net_model_path.exists()
        else None,
    )


def get_job_repository() -> JobRepository:
    """
    Get job repository based on configuration.

    Creates Redis repository if redis_url configured, otherwise in-memory fallback.
    Each request gets a new repository instance (stateless).

    Returns:
        JobRepository instance (Redis or InMemory)
    """
    if settings.redis_url:
        try:
            return RedisJobRepository(settings.redis_url)
        except Exception as e:
            logger.warning(
                f"Failed to connect to Redis: {e}. Falling back to in-memory storage."
            )
            return InMemoryJobRepository()

    return InMemoryJobRepository()


def get_job_service(
    repository: JobRepository = Depends(get_job_repository),
    processor: PhotoToLineProcessor = Depends(get_processor),
) -> JobService:
    """
    Get job service with injected dependencies.

    FastAPI will automatically inject repository and processor when needed.

    Args:
        repository: Injected job repository
        processor: Injected processor

    Returns:
        JobService instance with dependencies
    """
    return JobService(repository=repository, processor=processor)
