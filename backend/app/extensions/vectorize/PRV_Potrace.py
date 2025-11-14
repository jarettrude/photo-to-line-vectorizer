"""
Potrace-based vectorization provider.

Provides high-quality vectorization using the Potrace tracing algorithm,
which works well for line art and silhouettes.
"""

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any, ClassVar

import cv2
import numpy as np
from numpy.typing import NDArray

from extensions.base import AbstractProvider

logger = logging.getLogger(__name__)


class PRV_Potrace(AbstractProvider):
    """Potrace-based vectorization provider."""

    name: ClassVar[str] = "potrace"
    extension: ClassVar[str] = "vectorize"
    description: ClassVar[str] = "Potrace line art vectorization"

    @classmethod
    def is_available(cls) -> bool:
        """Check if potrace is installed."""
        try:
            result = subprocess.run(
                ["potrace", "--version"],
                check=False, capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    @classmethod
    def execute(
        cls,
        input_data: NDArray[np.uint8],
        line_threshold: int = 128,
        turdsize: int = 2,
        alphamax: float = 1.0,
        opttolerance: float = 0.2,
        **params: Any,
    ) -> str:
        """
        Vectorize image using Potrace.

        Args:
            input_data: Binary or grayscale image
            line_threshold: Threshold for binarization (0-255)
            turdsize: Suppress speckles of up to this size
            alphamax: Corner threshold parameter (0-1.3, higher = smoother)
            opttolerance: Curve optimization tolerance
            **params: Additional parameters

        Returns:
            SVG string

        Raises:
            RuntimeError: If potrace execution fails
        """
        # Ensure binary image
        if len(input_data.shape) == 3:
            gray: NDArray[np.uint8] = cv2.cvtColor(input_data, cv2.COLOR_RGB2GRAY)
        else:
            gray = input_data

        _, binary = cv2.threshold(gray, line_threshold, 255, cv2.THRESH_BINARY)

        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix=".pbm", delete=False) as tmp_input:
            tmp_input_path = Path(tmp_input.name)

        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp_output:
            tmp_output_path = Path(tmp_output.name)

        try:
            # Write PBM format (Portable Bitmap)
            height, width = binary.shape
            with tmp_input_path.open("wb") as f:
                # PBM header
                f.write(b"P4\n")
                f.write(f"{width} {height}\n".encode())
                # PBM data (packed bits)
                for row in binary:
                    # Pack 8 pixels per byte
                    packed_row = np.packbits(row > 0)
                    f.write(packed_row.tobytes())

            # Run potrace
            cmd = [
                "potrace",
                "-s",  # SVG output
                f"--turdsize={turdsize}",
                f"--alphamax={alphamax}",
                f"--opttolerance={opttolerance}",
                "-o",
                str(tmp_output_path),
                str(tmp_input_path),
            ]

            result = subprocess.run(
                cmd,
                check=False, capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                msg = f"Potrace failed: {result.stderr}"
                raise RuntimeError(msg)

            # Read and return SVG
            svg_content = tmp_output_path.read_text()
            logger.info("Potrace vectorization complete")
            return svg_content

        finally:
            tmp_input_path.unlink(missing_ok=True)
            tmp_output_path.unlink(missing_ok=True)
