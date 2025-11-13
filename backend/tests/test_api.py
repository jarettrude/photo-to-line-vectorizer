"""
Tests for FastAPI endpoints.

Validates API functionality with real HTTP requests.
"""

import io

import pytest
from fastapi.testclient import TestClient
from main import app
from PIL import Image


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def test_image_bytes():
    """Create test image as bytes."""
    img = Image.new("RGB", (800, 600), color=(255, 128, 64))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.getvalue()


def test_root_endpoint(client):
    """Test root endpoint returns API information."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "endpoints" in data


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_upload_endpoint(client, test_image_bytes):
    """Test image upload endpoint."""
    response = client.post(
        "/api/upload",
        files={"file": ("test.jpg", test_image_bytes, "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert "filename" in data
    assert "image_url" in data
    assert data["filename"] == "test.jpg"


def test_upload_invalid_format(client):
    """Test upload with invalid file format."""
    response = client.post(
        "/api/upload",
        files={"file": ("test.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 400


def test_status_endpoint_not_found(client):
    """Test status endpoint with non-existent job."""
    response = client.get("/api/status/nonexistent-job-id")

    assert response.status_code == 404


def test_upload_and_status(client, test_image_bytes):
    """Test upload followed by status check."""
    upload_response = client.post(
        "/api/upload",
        files={"file": ("test.jpg", test_image_bytes, "image/jpeg")},
    )

    assert upload_response.status_code == 200
    job_id = upload_response.json()["job_id"]

    status_response = client.get(f"/api/status/{job_id}")

    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["job_id"] == job_id
    assert status_data["status"] in ["pending", "processing", "completed", "failed"]


def test_process_endpoint_not_found(client):
    """Test process endpoint with non-existent job."""
    response = client.post(
        "/api/process",
        json={
            "job_id": "nonexistent-job-id",
            "mode": "auto",
        },
    )

    assert response.status_code == 404


def test_download_endpoint_not_found(client):
    """Test download endpoint with non-existent job."""
    response = client.get("/api/download/nonexistent-job-id")

    assert response.status_code == 404
