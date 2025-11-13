"""
API endpoints for photo-to-line-vectorizer.

Clean architecture: endpoints only handle HTTP concerns,
business logic is delegated to service layer.
"""

import logging
import re
from pathlib import Path

from config import settings
from dependencies import get_job_service
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from pipeline.export import PlotterExporter
from services.job_service import JobService
from slowapi import Limiter
from slowapi.util import get_remote_address

from api.models import (
    JobStats,
    JobStatusResponse,
    ProcessingStatus,
    ProcessRequest,
    ProcessResponse,
    UploadResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# UUID validation pattern
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)


def validate_job_id(job_id: str) -> None:
    """
    Validate job ID format.

    Args:
        job_id: Job identifier to validate

    Raises:
        HTTPException: If job_id is not a valid UUID
    """
    if not UUID_PATTERN.match(job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID format")


@router.post("/upload", response_model=UploadResponse)
@limiter.limit(settings.rate_limit_uploads)
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    job_service: JobService = Depends(get_job_service),
) -> UploadResponse:
    """
    Upload an image file for processing.

    Accepts JPEG, PNG, TIFF, WebP, HEIC/HEIF formats.
    Returns a job ID for tracking the processing.

    Args:
        request: FastAPI request (for rate limiting)
        file: Uploaded image file
        job_service: Injected job service

    Returns:
        UploadResponse with job_id and image URL

    Raises:
        HTTPException: If file format is unsupported or upload fails
    """
    job_id, filename, file_path = await job_service.create_job_from_upload(file)

    suffix = file_path.suffix
    return UploadResponse(
        job_id=job_id,
        filename=filename,
        image_url=f"/api/uploads/{job_id}{suffix}",
    )


async def process_job_background(
    job_id: str,
    body: ProcessRequest,
    job_service: JobService,
) -> None:
    """
    Background task to process a job.

    Args:
        job_id: Job identifier
        body: Processing request with parameters
        job_service: Job service instance
    """
    # Extract params from body
    from pipeline.processor import ProcessingParams

    if body.params:
        params = ProcessingParams(
            canvas_width_mm=body.params.canvas_width_mm,
            canvas_height_mm=body.params.canvas_height_mm,
            line_width_mm=body.params.line_width_mm,
            isolate_subject=body.params.isolate_subject,
            use_ml=body.params.use_ml,
            edge_threshold=body.params.edge_threshold,
            line_threshold=body.params.line_threshold,
            merge_tolerance=body.params.merge_tolerance,
            simplify_tolerance=body.params.simplify_tolerance,
            hatching_enabled=body.params.hatching_enabled,
            hatch_density=body.params.hatch_density,
            hatch_angle=body.params.hatch_angle,
            darkness_threshold=body.params.darkness_threshold,
        )
    else:
        # Default parameters
        params = ProcessingParams(
            canvas_width_mm=300.0,
            canvas_height_mm=200.0,
            line_width_mm=0.3,
        )

    try:
        await job_service.process_job(job_id, params)
    except HTTPException:
        # Already handled by service layer
        pass
    except Exception as e:
        logger.exception(f"Background processing failed for job {job_id}")


@router.post("/process", response_model=ProcessResponse)
@limiter.limit(settings.rate_limit_processing)
async def process_image(
    request: Request,
    body: ProcessRequest,
    background_tasks: BackgroundTasks,
    job_service: JobService = Depends(get_job_service),
) -> ProcessResponse:
    """
    Start processing an uploaded image.

    Initiates background processing and returns immediately.
    Use /status endpoint to check progress.

    Args:
        request: FastAPI request (for rate limiting)
        body: Processing request with job_id and parameters
        background_tasks: FastAPI background tasks
        job_service: Injected job service

    Returns:
        ProcessResponse with job status

    Raises:
        HTTPException: If job not found or parameters invalid
    """
    validate_job_id(body.job_id)

    # Verify job exists and is in correct state
    job = job_service.get_job(body.job_id)

    if job.status != ProcessingStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Job already {job.status.value}",
        )

    # Add background task
    background_tasks.add_task(process_job_background, body.job_id, body, job_service)

    return ProcessResponse(
        job_id=body.job_id,
        status=ProcessingStatus.PROCESSING,
        message="Processing started",
    )


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    job_service: JobService = Depends(get_job_service),
) -> JobStatusResponse:
    """
    Get processing status for a job.

    Args:
        job_id: Job identifier
        job_service: Injected job service

    Returns:
        JobStatusResponse with current status and results

    Raises:
        HTTPException: If job not found
    """
    validate_job_id(job_id)

    status_data = job_service.get_job_status(job_id)

    # Convert stats to JobStats model if present
    stats = None
    if status_data.get("stats"):
        stats = JobStats(
            path_count=status_data["stats"]["path_count"],
            total_length_mm=status_data["stats"]["total_length_mm"],
            width_mm=status_data["stats"].get("width_mm"),
            height_mm=status_data["stats"].get("height_mm"),
        )

    return JobStatusResponse(
        job_id=status_data["job_id"],
        status=status_data["status"],
        progress=status_data["progress"],
        result_url=status_data["result_url"],
        stats=stats,
        error=status_data["error"],
        device_used=status_data["device_used"],
    )


@router.get("/download/{job_id}")
async def download_result(
    job_id: str,
    export_format: str = "svg",
    job_service: JobService = Depends(get_job_service),
) -> FileResponse:
    """
    Download processed result in specified format.

    Args:
        job_id: Job identifier
        export_format: Export format (svg, hpgl, gcode)
        job_service: Injected job service

    Returns:
        File in requested format

    Raises:
        HTTPException: If job not found or not complete
    """
    validate_job_id(job_id)

    job = job_service.get_job(job_id)
    output_path = job_service.get_result_path(job_id)

    format_lower = export_format.lower()

    # For SVG, return the stored file directly
    if format_lower == "svg":
        return FileResponse(
            output_path,
            media_type="image/svg+xml",
            filename=f"{job.filename}.svg",
        )

    # For other formats, convert on-the-fly
    exporter = PlotterExporter()
    svg_content = output_path.read_text()

    # Create export file path
    export_ext = {
        "hpgl": ".hpgl",
        "gcode": ".gcode",
        "g-code": ".gcode",
        "nc": ".nc",
    }.get(format_lower, f".{format_lower}")

    export_path = settings.results_dir / f"{job_id}{export_ext}"

    try:
        exporter.export_to_format(svg_content, export_path, export_format=format_lower)

        media_type = {
            "hpgl": "application/octet-stream",
            "gcode": "text/plain",
            "g-code": "text/plain",
            "nc": "text/plain",
        }.get(format_lower, "application/octet-stream")

        return FileResponse(
            export_path,
            media_type=media_type,
            filename=f"{job.filename}{export_ext}",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {e}") from e
