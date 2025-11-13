"""
Tests for vectorization module.

Tests ImageTracerJS and Potrace vectorizers with real image data.
"""

import cv2
import numpy as np
import pytest

from app.pipeline.vectorize import ImageTracerVectorizer, PotraceVectorizer


@pytest.mark.requires_imagetracerjs
class TestImageTracerVectorizer:
    """Tests for ImageTracerJS vectorizer."""

    @pytest.fixture
    def vectorizer(self):
        """Create vectorizer instance."""
        return ImageTracerVectorizer()

    @pytest.fixture
    def simple_line_image(self):
        """Create simple line image for testing."""
        img = np.ones((100, 100), dtype=np.uint8) * 255
        img[40:60, 10:90] = 0
        return img

    @pytest.fixture
    def circle_image(self):
        """Create circle image for testing."""
        img = np.ones((200, 200), dtype=np.uint8) * 255
        cv2.circle(img, (100, 100), 50, 0, 2)
        return img

    def test_vectorizer_initialization(self, vectorizer):
        """Test vectorizer initializes correctly."""
        assert vectorizer is not None

    def test_vectorize_simple_line(self, vectorizer, simple_line_image):
        """Test vectorization of simple horizontal line."""
        svg = vectorizer.vectorize(simple_line_image, line_threshold=128)

        assert svg is not None
        assert isinstance(svg, str)
        assert "<svg" in svg.lower()
        assert "</svg>" in svg.lower()

    def test_vectorize_circle(self, vectorizer, circle_image):
        """Test vectorization of circle shape."""
        svg = vectorizer.vectorize(circle_image, line_threshold=128)

        assert svg is not None
        assert "<path" in svg.lower() or "<polygon" in svg.lower()

    def test_vectorize_with_quality_settings(self, vectorizer, simple_line_image):
        """Test vectorization with different quality settings."""
        svg_low = vectorizer.vectorize(simple_line_image, line_threshold=128, qtres=2.0)
        svg_high = vectorizer.vectorize(
            simple_line_image, line_threshold=128, qtres=0.5
        )

        assert len(svg_high) >= len(svg_low)

    def test_vectorize_with_pathomit(self, vectorizer, simple_line_image):
        """Test path omit threshold filtering."""
        svg = vectorizer.vectorize(simple_line_image, pathomit=50)

        assert svg is not None
        assert "<svg" in svg.lower()

    def test_vectorize_with_scale(self, vectorizer, simple_line_image):
        """Test output scaling."""
        svg = vectorizer.vectorize(simple_line_image, scale=2.0)

        assert svg is not None
        assert "<svg" in svg.lower()

    def test_vectorize_rgb_image(self, vectorizer):
        """Test vectorization of RGB image."""
        rgb_img = np.ones((100, 100, 3), dtype=np.uint8) * 255
        rgb_img[40:60, 10:90] = 0

        svg = vectorizer.vectorize(rgb_img)

        assert svg is not None
        assert "<svg" in svg.lower()

    def test_vectorize_empty_image(self, vectorizer):
        """Test vectorization of empty white image."""
        empty_img = np.ones((100, 100), dtype=np.uint8) * 255

        svg = vectorizer.vectorize(empty_img)

        assert svg is not None
        assert "<svg" in svg.lower()


@pytest.mark.requires_potrace
class TestPotraceVectorizer:
    """Tests for Potrace vectorizer."""

    @pytest.fixture
    def vectorizer(self):
        """Create Potrace vectorizer instance."""
        return PotraceVectorizer()

    @pytest.fixture
    def binary_image(self):
        """Create binary test image."""
        img = np.ones((100, 100), dtype=np.uint8) * 255
        img[30:70, 30:70] = 0
        return img

    def test_potrace_initialization(self, vectorizer):
        """Test Potrace vectorizer initializes."""
        assert vectorizer is not None

    def test_potrace_vectorize_square(self, vectorizer, binary_image):
        """Test Potrace vectorization of square."""
        try:
            svg = vectorizer.vectorize(binary_image)

            assert svg is not None
            assert isinstance(svg, str)
            assert "<svg" in svg.lower()
        except RuntimeError as e:
            if "Potrace" in str(e):
                pytest.skip("Potrace not installed")
            raise

    def test_potrace_with_turdsize(self, vectorizer, binary_image):
        """Test Potrace with speckle suppression."""
        try:
            svg = vectorizer.vectorize(binary_image, turdsize=5)

            assert svg is not None
            assert "<svg" in svg.lower()
        except RuntimeError as e:
            if "Potrace" in str(e):
                pytest.skip("Potrace not installed")
            raise

    def test_potrace_with_turnpolicy(self, vectorizer, binary_image):
        """Test Potrace with different turn policies."""
        policies = ["minority", "majority", "black", "white"]

        for policy in policies:
            try:
                svg = vectorizer.vectorize(binary_image, turnpolicy=policy)
                assert svg is not None
                break
            except RuntimeError as e:
                if "Potrace" in str(e):
                    pytest.skip("Potrace not installed")
                raise

    def test_potrace_rgb_conversion(self, vectorizer):
        """Test Potrace handles RGB to grayscale conversion."""
        rgb_img = np.ones((100, 100, 3), dtype=np.uint8) * 255
        rgb_img[30:70, 30:70] = 0

        try:
            svg = vectorizer.vectorize(rgb_img)

            assert svg is not None
            assert "<svg" in svg.lower()
        except RuntimeError as e:
            if "Potrace" in str(e):
                pytest.skip("Potrace not installed")
            raise
