"""
API endpoints for photo-to-line-vectorizer.

Implements REST endpoints for upload, processing, status, and download.
"""
import asyncio
import logging
import uuid
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse

from api.models import (
    JobStatusResponse,
    ProcessingStatus,
    ProcessParams,
    ProcessRequest,
    ProcessResponse,
    UploadResponse,
    JobStats,
)
from config import settings
from pipeline.processor import PhotoToLineProcessor, ProcessingParams

logger = logging.getLogger(__name__)

router = APIRouter()

jobs: Dict[str, dict] = {}

processor = None


def get_processor() -> PhotoToLineProcessor:
    """Get or create the global processor instance."""
    global processor
    if processor is None:
        processor = PhotoToLineProcessor(
            u2net_model_path=settings.u2net_model_path,
        )
    return processor


@router.post("/upload", response_model=UploadResponse)
async def upload_image(
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
    if suffix not in {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".webp", ".heic", ".heif"}:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {suffix}",
        )

    job_id = str(uuid.uuid4())
    file_path = settings.upload_dir / f"{job_id}{suffix}"

    try:
        content = await file.read()
        file_path.write_bytes(content)

        jobs[job_id] = {
            "status": ProcessingStatus.PENDING,
            "filename": file.filename,
            "input_path": file_path,
            "output_path": None,
            "error": None,
            "stats": None,
            "device_used": None,
        }

        logger.info(f"Uploaded {file.filename} as job {job_id}")

        return UploadResponse(
            job_id=job_id,
            filename=file.filename,
            image_url=f"/api/uploads/{job_id}{suffix}",
        )

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="Upload failed")


async def process_job(job_id: str, params: ProcessingParams) -> None:
    """
    Background task to process a job.

    Args:
        job_id: Job identifier
        params: Processing parameters
    """
    if job_id not in jobs:
        logger.error(f"Job {job_id} not found")
        return

    job = jobs[job_id]
    job["status"] = ProcessingStatus.PROCESSING

    try:
        proc = get_processor()

        result = proc.process(
            image_path=job["input_path"],
            params=params,
        )

        output_path = settings.results_dir / f"{job_id}.svg"
        output_path.write_text(result.svg_content)

        job["output_path"] = output_path
        job["status"] = ProcessingStatus.COMPLETED
        job["stats"] = result.stats
        job["device_used"] = result.device_used

        logger.info(f"Job {job_id} completed successfully")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        job["status"] = ProcessingStatus.FAILED
        job["error"] = str(e)


@router.post("/process", response_model=ProcessResponse)
async def process_image(
    request: ProcessRequest,
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
    if request.job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[request.job_id]

    if job["status"] != ProcessingStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Job already {job['status'].value}",
        )

    if request.params:
        params = ProcessingParams(
            canvas_width_mm=request.params.canvas_width_mm,
            canvas_height_mm=request.params.canvas_height_mm,
            line_width_mm=request.params.line_width_mm,
            isolate_subject=request.params.isolate_subject,
            use_ml=request.params.use_ml,
            edge_threshold=request.params.edge_threshold,
            line_threshold=request.params.line_threshold,
            merge_tolerance=request.params.merge_tolerance,
            simplify_tolerance=request.params.simplify_tolerance,
            hatching_enabled=request.params.hatching_enabled,
            hatch_density=request.params.hatch_density,
            hatch_angle=request.params.hatch_angle,
            darkness_threshold=request.params.darkness_threshold,
        )
    else:
        params = ProcessingParams(
            canvas_width_mm=300.0,
            canvas_height_mm=200.0,
            line_width_mm=0.3,
        )

    background_tasks.add_task(process_job, request.job_id, params)

    return ProcessResponse(
        job_id=request.job_id,
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
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

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
async def download_result(job_id: str) -> FileResponse:
    """
    Download processed SVG result.

    Args:
        job_id: Job identifier

    Returns:
        SVG file

    Raises:
        HTTPException: If job not found or not complete
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job["status"] != ProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Job not completed",
        )

    if not job["output_path"] or not job["output_path"].exists():
        raise HTTPException(status_code=404, detail="Result file not found")

    return FileResponse(
        job["output_path"],
        media_type="image/svg+xml",
        filename=f"{job['filename']}.svg",
    )
