"""
Job service for business logic orchestration.

Coordinates between storage, processor, and other components.
Handles all business rules and validations.
"""

import asyncio
import logging
import uuid
from pathlib import Path

from api.models import ProcessingStatus
from api.websocket import ws_manager
from config import settings
from fastapi import HTTPException, UploadFile
from pipeline.processor import PhotoToLineProcessor, ProcessingParams, ProcessingResult
from storage import JobStorage

logger = logging.getLogger(__name__)


class JobService:
    """
    Service layer for job management and processing.

    Orchestrates job creation, processing, status updates, and result retrieval.
    Contains all business logic separated from API layer.
    """

    def __init__(self, storage: JobStorage, processor: PhotoToLineProcessor):
        """
        Initialize job service.

        Args:
            storage: Job storage for data access
            processor: Photo processing pipeline
        """
        self.storage = storage
        self.processor = processor

    async def create_job_from_upload(
        self, file: UploadFile
    ) -> tuple[str, str, Path]:
        """
        Create job from uploaded file with validation.

        Args:
            file: Uploaded image file

        Returns:
            Tuple of (job_id, filename, file_path)

        Raises:
            HTTPException: If file invalid or upload fails
        """
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        # Validate file format
        suffix = Path(file.filename).suffix.lower()
        allowed_formats = {
            ".jpg",
            ".jpeg",
            ".png",
            ".tiff",
            ".tif",
            ".webp",
            ".heic",
            ".heif",
        }

        if suffix not in allowed_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format: {suffix}. Supported: {', '.join(allowed_formats)}",
            )

        # Read and validate file size
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)

        if file_size_mb > settings.max_upload_size_mb:
            raise HTTPException(
                status_code=413,
                detail=f"File too large: {file_size_mb:.1f}MB (max: {settings.max_upload_size_mb}MB)",
            )

        # Create job with unique ID
        job_id = str(uuid.uuid4())
        file_path = settings.upload_dir / f"{job_id}{suffix}"

        try:
            # Save file
            file_path.write_bytes(content)

            # Create job in storage
            self.storage.create_job(
                job_id=job_id,
                filename=file.filename,
                input_path=file_path,
                status=ProcessingStatus.PENDING,
            )

            logger.info(
                f"Created job {job_id} for file {file.filename} ({file_size_mb:.1f}MB)"
            )

            return job_id, file.filename, file_path

        except Exception as e:
            # Clean up file on error
            if file_path.exists():
                file_path.unlink()
            logger.exception("Job creation failed")
            raise HTTPException(status_code=500, detail="Upload failed") from e

    def get_job(self, job_id: str) -> dict:
        """
        Get job by ID.

        Args:
            job_id: Job identifier

        Returns:
            Job data dictionary

        Raises:
            HTTPException: If job not found
        """
        job = self.storage.get_job(job_id)

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return job

    async def process_job(self, job_id: str, params: ProcessingParams) -> None:
        """
        Process job with given parameters.

        Executes complete pipeline: preprocessing, line extraction,
        vectorization, optimization, and optional hatching.

        Args:
            job_id: Job identifier
            params: Processing parameters

        Raises:
            HTTPException: If job not found or invalid state
        """
        # Get job from storage
        job = self.storage.get_job(job_id)

        if not job:
            logger.error(f"Job {job_id} not found")
            raise HTTPException(status_code=404, detail="Job not found")

        if job["status"] != ProcessingStatus.PENDING.value:
            raise HTTPException(
                status_code=400,
                detail=f"Job already {job['status']}",
            )

        # Update status to processing
        self.storage.set_status(job_id, ProcessingStatus.PROCESSING)

        logger.info(f"Starting processing for job {job_id}")

        # Broadcast initial progress
        await ws_manager.broadcast_progress(
            job_id, progress=10, stage="preprocessing", message="Loading image"
        )

        try:
            # Execute processing pipeline with progress updates
            # Note: Running processor synchronously in thread pool
            await ws_manager.broadcast_progress(
                job_id, progress=20, stage="line_extraction", message="Extracting lines"
            )

            # Run processor in thread pool to avoid blocking
            result: ProcessingResult = await asyncio.to_thread(
                self.processor.process_sync,
                image_path=Path(job["input_path"]),
                params=params,
            )

            await ws_manager.broadcast_progress(
                job_id, progress=80, stage="export", message="Generating SVG"
            )

            # Save result
            output_path = settings.results_dir / f"{job_id}.svg"
            output_path.write_text(result.svg_content)

            # Update job with results
            self.storage.set_result(
                job_id=job_id,
                output_path=output_path,
                stats=dict(result.stats),
                device_used=result.device_used,
            )

            logger.info(
                f"Job {job_id} completed: {result.stats.get('path_count', 0)} paths, "
                f"device={result.device_used}"
            )

            # Broadcast completion
            result_url = f"/api/download/{job_id}"
            await ws_manager.broadcast_complete(
                job_id, result_url=result_url, stats=dict(result.stats)
            )

        except Exception as e:
            logger.exception(f"Job {job_id} failed")

            # Update job with error
            self.storage.set_status(job_id, ProcessingStatus.FAILED, error=str(e))

            # Broadcast error
            await ws_manager.broadcast_error(job_id, error=str(e))

            raise HTTPException(
                status_code=500, detail=f"Processing failed: {e}"
            ) from e

    def get_job_status(self, job_id: str) -> dict:
        """
        Get job status with progress calculation.

        Args:
            job_id: Job identifier

        Returns:
            Status dictionary with progress, results, and metadata

        Raises:
            HTTPException: If job not found
        """
        job = self.get_job(job_id)

        # Calculate progress
        progress = 0
        if job["status"] == ProcessingStatus.PROCESSING.value:
            progress = 50
        elif job["status"] == ProcessingStatus.COMPLETED.value:
            progress = 100

        # Build result URL
        result_url = None
        if job.get("output_path"):
            result_url = f"/api/download/{job_id}"

        return {
            "job_id": job["job_id"],
            "status": ProcessingStatus(job["status"]),
            "progress": progress,
            "result_url": result_url,
            "stats": job.get("stats"),
            "error": job.get("error"),
            "device_used": job.get("device_used"),
        }

    def get_result_path(self, job_id: str) -> Path:
        """
        Get result file path for completed job.

        Args:
            job_id: Job identifier

        Returns:
            Path to result SVG file

        Raises:
            HTTPException: If job not found or not completed
        """
        job = self.get_job(job_id)

        if job["status"] != ProcessingStatus.COMPLETED.value:
            raise HTTPException(
                status_code=400,
                detail="Job not completed",
            )

        output_path = Path(job["output_path"]) if job.get("output_path") else None

        if not output_path or not output_path.exists():
            raise HTTPException(status_code=404, detail="Result file not found")

        return output_path

    def delete_job(self, job_id: str) -> bool:
        """
        Delete job and associated files.

        Args:
            job_id: Job identifier

        Returns:
            True if deleted successfully
        """
        job = self.storage.get_job(job_id)

        if not job:
            return False

        # Clean up files
        try:
            input_path = Path(job["input_path"]) if job.get("input_path") else None
            if input_path and input_path.exists():
                input_path.unlink()

            output_path = Path(job["output_path"]) if job.get("output_path") else None
            if output_path and output_path.exists():
                output_path.unlink()

        except Exception as e:
            logger.warning(f"Failed to delete files for job {job_id}: {e}")

        # Delete from storage
        return self.storage.delete_job(job_id)
