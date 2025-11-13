"""
Job repository following repository pattern for clean architecture.

Provides abstract interface for job data access with Redis and in-memory implementations.
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import redis
from api.models import ProcessingStatus

logger = logging.getLogger(__name__)


@dataclass
class Job:
    """
    Job domain model.

    Represents a processing job with all metadata.
    """

    job_id: str
    filename: str
    input_path: Path
    output_path: Path | None = None
    status: ProcessingStatus = ProcessingStatus.PENDING
    error: str | None = None
    stats: dict[str, Any] | None = None
    device_used: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "job_id": self.job_id,
            "filename": self.filename,
            "input_path": str(self.input_path),
            "output_path": str(self.output_path) if self.output_path else None,
            "status": self.status.value,
            "error": self.error,
            "stats": self.stats,
            "device_used": self.device_used,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Job":
        """Create Job from dictionary."""
        return cls(
            job_id=data["job_id"],
            filename=data["filename"],
            input_path=Path(data["input_path"]),
            output_path=Path(data["output_path"]) if data.get("output_path") else None,
            status=ProcessingStatus(data["status"]),
            error=data.get("error"),
            stats=data.get("stats"),
            device_used=data.get("device_used"),
        )


class JobRepository(ABC):
    """
    Abstract repository interface for job data access.

    Defines the contract that all job storage implementations must follow.
    Enables easy swapping of storage backends (Redis, PostgreSQL, etc).
    """

    @abstractmethod
    def create(self, job: Job) -> None:
        """
        Create a new job.

        Args:
            job: Job instance to create

        Raises:
            ValueError: If job with same ID already exists
        """
        pass

    @abstractmethod
    def get_by_id(self, job_id: str) -> Job | None:
        """
        Get job by ID.

        Args:
            job_id: Job identifier

        Returns:
            Job instance or None if not found
        """
        pass

    @abstractmethod
    def update(self, job: Job) -> bool:
        """
        Update existing job.

        Args:
            job: Job instance with updated fields

        Returns:
            True if updated, False if job not found
        """
        pass

    @abstractmethod
    def delete(self, job_id: str) -> bool:
        """
        Delete job by ID.

        Args:
            job_id: Job identifier

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    def exists(self, job_id: str) -> bool:
        """
        Check if job exists.

        Args:
            job_id: Job identifier

        Returns:
            True if job exists
        """
        pass


class RedisJobRepository(JobRepository):
    """
    Redis implementation of job repository.

    Stores jobs in Redis with 7-day TTL for automatic cleanup.
    """

    def __init__(self, redis_url: str):
        """
        Initialize Redis repository.

        Args:
            redis_url: Redis connection URL (e.g., "redis://localhost:6379/0")

        Raises:
            redis.ConnectionError: If cannot connect to Redis
        """
        self.redis_url = redis_url
        self.redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
        )
        # Test connection
        self.redis_client.ping()
        logger.info(f"Connected to Redis: {redis_url}")

    def _get_key(self, job_id: str) -> str:
        """Get Redis key for job ID."""
        return f"job:{job_id}"

    def create(self, job: Job) -> None:
        """Create a new job in Redis."""
        key = self._get_key(job.job_id)

        if self.redis_client.exists(key):
            msg = f"Job {job.job_id} already exists"
            raise ValueError(msg)

        self.redis_client.setex(
            key,
            86400 * 7,  # 7 days TTL
            json.dumps(job.to_dict()),
        )
        logger.debug(f"Created job {job.job_id} in Redis")

    def get_by_id(self, job_id: str) -> Job | None:
        """Get job from Redis."""
        key = self._get_key(job_id)
        data = self.redis_client.get(key)

        if not data:
            return None

        return Job.from_dict(json.loads(data))

    def update(self, job: Job) -> bool:
        """Update job in Redis."""
        key = self._get_key(job.job_id)

        if not self.redis_client.exists(key):
            return False

        self.redis_client.setex(
            key,
            86400 * 7,  # 7 days TTL
            json.dumps(job.to_dict()),
        )
        logger.debug(f"Updated job {job.job_id} in Redis")
        return True

    def delete(self, job_id: str) -> bool:
        """Delete job from Redis."""
        key = self._get_key(job_id)
        deleted = self.redis_client.delete(key)
        return bool(deleted)

    def exists(self, job_id: str) -> bool:
        """Check if job exists in Redis."""
        key = self._get_key(job_id)
        return bool(self.redis_client.exists(key))


class InMemoryJobRepository(JobRepository):
    """
    In-memory implementation of job repository.

    For development, testing, and fallback when Redis unavailable.
    Data is lost on application restart.
    """

    def __init__(self):
        """Initialize in-memory repository."""
        self._storage: dict[str, Job] = {}
        logger.info("Using in-memory job repository")

    def create(self, job: Job) -> None:
        """Create a new job in memory."""
        if job.job_id in self._storage:
            msg = f"Job {job.job_id} already exists"
            raise ValueError(msg)

        self._storage[job.job_id] = job
        logger.debug(f"Created job {job.job_id} in memory")

    def get_by_id(self, job_id: str) -> Job | None:
        """Get job from memory."""
        return self._storage.get(job_id)

    def update(self, job: Job) -> bool:
        """Update job in memory."""
        if job.job_id not in self._storage:
            return False

        self._storage[job.job_id] = job
        logger.debug(f"Updated job {job.job_id} in memory")
        return True

    def delete(self, job_id: str) -> bool:
        """Delete job from memory."""
        if job_id in self._storage:
            del self._storage[job_id]
            return True
        return False

    def exists(self, job_id: str) -> bool:
        """Check if job exists in memory."""
        return job_id in self._storage
