"""Unit tests for JobService service layer."""

import uuid
from unittest.mock import AsyncMock, Mock

import pytest
from api.models import ProcessingStatus
from config import settings
from fastapi import HTTPException, UploadFile
from pipeline.processor import PhotoToLineProcessor, ProcessingParams, ProcessingResult
from services.job_service import JobService
from storage import JobStorage

STATUS_BAD_REQUEST = 400
STATUS_PAYLOAD_TOO_LARGE = 413
STATUS_NOT_FOUND = 404
STATUS_INTERNAL_SERVER_ERROR = 500
JOB_PROGRESS_COMPLETE = 100
PATH_COUNT_EXAMPLE = 42


@pytest.fixture
def mock_storage():
    """Mock JobStorage."""
    storage = Mock(spec=JobStorage)
    storage.create_job = Mock()
    storage.get_job = Mock()
    storage.update_job = Mock()
    storage.set_status = Mock(return_value=True)
    storage.set_result = Mock(return_value=True)
    storage.job_exists = Mock(return_value=False)
    return storage


@pytest.fixture
def mock_processor():
    """Mock PhotoToLineProcessor."""
    processor = Mock(spec=PhotoToLineProcessor)
    processor.process = Mock(
        return_value=(
            Mock(),
            {"path_count": PATH_COUNT_EXAMPLE, "total_length_mm": 123.45},
        )
    )
    return processor


@pytest.fixture
def job_service(mock_storage, mock_processor):
    """Create JobService with mocked dependencies."""
    return JobService(storage=mock_storage, processor=mock_processor)


@pytest.mark.asyncio
async def test_create_job_from_upload_success(job_service, mock_storage, tmp_path):
    """Test successful job creation from file upload."""
    # Create mock upload file
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "test.jpg"
    mock_file.read = AsyncMock(return_value=b"fake image data")

    settings.upload_dir = tmp_path
    settings.max_upload_size_mb = 100.0

    # Call method
    _job_id, filename, file_path = await job_service.create_job_from_upload(mock_file)

    # Verify
    assert filename == "test.jpg"
    assert file_path.suffix == ".jpg"
    assert file_path.exists()
    mock_storage.create_job.assert_called_once()

    # Verify job created with correct status
    call_args = mock_storage.create_job.call_args
    assert call_args.kwargs["status"] == ProcessingStatus.PENDING
    assert call_args.kwargs["filename"] == "test.jpg"


@pytest.mark.asyncio
async def test_create_job_from_upload_unsupported_format(job_service):
    """Test upload with unsupported file format."""
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "test.txt"
    mock_file.read = AsyncMock(return_value=b"not an image")

    with pytest.raises(HTTPException) as exc_info:
        await job_service.create_job_from_upload(mock_file)

    assert exc_info.value.status_code == STATUS_BAD_REQUEST
    assert "Unsupported file format" in exc_info.value.detail


@pytest.mark.asyncio
async def test_create_job_from_upload_file_too_large(job_service):
    """Test upload with file exceeding size limit."""
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "large.jpg"
    # Create 101MB file (exceeds default 100MB limit)
    large_data = b"x" * (101 * 1024 * 1024)
    mock_file.read = AsyncMock(return_value=large_data)

    settings.max_upload_size_mb = 100.0

    with pytest.raises(HTTPException) as exc_info:
        await job_service.create_job_from_upload(mock_file)

    assert exc_info.value.status_code == STATUS_PAYLOAD_TOO_LARGE
    assert "File too large" in exc_info.value.detail


def test_get_job_success(job_service, mock_storage):
    """Test retrieving job by ID."""
    job_id = str(uuid.uuid4())
    expected_job = {
        "job_id": job_id,
        "filename": "test.jpg",
        "status": ProcessingStatus.PENDING.value,
    }
    mock_storage.get_job.return_value = expected_job

    result = job_service.get_job(job_id)

    assert result == expected_job
    mock_storage.get_job.assert_called_once_with(job_id)


def test_get_job_not_found(job_service, mock_storage):
    """Test retrieving non-existent job."""
    mock_storage.get_job.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        job_service.get_job("nonexistent-id")

    assert exc_info.value.status_code == STATUS_NOT_FOUND


def test_get_job_status(job_service, mock_storage):
    """Test getting job status with stats."""
    job_id = str(uuid.uuid4())
    mock_job = {
        "job_id": job_id,
        "filename": "test.jpg",
        "status": ProcessingStatus.COMPLETED.value,
        "progress": 100,
        "result_url": "/api/download/123",
        "stats": {"path_count": 42, "total_length_mm": 123.45},
        "error": None,
        "device_used": "cpu",
    }
    mock_storage.get_job.return_value = mock_job

    status = job_service.get_job_status(job_id)

    assert status["status"] == ProcessingStatus.COMPLETED.value
    assert status["progress"] == JOB_PROGRESS_COMPLETE
    assert status["stats"]["path_count"] == PATH_COUNT_EXAMPLE


def test_get_result_path_success(job_service, mock_storage, tmp_path):
    """Test getting result file path."""
    settings.results_dir = tmp_path

    job_id = str(uuid.uuid4())
    result_file = tmp_path / f"{job_id}.svg"
    result_file.write_text("<svg></svg>")

    mock_storage.get_job.return_value = {
        "job_id": job_id,
        "status": ProcessingStatus.COMPLETED.value,
        "output_path": str(result_file),
    }

    path = job_service.get_result_path(job_id)

    assert path == result_file
    assert path.exists()


def test_get_result_path_not_complete(job_service, mock_storage):
    """Test getting result path for incomplete job."""
    job_id = str(uuid.uuid4())
    mock_storage.get_job.return_value = {
        "job_id": job_id,
        "status": ProcessingStatus.PROCESSING.value,
    }

    with pytest.raises(HTTPException) as exc_info:
        job_service.get_result_path(job_id)

    assert exc_info.value.status_code == STATUS_BAD_REQUEST
    assert "not complete" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_process_job_success(job_service, mock_storage, mock_processor, tmp_path):
    """Test successful job processing."""
    settings.upload_dir = tmp_path
    settings.results_dir = tmp_path

    job_id = str(uuid.uuid4())
    input_file = tmp_path / f"{job_id}.jpg"
    input_file.write_bytes(b"fake image")

    mock_storage.get_job.return_value = {
        "job_id": job_id,
        "filename": "test.jpg",
        "input_path": str(input_file),
        "status": ProcessingStatus.PENDING.value,
    }

    params = ProcessingParams(
        canvas_width_mm=200.0,
        canvas_height_mm=150.0,
        line_width_mm=0.3,
    )

    # Mock successful processing - create ProcessingResult mock
    mock_result = Mock(spec=ProcessingResult)
    mock_result.svg_content = "<svg></svg>"
    mock_result.stats = {
        "path_count": 10,
        "total_length_mm": 500.0,
        "width_mm": 200.0,
        "height_mm": 150.0,
    }
    mock_result.device_used = "cpu"
    mock_processor.process.return_value = mock_result

    await job_service.process_job(job_id, params)

    # Verify status was set to PROCESSING then result was set
    assert mock_storage.set_status.called
    assert mock_storage.set_result.called

    # Verify set_result was called with correct parameters
    set_result_call = mock_storage.set_result.call_args
    assert set_result_call.kwargs["stats"] == {
        "path_count": 10,
        "total_length_mm": 500.0,
        "width_mm": 200.0,
        "height_mm": 150.0,
    }
    assert set_result_call.kwargs["device_used"] == "cpu"


@pytest.mark.asyncio
async def test_process_job_not_found(job_service, mock_storage):
    """Test processing non-existent job."""
    mock_storage.get_job.return_value = None

    params = ProcessingParams(
        canvas_width_mm=200.0, canvas_height_mm=150.0, line_width_mm=0.3
    )

    with pytest.raises(HTTPException) as exc_info:
        await job_service.process_job("nonexistent-id", params)

    assert exc_info.value.status_code == STATUS_NOT_FOUND


@pytest.mark.asyncio
async def test_process_job_handles_error(
    job_service, mock_storage, mock_processor, tmp_path
):
    """Test job processing error handling."""
    settings.upload_dir = tmp_path

    job_id = str(uuid.uuid4())
    input_file = tmp_path / f"{job_id}.jpg"
    input_file.write_bytes(b"fake image")

    mock_storage.get_job.return_value = {
        "job_id": job_id,
        "input_path": str(input_file),
        "status": ProcessingStatus.PENDING.value,
    }

    # Mock processing failure
    mock_processor.process.side_effect = RuntimeError("Processing failed")

    params = ProcessingParams(
        canvas_width_mm=200.0, canvas_height_mm=150.0, line_width_mm=0.3
    )

    # Service raises HTTPException after recording error
    with pytest.raises(HTTPException) as exc_info:
        await job_service.process_job(job_id, params)

    # Verify error response
    assert exc_info.value.status_code == STATUS_INTERNAL_SERVER_ERROR
    assert "Processing failed" in exc_info.value.detail

    # Verify error was recorded via set_status
    mock_storage.set_status.assert_called()
    # Check that FAILED status was set with error message
    status_call = mock_storage.set_status.call_args
    assert status_call.args[1] == ProcessingStatus.FAILED
    assert "Processing failed" in status_call.kwargs.get("error", "")
