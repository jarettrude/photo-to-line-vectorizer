"""
Line art extraction extension.

Provides line extraction through multiple provider implementations
using classical CV and ML-based methods.
"""

import logging
from typing import Any, ClassVar

import numpy as np
from numpy.typing import NDArray

from extensions.base import AbstractStaticExtension, HookContext
from extensions.hooks import HookTiming

logger = logging.getLogger(__name__)


class EXT_LineExtraction(AbstractStaticExtension):
    """
    Line art extraction extension.

    Coordinates multiple line extraction providers and provides
    a unified interface for extracting lines from preprocessed images.
    """

    name: ClassVar[str] = "line_extraction"
    version: ClassVar[str] = "1.0.0"
    description: ClassVar[str] = "Line art extraction from images"

    @classmethod
    def extract(
        cls,
        image: NDArray[np.uint8],
        provider_preferences: list[str] | None = None,
        **params: Any,
    ) -> NDArray[np.uint8]:
        """
        Extract line art from image.

        Args:
            image: Input RGB or grayscale image
            provider_preferences: Ordered list of preferred providers
            **params: Provider-specific parameters

        Returns:
            Binary line art image (255 = line, 0 = background)

        Raises:
            RuntimeError: If no providers are available
        """
        context = HookContext(
            extension=cls.name,
            stage="extract",
            method_name="extract",
            timing=HookTiming.BEFORE.value,
            input_data=image,
            params=params,
        )
        cls.execute_hooks("extract", HookTiming.BEFORE.value, context)

        provider = cls.select_provider(provider_preferences)
        logger.info("Using line extraction provider: %s", provider.name)

        result = provider.execute(image, **params)

        context.output_data = result
        context.timing = HookTiming.AFTER.value
        cls.execute_hooks("extract", HookTiming.AFTER.value, context)

        return context.output_data if context.output_data is not None else result
