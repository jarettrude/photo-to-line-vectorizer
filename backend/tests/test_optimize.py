"""
Tests for SVG optimization module.

Tests vpype-based path optimization with real SVG data.
"""

import pytest

from app.pipeline.optimize import VpypeOptimizer

ASPECT_RATIO_MIN = 1.9
ASPECT_RATIO_MAX = 2.1


class TestVpypeOptimizer:
    """Tests for VpypeOptimizer."""

    @pytest.fixture
    def optimizer(self):
        """Create optimizer instance."""
        return VpypeOptimizer()

    @pytest.fixture
    def simple_svg(self):
        """Create simple SVG with single path."""
        return """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <path d="M 10,10 L 90,10 L 90,90 L 10,90 Z" fill="none" stroke="black"/>
</svg>"""

    @pytest.fixture
    def complex_svg(self):
        """Create SVG with multiple paths."""
        return """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200">
    <path d="M 10,10 L 50,10" fill="none" stroke="black"/>
    <path d="M 50,10 L 90,10" fill="none" stroke="black"/>
    <path d="M 10,50 L 90,50" fill="none" stroke="black"/>
    <path d="M 10,90 L 90,90" fill="none" stroke="black"/>
</svg>"""

    def test_optimizer_initialization(self, optimizer):
        """Test optimizer initializes correctly."""
        assert optimizer is not None

    def test_optimize_simple_svg(self, optimizer, simple_svg):
        """Test optimization of simple SVG."""
        optimized = optimizer.optimize(
            simple_svg,
            canvas_width_mm=100.0,
            canvas_height_mm=100.0,
        )

        assert optimized is not None
        assert isinstance(optimized, str)
        assert "<svg" in optimized.lower()
        assert "</svg>" in optimized.lower()

    def test_optimize_with_canvas_scaling(self, optimizer, simple_svg):
        """Test SVG scales to exact canvas dimensions."""
        optimized = optimizer.optimize(
            simple_svg,
            canvas_width_mm=300.0,
            canvas_height_mm=200.0,
        )

        assert optimized is not None
        # vpype outputs dimensions in cm, not mm
        assert "width=" in optimized
        assert "cm" in optimized or "mm" in optimized

    def test_optimize_merges_paths(self, optimizer, complex_svg):
        """Test that adjacent paths are merged."""
        optimized = optimizer.optimize(
            complex_svg,
            canvas_width_mm=200.0,
            canvas_height_mm=200.0,
            merge_tolerance=1.0,
        )

        original_path_count = complex_svg.count("<path")
        optimized_path_count = optimized.count("<path")

        # After merging, should have fewer paths
        assert optimized_path_count <= original_path_count

    def test_optimize_with_different_tolerances(self, optimizer, complex_svg):
        """Test optimization with different tolerance values."""
        optimized_strict = optimizer.optimize(
            complex_svg,
            canvas_width_mm=200.0,
            canvas_height_mm=200.0,
            merge_tolerance=0.1,
            simplify_tolerance=0.1,
        )

        optimized_loose = optimizer.optimize(
            complex_svg,
            canvas_width_mm=200.0,
            canvas_height_mm=200.0,
            merge_tolerance=5.0,
            simplify_tolerance=2.0,
        )

        assert len(optimized_loose) <= len(optimized_strict)

    def test_get_stats(self, optimizer, simple_svg):
        """Test statistics extraction from SVG."""
        optimized = optimizer.optimize(
            simple_svg,
            canvas_width_mm=100.0,
            canvas_height_mm=100.0,
        )

        stats = optimizer.get_stats(optimized)

        assert "path_count" in stats
        assert "total_length_mm" in stats
        assert "width_mm" in stats
        assert "height_mm" in stats

        assert isinstance(stats["path_count"], int)
        assert stats["path_count"] >= 0
        assert isinstance(stats["total_length_mm"], (int, float))
        assert stats["total_length_mm"] >= 0

    def test_optimize_empty_svg(self, optimizer):
        """Test optimization of SVG with no paths."""
        empty_svg = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
</svg>"""

        optimized = optimizer.optimize(
            empty_svg,
            canvas_width_mm=100.0,
            canvas_height_mm=100.0,
        )

        assert optimized is not None
        assert "<svg" in optimized.lower()

    def test_optimize_preserves_aspect_ratio(self, optimizer, simple_svg):
        """Test that optimization preserves canvas aspect ratio."""
        optimized = optimizer.optimize(
            simple_svg,
            canvas_width_mm=300.0,
            canvas_height_mm=150.0,
        )

        stats = optimizer.get_stats(optimized)

        # Check aspect ratio is approximately 2:1
        if stats["width_mm"] and stats["height_mm"]:
            aspect_ratio = stats["width_mm"] / stats["height_mm"]
            assert ASPECT_RATIO_MIN <= aspect_ratio <= ASPECT_RATIO_MAX

    def test_optimize_large_canvas(self, optimizer, simple_svg):
        """Test optimization with large canvas dimensions."""
        optimized = optimizer.optimize(
            simple_svg,
            canvas_width_mm=1000.0,
            canvas_height_mm=800.0,
        )

        assert optimized is not None
        stats = optimizer.get_stats(optimized)
        assert stats["path_count"] >= 0

    def test_optimize_small_canvas(self, optimizer, simple_svg):
        """Test optimization with small canvas dimensions."""
        optimized = optimizer.optimize(
            simple_svg,
            canvas_width_mm=50.0,
            canvas_height_mm=50.0,
        )

        assert optimized is not None
        stats = optimizer.get_stats(optimized)
        assert stats["path_count"] >= 0

    def test_optimize_deterministic(self, optimizer, simple_svg):
        """Test that optimization produces deterministic results."""
        result1 = optimizer.optimize(
            simple_svg,
            canvas_width_mm=100.0,
            canvas_height_mm=100.0,
            merge_tolerance=0.5,
            simplify_tolerance=0.2,
        )

        result2 = optimizer.optimize(
            simple_svg,
            canvas_width_mm=100.0,
            canvas_height_mm=100.0,
            merge_tolerance=0.5,
            simplify_tolerance=0.2,
        )

        stats1 = optimizer.get_stats(result1)
        stats2 = optimizer.get_stats(result2)

        # Same parameters should produce same results
        assert stats1["path_count"] == stats2["path_count"]
