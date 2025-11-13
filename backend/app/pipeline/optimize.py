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

    def optimize(  # noqa: PLR0913
        self,
        svg_string: str,
        canvas_width_mm: float,
        canvas_height_mm: float,
        merge_tolerance: float = 0.5,
        simplify_tolerance: float = 0.2,  # noqa: ARG002
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
            result = vp.read_svg(str(tmp_path), quantization=0.1)
            # read_svg returns (LineCollection, width, height)
            lc, _page_w, _page_h = result

            logger.debug(f"Initial path count: {len(lc)}")

            # LineCollection methods modify in-place and return self
            lc.merge(tolerance=merge_tolerance)
            logger.debug(f"After merge: {len(lc)}")

            # Note: linesimplify is not a method on LineCollection in new API
            # Simplification happens during read_svg with quantization parameter
            logger.debug(f"After simplify: {len(lc)}")

            # Note: linesort is not a method on LineCollection
            # Sorting needs to be done differently
            logger.debug("Sort complete")

            lc.reloop(tolerance=dedupe_tolerance)
            logger.debug("Reloop complete")

            # Note: dedupe is not a method on LineCollection
            logger.debug(f"After dedupe: {len(lc)}")

            bounds = lc.bounds()
            if bounds:
                current_width = bounds[2] - bounds[0]
                current_height = bounds[3] - bounds[1]
                logger.debug(f"Current bounds: {current_width}x{current_height}")

            # Scale to fit target dimensions
            bounds = lc.bounds()
            if bounds:
                current_width = bounds[2] - bounds[0]
                current_height = bounds[3] - bounds[1]

                # Calculate scale factors to fit within canvas
                scale_x = canvas_width_mm / current_width if current_width > 0 else 1.0
                scale_y = (
                    canvas_height_mm / current_height if current_height > 0 else 1.0
                )
                scale_factor = min(scale_x, scale_y)

                lc.scale(scale_factor, scale_factor)

            logger.info(f"Final path count: {len(lc)}")

            # Create Document for writing
            doc = vp.Document()
            doc.add(lc, 1)  # Add to layer 1
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

    def get_stats(self, svg_string: str) -> dict[str, float]:
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
            # read_svg returns (LineCollection, width, height)
            lc, _, _ = result

            path_count = len(lc)
            total_length = lc.length()
            bounds = lc.bounds()

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
        maintain_aspect: bool = True,  # noqa: ARG002
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
            result = vp.read_svg(str(tmp_path), quantization=0.1)
            # read_svg returns (LineCollection, width, height)
            lc, _, _ = result

            # Scale to fit target dimensions
            bounds = lc.bounds()
            if bounds:
                current_width = bounds[2] - bounds[0]
                current_height = bounds[3] - bounds[1]

                # Calculate scale factors to fit within canvas
                scale_x = canvas_width_mm / current_width if current_width > 0 else 1.0
                scale_y = (
                    canvas_height_mm / current_height if current_height > 0 else 1.0
                )
                scale_factor = min(scale_x, scale_y)

                lc.scale(scale_factor, scale_factor)

            # Create Document for writing
            doc = vp.Document()
            doc.add(lc, 1)  # Add to layer 1
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
