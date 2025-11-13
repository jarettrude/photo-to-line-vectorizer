"""
SVG path optimization using vpype.

Implements path optimization, merging, simplification, and canvas scaling
using the vpype library.
"""

import logging
import tempfile
from pathlib import Path

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

        output_path = None
        try:
            # read_svg returns (LineCollection, width, height)
            line_collection, width, height = vp.read_svg(str(tmp_path), quantization=0.1)
            doc = vp.Document(line_collection=line_collection, page_size=(width, height))

            logger.debug(f"Initial layer count: {doc.count()}")

            # Apply vpype commands
            doc = vp.linemerge(doc, tolerance=merge_tolerance)
            doc = vp.linesimplify(doc, tolerance=simplify_tolerance)
            doc = vp.linesort(doc)
            doc = vp.reloop(doc, tolerance=dedupe_tolerance)
            doc = vp.dedupe(doc, tolerance=dedupe_tolerance)

            logger.debug(f"Optimized layer count: {doc.count()}")

            # Scale to canvas dimensions
            target_width_px = vp.convert(f"{canvas_width_mm}mm")
            target_height_px = vp.convert(f"{canvas_height_mm}mm")

            doc = vp.scaleto(doc, target_width_px, target_height_px)
            doc.page_size = (target_width_px, target_height_px)

            logger.info(f"Final layer count: {doc.count()}")

            output_path = tmp_path.with_suffix(".optimized.svg")
            vp.write_svg(str(output_path), doc, color_mode="layer")

            return output_path.read_text()

        finally:
            tmp_path.unlink(missing_ok=True)
            if output_path:
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
            line_collection, width, height = vp.read_svg(str(tmp_path), quantization=0.1)
            doc = vp.Document(line_collection=line_collection, page_size=(width, height))

            # Count total paths across all layers
            path_count = sum(len(layer) for layer in doc.layers.values())
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

        output_path = None
        try:
            line_collection, width, height = vp.read_svg(str(tmp_path), quantization=0.1)
            doc = vp.Document(line_collection=line_collection, page_size=(width, height))

            target_width_px = vp.convert(f"{canvas_width_mm}mm")
            target_height_px = vp.convert(f"{canvas_height_mm}mm")

            doc = vp.scaleto(doc, target_width_px, target_height_px)
            doc.page_size = (target_width_px, target_height_px)

            output_path = tmp_path.with_suffix(".scaled.svg")
            vp.write_svg(str(output_path), doc, color_mode="layer")

            return output_path.read_text()

        finally:
            tmp_path.unlink(missing_ok=True)
            if output_path and output_path.exists():
                output_path.unlink()
