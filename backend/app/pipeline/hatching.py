"""
Hatching and shading generation for line art.

Implements scanline hatching for dark regions to add shading
to line drawings.
"""

import logging

import cv2
import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)

RGB_CHANNELS = 3
ANGLE_45 = 45
ANGLE_NEG_45 = -45
ANGLE_0 = 0
ANGLE_90 = 90


class HatchGenerator:
    """
    Generates hatching lines for dark regions in images.

    Creates parallel lines at configurable spacing and angles
    for shading effects.
    """

    def __init__(
        self,
        line_width_mm: float,
        density_factor: float = 2.0,
        darkness_threshold: int = 100,
        crosshatch_threshold: int = 50,
    ):
        """
        Initialize hatch generator.

        Args:
            line_width_mm: Line width in mm for spacing calculation
            density_factor: Multiplier for line spacing (spacing = line_width * factor)
            darkness_threshold: Pixel value below which to apply hatching
            crosshatch_threshold: Pixel value below which to apply crosshatch
        """
        self.line_width_mm = line_width_mm
        self.density_factor = density_factor
        self.darkness_threshold = darkness_threshold
        self.crosshatch_threshold = crosshatch_threshold

    def generate_hatches(
        self,
        image: NDArray[np.uint8],
        canvas_width_mm: float,
        canvas_height_mm: float,
        angle: int = 45,
    ) -> NDArray[np.uint8]:
        """
        Generate hatching lines for dark regions.

        Args:
            image: Grayscale input image
            canvas_width_mm: Canvas width for spacing calculation
            canvas_height_mm: Canvas height for spacing calculation
            angle: Hatch angle in degrees

        Returns:
            Binary image with hatch lines
        """
        if len(image.shape) == RGB_CHANNELS:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        h, w = gray.shape
        pixels_per_mm = w / canvas_width_mm
        spacing_px = int(self.line_width_mm * self.density_factor * pixels_per_mm)
        spacing_px = max(spacing_px, 2)

        hatch_mask = np.zeros_like(gray)
        crosshatch_mask = np.zeros_like(gray)

        for i in range(0, max(h, w) * 2, spacing_px):
            if angle == ANGLE_45:
                cv2.line(hatch_mask, (-w, i), (i, -h), 255, 1)
            elif angle == ANGLE_NEG_45:
                cv2.line(hatch_mask, (w * 2, i), (i, h * 2), 255, 1)
            elif angle == ANGLE_0:
                if i < h:
                    cv2.line(hatch_mask, (0, i), (w, i), 255, 1)
            elif angle == ANGLE_90 and i < w:
                cv2.line(hatch_mask, (i, 0), (i, h), 255, 1)

        dark_regions = gray < self.darkness_threshold
        hatching = np.where(dark_regions, hatch_mask, 0).astype(np.uint8)

        if self.crosshatch_threshold > 0:
            very_dark_regions = gray < self.crosshatch_threshold

            for i in range(0, max(h, w) * 2, spacing_px):
                if angle == ANGLE_45:
                    cv2.line(crosshatch_mask, (w * 2, i), (i, h * 2), 255, 1)
                elif angle == ANGLE_NEG_45:
                    cv2.line(crosshatch_mask, (-w, i), (i, -h), 255, 1)

            crosshatching = np.where(very_dark_regions, crosshatch_mask, 0).astype(
                np.uint8
            )
            hatching = cv2.bitwise_or(hatching, crosshatching)  # type: ignore[assignment]

        logger.debug(f"Generated hatching with {np.sum(hatching > 0)} pixels")
        return hatching

    def add_hatching_to_edges(
        self,
        edges: NDArray[np.uint8],
        original_image: NDArray[np.uint8],
        canvas_width_mm: float,
        canvas_height_mm: float,
    ) -> NDArray[np.uint8]:
        """
        Combine edge detection with hatching.

        Args:
            edges: Binary edge image
            original_image: Original grayscale image for darkness analysis
            canvas_width_mm: Canvas width in mm
            canvas_height_mm: Canvas height in mm

        Returns:
            Combined edge + hatch image
        """
        hatching = self.generate_hatches(
            original_image,
            canvas_width_mm,
            canvas_height_mm,
            angle=45,
        )

        combined: NDArray[np.uint8] = cv2.bitwise_or(edges, hatching)  # type: ignore[assignment]

        logger.info("Hatching added to edges")
        return combined
