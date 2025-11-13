"""
Image preprocessing pipeline.

Handles image loading, format conversion, subject isolation,
and preparation for line extraction.
"""
import logging
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
from PIL import Image
import pillow_heif

from models.u2net import U2NetPredictor

logger = logging.getLogger(__name__)

pillow_heif.register_heif_opener()


class ImagePreprocessor:
    """
    Handles image preprocessing including loading, format conversion,
    and optional subject isolation.
    """

    SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".webp", ".heic", ".heif"}

    def __init__(self, u2net_predictor: Optional[U2NetPredictor] = None):
        """
        Initialize preprocessor.

        Args:
            u2net_predictor: Optional U²-Net model for subject isolation
        """
        self.u2net = u2net_predictor

    def load_image(self, image_path: Path) -> np.ndarray:
        """
        Load image from file with format detection.

        Supports JPEG, PNG, TIFF, WebP, HEIC/HEIF formats.

        Args:
            image_path: Path to image file

        Returns:
            RGB image as numpy array (H, W, 3)

        Raises:
            ValueError: If format is unsupported
            FileNotFoundError: If file doesn't exist
        """
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        suffix = image_path.suffix.lower()
        if suffix not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {suffix}")

        try:
            pil_image = Image.open(image_path)
            if pil_image.mode != "RGB":
                pil_image = pil_image.convert("RGB")

            image = np.array(pil_image)
            logger.info(f"Loaded image: {image_path} ({image.shape[1]}x{image.shape[0]})")
            return image

        except Exception as e:
            logger.error(f"Failed to load image {image_path}: {e}")
            raise

    def resize_if_needed(
        self,
        image: np.ndarray,
        max_dimension: int = 2048,
    ) -> np.ndarray:
        """
        Resize image if it exceeds maximum dimension.

        Maintains aspect ratio during resize.

        Args:
            image: Input image
            max_dimension: Maximum width or height

        Returns:
            Resized image
        """
        h, w = image.shape[:2]
        if max(h, w) <= max_dimension:
            return image

        scale = max_dimension / max(h, w)
        new_w = int(w * scale)
        new_h = int(h * scale)

        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        logger.info(f"Resized image from {w}x{h} to {new_w}x{new_h}")
        return resized

    def isolate_subject(
        self,
        image: np.ndarray,
        threshold: int = 128,
        background_color: Tuple[int, int, int] = (255, 255, 255),
    ) -> np.ndarray:
        """
        Isolate subject from background using U²-Net.

        Args:
            image: Input RGB image
            threshold: Mask threshold for segmentation
            background_color: Color for removed background

        Returns:
            RGB image with background replaced

        Raises:
            RuntimeError: If U²-Net predictor not available
        """
        if self.u2net is None:
            raise RuntimeError("U²-Net predictor not initialized")

        rgba = self.u2net.isolate_subject(image, threshold)

        rgb_with_bg = np.full_like(image, background_color, dtype=np.uint8)
        alpha = rgba[:, :, 3:4] / 255.0
        rgb_with_bg = (rgba[:, :, :3] * alpha + rgb_with_bg * (1 - alpha)).astype(np.uint8)

        logger.info("Subject isolation complete")
        return rgb_with_bg

    def normalize_contrast(self, image: np.ndarray, clip_limit: float = 2.0) -> np.ndarray:
        """
        Enhance image contrast using CLAHE.

        Args:
            image: Input RGB image
            clip_limit: CLAHE clip limit

        Returns:
            Contrast-enhanced image
        """
        if len(image.shape) == 3:
            lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
            l = clahe.apply(l)
            enhanced = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)
        else:
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
            enhanced = clahe.apply(image)

        logger.debug("Contrast normalization applied")
        return enhanced

    def preprocess(
        self,
        image_path: Path,
        isolate_subject: bool = False,
        max_dimension: int = 2048,
        enhance_contrast: bool = False,
    ) -> np.ndarray:
        """
        Complete preprocessing pipeline.

        Args:
            image_path: Path to input image
            isolate_subject: Whether to isolate subject from background
            max_dimension: Maximum image dimension
            enhance_contrast: Whether to apply contrast enhancement

        Returns:
            Preprocessed RGB image
        """
        image = self.load_image(image_path)
        image = self.resize_if_needed(image, max_dimension)

        if enhance_contrast:
            image = self.normalize_contrast(image)

        if isolate_subject and self.u2net is not None:
            image = self.isolate_subject(image)

        return image
