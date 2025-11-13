"""
Main processing pipeline coordinator.

Orchestrates the complete photo-to-line-vectorizer pipeline from
image upload through preprocessing, line extraction, vectorization,
optimization, and export.
"""

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
from models.u2net import U2NetPredictor

from pipeline.hatching import HatchGenerator
from pipeline.line_extraction import LineExtractor
from pipeline.optimize import VpypeOptimizer
from pipeline.preprocess import ImagePreprocessor
from pipeline.vectorize import ImageTracerVectorizer

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

logger = logging.getLogger(__name__)


@dataclass
class ProcessingParams:
    """
    Parameters for image processing pipeline.

    All canvas and line width parameters are required and specified in mm.
    """

    canvas_width_mm: float
    canvas_height_mm: float
    line_width_mm: float
    isolate_subject: bool = False
    use_ml: bool = False
    edge_threshold: tuple[int, int] = (50, 150)
    line_threshold: int = 16
    merge_tolerance: float = 0.5
    simplify_tolerance: float = 0.2
    hatching_enabled: bool = False
    hatch_density: float = 2.0
    hatch_angle: int = 45
    darkness_threshold: int = 100


@dataclass
class ProcessingResult:
    """
    Result of processing pipeline.

    Attributes:
        svg_content: Optimized SVG string
        stats: Dictionary containing processing statistics
        device_used: Name of device used for processing
    """

    svg_content: str
    stats: Mapping[str, float | int | tuple[float, float, float, float] | None]
    device_used: str


class PhotoToLineProcessor:
    """
    Main pipeline coordinator for photo-to-line conversion.

    Manages all processing stages and provides unified interface
    for the complete pipeline.
    """

    def __init__(
        self,
        u2net_model_path: Path | None = None,
    ):
        """
        Initialize processor with models and pipeline components.

        Args:
            u2net_model_path: Optional path to U²-Net weights
        """
        from utils.device import device_manager  # noqa: PLC0415

        self.device_manager = device_manager

        if u2net_model_path and u2net_model_path.exists():
            logger.info("Loading U²-Net model...")
            self.u2net: U2NetPredictor | None = U2NetPredictor(u2net_model_path)
            self.preprocessor = ImagePreprocessor(self.u2net)
        else:
            logger.warning("U²-Net model not found, subject isolation unavailable")
            self.u2net = None
            self.preprocessor = ImagePreprocessor()

        self.line_extractor = LineExtractor()
        self.vectorizer = ImageTracerVectorizer()
        self.optimizer = VpypeOptimizer()

        logger.info("PhotoToLineProcessor initialized")

    def process(
        self,
        image_path: Path,
        params: ProcessingParams,
    ) -> ProcessingResult:
        """
        Execute complete processing pipeline.

        Args:
            image_path: Path to input image
            params: Processing parameters with required canvas dimensions

        Returns:
            ProcessingResult with SVG content and statistics

        Raises:
            ValueError: If required parameters missing
            RuntimeError: If processing fails
        """
        logger.info(f"Starting processing: {image_path}")

        preprocessed = self.preprocessor.preprocess(
            image_path,
            isolate_subject=params.isolate_subject,
            max_dimension=2048,
            enhance_contrast=False,
        )

        logger.info("Extracting line art...")
        edges = self.line_extractor.extract_with_params(
            preprocessed,
            edge_threshold=params.edge_threshold,
            use_ml=params.use_ml,
        )

        if params.hatching_enabled:
            logger.info("Adding hatching...")
            hatch_gen = HatchGenerator(
                line_width_mm=params.line_width_mm,
                density_factor=params.hatch_density,
                darkness_threshold=params.darkness_threshold,
            )
            gray_image: NDArray[np.uint8] = cv2.cvtColor(
                preprocessed, cv2.COLOR_RGB2GRAY
            )  # type: ignore[assignment]
            edges = hatch_gen.add_hatching_to_edges(
                edges,
                gray_image,
                params.canvas_width_mm,
                params.canvas_height_mm,
            )

        edges_inverted: NDArray[np.uint8] = cv2.bitwise_not(edges)  # type: ignore[assignment]

        logger.info("Vectorizing...")
        svg_raw = self.vectorizer.vectorize(
            edges_inverted,
            line_threshold=params.line_threshold,
            qtres=1.0,
            pathomit=8,
        )

        logger.info("Optimizing paths...")
        svg_optimized = self.optimizer.optimize(
            svg_raw,
            canvas_width_mm=params.canvas_width_mm,
            canvas_height_mm=params.canvas_height_mm,
            merge_tolerance=params.merge_tolerance,
            simplify_tolerance=params.simplify_tolerance,
        )

        stats: Mapping[str, float | int | tuple[float, float, float, float] | None] = (
            self.optimizer.get_stats(svg_optimized)
        )

        logger.info(f"Processing complete: {stats['path_count']} paths")

        return ProcessingResult(
            svg_content=svg_optimized,
            stats=stats,
            device_used=self.device_manager.device_name,
        )

    def process_preset(
        self,
        image_path: Path,
        preset: str,
        canvas_width_mm: float,
        canvas_height_mm: float,
        line_width_mm: float,
    ) -> ProcessingResult:
        """
        Process image using named preset.

        Args:
            image_path: Path to input image
            preset: Preset name (portrait, animal, etc.)
            canvas_width_mm: Required canvas width in mm
            canvas_height_mm: Required canvas height in mm
            line_width_mm: Required line width in mm

        Returns:
            ProcessingResult
        """
        presets = {
            "portrait": ProcessingParams(
                canvas_width_mm=canvas_width_mm,
                canvas_height_mm=canvas_height_mm,
                line_width_mm=line_width_mm,
                isolate_subject=True,
                use_ml=False,
                edge_threshold=(50, 150),
                line_threshold=16,
                merge_tolerance=0.5,
                simplify_tolerance=0.2,
                hatching_enabled=True,
                hatch_density=2.0,
                hatch_angle=45,
                darkness_threshold=100,
            ),
            "animal": ProcessingParams(
                canvas_width_mm=canvas_width_mm,
                canvas_height_mm=canvas_height_mm,
                line_width_mm=line_width_mm,
                isolate_subject=True,
                use_ml=False,
                edge_threshold=(30, 120),
                line_threshold=12,
                merge_tolerance=0.3,
                simplify_tolerance=0.15,
                hatching_enabled=True,
                hatch_density=1.5,
                hatch_angle=45,
                darkness_threshold=80,
            ),
        }

        if preset not in presets:
            msg = f"Unknown preset: {preset}"
            raise ValueError(msg)

        params = presets[preset]
        return self.process(image_path, params)
