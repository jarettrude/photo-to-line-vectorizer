"""
Export extension for various plotter formats.

Provides export to SVG, HPGL, and G-code formats through
multiple provider implementations.
"""

import logging
from pathlib import Path
from typing import Any, ClassVar

from extensions.base import AbstractStaticExtension, HookContext
from extensions.hooks import HookTiming

logger = logging.getLogger(__name__)


class EXT_Export(AbstractStaticExtension):
    """
    Export extension for plotter formats.

    Coordinates multiple export providers and provides
    a unified interface for exporting to various formats.
    """

    name: ClassVar[str] = "export"
    version: ClassVar[str] = "1.0.0"
    description: ClassVar[str] = "Export to SVG, HPGL, G-code formats"

    @classmethod
    def export(
        cls,
        svg_string: str,
        output_path: Path,
        export_format: str = "svg",
        provider_preferences: list[str] | None = None,
        **params: Any,
    ) -> None:
        """
        Export SVG to specified format.

        Args:
            svg_string: Input SVG string
            output_path: Output file path
            export_format: Export format (svg, hpgl, gcode)
            provider_preferences: Ordered list of preferred providers
            **params: Format-specific parameters

        Raises:
            RuntimeError: If no providers are available
            ValueError: If format is unsupported
        """
        context = HookContext(
            extension=cls.name,
            stage="export",
            method_name="export",
            timing=HookTiming.BEFORE.value,
            input_data=svg_string,
            params={
                "output_path": output_path,
                "export_format": export_format,
                **params,
            },
        )
        cls.execute_hooks("export", HookTiming.BEFORE.value, context)

        provider = cls.select_provider(provider_preferences)
        logger.info("Using export provider: %s", provider.name)

        provider.execute(
            svg_string,
            output_path=output_path,
            export_format=export_format,
            **params,
        )

        context.timing = HookTiming.AFTER.value
        cls.execute_hooks("export", HookTiming.AFTER.value, context)
