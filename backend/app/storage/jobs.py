"""
Redis-based job storage for persistent job management.

Replaces in-memory dict storage with Redis for production reliability.
"""

import json
import logging
from pathlib import Path
from typing import Any

import redis
from api.models import ProcessingStatus

logger = logging.getLogger(__name__)


class JobStorage:
    """
    Redis-based job storage with fallback to in-memory dict.

    Provides persistent storage for job data including status,
    file paths, results, and metadata.
    """

    def __init__(self, redis_url: str | None = None, use_redis: bool = True):
        """
        Initialize job storage.

        Args:
            redis_url: Redis connection URL (e.g., "redis://localhost:6379/0")
            use_redis: Whether to use Redis or fallback to in-memory
        """
        self.use_redis = use_redis and redis_url is not None
        self.redis_url = redis_url

        if self.use_redis:
            try:
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                )
                # Test connection
                self.redis_client.ping()
                logger.info(f"Connected to Redis: {redis_url}")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Using in-memory storage.")
                self.use_redis = False
                self.redis_client = None
                self._memory_storage: dict[str, dict] = {}
        else:
            self.redis_client = None
            self._memory_storage: dict[str, dict] = {}
            logger.info("Using in-memory job storage")

    def _get_key(self, job_id: str) -> str:
        """Get Redis key for job ID."""
        return f"job:{job_id}"

    def create_job(
        self,
        job_id: str,
        filename: str,
        input_path: Path,
        status: ProcessingStatus = ProcessingStatus.PENDING,
    ) -> None:
        """
        Create a new job.

        Args:
            job_id: Unique job identifier
            filename: Original filename
            input_path: Path to uploaded file
            status: Initial status
        """
        job_data = {
            "job_id": job_id,
            "filename": filename,
            "input_path": str(input_path),
            "output_path": None,
            "status": status.value,
            "error": None,
            "stats": None,
            "device_used": None,
        }

        if self.use_redis:
            key = self._get_key(job_id)
            self.redis_client.setex(
                key,
                86400 * 7,  # 7 days TTL
                json.dumps(job_data),
            )
        else:
            self._memory_storage[job_id] = job_data

        logger.debug(f"Created job {job_id}")

    def get_job(self, job_id: str) -> dict | None:
        """
        Get job data.

        Args:
            job_id: Job identifier

        Returns:
            Job data dict or None if not found
        """
        if self.use_redis:
            key = self._get_key(job_id)
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        return self._memory_storage.get(job_id)

    def update_job(self, job_id: str, updates: dict[str, Any]) -> bool:
        """
        Update job data.

        Args:
            job_id: Job identifier
            updates: Dictionary of fields to update

        Returns:
            True if job found and updated, False otherwise
        """
        job = self.get_job(job_id)
        if not job:
            return False

        job.update(updates)

        if self.use_redis:
            key = self._get_key(job_id)
            self.redis_client.setex(
                key,
                86400 * 7,  # 7 days TTL
                json.dumps(job),
            )
        else:
            self._memory_storage[job_id] = job

        return True

    def set_status(
        self, job_id: str, status: ProcessingStatus, error: str | None = None
    ) -> bool:
        """
        Update job status.

        Args:
            job_id: Job identifier
            status: New status
            error: Error message if status is FAILED

        Returns:
            True if updated, False if job not found
        """
        updates = {"status": status.value}
        if error:
            updates["error"] = error

        return self.update_job(job_id, updates)

    def set_result(
        self,
        job_id: str,
        output_path: Path,
        stats: dict | None = None,
        device_used: str | None = None,
    ) -> bool:
        """
        Set job result data.

        Args:
            job_id: Job identifier
            output_path: Path to result file
            stats: Processing statistics
            device_used: Device name used for processing

        Returns:
            True if updated, False if job not found
        """
        updates = {
            "output_path": str(output_path),
            "status": ProcessingStatus.COMPLETED.value,
        }
        if stats:
            updates["stats"] = stats
        if device_used:
            updates["device_used"] = device_used

        return self.update_job(job_id, updates)

    def delete_job(self, job_id: str) -> bool:
        """
        Delete a job.

        Args:
            job_id: Job identifier

        Returns:
            True if deleted, False if not found
        """
        if self.use_redis:
            key = self._get_key(job_id)
            return bool(self.redis_client.delete(key))
        if job_id in self._memory_storage:
            del self._memory_storage[job_id]
            return True
        return False

    def exists(self, job_id: str) -> bool:
        """
        Check if job exists.

        Args:
            job_id: Job identifier

        Returns:
            True if job exists
        """
        if self.use_redis:
            key = self._get_key(job_id)
            return bool(self.redis_client.exists(key))
        return job_id in self._memory_storage

    def cleanup_old_jobs(self, days: int = 7) -> int:
        """
        Clean up jobs older than specified days.

        Note: With Redis TTL, this is automatic. For in-memory,
        we don't track creation time, so this is a no-op.

        Args:
            days: Age threshold in days

        Returns:
            Number of jobs deleted
        """
        if self.use_redis:
            # Redis TTL handles this automatically
            return 0
        # In-memory storage doesn't track creation time
        return 0


# Global instance (initialized in main.py)
job_storage: JobStorage | None = None


def get_job_storage() -> JobStorage:
    """Get the global job storage instance."""
    global job_storage
    if job_storage is None:
        raise RuntimeError("Job storage not initialized")
    return job_storage


def init_job_storage(redis_url: str | None = None) -> JobStorage:
    """
    Initialize global job storage.

    Args:
        redis_url: Redis connection URL or None for in-memory

    Returns:
        JobStorage instance
    """
    global job_storage
    job_storage = JobStorage(redis_url=redis_url)
    return job_storage
