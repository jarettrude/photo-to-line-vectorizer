"""
Tests for hatching generation module.

Tests scanline and crosshatch generation with real image data.
"""

import numpy as np
import pytest

from app.pipeline.hatching import HatchGenerator


class TestHatchGenerator:
    """Tests for HatchGenerator."""

    @pytest.fixture
    def generator(self):
        """Create hatch generator with default settings."""
        return HatchGenerator(
            line_width_mm=0.3,
            density_factor=2.0,
            darkness_threshold=100,
        )

    @pytest.fixture
    def dark_region_image(self):
        """Create grayscale image with dark region."""
        img = np.ones((200, 200), dtype=np.uint8) * 255
        img[50:150, 50:150] = 30
        return img

    @pytest.fixture
    def gradient_image(self):
        """Create gradient image from white to black."""
        img = np.linspace(255, 0, 200, dtype=np.uint8)
        return np.repeat(img.reshape(-1, 1), 200, axis=1)

    @pytest.fixture
    def empty_edges(self):
        """Create empty edge image."""
        return np.ones((200, 200), dtype=np.uint8) * 255

    def test_generator_initialization(self, generator):
        """Test hatch generator initializes correctly."""
        assert generator is not None
        assert generator.line_width_mm == 0.3
        assert generator.density_factor == 2.0
        assert generator.darkness_threshold == 100

    def test_generate_hatches_default(self, generator, dark_region_image):
        """Test basic hatch generation."""
        hatch_image = generator.generate_hatches(
            dark_region_image,
            canvas_width_mm=200.0,
            canvas_height_mm=200.0,
        )

        assert hatch_image is not None
        assert hatch_image.shape == dark_region_image.shape
        assert hatch_image.dtype == np.uint8

        # Should have some white pixels from hatching
        assert np.max(hatch_image) == 255

    def test_generate_hatches_45_degrees(self, generator, dark_region_image):
        """Test hatching at 45 degree angle."""
        hatch_image = generator.generate_hatches(
            dark_region_image,
            canvas_width_mm=200.0,
            canvas_height_mm=200.0,
            angle=45,
        )

        assert hatch_image is not None
        assert np.max(hatch_image) == 255

    def test_generate_hatches_90_degrees(self, generator, dark_region_image):
        """Test vertical hatching."""
        hatch_image = generator.generate_hatches(
            dark_region_image,
            canvas_width_mm=200.0,
            canvas_height_mm=200.0,
            angle=90,
        )

        assert hatch_image is not None
        assert np.max(hatch_image) == 255

    def test_generate_crosshatch(self, generator):
        """Test crosshatch generation for very dark regions."""
        # Create very dark image
        very_dark = np.ones((200, 200), dtype=np.uint8) * 255
        very_dark[50:150, 50:150] = 10

        crosshatch = generator.generate_hatches(
            very_dark,
            canvas_width_mm=200.0,
            canvas_height_mm=200.0,
        )

        assert crosshatch is not None
        assert crosshatch.shape == very_dark.shape
        # Crosshatching creates white lines on dark background
        assert np.max(crosshatch) == 255

    def test_add_hatching_to_edges(self, generator, empty_edges, dark_region_image):
        """Test adding hatching to existing edges."""
        result = generator.add_hatching_to_edges(
            empty_edges,
            dark_region_image,
            canvas_width_mm=200.0,
            canvas_height_mm=200.0,
        )

        assert result is not None
        assert result.shape == empty_edges.shape

        # Should have at least as many white pixels as original edges
        assert np.sum(result == 255) >= np.sum(empty_edges == 255)

    def test_hatching_with_gradient(self, generator, gradient_image):
        """Test hatching responds to gradient darkness."""
        hatch = generator.generate_hatches(
            gradient_image,
            canvas_width_mm=200.0,
            canvas_height_mm=200.0,
        )

        assert hatch is not None

        # Dark side should have more hatch lines (white pixels)
        dark_half_coverage = np.sum(hatch[150:, :] == 255)
        light_half_coverage = np.sum(hatch[:50, :] == 255)
        assert dark_half_coverage > light_half_coverage

    def test_hatching_density_factor(self):
        """Test different density factors produce different spacing."""
        sparse = HatchGenerator(
            line_width_mm=0.3,
            density_factor=4.0,
            darkness_threshold=100,
        )

        dense = HatchGenerator(
            line_width_mm=0.3,
            density_factor=1.0,
            darkness_threshold=100,
        )

        dark_img = np.ones((200, 200), dtype=np.uint8) * 50

        sparse_hatch = sparse.generate_hatches(
            dark_img, canvas_width_mm=200.0, canvas_height_mm=200.0
        )
        dense_hatch = dense.generate_hatches(
            dark_img, canvas_width_mm=200.0, canvas_height_mm=200.0
        )

        # Dense hatching should have more white pixels
        assert np.sum(dense_hatch == 255) >= np.sum(sparse_hatch == 255)

    def test_hatching_respects_threshold(self, generator):
        """Test darkness threshold filters light regions."""
        mixed_img = np.ones((200, 200), dtype=np.uint8) * 255
        mixed_img[:100, :] = 50  # Dark
        mixed_img[100:, :] = 150  # Light (above threshold)

        hatch = generator.generate_hatches(
            mixed_img,
            canvas_width_mm=200.0,
            canvas_height_mm=200.0,
        )

        # Only dark region should have hatching
        dark_coverage = np.sum(hatch[:100, :] == 255)
        light_coverage = np.sum(hatch[100:, :] == 255)

        assert dark_coverage > light_coverage

    def test_hatching_with_different_line_widths(self):
        """Test that line width affects hatch spacing."""
        thin = HatchGenerator(
            line_width_mm=0.1,
            density_factor=2.0,
            darkness_threshold=100,
        )

        thick = HatchGenerator(
            line_width_mm=0.5,
            density_factor=2.0,
            darkness_threshold=100,
        )

        dark_img = np.ones((200, 200), dtype=np.uint8) * 50

        thin_hatch = thin.generate_hatches(
            dark_img, canvas_width_mm=200.0, canvas_height_mm=200.0
        )
        thick_hatch = thick.generate_hatches(
            dark_img, canvas_width_mm=200.0, canvas_height_mm=200.0
        )

        # Thinner line width should allow denser hatching
        assert np.sum(thin_hatch == 255) >= np.sum(thick_hatch == 255)

    def test_empty_image_no_hatching(self, generator):
        """Test that white image produces no hatching."""
        white_img = np.ones((200, 200), dtype=np.uint8) * 255

        hatch = generator.generate_hatches(
            white_img,
            canvas_width_mm=200.0,
            canvas_height_mm=200.0,
        )

        # Should be all black (no hatching)
        assert np.all(hatch == 0)

    def test_black_image_full_hatching(self, generator):
        """Test that black image gets full hatching."""
        black_img = np.zeros((200, 200), dtype=np.uint8)

        hatch = generator.generate_hatches(
            black_img,
            canvas_width_mm=200.0,
            canvas_height_mm=200.0,
        )

        # Should have significant hatching coverage (white pixels)
        white_pixel_ratio = np.sum(hatch == 255) / hatch.size
        assert white_pixel_ratio > 0.01  # At least 1% coverage
