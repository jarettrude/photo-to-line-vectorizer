"""
Shared fixtures for integration tests.

Provides real test images and test client setup.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from main import app
from storage import init_job_storage


@pytest.fixture(scope="session", autouse=True)
def setup_test_storage():
    """Initialize in-memory job storage for integration tests."""
    init_job_storage(redis_url=None)


@pytest.fixture(scope="session")
def test_images_dir():
    """Path to real test images directory."""
    repo_root = Path(__file__).parent.parent.parent.parent
    return repo_root / "test-images"


@pytest.fixture(scope="session")
def heic_image_path(test_images_dir):
    """Path to HEIC test image."""
    path = test_images_dir / "IMG_9195.HEIC"
    if not path.exists():
        pytest.skip(f"HEIC test image not found at {path}")
    return path


@pytest.fixture(scope="session")
def jpeg_image_path(test_images_dir):
    """Path to JPEG test image."""
    path = test_images_dir / "IMG_9393.jpeg"
    if not path.exists():
        pytest.skip(f"JPEG test image not found at {path}")
    return path


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)
