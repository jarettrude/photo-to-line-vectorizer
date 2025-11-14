"""
Bilateral Canny edge detection provider.

Provides line extraction using bilateral filtering followed by
Canny edge detection for cleaner line art.
"""

import logging
from typing import Any, ClassVar

import numpy as np
from models.classical_cv import BilateralCannyDetector
from numpy.typing import NDArray

from extensions.base import AbstractProvider

logger = logging.getLogger(__name__)


class PRV_BilateralCanny(AbstractProvider):
    """Bilateral Canny edge detection provider."""

    name: ClassVar[str] = "bilateral_canny"
    extension: ClassVar[str] = "line_extraction"
    description: ClassVar[str] = "Bilateral filtering + Canny edge detection"

    @classmethod
    def is_available(cls) -> bool:
        """Check if required libraries are available."""
        try:
            return True
        except ImportError:
            return False

    @classmethod
    def execute(
        cls,
        input_data: NDArray[np.uint8],
        edge_threshold: tuple[int, int] = (50, 150),
        use_ml: bool = False,
        **params: Any,
    ) -> NDArray[np.uint8]:
        """
        Extract lines using bilateral Canny edge detection.

        Args:
            input_data: Input RGB or grayscale image
            edge_threshold: Tuple of (low, high) Canny thresholds
            use_ml: Whether to use ML (not supported by this provider)
            **params: Additional parameters

        Returns:
            Binary line art image (255 = line, 0 = background)

        Raises:
            RuntimeError: If use_ml is requested (not supported)
        """
        if use_ml:
            msg = "ML extraction not supported by bilateral_canny provider"
            raise RuntimeError(msg)

        low, high = edge_threshold
        detector = BilateralCannyDetector(low, high)
        return detector.extract_lines(input_data)
