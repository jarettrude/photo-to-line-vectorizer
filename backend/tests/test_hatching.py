"""Tests for hatching generation module.

Tests scanline and crosshatch generation with real image data.
"""

import numpy as np
import pytest

from app.pipeline.hatching import HatchGenerator

CANVAS_SIZE = 200
CANVAS_WIDTH_MM = 200.0
CANVAS_HEIGHT_MM = 200.0
PIXEL_WHITE = 255
PIXEL_BLACK = 0
DARK_PIXEL_VALUE = 50
VERY_DARK_PIXEL_VALUE = 10
MID_DARK_PIXEL_VALUE = 30
LIGHT_PIXEL_VALUE = 150
DEFAULT_LINE_WIDTH_MM = 0.3
THIN_LINE_WIDTH_MM = 0.1
THICK_LINE_WIDTH_MM = 0.5
DEFAULT_DENSITY_FACTOR = 2.0
SPARSE_DENSITY_FACTOR = 4.0
DARKNESS_THRESHOLD_DEFAULT = 100
MIN_WHITE_COVERAGE_RATIO = 0.01


class TestHatchGenerator:
    """Tests for HatchGenerator."""

    @pytest.fixture
    def generator(self):
        """Create hatch generator with default settings."""
        return HatchGenerator(
            line_width_mm=DEFAULT_LINE_WIDTH_MM,
            density_factor=DEFAULT_DENSITY_FACTOR,
            darkness_threshold=DARKNESS_THRESHOLD_DEFAULT,
        )

    @pytest.fixture
    def dark_region_image(self):
        """Create grayscale image with dark region."""
        img = np.ones((CANVAS_SIZE, CANVAS_SIZE), dtype=np.uint8) * PIXEL_WHITE
        img[50:150, 50:150] = MID_DARK_PIXEL_VALUE
        return img

    @pytest.fixture
    def gradient_image(self):
        """Create gradient image from white to black."""
        img = np.linspace(PIXEL_WHITE, PIXEL_BLACK, CANVAS_SIZE, dtype=np.uint8)
        return np.repeat(img.reshape(-1, 1), CANVAS_SIZE, axis=1)

    @pytest.fixture
    def empty_edges(self):
        """Create empty edge image."""
        return np.ones((CANVAS_SIZE, CANVAS_SIZE), dtype=np.uint8) * PIXEL_WHITE

    def test_generator_initialization(self, generator):
        """Test hatch generator initializes correctly."""
        assert generator is not None
        assert generator.line_width_mm == DEFAULT_LINE_WIDTH_MM
        assert generator.density_factor == DEFAULT_DENSITY_FACTOR
        assert generator.darkness_threshold == DARKNESS_THRESHOLD_DEFAULT

    def test_generate_hatches_default(self, generator, dark_region_image):
        """Test basic hatch generation."""
        hatch_image = generator.generate_hatches(
            dark_region_image,
            canvas_width_mm=CANVAS_WIDTH_MM,
            canvas_height_mm=CANVAS_HEIGHT_MM,
        )

        assert hatch_image is not None
        assert hatch_image.shape == dark_region_image.shape
        assert hatch_image.dtype == np.uint8

        # Should have some white pixels from hatching
        assert np.max(hatch_image) == PIXEL_WHITE

    def test_generate_hatches_45_degrees(self, generator, dark_region_image):
        """Test hatching at 45 degree angle."""
        hatch_image = generator.generate_hatches(
            dark_region_image,
            canvas_width_mm=CANVAS_WIDTH_MM,
            canvas_height_mm=CANVAS_HEIGHT_MM,
            angle=45,
        )

        assert hatch_image is not None
        assert np.max(hatch_image) == PIXEL_WHITE

    def test_generate_hatches_90_degrees(self, generator, dark_region_image):
        """Test vertical hatching."""
        hatch_image = generator.generate_hatches(
            dark_region_image,
            canvas_width_mm=CANVAS_WIDTH_MM,
            canvas_height_mm=CANVAS_HEIGHT_MM,
            angle=90,
        )

        assert hatch_image is not None
        assert np.max(hatch_image) == PIXEL_WHITE

    def test_generate_crosshatch(self, generator):
        """Test crosshatch generation for very dark regions."""
        # Create very dark image
        very_dark = np.ones((CANVAS_SIZE, CANVAS_SIZE), dtype=np.uint8) * PIXEL_WHITE
        very_dark[50:150, 50:150] = VERY_DARK_PIXEL_VALUE

        crosshatch = generator.generate_hatches(
            very_dark,
            canvas_width_mm=CANVAS_WIDTH_MM,
            canvas_height_mm=CANVAS_HEIGHT_MM,
        )

        assert crosshatch is not None
        assert crosshatch.shape == very_dark.shape
        # Crosshatching creates white lines on dark background
        assert np.max(crosshatch) == PIXEL_WHITE

    def test_add_hatching_to_edges(self, generator, empty_edges, dark_region_image):
        """Test adding hatching to existing edges."""
        result = generator.add_hatching_to_edges(
            empty_edges,
            dark_region_image,
            canvas_width_mm=CANVAS_WIDTH_MM,
            canvas_height_mm=CANVAS_HEIGHT_MM,
        )

        assert result is not None
        assert result.shape == empty_edges.shape

        # Should have at least as many white pixels as original edges
        assert np.sum(result == PIXEL_WHITE) >= np.sum(empty_edges == PIXEL_WHITE)

    def test_hatching_with_gradient(self, generator, gradient_image):
        """Test hatching responds to gradient darkness."""
        hatch = generator.generate_hatches(
            gradient_image,
            canvas_width_mm=CANVAS_WIDTH_MM,
            canvas_height_mm=CANVAS_HEIGHT_MM,
        )

        assert hatch is not None

        # Dark side should have more hatch lines (white pixels)
        dark_half_coverage = np.sum(hatch[150:, :] == PIXEL_WHITE)
        light_half_coverage = np.sum(hatch[:50, :] == PIXEL_WHITE)
        assert dark_half_coverage > light_half_coverage

    def test_hatching_density_factor(self):
        """Test different density factors produce different spacing."""
        sparse = HatchGenerator(
            line_width_mm=DEFAULT_LINE_WIDTH_MM,
            density_factor=SPARSE_DENSITY_FACTOR,
            darkness_threshold=DARKNESS_THRESHOLD_DEFAULT,
        )

        dense = HatchGenerator(
            line_width_mm=DEFAULT_LINE_WIDTH_MM,
            density_factor=DEFAULT_DENSITY_FACTOR,
            darkness_threshold=DARKNESS_THRESHOLD_DEFAULT,
        )

        dark_img = (
            np.ones((CANVAS_SIZE, CANVAS_SIZE), dtype=np.uint8) * DARK_PIXEL_VALUE
        )

        sparse_hatch = sparse.generate_hatches(
            dark_img,
            canvas_width_mm=CANVAS_WIDTH_MM,
            canvas_height_mm=CANVAS_HEIGHT_MM,
        )
        dense_hatch = dense.generate_hatches(
            dark_img,
            canvas_width_mm=CANVAS_WIDTH_MM,
            canvas_height_mm=CANVAS_HEIGHT_MM,
        )

        # Dense hatching should have more white pixels
        assert np.sum(dense_hatch == PIXEL_WHITE) >= np.sum(sparse_hatch == PIXEL_WHITE)

    def test_hatching_respects_threshold(self, generator):
        """Test darkness threshold filters light regions."""
        mixed_img = np.ones((CANVAS_SIZE, CANVAS_SIZE), dtype=np.uint8) * PIXEL_WHITE
        mixed_img[:100, :] = DARK_PIXEL_VALUE
        mixed_img[100:, :] = LIGHT_PIXEL_VALUE

        hatch = generator.generate_hatches(
            mixed_img,
            canvas_width_mm=CANVAS_WIDTH_MM,
            canvas_height_mm=CANVAS_HEIGHT_MM,
        )

        # Only dark region should have hatching
        dark_coverage = np.sum(hatch[:100, :] == PIXEL_WHITE)
        light_coverage = np.sum(hatch[100:, :] == PIXEL_WHITE)

        assert dark_coverage > light_coverage

    def test_hatching_with_different_line_widths(self):
        """Test that line width affects hatch spacing."""
        thin = HatchGenerator(
            line_width_mm=THIN_LINE_WIDTH_MM,
            density_factor=DEFAULT_DENSITY_FACTOR,
            darkness_threshold=DARKNESS_THRESHOLD_DEFAULT,
        )

        thick = HatchGenerator(
            line_width_mm=THICK_LINE_WIDTH_MM,
            density_factor=DEFAULT_DENSITY_FACTOR,
            darkness_threshold=DARKNESS_THRESHOLD_DEFAULT,
        )

        dark_img = (
            np.ones((CANVAS_SIZE, CANVAS_SIZE), dtype=np.uint8) * DARK_PIXEL_VALUE
        )

        thin_hatch = thin.generate_hatches(
            dark_img,
            canvas_width_mm=CANVAS_WIDTH_MM,
            canvas_height_mm=CANVAS_HEIGHT_MM,
        )
        thick_hatch = thick.generate_hatches(
            dark_img,
            canvas_width_mm=CANVAS_WIDTH_MM,
            canvas_height_mm=CANVAS_HEIGHT_MM,
        )

        # Thinner line width should allow denser hatching
        assert np.sum(thin_hatch == PIXEL_WHITE) >= np.sum(thick_hatch == PIXEL_WHITE)

    def test_empty_image_no_hatching(self, generator):
        """Test that white image produces no hatching."""
        white_img = np.ones((CANVAS_SIZE, CANVAS_SIZE), dtype=np.uint8) * PIXEL_WHITE

        hatch = generator.generate_hatches(
            white_img,
            canvas_width_mm=CANVAS_WIDTH_MM,
            canvas_height_mm=CANVAS_HEIGHT_MM,
        )

        # Should be all black (no hatching)
        assert np.all(hatch == PIXEL_BLACK)

    def test_black_image_full_hatching(self, generator):
        """Test that black image gets full hatching."""
        black_img = np.zeros((CANVAS_SIZE, CANVAS_SIZE), dtype=np.uint8)

        hatch = generator.generate_hatches(
            black_img,
            canvas_width_mm=CANVAS_WIDTH_MM,
            canvas_height_mm=CANVAS_HEIGHT_MM,
        )

        # Should have significant hatching coverage (white pixels)
        white_pixel_ratio = np.sum(hatch == PIXEL_WHITE) / hatch.size
        assert white_pixel_ratio > MIN_WHITE_COVERAGE_RATIO
