"""
Vectorization extension.

Converts raster line art to SVG vector paths using various providers.
Supports multiple vectorization engines with automatic failover.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

from extensions.base import AbstractStaticExtension

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


logger = logging.getLogger(__name__)


class EXT_Vectorize(AbstractStaticExtension):
    """
    Vectorization extension.

    Converts raster edge maps to SVG paths using various providers:
    - ImageTracerJS (public domain)
    - Potrace (GPL-isolated)
    - vtracer (MIT - future implementation)
    """

    name: ClassVar[str] = "vectorize"
    version: ClassVar[str] = "1.0.0"
    description: ClassVar[str] = "Raster to vector conversion"

    @classmethod
    def vectorize(
        cls,
        image: NDArray[np.uint8],
        provider_preferences: list[str] | None = None,
        **params,
    ) -> str:
        """
        Vectorize raster image to SVG.

        Args:
            image: Input grayscale or RGB image
            provider_preferences: Ordered list of preferred providers
            **params: Provider-specific parameters

        Returns:
            SVG string

        Raises:
            RuntimeError: If no available providers
        """
        from extensions.base import HookContext
        from extensions.hooks import HookTiming

        # Execute before hooks
        context = HookContext(
            extension=cls.name,
            stage="vectorize",
            method_name="vectorize",
            timing=HookTiming.BEFORE.value,
            input_data=image,
            params=params,
        )
        cls.execute_hooks("vectorize", HookTiming.BEFORE.value, context)

        # Select provider
        provider = cls.select_provider(provider_preferences)
        logger.info("Using provider: %s", provider.name)

        # Execute vectorization
        svg_content = provider.execute(image, **params)

        # Execute after hooks
        context.output_data = svg_content
        context.timing = HookTiming.AFTER.value
        cls.execute_hooks("vectorize", HookTiming.AFTER.value, context)

        return context.output_data if context.output_data is not None else svg_content
