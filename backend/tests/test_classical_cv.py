"""
Tests for classical computer vision line extraction.

Validates edge detection algorithms with real image processing.
"""

import cv2
import numpy as np
import pytest
from models.classical_cv import (
    BilateralCannyDetector,
    CannyEdgeDetector,
    XDoGExtractor,
    auto_canny,
)


@pytest.fixture
def test_image():
    """Create test image with simple shapes."""
    image = np.ones((100, 100, 3), dtype=np.uint8) * 255
    cv2.rectangle(image, (20, 20), (80, 80), (0, 0, 0), 2)
    cv2.circle(image, (50, 50), 15, (0, 0, 0), 2)
    return image


@pytest.fixture
def test_image_gray():
    """Create grayscale test image."""
    image = np.ones((100, 100), dtype=np.uint8) * 255
    cv2.rectangle(image, (20, 20), (80, 80), 0, 2)
    cv2.circle(image, (50, 50), 15, 0, 2)
    return image


def test_canny_edge_detector_rgb(test_image):
    """Test Canny edge detection on RGB image."""
    detector = CannyEdgeDetector()
    edges = detector.extract_lines(test_image)

    assert edges.shape == test_image.shape[:2]
    assert edges.dtype == np.uint8
    assert np.any(edges > 0)
    assert np.max(edges) == 255


def test_canny_edge_detector_gray(test_image_gray):
    """Test Canny edge detection on grayscale image."""
    detector = CannyEdgeDetector()
    edges = detector.extract_lines(test_image_gray)

    assert edges.shape == test_image_gray.shape
    assert np.any(edges > 0)


def test_canny_custom_thresholds(test_image):
    """Test Canny with custom thresholds."""
    detector = CannyEdgeDetector(low_threshold=30, high_threshold=100)
    edges = detector.extract_lines(test_image)

    assert edges.shape == test_image.shape[:2]
    assert np.any(edges > 0)


def test_bilateral_canny_detector(test_image):
    """Test bilateral filtering + Canny edge detection."""
    detector = BilateralCannyDetector()
    edges = detector.extract_lines(test_image)

    assert edges.shape == test_image.shape[:2]
    assert edges.dtype == np.uint8
    assert np.any(edges > 0)


def test_xdog_extractor(test_image):
    """Test XDoG line art extraction."""
    extractor = XDoGExtractor()
    lines = extractor.extract_lines(test_image)

    assert lines.shape == test_image.shape[:2]
    assert lines.dtype == np.uint8
    assert np.min(lines) >= 0
    assert np.max(lines) == 255


def test_auto_canny(test_image_gray):
    """Test automatic Canny threshold selection."""
    edges = auto_canny(test_image_gray)

    assert edges.shape == test_image_gray.shape
    assert edges.dtype == np.uint8
    assert np.any(edges > 0)


def test_edge_detection_produces_edges(test_image):
    """Test that edge detection produces non-empty results."""
    detector = CannyEdgeDetector()
    edges = detector.extract_lines(test_image)

    edge_pixel_count = np.sum(edges > 0)
    total_pixels = edges.shape[0] * edges.shape[1]

    assert edge_pixel_count > 0
    assert edge_pixel_count < total_pixels * 0.5


def test_deterministic_output(test_image):
    """Test that same input produces same output."""
    detector = CannyEdgeDetector(low_threshold=50, high_threshold=150)

    edges1 = detector.extract_lines(test_image.copy())
    edges2 = detector.extract_lines(test_image.copy())

    np.testing.assert_array_equal(edges1, edges2)
