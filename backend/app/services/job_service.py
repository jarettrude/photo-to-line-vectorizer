"""
Job service for business logic orchestration.

Coordinates between repository, processor, and other components.
Handles all business rules and validations.
"""

import logging
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from repositories.job_repository import Job, JobRepository
from api.models import ProcessingStatus
from pipeline.processor import PhotoToLineProcessor, ProcessingParams, ProcessingResult
from config import settings

logger = logging.getLogger(__name__)


class JobService:
    """
    Service layer for job management and processing.

    Orchestrates job creation, processing, status updates, and result retrieval.
    Contains all business logic separated from API layer.
    """

    def __init__(self, repository: JobRepository, processor: PhotoToLineProcessor):
        """
        Initialize job service.

        Args:
            repository: Job repository for data access
            processor: Photo processing pipeline
        """
        self.repository = repository
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

            # Create job in repository
            job = Job(
                job_id=job_id,
                filename=file.filename,
                input_path=file_path,
                status=ProcessingStatus.PENDING,
            )

            self.repository.create(job)

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

    def get_job(self, job_id: str) -> Job:
        """
        Get job by ID.

        Args:
            job_id: Job identifier

        Returns:
            Job instance

        Raises:
            HTTPException: If job not found
        """
        job = self.repository.get_by_id(job_id)

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
        # Get job from repository
        job = self.repository.get_by_id(job_id)

        if not job:
            logger.error(f"Job {job_id} not found")
            raise HTTPException(status_code=404, detail="Job not found")

        if job.status != ProcessingStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail=f"Job already {job.status.value}",
            )

        # Update status to processing
        job.status = ProcessingStatus.PROCESSING
        self.repository.update(job)

        logger.info(f"Starting processing for job {job_id}")

        try:
            # Execute processing pipeline
            result: ProcessingResult = self.processor.process(
                image_path=job.input_path,
                params=params,
            )

            # Save result
            output_path = settings.results_dir / f"{job_id}.svg"
            output_path.write_text(result.svg_content)

            # Update job with results
            job.output_path = output_path
            job.status = ProcessingStatus.COMPLETED
            job.stats = dict(result.stats)
            job.device_used = result.device_used

            self.repository.update(job)

            logger.info(
                f"Job {job_id} completed: {job.stats.get('path_count', 0)} paths, "
                f"device={result.device_used}"
            )

        except Exception as e:
            logger.exception(f"Job {job_id} failed")

            # Update job with error
            job.status = ProcessingStatus.FAILED
            job.error = str(e)
            self.repository.update(job)

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
        if job.status == ProcessingStatus.PROCESSING:
            progress = 50
        elif job.status == ProcessingStatus.COMPLETED:
            progress = 100

        # Build result URL
        result_url = None
        if job.output_path:
            result_url = f"/api/download/{job_id}"

        return {
            "job_id": job.job_id,
            "status": job.status,
            "progress": progress,
            "result_url": result_url,
            "stats": job.stats,
            "error": job.error,
            "device_used": job.device_used,
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

        if job.status != ProcessingStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail="Job not completed",
            )

        if not job.output_path or not job.output_path.exists():
            raise HTTPException(status_code=404, detail="Result file not found")

        return job.output_path

    def delete_job(self, job_id: str) -> bool:
        """
        Delete job and associated files.

        Args:
            job_id: Job identifier

        Returns:
            True if deleted successfully
        """
        job = self.repository.get_by_id(job_id)

        if not job:
            return False

        # Clean up files
        try:
            if job.input_path and job.input_path.exists():
                job.input_path.unlink()

            if job.output_path and job.output_path.exists():
                job.output_path.unlink()

        except Exception as e:
            logger.warning(f"Failed to delete files for job {job_id}: {e}")

        # Delete from repository
        return self.repository.delete(job_id)
