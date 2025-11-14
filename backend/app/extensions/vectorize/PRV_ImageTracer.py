"""
ImageTracerJS provider for vectorization.

Uses ImageTracerJS (public domain) via Node.js subprocess for
high-quality vector conversion.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

import cv2

from extensions.base import AbstractProvider

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

logger = logging.getLogger(__name__)

PROJECT_ROOT_LEVELS_UP = 3
NODE_MODULES_DIRNAME = "node_modules"
NODE_PATH_ENV_VAR = "NODE_PATH"


class PRV_ImageTracer(AbstractProvider):
    """ImageTracerJS vectorization provider."""

    name: ClassVar[str] = "imagetracer"
    extension: ClassVar[str] = "vectorize"
    description: ClassVar[str] = "ImageTracerJS vectorization (public domain)"

    @classmethod
    def is_available(cls) -> bool:
        """
        Check if ImageTracerJS is available.

        Returns:
            True if Node.js and ImageTracerJS are installed
        """
        try:
            result = subprocess.run(
                ["node", "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    @classmethod
    def execute(cls, input_data: NDArray[np.uint8], **params: Any) -> str:
        """
        Vectorize raster image using ImageTracerJS.

        Args:
            input_data: Input grayscale or RGB image
            **params: Vectorization parameters:
                - line_threshold: Threshold for line detection (0-255), default 128
                - qtres: Quality resolution (lower = more detail), default 1.0
                - pathomit: Minimum path length in pixels, default 8
                - scale: Output scaling factor, default 1.0

        Returns:
            SVG string

        Raises:
            RuntimeError: If vectorization fails
        """
        line_threshold = params.get("line_threshold", 128)
        qtres = params.get("qtres", 1.0)
        pathomit = params.get("pathomit", 8)
        scale = params.get("scale", 1.0)

        # Write image to temp file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_input:
            input_path = Path(tmp_input.name)
            cv2.imwrite(str(input_path), input_data)

        try:
            return cls._run_imagetracer(
                input_path,
                line_threshold,
                qtres,
                pathomit,
                scale,
            )
        finally:
            input_path.unlink(missing_ok=True)

    @classmethod
    def _run_imagetracer(
        cls,
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

        # Set up Node.js environment
        project_root = Path(__file__).resolve().parents[PROJECT_ROOT_LEVELS_UP]
        node_modules_dir = project_root / NODE_MODULES_DIRNAME
        env = os.environ.copy()
        env[NODE_PATH_ENV_VAR] = str(node_modules_dir)

        try:
            result = subprocess.run(
                ["node", str(script_path)],
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
                env=env,
            )

            if result.returncode == 0:
                return result.stdout

            msg = f"ImageTracerJS failed: {result.stderr}"
            raise RuntimeError(msg)

        except subprocess.TimeoutExpired as err:
            msg = "ImageTracerJS timeout"
            raise RuntimeError(msg) from err
        finally:
            script_path.unlink(missing_ok=True)
