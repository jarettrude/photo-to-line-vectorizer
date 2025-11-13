"""
SVG path optimization using vpype.

Implements path optimization, merging, simplification, and canvas scaling
using the vpype library.
"""

import logging
import tempfile
from pathlib import Path
from typing import Optional, Tuple

import vpype as vp

logger = logging.getLogger(__name__)


class VpypeOptimizer:
    """
    SVG optimization using vpype library.

    Provides path merging, simplification, sorting, deduplication,
    and canvas sizing operations.
    """

    def optimize(
        self,
        svg_string: str,
        canvas_width_mm: float,
        canvas_height_mm: float,
        merge_tolerance: float = 0.5,
        simplify_tolerance: float = 0.2,
        dedupe_tolerance: float = 0.1,
    ) -> str:
        """
        Optimize SVG paths with full pipeline.

        Args:
            svg_string: Input SVG
            canvas_width_mm: Target canvas width in mm
            canvas_height_mm: Target canvas height in mm
            merge_tolerance: Line merge tolerance in mm
            simplify_tolerance: Simplification tolerance in mm
            dedupe_tolerance: Deduplication tolerance in mm

        Returns:
            Optimized SVG string
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".svg", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(svg_string)

        try:
            doc = vp.read_svg(str(tmp_path), quantization=0.1)

            logger.debug(f"Initial path count: {doc.count()}")

            doc = vp.linemerge(doc, tolerance=merge_tolerance)
            logger.debug(f"After linemerge: {doc.count()}")

            doc = vp.linesimplify(doc, tolerance=simplify_tolerance)
            logger.debug(f"After linesimplify: {doc.count()}")

            doc = vp.linesort(doc, no_flip=False)
            logger.debug("Linesort complete")

            doc = vp.reloop(doc, tolerance=dedupe_tolerance)
            logger.debug("Reloop complete")

            doc = vp.dedupe(doc, tolerance=dedupe_tolerance)
            logger.debug(f"After dedupe: {doc.count()}")

            bounds = doc.bounds()
            if bounds is not None:
                current_width = bounds[2] - bounds[0]
                current_height = bounds[3] - bounds[1]
                logger.debug(f"Current bounds: {current_width}x{current_height}")

            target_width = vp.convert_length(f"{canvas_width_mm}mm")
            target_height = vp.convert_length(f"{canvas_height_mm}mm")

            doc = vp.scaleto(
                doc,
                target_width,
                target_height,
            )

            doc = vp.pagesize(
                doc,
                f"{canvas_width_mm}mm",
                f"{canvas_height_mm}mm",
            )

            logger.info(f"Final path count: {doc.count()}")

            output_path = tmp_path.with_suffix(".optimized.svg")
            vp.write_svg(str(output_path), doc, color_mode="layer")

            return output_path.read_text()

        finally:
            tmp_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)

    def get_stats(self, svg_string: str) -> dict:
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
            doc = vp.read_svg(str(tmp_path), quantization=0.1)

            path_count = doc.count()
            total_length = doc.length()
            bounds = doc.bounds()

            stats = {
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

    def scale_to_canvas(
        self,
        svg_string: str,
        canvas_width_mm: float,
        canvas_height_mm: float,
        maintain_aspect: bool = True,
    ) -> str:
        """
        Scale SVG to fit canvas dimensions.

        Args:
            svg_string: Input SVG
            canvas_width_mm: Target width in mm
            canvas_height_mm: Target height in mm
            maintain_aspect: Whether to maintain aspect ratio

        Returns:
            Scaled SVG string
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".svg", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(svg_string)

        try:
            doc = vp.read_svg(str(tmp_path), quantization=0.1)

            target_width = vp.convert_length(f"{canvas_width_mm}mm")
            target_height = vp.convert_length(f"{canvas_height_mm}mm")

            doc = vp.scaleto(doc, target_width, target_height)

            doc = vp.pagesize(
                doc,
                f"{canvas_width_mm}mm",
                f"{canvas_height_mm}mm",
            )

            output_path = tmp_path.with_suffix(".scaled.svg")
            vp.write_svg(str(output_path), doc, color_mode="layer")

            return output_path.read_text()

        finally:
            tmp_path.unlink(missing_ok=True)
            if output_path.exists():
                output_path.unlink()
