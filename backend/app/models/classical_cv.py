"""
Classical computer vision line extraction methods.

Implements traditional edge detection algorithms (Canny, XDoG)
as fast, deterministic alternatives to ML models.
"""
import logging
from typing import Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class CannyEdgeDetector:
    """
    Canny edge detection for line art extraction.

    Fast, deterministic edge detection suitable for CPU processing.
    """

    def __init__(
        self,
        low_threshold: int = 50,
        high_threshold: int = 150,
        aperture_size: int = 3,
        l2_gradient: bool = True,
    ):
        """
        Initialize Canny edge detector.

        Args:
            low_threshold: Lower threshold for edge detection
            high_threshold: Upper threshold for edge detection
            aperture_size: Aperture size for Sobel operator (3, 5, or 7)
            l2_gradient: Use L2 norm for gradient calculation
        """
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold
        self.aperture_size = aperture_size
        self.l2_gradient = l2_gradient

    def extract_lines(
        self,
        image: np.ndarray,
        blur_kernel: Tuple[int, int] = (5, 5),
        blur_sigma: float = 1.0,
    ) -> np.ndarray:
        """
        Extract line art from image using Canny edge detection.

        Args:
            image: Input RGB or grayscale image
            blur_kernel: Gaussian blur kernel size
            blur_sigma: Gaussian blur sigma

        Returns:
            Binary edge map (255 = edge, 0 = no edge)
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        blurred = cv2.GaussianBlur(gray, blur_kernel, blur_sigma)

        edges = cv2.Canny(
            blurred,
            self.low_threshold,
            self.high_threshold,
            apertureSize=self.aperture_size,
            L2gradient=self.l2_gradient,
        )

        logger.debug(f"Canny edge detection: {np.sum(edges > 0)} edge pixels")
        return edges


class BilateralCannyDetector:
    """
    Enhanced Canny edge detection with bilateral filtering.

    Preserves edges while smoothing noise, producing cleaner line art.
    """

    def __init__(
        self,
        low_threshold: int = 50,
        high_threshold: int = 150,
        bilateral_d: int = 9,
        bilateral_sigma_color: float = 75.0,
        bilateral_sigma_space: float = 75.0,
    ):
        """
        Initialize bilateral Canny detector.

        Args:
            low_threshold: Canny lower threshold
            high_threshold: Canny upper threshold
            bilateral_d: Diameter of bilateral filter
            bilateral_sigma_color: Filter sigma in color space
            bilateral_sigma_space: Filter sigma in coordinate space
        """
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold
        self.bilateral_d = bilateral_d
        self.bilateral_sigma_color = bilateral_sigma_color
        self.bilateral_sigma_space = bilateral_sigma_space

    def extract_lines(self, image: np.ndarray) -> np.ndarray:
        """
        Extract line art using bilateral filtering + Canny.

        Args:
            image: Input RGB or grayscale image

        Returns:
            Binary edge map
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        filtered = cv2.bilateralFilter(
            gray,
            self.bilateral_d,
            self.bilateral_sigma_color,
            self.bilateral_sigma_space,
        )

        edges = cv2.Canny(filtered, self.low_threshold, self.high_threshold)

        logger.debug(f"Bilateral Canny: {np.sum(edges > 0)} edge pixels")
        return edges


class XDoGExtractor:
    """
    Extended Difference of Gaussians (XDoG) for stylized line art.

    Produces artistic line drawings with adjustable line thickness
    and contrast.
    """

    def __init__(
        self,
        sigma: float = 1.4,
        k: float = 1.6,
        tau: float = 0.98,
        epsilon: float = -0.5,
        phi: float = 10.0,
    ):
        """
        Initialize XDoG extractor.

        Args:
            sigma: Base Gaussian sigma
            k: Ratio between two Gaussians
            tau: Threshold for edge detection
            epsilon: Sharpening parameter
            phi: Line darkness multiplier
        """
        self.sigma = sigma
        self.k = k
        self.tau = tau
        self.epsilon = epsilon
        self.phi = phi

    def extract_lines(self, image: np.ndarray) -> np.ndarray:
        """
        Extract stylized line art using XDoG algorithm.

        Args:
            image: Input RGB or grayscale image

        Returns:
            Binary line art image
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        gray = gray.astype(np.float32) / 255.0

        g1 = cv2.GaussianBlur(gray, (0, 0), self.sigma)
        g2 = cv2.GaussianBlur(gray, (0, 0), self.sigma * self.k)

        dog = g1 - self.tau * g2

        xdog = np.where(
            dog < self.epsilon,
            1.0 + np.tanh(self.phi * dog),
            1.0,
        )

        xdog = (xdog * 255).astype(np.uint8)

        logger.debug("XDoG line extraction complete")
        return xdog


def auto_canny(image: np.ndarray, sigma: float = 0.33) -> np.ndarray:
    """
    Automatic Canny edge detection with adaptive thresholds.

    Computes thresholds based on image median for robust detection
    across varying image intensities.

    Args:
        image: Grayscale input image
        sigma: Factor for threshold calculation

    Returns:
        Binary edge map
    """
    v = np.median(image)
    lower = int(max(0, (1.0 - sigma) * v))
    upper = int(min(255, (1.0 + sigma) * v))

    edges = cv2.Canny(image, lower, upper)

    logger.debug(f"Auto Canny thresholds: {lower}, {upper}")
    return edges
