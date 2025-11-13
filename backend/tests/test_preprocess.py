"""
Tests for image preprocessing pipeline.

Validates image loading, format support, and preprocessing operations.
"""

import pytest
import numpy as np
import tempfile
from pathlib import Path
from PIL import Image

from pipeline.preprocess import ImagePreprocessor


@pytest.fixture
def test_image_path():
    """Create temporary test image file."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        img = Image.new("RGB", (800, 600), color=(255, 128, 64))
        img.save(tmp.name, "JPEG")
        path = Path(tmp.name)

    yield path

    path.unlink(missing_ok=True)


@pytest.fixture
def test_png_image_path():
    """Create temporary PNG test image."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        img = Image.new("RGB", (800, 600), color=(100, 150, 200))
        img.save(tmp.name, "PNG")
        path = Path(tmp.name)

    yield path

    path.unlink(missing_ok=True)


def test_load_image_jpeg(test_image_path):
    """Test loading JPEG image."""
    preprocessor = ImagePreprocessor()
    image = preprocessor.load_image(test_image_path)

    assert image.shape == (600, 800, 3)
    assert image.dtype == np.uint8


def test_load_image_png(test_png_image_path):
    """Test loading PNG image."""
    preprocessor = ImagePreprocessor()
    image = preprocessor.load_image(test_png_image_path)

    assert image.shape == (600, 800, 3)
    assert image.dtype == np.uint8


def test_load_image_not_found():
    """Test loading non-existent image raises error."""
    preprocessor = ImagePreprocessor()

    with pytest.raises(FileNotFoundError):
        preprocessor.load_image(Path("/nonexistent/image.jpg"))


def test_load_image_unsupported_format():
    """Test loading unsupported format raises error."""
    preprocessor = ImagePreprocessor()

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp.write(b"not an image")
        path = Path(tmp.name)

    try:
        with pytest.raises(ValueError):
            preprocessor.load_image(path)
    finally:
        path.unlink(missing_ok=True)


def test_resize_if_needed_no_resize():
    """Test that small images are not resized."""
    preprocessor = ImagePreprocessor()
    image = np.random.randint(0, 255, (500, 500, 3), dtype=np.uint8)

    resized = preprocessor.resize_if_needed(image, max_dimension=1000)

    assert resized.shape == image.shape


def test_resize_if_needed_width_exceeded():
    """Test resizing when width exceeds maximum."""
    preprocessor = ImagePreprocessor()
    image = np.random.randint(0, 255, (500, 2000, 3), dtype=np.uint8)

    resized = preprocessor.resize_if_needed(image, max_dimension=1000)

    assert resized.shape[1] == 1000
    assert resized.shape[0] == 250
    assert resized.shape[2] == 3


def test_resize_if_needed_height_exceeded():
    """Test resizing when height exceeds maximum."""
    preprocessor = ImagePreprocessor()
    image = np.random.randint(0, 255, (2000, 500, 3), dtype=np.uint8)

    resized = preprocessor.resize_if_needed(image, max_dimension=1000)

    assert resized.shape[0] == 1000
    assert resized.shape[1] == 250
    assert resized.shape[2] == 3


def test_normalize_contrast():
    """Test contrast normalization with CLAHE."""
    preprocessor = ImagePreprocessor()
    image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

    enhanced = preprocessor.normalize_contrast(image)

    assert enhanced.shape == image.shape
    assert enhanced.dtype == np.uint8


def test_preprocess_complete_pipeline(test_image_path):
    """Test complete preprocessing pipeline."""
    preprocessor = ImagePreprocessor()

    result = preprocessor.preprocess(
        test_image_path,
        isolate_subject=False,
        max_dimension=1000,
        enhance_contrast=True,
    )

    assert result.shape[2] == 3
    assert result.dtype == np.uint8
    assert result.shape[0] == 600
    assert result.shape[1] == 800
