"""
Raster to vector conversion using ImageTracerJS.

Converts bitmap line art to SVG paths using ImageTracerJS
running in a Node.js subprocess.
"""

import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class ImageTracerVectorizer:
    """
    Vectorization using ImageTracerJS via Node.js subprocess.

    Converts raster line art to SVG vector paths with configurable
    quality and simplification settings.
    """

    def __init__(self):
        """Initialize vectorizer and verify ImageTracerJS availability."""
        self._check_availability()

    def _check_availability(self) -> None:
        """Check if Node.js and ImageTracerJS are available."""
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                logger.warning("Node.js not available, vectorization may fail")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("Node.js not found, vectorization will not work")

    def vectorize(
        self,
        image: np.ndarray,
        line_threshold: int = 128,
        qtres: float = 1.0,
        pathomit: int = 8,
        scale: float = 1.0,
    ) -> str:
        """
        Convert raster image to SVG.

        Args:
            image: Input grayscale or RGB image
            line_threshold: Threshold for line detection (0-255)
            qtres: Quality/resolution (lower = more detail)
            pathomit: Minimum path length in pixels
            scale: Output scaling factor

        Returns:
            SVG string

        Raises:
            RuntimeError: If vectorization fails
        """
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_input:
            input_path = Path(tmp_input.name)
            cv2.imwrite(str(input_path), image)

        try:
            svg_string = self._run_imagetracer(
                input_path,
                line_threshold,
                qtres,
                pathomit,
                scale,
            )
            return svg_string
        finally:
            input_path.unlink(missing_ok=True)

    def _run_imagetracer(
        self,
        image_path: Path,
        threshold: int,
        qtres: float,
        pathomit: int,
        scale: float,
    ) -> str:
        """
        Run ImageTracerJS via Node.js subprocess.

        Args:
            image_path: Path to input image
            threshold: Line threshold
            qtres: Quality resolution
            pathomit: Path omit threshold
            scale: Scale factor

        Returns:
            SVG string

        Raises:
            RuntimeError: If subprocess fails
        """
        # Use JSON encoding for safe parameter passing
        config = {
            "imagePath": str(image_path),
            "threshold": threshold,
            "qtres": qtres,
            "pathomit": pathomit,
            "scale": scale,
        }

        tracer_script = f"""
        const ImageTracer = require('imagetracerjs');
        const config = {json.dumps(config)};

        const options = {{
            ltres: config.threshold / 255.0,
            qtres: config.qtres,
            pathomit: config.pathomit,
            scale: config.scale,
            strokewidth: 1,
            linefilter: true,
            pal: [{{r:0, g:0, b:0, a:255}}, {{r:255, g:255, b:255, a:255}}]
        }};

        ImageTracer.imageToSVG(config.imagePath, (svgstr) => {{
            console.log(svgstr);
        }}, options);
        """

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", delete=False
        ) as tmp_script:
            script_path = Path(tmp_script.name)
            tmp_script.write(tracer_script)

        try:
            result = subprocess.run(
                ["node", str(script_path)],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                raise RuntimeError(f"ImageTracerJS failed: {result.stderr}")

            return result.stdout

        except subprocess.TimeoutExpired:
            raise RuntimeError("ImageTracerJS timeout")
        finally:
            script_path.unlink(missing_ok=True)


class PotraceVectorizer:
    """
    Fallback vectorization using Potrace.

    Uses Potrace via subprocess for GPL-safe isolation.
    """

    def __init__(self):
        """Initialize Potrace vectorizer."""
        self._check_availability()

    def _check_availability(self) -> None:
        """Check if potrace is available."""
        try:
            result = subprocess.run(
                ["potrace", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                logger.warning("Potrace not available")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("Potrace not found")

    def vectorize(
        self,
        image: np.ndarray,
        turdsize: int = 2,
        turnpolicy: str = "minority",
    ) -> str:
        """
        Convert raster image to SVG using Potrace.

        Args:
            image: Input grayscale image
            turdsize: Suppress speckles of this size
            turnpolicy: Turn policy (black, white, left, right, minority, majority)

        Returns:
            SVG string
        """
        with tempfile.NamedTemporaryFile(suffix=".pbm", delete=False) as tmp_input:
            input_path = Path(tmp_input.name)

            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image

            _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
            cv2.imwrite(str(input_path), binary)

        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp_output:
            output_path = Path(tmp_output.name)

        try:
            result = subprocess.run(
                [
                    "potrace",
                    "-s",
                    "-t",
                    str(turdsize),
                    "-k",
                    turnpolicy,
                    str(input_path),
                    "-o",
                    str(output_path),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise RuntimeError(f"Potrace failed: {result.stderr}")

            return output_path.read_text()

        finally:
            input_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)
