"""
vpype-based SVG optimization provider.

Provides path optimization, merging, simplification, and canvas scaling
using the vpype library.
"""

import logging
import tempfile
from pathlib import Path
from typing import Any, ClassVar

import vpype as vp

from extensions.base import AbstractProvider

logger = logging.getLogger(__name__)


class PRV_Vpype(AbstractProvider):
    """vpype-based SVG optimization provider."""

    name: ClassVar[str] = "vpype"
    extension: ClassVar[str] = "optimize"
    description: ClassVar[str] = "vpype SVG optimization"

    @classmethod
    def is_available(cls) -> bool:
        """Check if vpype is available."""
        try:
            return True
        except ImportError:
            return False

    @classmethod
    def execute(
        cls,
        input_data: str,
        canvas_width_mm: float,
        canvas_height_mm: float,
        merge_tolerance: float = 0.5,
        simplify_tolerance: float = 0.2,
        dedupe_tolerance: float = 0.1,
        **params: Any,
    ) -> str:
        """
        Optimize SVG paths with full pipeline.

        Args:
            input_data: Input SVG string
            canvas_width_mm: Target canvas width in mm
            canvas_height_mm: Target canvas height in mm
            merge_tolerance: Line merge tolerance in mm
            simplify_tolerance: Simplification tolerance in mm
            dedupe_tolerance: Deduplication tolerance in mm
            **params: Additional provider-specific parameters

        Returns:
            Optimized SVG string
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".svg", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(input_data)

        output_path = None
        try:
            result = vp.read_svg(str(tmp_path), quantization=0.1)
            lc, _page_w, _page_h = result

            logger.debug("Initial path count: %d", len(lc))

            lc.merge(tolerance=merge_tolerance)
            logger.debug("After merge: %d", len(lc))
            lc.reloop(tolerance=dedupe_tolerance)
            logger.debug("Reloop complete")

            bounds = lc.bounds()
            if bounds:
                current_width = bounds[2] - bounds[0]
                current_height = bounds[3] - bounds[1]
                logger.debug("Current bounds: %fx%f", current_width, current_height)

                scale_x = canvas_width_mm / current_width if current_width > 0 else 1.0
                scale_y = (
                    canvas_height_mm / current_height if current_height > 0 else 1.0
                )
                scale_factor = min(scale_x, scale_y)
                lc.scale(scale_factor, scale_factor)

            logger.info("Final path count: %d", len(lc))

            doc = vp.Document()
            doc.add(lc, 1)
            doc.page_size = (canvas_width_mm, canvas_height_mm)

            output_path = tmp_path.with_suffix(".optimized.svg")
            with output_path.open("w") as f:
                vp.write_svg(
                    f,
                    doc,
                    page_size=(canvas_width_mm, canvas_height_mm),
                    color_mode="layer",
                )

            return output_path.read_text()

        finally:
            tmp_path.unlink(missing_ok=True)
            if output_path is not None:
                output_path.unlink(missing_ok=True)

    @classmethod
    def get_stats(
        cls, svg_string: str
    ) -> dict[str, float | int | tuple[float, float, float, float] | None]:
        """
        Get statistics about SVG paths.

        Args:
            svg_string: Input SVG

        Returns:
            Dictionary with path statistics
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".svg", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(svg_string)

        try:
            result = vp.read_svg(str(tmp_path), quantization=0.1)
            lc, _, _ = result

            path_count = len(lc)
            total_length = lc.length()
            bounds = lc.bounds()

            stats: dict[str, float | int | tuple[float, float, float, float] | None] = {
                "path_count": path_count,
                "total_length_mm": total_length,
                "bounds": bounds,
            }

            if bounds:
                stats["width_mm"] = bounds[2] - bounds[0]
                stats["height_mm"] = bounds[3] - bounds[1]

            return stats

        finally:
            tmp_path.unlink(missing_ok=True)

    @classmethod
    def scale_to_canvas(
        cls,
        svg_string: str,
        canvas_width_mm: float,
        canvas_height_mm: float,
        maintain_aspect: bool = True,
        **params: Any,
    ) -> str:
        """
        Scale SVG to fit canvas dimensions.

        Args:
            svg_string: Input SVG
            canvas_width_mm: Target width in mm
            canvas_height_mm: Target height in mm
            maintain_aspect: Whether to maintain aspect ratio
            **params: Additional parameters

        Returns:
            Scaled SVG string
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".svg", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(svg_string)

        output_path = None
        try:
            result = vp.read_svg(str(tmp_path), quantization=0.1)
            lc, _, _ = result

            bounds = lc.bounds()
            if bounds:
                current_width = bounds[2] - bounds[0]
                current_height = bounds[3] - bounds[1]

                scale_x = canvas_width_mm / current_width if current_width > 0 else 1.0
                scale_y = (
                    canvas_height_mm / current_height if current_height > 0 else 1.0
                )
                scale_factor = min(scale_x, scale_y)
                lc.scale(scale_factor, scale_factor)

            doc = vp.Document()
            doc.add(lc, 1)
            doc.page_size = (canvas_width_mm, canvas_height_mm)

            output_path = tmp_path.with_suffix(".scaled.svg")
            with output_path.open("w") as f:
                vp.write_svg(
                    f,
                    doc,
                    page_size=(canvas_width_mm, canvas_height_mm),
                    color_mode="layer",
                )

            return output_path.read_text()

        finally:
            tmp_path.unlink(missing_ok=True)
            if output_path is not None and output_path.exists():
                output_path.unlink()
