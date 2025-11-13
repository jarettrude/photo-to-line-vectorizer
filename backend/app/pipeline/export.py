"""
Export module for various plotter formats.

Supports SVG, HPGL, and G-code export using vpype.
"""

import logging
import tempfile
from pathlib import Path

import vpype as vp

logger = logging.getLogger(__name__)


class PlotterExporter:
    """
    Multi-format exporter for plotter files.

    Converts optimized SVG to SVG, HPGL, or G-code formats
    using vpype and vpype-gcode.
    """

    def export_svg(
        self,
        svg_string: str,
        output_path: Path,
        layer_mode: str = "layer",
    ) -> None:
        """
        Export to SVG format.

        Args:
            svg_string: Input SVG string
            output_path: Output file path
            layer_mode: Color mode (layer, device, or default)
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".svg", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(svg_string)

        try:
            result = vp.read_svg(str(tmp_path), quantization=0.1)
            # read_svg returns (LineCollection, width, height)
            lc, page_w, page_h = result

            # Create Document for writing
            doc = vp.Document()
            doc.add(lc, 1)  # Add to layer 1
            doc.page_size = (page_w, page_h)

            with output_path.open("w") as f:
                vp.write_svg(f, doc, color_mode=layer_mode)
            logger.info(f"Exported SVG to {output_path}")

        finally:
            tmp_path.unlink(missing_ok=True)

    def export_hpgl(
        self,
        svg_string: str,
        output_path: Path,
        device: str = "",
        velocity: int | None = None,
        force: int | None = None,
    ) -> None:
        """
        Export to HPGL format for pen plotters.

        Args:
            svg_string: Input SVG string
            output_path: Output file path
            device: HPGL device type (hp7475a, hp7576a, etc.)
            velocity: Pen velocity (device-specific units)
            force: Pen force (device-specific units)

        Raises:
            RuntimeError: If HPGL export fails
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".svg", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(svg_string)

        try:
            result = vp.read_svg(str(tmp_path), quantization=0.1)
            # read_svg returns (LineCollection, width, height)
            lc, _, _ = result

            # Build HPGL command
            hpgl_content = []

            # Initialize plotter
            hpgl_content.append("IN;")  # Initialize
            hpgl_content.append("SC;")  # Set scaling

            if velocity is not None:
                hpgl_content.append(f"VS{velocity};")
            if force is not None:
                hpgl_content.append(f"FS{force};")

            # Select pen
            hpgl_content.append("SP1;")  # Select pen 1

            # Export paths - LineCollection is iterable of lines
            for line in lc:
                if len(line) == 0:
                    continue

                # Move to first point (pen up)
                x, y = line[0].real, line[0].imag
                hpgl_content.append(f"PU{int(x)},{int(y)};")

                # Draw subsequent points (pen down)
                if len(line) > 1:
                    points = ",".join(f"{int(p.real)},{int(p.imag)}" for p in line[1:])
                    hpgl_content.append(f"PD{points};")

            # End plotter commands
            hpgl_content.append("PU;")  # Pen up
            hpgl_content.append("SP0;")  # Park pen

            output_path.write_text("\n".join(hpgl_content))
            logger.info(f"Exported HPGL to {output_path}")

        except Exception as e:
            error_msg = f"HPGL export failed: {e}"
            raise RuntimeError(error_msg) from e
        finally:
            tmp_path.unlink(missing_ok=True)

    def export_gcode(
        self,
        svg_string: str,
        output_path: Path,
        profile: str = "gcode",
        feed_rate: int = 1000,
        z_up: float = 5.0,
        z_down: float = 0.0,
    ) -> None:
        """
        Export to G-code format for CNC/laser cutters.

        Args:
            svg_string: Input SVG string
            output_path: Output file path
            profile: G-code profile (gcode, gcode_relative, etc.)
            feed_rate: Feed rate in mm/min
            z_up: Z-axis position when pen is up (mm)
            z_down: Z-axis position when pen is down (mm)

        Raises:
            RuntimeError: If G-code export fails
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".svg", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(svg_string)

        try:
            # Use vpype-gcode plugin
            from vpype_gcode import (
                gwrite,  # type: ignore[import-untyped]
            )

            result = vp.read_svg(str(tmp_path), quantization=0.1)
            # read_svg returns (LineCollection, width, height)
            lc, _, _ = result

            # Generate G-code
            gcode_lines = []

            # Header
            gcode_lines.extend(
                [
                    "G21 ; Set units to millimeters",
                    "G90 ; Absolute positioning",
                    f"G0 Z{z_up} ; Pen up",
                    "G0 X0 Y0 ; Home position",
                    f"F{feed_rate} ; Set feed rate",
                    "",
                ]
            )

            # Export paths - LineCollection is iterable of lines
            for line in lc:
                if len(line) == 0:
                    continue

                # Move to first point with pen up
                x0, y0 = line[0].real, line[0].imag
                gcode_lines.append(f"G0 Z{z_up}")
                gcode_lines.append(f"G0 X{x0:.3f} Y{y0:.3f}")
                gcode_lines.append(f"G1 Z{z_down}")

                # Draw subsequent points with pen down
                for point in line[1:]:
                    x, y = point.real, point.imag
                    gcode_lines.append(f"G1 X{x:.3f} Y{y:.3f}")

            # Footer
            gcode_lines.extend(
                [
                    "",
                    f"G0 Z{z_up} ; Pen up",
                    "G0 X0 Y0 ; Return to home",
                    "M2 ; End program",
                ]
            )

            output_path.write_text("\n".join(gcode_lines))
            logger.info(f"Exported G-code to {output_path}")

        except ImportError as e:
            logger.exception("vpype-gcode plugin not available")
            error_msg = "vpype-gcode plugin required for G-code export"
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"G-code export failed: {e}"
            raise RuntimeError(error_msg) from e
        finally:
            tmp_path.unlink(missing_ok=True)

    def export_to_format(
        self,
        svg_string: str,
        output_path: Path,
        export_format: str = "svg",
        **kwargs: object,
    ) -> None:
        """
        Export to specified format.

        Args:
            svg_string: Input SVG string
            output_path: Output file path
            export_format: Export format (svg, hpgl, gcode)
            **kwargs: Format-specific parameters

        Raises:
            ValueError: If format is unsupported
        """
        format_lower = export_format.lower()

        if format_lower == "svg":
            self.export_svg(svg_string, output_path, **kwargs)  # type: ignore[arg-type]
        elif format_lower == "hpgl":
            self.export_hpgl(svg_string, output_path, **kwargs)  # type: ignore[arg-type]
        elif format_lower in ("gcode", "g-code", "nc"):
            self.export_gcode(svg_string, output_path, **kwargs)  # type: ignore[arg-type]
        else:
            error_msg = f"Unsupported export format: {export_format}"
            raise ValueError(error_msg)

        logger.info(f"Exported to {format_lower.upper()}: {output_path}")
