"""
Dependency injection for FastAPI.

Provides factory functions for services and other dependencies.
Enables clean architecture with proper dependency inversion.
"""

import logging
from functools import lru_cache

from config import settings
from fastapi import Depends
from pipeline.processor import PhotoToLineProcessor
from services.job_service import JobService
from storage import JobStorage, get_job_storage

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


def get_job_service(
    storage: JobStorage = Depends(get_job_storage),
    processor: PhotoToLineProcessor = Depends(get_processor),
) -> JobService:
    """
    Get job service with injected dependencies.

    FastAPI will automatically inject storage and processor when needed.

    Args:
        storage: Injected job storage
        processor: Injected processor

    Returns:
        JobService instance with dependencies
    """
    return JobService(storage=storage, processor=processor)
