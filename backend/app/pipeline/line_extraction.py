"""
Line art extraction pipeline.

Coordinates classical CV and ML-based line extraction methods.
"""

import logging
from enum import Enum

import cv2
import numpy as np
from models.classical_cv import (
    BilateralCannyDetector,
    CannyEdgeDetector,
    XDoGExtractor,
    auto_canny,
)
from numpy.typing import NDArray

logger = logging.getLogger(__name__)

RGB_CHANNELS = 3


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

    def __init__(self) -> None:
        """Initialize line extractor with default methods."""
        self.canny = CannyEdgeDetector()
        self.bilateral_canny = BilateralCannyDetector()
        self.xdog = XDoGExtractor()

    def extract(
        self,
        image: NDArray[np.uint8],
        method: LineExtractionMethod = LineExtractionMethod.AUTO,
        low_threshold: int | None = None,
        high_threshold: int | None = None,
    ) -> NDArray[np.uint8]:
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
                canny_detector = CannyEdgeDetector(low_threshold, high_threshold)
            else:
                canny_detector = self.canny
            return canny_detector.extract_lines(image)

        if method == LineExtractionMethod.BILATERAL_CANNY:
            if low_threshold and high_threshold:
                bilateral_detector = BilateralCannyDetector(
                    low_threshold, high_threshold
                )
            else:
                bilateral_detector = self.bilateral_canny
            return bilateral_detector.extract_lines(image)

        if method == LineExtractionMethod.AUTO_CANNY:
            if len(image.shape) == RGB_CHANNELS:
                gray: NDArray[np.uint8] = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)  # type: ignore[assignment]
            else:
                gray = image
            return auto_canny(gray)

        if method == LineExtractionMethod.XDOG:
            return self.xdog.extract_lines(image)

        msg = f"Unknown extraction method: {method}"
        raise ValueError(msg)

    def extract_with_params(
        self,
        image: NDArray[np.uint8],
        edge_threshold: tuple[int, int] = (50, 150),
        use_ml: bool = False,
    ) -> NDArray[np.uint8]:
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
