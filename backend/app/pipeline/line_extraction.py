"""
Line art extraction pipeline.

Coordinates classical CV and ML-based line extraction methods.
"""

import logging
from enum import Enum

import numpy as np
from models.classical_cv import (
    BilateralCannyDetector,
    CannyEdgeDetector,
    XDoGExtractor,
    auto_canny,
)

logger = logging.getLogger(__name__)


class LineExtractionMethod(str, Enum):
    """Available line extraction methods."""

    AUTO = "auto"
    CANNY = "canny"
    BILATERAL_CANNY = "bilateral_canny"
    AUTO_CANNY = "auto_canny"
    XDOG = "xdog"


class LineExtractor:
    """
    Unified interface for line art extraction.

    Supports multiple extraction methods with consistent API.
    """

    def __init__(self):
        """Initialize line extractor with default methods."""
        self.canny = CannyEdgeDetector()
        self.bilateral_canny = BilateralCannyDetector()
        self.xdog = XDoGExtractor()

    def extract(
        self,
        image: np.ndarray,
        method: LineExtractionMethod = LineExtractionMethod.AUTO,
        low_threshold: int | None = None,
        high_threshold: int | None = None,
    ) -> np.ndarray:
        """
        Extract line art from image using specified method.

        Args:
            image: Input RGB or grayscale image
            method: Line extraction method to use
            low_threshold: Optional Canny lower threshold override
            high_threshold: Optional Canny upper threshold override

        Returns:
            Binary line art image (255 = line, 0 = background)
        """
        if method == LineExtractionMethod.AUTO:
            method = LineExtractionMethod.BILATERAL_CANNY

        if method == LineExtractionMethod.CANNY:
            if low_threshold and high_threshold:
                detector = CannyEdgeDetector(low_threshold, high_threshold)
            else:
                detector = self.canny
            return detector.extract_lines(image)

        if method == LineExtractionMethod.BILATERAL_CANNY:
            if low_threshold and high_threshold:
                detector = BilateralCannyDetector(low_threshold, high_threshold)
            else:
                detector = self.bilateral_canny
            return detector.extract_lines(image)

        if method == LineExtractionMethod.AUTO_CANNY:
            import cv2

            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image
            return auto_canny(gray)

        if method == LineExtractionMethod.XDOG:
            return self.xdog.extract_lines(image)

        raise ValueError(f"Unknown extraction method: {method}")

    def extract_with_params(
        self,
        image: np.ndarray,
        edge_threshold: tuple[int, int] = (50, 150),
        use_ml: bool = False,
    ) -> np.ndarray:
        """
        Extract lines with explicit parameters.

        Args:
            image: Input image
            edge_threshold: Tuple of (low, high) thresholds
            use_ml: Whether to use ML-based extraction (not implemented)

        Returns:
            Binary line art
        """
        if use_ml:
            logger.warning("ML extraction not yet implemented, falling back to CV")

        low, high = edge_threshold
        return self.extract(
            image,
            LineExtractionMethod.BILATERAL_CANNY,
            low,
            high,
        )
