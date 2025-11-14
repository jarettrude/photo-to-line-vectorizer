"""
vpype-based export provider.

Provides export to SVG, HPGL, and G-code formats using vpype.
"""

import logging
import tempfile
from pathlib import Path
from typing import Any, ClassVar

import vpype as vp

from extensions.base import AbstractProvider

logger = logging.getLogger(__name__)


class PRV_Vpype(AbstractProvider):
    """vpype-based export provider for multiple formats."""

    name: ClassVar[str] = "vpype"
    extension: ClassVar[str] = "export"
    description: ClassVar[str] = "vpype-based export to SVG/HPGL/G-code"

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
        output_path: Path,
        export_format: str = "svg",
        **params: Any,
    ) -> None:
        """
        Export SVG to specified format.

        Args:
            input_data: Input SVG string
            output_path: Output file path
            export_format: Export format (svg, hpgl, gcode)
            **params: Format-specific parameters

        Raises:
            ValueError: If format is unsupported
        """
        format_lower = export_format.lower()

        if format_lower == "svg":
            cls.export_svg(input_data, output_path, **params)
        elif format_lower == "hpgl":
            cls.export_hpgl(input_data, output_path, **params)
        elif format_lower in ("gcode", "g-code", "nc"):
            cls.export_gcode(input_data, output_path, **params)
        else:
            msg = f"Unsupported export format: {export_format}"
            raise ValueError(msg)

        logger.info("Exported to %s: %s", format_lower.upper(), output_path)

    @classmethod
    def export_svg(
        cls,
        svg_string: str,
        output_path: Path,
        layer_mode: str = "layer",
        **params: Any,
    ) -> None:
        """
        Export to SVG format.

        Args:
            svg_string: Input SVG string
            output_path: Output file path
            layer_mode: Color mode (layer, device, or default)
            **params: Additional parameters
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".svg", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(svg_string)

        try:
            result = vp.read_svg(str(tmp_path), quantization=0.1)
            lc, page_w, page_h = result

            doc = vp.Document()
            doc.add(lc, 1)
            doc.page_size = (page_w, page_h)

            with output_path.open("w") as f:
                vp.write_svg(f, doc, color_mode=layer_mode)
            logger.info("Exported SVG to %s", output_path)

        finally:
            tmp_path.unlink(missing_ok=True)

    @classmethod
    def export_hpgl(
        cls,
        svg_string: str,
        output_path: Path,
        device: str = "",
        velocity: int | None = None,
        force: int | None = None,
        **params: Any,
    ) -> None:
        """
        Export to HPGL format for pen plotters.

        Args:
            svg_string: Input SVG string
            output_path: Output file path
            device: HPGL device type (hp7475a, hp7576a, etc.)
            velocity: Pen velocity (device-specific units)
            force: Pen force (device-specific units)
            **params: Additional parameters

        Raises:
            RuntimeError: If HPGL export fails
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".svg", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(svg_string)

        try:
            result = vp.read_svg(str(tmp_path), quantization=0.1)
            lc, _, _ = result

            hpgl_content = []

            hpgl_content.append("IN;")
            hpgl_content.append("SC;")

            if velocity is not None:
                hpgl_content.append(f"VS{velocity};")
            if force is not None:
                hpgl_content.append(f"FS{force};")

            hpgl_content.append("SP1;")

            for line in lc:
                if len(line) == 0:
                    continue

                x, y = line[0].real, line[0].imag
                hpgl_content.append(f"PU{int(x)},{int(y)};")

                if len(line) > 1:
                    points = ",".join(f"{int(p.real)},{int(p.imag)}" for p in line[1:])
                    hpgl_content.append(f"PD{points};")

            hpgl_content.append("PU;")
            hpgl_content.append("SP0;")

            output_path.write_text("\n".join(hpgl_content))
            logger.info("Exported HPGL to %s", output_path)

        except Exception as e:
            msg = f"HPGL export failed: {e}"
            raise RuntimeError(msg) from e
        finally:
            tmp_path.unlink(missing_ok=True)

    @classmethod
    def export_gcode(
        cls,
        svg_string: str,
        output_path: Path,
        profile: str = "gcode",
        feed_rate: int = 1000,
        z_up: float = 5.0,
        z_down: float = 0.0,
        **params: Any,
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
            **params: Additional parameters

        Raises:
            RuntimeError: If G-code export fails
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".svg", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(svg_string)

        try:
            result = vp.read_svg(str(tmp_path), quantization=0.1)
            lc, _, _ = result

            gcode_lines = []

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

            for line in lc:
                if len(line) == 0:
                    continue

                x0, y0 = line[0].real, line[0].imag
                gcode_lines.append(f"G0 Z{z_up}")
                gcode_lines.append(f"G0 X{x0:.3f} Y{y0:.3f}")
                gcode_lines.append(f"G1 Z{z_down}")

                for point in line[1:]:
                    x, y = point.real, point.imag
                    gcode_lines.append(f"G1 X{x:.3f} Y{y:.3f}")

            gcode_lines.extend(
                [
                    "",
                    f"G0 Z{z_up} ; Pen up",
                    "G0 X0 Y0 ; Return to home",
                    "M2 ; End program",
                ]
            )

            output_path.write_text("\n".join(gcode_lines))
            logger.info("Exported G-code to %s", output_path)

        except Exception as e:
            msg = f"G-code export failed: {e}"
            raise RuntimeError(msg) from e
        finally:
            tmp_path.unlink(missing_ok=True)
