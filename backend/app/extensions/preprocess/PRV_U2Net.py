"""
U²-Net-based preprocessing provider.

Provides ML-based subject isolation using U²-Net model
in addition to standard preprocessing operations.
"""

import logging
from pathlib import Path
from typing import Any, ClassVar

import cv2
import numpy as np
import pillow_heif
from numpy.typing import NDArray
from PIL import Image

from extensions.base import AbstractProvider

logger = logging.getLogger(__name__)

pillow_heif.register_heif_opener()

RGB_CHANNELS = 3
ALPHA_MAX = 255.0


class PRV_U2Net(AbstractProvider):
    """U²-Net-based preprocessing provider with ML subject isolation."""

    name: ClassVar[str] = "u2net"
    extension: ClassVar[str] = "preprocess"
    description: ClassVar[str] = "U²-Net ML-based preprocessing"

    SUPPORTED_FORMATS: ClassVar[set[str]] = {
        ".jpg",
        ".jpeg",
        ".png",
        ".tiff",
        ".tif",
        ".webp",
        ".heic",
        ".heif",
    }

    _u2net_predictor: ClassVar[Any | None] = None

    @classmethod
    def is_available(cls) -> bool:
        """Check if U²-Net model is available."""
        try:
            if cls._u2net_predictor is None:
                from models.u2net import U2NetPredictor

                model_path = Path("models/u2net/u2net.pth")
                if not model_path.exists():
                    return False

                cls._u2net_predictor = U2NetPredictor(model_path)
            return True
        except (ImportError, FileNotFoundError):
            return False

    @classmethod
    def execute(
        cls,
        input_data: Path,
        isolate_subject: bool = False,
        max_dimension: int = 2048,
        enhance_contrast: bool = False,
        threshold: int = 128,
        background_color: tuple[int, int, int] = (255, 255, 255),
        **params: Any,
    ) -> NDArray[np.uint8]:
        """
        Complete preprocessing pipeline with ML subject isolation.

        Args:
            input_data: Path to input image
            isolate_subject: Whether to isolate subject using U²-Net
            max_dimension: Maximum image dimension
            enhance_contrast: Whether to apply contrast enhancement
            threshold: Mask threshold for segmentation
            background_color: Color for removed background
            **params: Additional parameters

        Returns:
            Preprocessed RGB image
        """
        image = cls.load_image(input_data)
        image = cls.resize_if_needed(image, max_dimension)

        if enhance_contrast:
            image = cls.normalize_contrast(image)

        if isolate_subject:
            image = cls.isolate_subject(image, threshold, background_color)

        return image

    @classmethod
    def load_image(cls, image_path: Path) -> NDArray[np.uint8]:
        """
        Load image from file with format detection.

        Args:
            image_path: Path to image file

        Returns:
            RGB image as numpy array (H, W, 3)

        Raises:
            ValueError: If format is unsupported
            FileNotFoundError: If file doesn't exist
        """
        if not image_path.exists():
            msg = f"Image not found: {image_path}"
            raise FileNotFoundError(msg)

        suffix = image_path.suffix.lower()
        if suffix not in cls.SUPPORTED_FORMATS:
            msg = f"Unsupported format: {suffix}"
            raise ValueError(msg)

        pil_image: Image.Image = Image.open(image_path)
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")

        image = np.array(pil_image)
        logger.info(
            "Loaded image: %s (%dx%d)", image_path, image.shape[1], image.shape[0]
        )
        return image

    @classmethod
    def resize_if_needed(
        cls,
        image: NDArray[np.uint8],
        max_dimension: int = 2048,
    ) -> NDArray[np.uint8]:
        """
        Resize image if it exceeds maximum dimension.

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

        resized: NDArray[np.uint8] = cv2.resize(
            image, (new_w, new_h), interpolation=cv2.INTER_AREA
        )
        logger.info("Resized image from %dx%d to %dx%d", w, h, new_w, new_h)
        return resized

    @classmethod
    def isolate_subject(
        cls,
        image: NDArray[np.uint8],
        threshold: int = 128,
        background_color: tuple[int, int, int] = (255, 255, 255),
    ) -> NDArray[np.uint8]:
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
        if cls._u2net_predictor is None:
            msg = "U²-Net predictor not initialized"
            raise RuntimeError(msg)

        rgba = cls._u2net_predictor.isolate_subject(image, threshold)

        rgb_with_bg = np.full_like(image, background_color, dtype=np.uint8)
        alpha = rgba[:, :, 3:4] / ALPHA_MAX
        rgb_with_bg = (rgba[:, :, :3] * alpha + rgb_with_bg * (1 - alpha)).astype(
            np.uint8
        )

        logger.info("Subject isolation complete")
        return rgb_with_bg

    @classmethod
    def normalize_contrast(
        cls, image: NDArray[np.uint8], clip_limit: float = 2.0
    ) -> NDArray[np.uint8]:
        """
        Enhance image contrast using CLAHE.

        Args:
            image: Input RGB image
            clip_limit: CLAHE clip limit

        Returns:
            Contrast-enhanced image
        """
        if len(image.shape) == RGB_CHANNELS:
            lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
            lightness, a_channel, b_channel = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
            lightness = clahe.apply(lightness)
            enhanced_lab = cv2.merge([lightness, a_channel, b_channel])
            enhanced: NDArray[np.uint8] = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2RGB)
        else:
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
            enhanced = clahe.apply(image)

        logger.debug("Contrast normalization applied")
        return enhanced
