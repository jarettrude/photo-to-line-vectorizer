"""
API endpoints for photo-to-line-vectorizer.

Implements REST endpoints for upload, processing, status, and download.
"""

import logging
import re
import uuid
from pathlib import Path

from config import settings
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from pipeline.processor import PhotoToLineProcessor, ProcessingParams
from slowapi import Limiter
from slowapi.util import get_remote_address
from storage import get_job_storage

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

processor = None

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


def get_processor() -> PhotoToLineProcessor:
    """Get or create the global processor instance."""
    global processor
    if processor is None:
        processor = PhotoToLineProcessor(
            u2net_model_path=settings.u2net_model_path,
        )
    return processor


@router.post("/upload", response_model=UploadResponse)
@limiter.limit(settings.rate_limit_uploads)
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
) -> UploadResponse:
    """
    Upload an image file for processing.

    Accepts JPEG, PNG, TIFF, WebP, HEIC/HEIF formats.
    Returns a job ID for tracking the processing.

    Args:
        file: Uploaded image file

    Returns:
        UploadResponse with job_id and image URL

    Raises:
        HTTPException: If file format is unsupported or upload fails
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in {
        ".jpg",
        ".jpeg",
        ".png",
        ".tiff",
        ".tif",
        ".webp",
        ".heic",
        ".heif",
    }:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {suffix}",
        )

    job_id = str(uuid.uuid4())
    file_path = settings.upload_dir / f"{job_id}{suffix}"

    try:
        content = await file.read()

        # Check file size
        file_size_mb = len(content) / (1024 * 1024)
        if file_size_mb > settings.max_upload_size_mb:
            raise HTTPException(
                status_code=413,
                detail=f"File too large: {file_size_mb:.1f}MB (max: {settings.max_upload_size_mb}MB)",
            )

        file_path.write_bytes(content)

        # Store job in Redis/in-memory storage
        job_storage = get_job_storage()
        job_storage.create_job(
            job_id=job_id,
            filename=file.filename,
            input_path=file_path,
            status=ProcessingStatus.PENDING,
        )

        logger.info(f"Uploaded {file.filename} as job {job_id}")

        return UploadResponse(
            job_id=job_id,
            filename=file.filename,
            image_url=f"/api/uploads/{job_id}{suffix}",
        )

    except Exception as e:
        logger.exception(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="Upload failed") from None


async def process_job(job_id: str, params: ProcessingParams) -> None:
    """
    Background task to process a job.

    Args:
        job_id: Job identifier
        params: Processing parameters
    """
    job_storage = get_job_storage()
    job = job_storage.get_job(job_id)

    if not job:
        logger.error(f"Job {job_id} not found")
        return

    job_storage.set_status(job_id, ProcessingStatus.PROCESSING)

    try:
        proc = get_processor()

        result = proc.process(
            image_path=Path(job["input_path"]),
            params=params,
        )

        output_path = settings.results_dir / f"{job_id}.svg"
        output_path.write_text(result.svg_content)

        # set_result() automatically sets status to COMPLETED
        job_storage.set_result(
            job_id=job_id,
            output_path=output_path,
            stats=result.stats,
            device_used=result.device_used,
        )

        logger.info(f"Job {job_id} completed successfully")

    except Exception as e:
        logger.exception(f"Job {job_id} failed: {e}")
        job_storage.set_status(job_id, ProcessingStatus.FAILED, error=str(e))


@router.post("/process", response_model=ProcessResponse)
@limiter.limit(settings.rate_limit_processing)
async def process_image(
    request: Request,
    body: ProcessRequest,
    background_tasks: BackgroundTasks,
) -> ProcessResponse:
    """
    Start processing an uploaded image.

    Initiates background processing and returns immediately.
    Use /status endpoint to check progress.

    Args:
        request: Processing request with job_id and parameters
        background_tasks: FastAPI background tasks

    Returns:
        ProcessResponse with job status

    Raises:
        HTTPException: If job not found or parameters invalid
    """
    validate_job_id(body.job_id)

    job_storage = get_job_storage()
    job = job_storage.get_job(body.job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] != ProcessingStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Job already {job['status'].value}",
        )

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
        params = ProcessingParams(
            canvas_width_mm=300.0,
            canvas_height_mm=200.0,
            line_width_mm=0.3,
        )

    background_tasks.add_task(process_job, body.job_id, params)

    return ProcessResponse(
        job_id=body.job_id,
        status=ProcessingStatus.PROCESSING,
        message="Processing started",
    )


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """
    Get processing status for a job.

    Args:
        job_id: Job identifier

    Returns:
        JobStatusResponse with current status and results

    Raises:
        HTTPException: If job not found
    """
    validate_job_id(job_id)

    job_storage = get_job_storage()
    job = job_storage.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    progress = 0
    if job["status"] == ProcessingStatus.PROCESSING:
        progress = 50
    elif job["status"] == ProcessingStatus.COMPLETED:
        progress = 100

    result_url = None
    if job["output_path"]:
        result_url = f"/api/download/{job_id}"

    stats = None
    if job["stats"]:
        stats = JobStats(
            path_count=job["stats"]["path_count"],
            total_length_mm=job["stats"]["total_length_mm"],
            width_mm=job["stats"].get("width_mm"),
            height_mm=job["stats"].get("height_mm"),
        )

    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=progress,
        result_url=result_url,
        stats=stats,
        error=job["error"],
        device_used=job["device_used"],
    )


@router.get("/download/{job_id}")
async def download_result(job_id: str, format: str = "svg") -> FileResponse:
    """
    Download processed result in specified format.

    Args:
        job_id: Job identifier
        format: Export format (svg, hpgl, gcode)

    Returns:
        File in requested format

    Raises:
        HTTPException: If job not found or not complete
    """
    validate_job_id(job_id)

    job_storage = get_job_storage()
    job = job_storage.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] != ProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Job not completed",
        )

    output_path = Path(job["output_path"]) if job["output_path"] else None

    if not output_path or not output_path.exists():
        raise HTTPException(status_code=404, detail="Result file not found")

    format_lower = format.lower()

    # For SVG, return the stored file directly
    if format_lower == "svg":
        return FileResponse(
            output_path,
            media_type="image/svg+xml",
            filename=f"{job['filename']}.svg",
        )

    # For other formats, convert on-the-fly
    from pipeline.export import PlotterExporter

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
        exporter.export_to_format(svg_content, export_path, format=format_lower)

        media_type = {
            "hpgl": "application/octet-stream",
            "gcode": "text/plain",
            "g-code": "text/plain",
            "nc": "text/plain",
        }.get(format_lower, "application/octet-stream")

        return FileResponse(
            export_path,
            media_type=media_type,
            filename=f"{job['filename']}{export_ext}",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {e}") from None
