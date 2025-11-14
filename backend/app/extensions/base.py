"""
Abstract base classes for extensions and providers.

Defines the core interfaces for the extension system:
- AbstractStaticExtension: Base class for all extensions
- AbstractProvider: Base class for all providers
- HookContext: Context passed to hook handlers
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass
class HookContext:
    """
    Context passed to hook handlers.

    Contains all information about the current execution context,
    including input data, output data, parameters, and metadata.
    """

    extension: str
    stage: str
    method_name: str
    timing: str  # "before" or "after"
    input_data: Any = None
    output_data: Any = None
    params: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def set_output(self, data: Any) -> None:
        """Set output data (for after hooks to modify results)."""
        self.output_data = data


class AbstractStaticExtension(ABC):
    """
    Base class for all extensions.

    Extensions are static classes that coordinate providers and hooks
    for a specific pipeline stage. They use auto-discovery to find
    their providers and manage hook execution.
    """

    name: ClassVar[str]
    version: ClassVar[str] = "1.0.0"
    description: ClassVar[str] = ""

    # Auto-discovered providers (populated by registry)
    _providers: ClassVar[list[type[AbstractProvider]]] = []

    # Registered hooks (populated by hook decorator)
    _hooks: ClassVar[dict[tuple[str, str], list[tuple[int, Callable]]]] = {}

    @classmethod
    def get_providers(cls) -> list[type[AbstractProvider]]:
        """
        Return all discovered providers for this extension.

        Providers are auto-discovered from PRV_*.py files in the
        extension's directory. This method queries the registry to
        ensure up-to-date provider lists.
        """
        # Import here to avoid circular dependency
        from extensions.registry import ExtensionRegistry

        # Ensure discovery has run
        if not ExtensionRegistry._discovered:
            ExtensionRegistry.discover()

        # Query registry for providers
        return ExtensionRegistry.get_providers(cls.name)

    @classmethod
    def select_provider(
        cls, preferences: list[str] | None = None
    ) -> type[AbstractProvider]:
        """
        Select best available provider based on preferences.

        Args:
            preferences: Ordered list of preferred provider names

        Returns:
            First available provider matching preferences

        Raises:
            RuntimeError: If no available providers found
        """
        providers = cls.get_providers()

        if preferences:
            for pref in preferences:
                provider = next((p for p in providers if p.name == pref), None)
                if provider and provider.is_available():
                    return provider

        # Fallback to first available provider
        for provider in providers:
            if provider.is_available():
                return provider

        msg = f"No available providers for extension '{cls.name}'"
        raise RuntimeError(msg)

    @classmethod
    def execute_hooks(cls, stage: str, timing: str, context: HookContext) -> None:
        """
        Execute all registered hooks for a given stage and timing.

        Hooks are executed in priority order (lower priority first).

        Args:
            stage: Hook stage name
            timing: "before" or "after"
            context: Hook execution context
        """
        hook_key = (stage, timing)
        if hook_key not in cls._hooks:
            return

        # Sort by priority (lower priority executes first)
        hooks = sorted(cls._hooks[hook_key], key=lambda x: x[0])

        for _priority, hook_func in hooks:
            hook_func(context)


class AbstractProvider(ABC):
    """
    Base class for all providers.

    Providers implement specific algorithms or tools for a pipeline stage.
    Multiple providers can exist for the same extension, allowing runtime
    selection based on availability and preferences.
    """

    name: ClassVar[str]
    extension: ClassVar[str]  # Parent extension name
    description: ClassVar[str] = ""

    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        """
        Check if provider is available.

        Returns:
            True if provider can be used (dependencies installed, etc.)
        """

    @classmethod
    @abstractmethod
    def execute(cls, input_data: Any, **params: Any) -> Any:
        """
        Execute provider-specific processing.

        Args:
            input_data: Input data for processing
            **params: Provider-specific parameters

        Returns:
            Processed output data
        """
