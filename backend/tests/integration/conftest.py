"""
Shared fixtures for integration tests.

Provides real test images and test client setup.
"""

import os
import socket
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from main import app
from storage import init_job_storage

DEFAULT_REDIS_URL = "redis://localhost:6379/0"


def _redis_port_open(url: str) -> bool:
    host = "localhost"
    port = 6379

    if url.startswith("redis://"):
        remainder = url[len("redis://") :]
        if "/" in remainder:
            host_port, _db = remainder.split("/", 1)
        else:
            host_port = remainder
        if ":" in host_port:
            host, port_str = host_port.split(":", 1)
            try:
                port = int(port_str)
            except ValueError:
                port = 6379
        elif host_port:
            host = host_port

    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


@pytest.fixture(scope="session", autouse=True)
def setup_test_storage():
    """Initialize job storage for integration tests."""
    redis_url = os.getenv("REDIS_URL", DEFAULT_REDIS_URL)
    if _redis_port_open(redis_url):
        init_job_storage(redis_url=redis_url)
    else:
        init_job_storage(redis_url=None)


@pytest.fixture(scope="session")
def require_redis():
    redis_url = os.getenv("REDIS_URL", DEFAULT_REDIS_URL)
    if not _redis_port_open(redis_url):
        pytest.skip(f"Redis not available at {redis_url}")


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
