"""
Image preprocessing extension.

Handles image loading, format conversion, subject isolation,
and preparation for line extraction through multiple provider implementations.
"""

import logging
from pathlib import Path
from typing import Any, ClassVar

import numpy as np
from numpy.typing import NDArray

from extensions.base import AbstractStaticExtension, HookContext
from extensions.hooks import HookTiming

logger = logging.getLogger(__name__)


class EXT_Preprocess(AbstractStaticExtension):
    """
    Image preprocessing extension.

    Coordinates multiple preprocessing providers and provides
    a unified interface for image loading and preprocessing operations.
    """

    name: ClassVar[str] = "preprocess"
    version: ClassVar[str] = "1.0.0"
    description: ClassVar[str] = "Image loading, resizing, and subject isolation"

    @classmethod
    def preprocess(
        cls,
        image_path: Path,
        provider_preferences: list[str] | None = None,
        **params: Any,
    ) -> NDArray[np.uint8]:
        """
        Complete preprocessing pipeline.

        Args:
            image_path: Path to input image
            provider_preferences: Ordered list of preferred providers
            **params: Provider-specific parameters (isolate_subject, max_dimension, etc.)

        Returns:
            Preprocessed RGB image

        Raises:
            RuntimeError: If no providers are available
        """
        context = HookContext(
            extension=cls.name,
            stage="preprocess",
            method_name="preprocess",
            timing=HookTiming.BEFORE.value,
            input_data=image_path,
            params=params,
        )
        cls.execute_hooks("preprocess", HookTiming.BEFORE.value, context)

        provider = cls.select_provider(provider_preferences)
        logger.info("Using preprocessing provider: %s", provider.name)

        result = provider.execute(image_path, **params)

        context.output_data = result
        context.timing = HookTiming.AFTER.value
        cls.execute_hooks("preprocess", HookTiming.AFTER.value, context)

        return context.output_data if context.output_data is not None else result
