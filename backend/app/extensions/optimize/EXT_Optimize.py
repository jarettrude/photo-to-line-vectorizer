"""
SVG path optimization extension.

Provides path optimization, merging, simplification, and canvas scaling
through multiple provider implementations.
"""

import logging
from typing import Any, ClassVar

from extensions.base import AbstractStaticExtension, HookContext
from extensions.hooks import HookTiming

logger = logging.getLogger(__name__)


class EXT_Optimize(AbstractStaticExtension):
    """
    SVG path optimization extension.

    Coordinates multiple optimization providers and provides
    a unified interface for SVG path optimization operations.
    """

    name: ClassVar[str] = "optimize"
    version: ClassVar[str] = "1.0.0"
    description: ClassVar[str] = "SVG path optimization and canvas scaling"

    @classmethod
    def optimize(
        cls,
        svg_string: str,
        canvas_width_mm: float,
        canvas_height_mm: float,
        provider_preferences: list[str] | None = None,
        **params: Any,
    ) -> str:
        """
        Optimize SVG paths with full pipeline.

        Args:
            svg_string: Input SVG
            canvas_width_mm: Target canvas width in mm
            canvas_height_mm: Target canvas height in mm
            provider_preferences: Ordered list of preferred providers
            **params: Provider-specific parameters

        Returns:
            Optimized SVG string

        Raises:
            RuntimeError: If no providers are available
        """
        context = HookContext(
            extension=cls.name,
            stage="optimize",
            method_name="optimize",
            timing=HookTiming.BEFORE.value,
            input_data=svg_string,
            params={
                "canvas_width_mm": canvas_width_mm,
                "canvas_height_mm": canvas_height_mm,
                **params,
            },
        )
        cls.execute_hooks("optimize", HookTiming.BEFORE.value, context)

        provider = cls.select_provider(provider_preferences)
        logger.info("Using optimization provider: %s", provider.name)

        result = provider.execute(
            svg_string,
            canvas_width_mm=canvas_width_mm,
            canvas_height_mm=canvas_height_mm,
            **params,
        )

        context.output_data = result
        context.timing = HookTiming.AFTER.value
        cls.execute_hooks("optimize", HookTiming.AFTER.value, context)

        return context.output_data if context.output_data is not None else result

    @classmethod
    def get_stats(
        cls,
        svg_string: str,
        provider_preferences: list[str] | None = None,
    ) -> dict[str, float | int | tuple[float, float, float, float] | None]:
        """
        Get statistics about SVG paths.

        Args:
            svg_string: Input SVG
            provider_preferences: Ordered list of preferred providers

        Returns:
            Dictionary with path statistics
        """
        provider = cls.select_provider(provider_preferences)
        return provider.get_stats(svg_string)

    @classmethod
    def scale_to_canvas(
        cls,
        svg_string: str,
        canvas_width_mm: float,
        canvas_height_mm: float,
        provider_preferences: list[str] | None = None,
        **params: Any,
    ) -> str:
        """
        Scale SVG to fit canvas dimensions.

        Args:
            svg_string: Input SVG
            canvas_width_mm: Target width in mm
            canvas_height_mm: Target height in mm
            provider_preferences: Ordered list of preferred providers
            **params: Provider-specific parameters

        Returns:
            Scaled SVG string
        """
        provider = cls.select_provider(provider_preferences)
        return provider.scale_to_canvas(
            svg_string,
            canvas_width_mm=canvas_width_mm,
            canvas_height_mm=canvas_height_mm,
            **params,
        )
