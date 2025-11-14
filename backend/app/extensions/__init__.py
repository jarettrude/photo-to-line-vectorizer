"""
Extension system for modular pipeline architecture.

Provides abstract base classes and infrastructure for building
extensible processing pipelines with hook support and provider rotation.
"""

from extensions.base import AbstractProvider, AbstractStaticExtension, HookContext
from extensions.hooks import HookTiming, hook
from extensions.registry import ExtensionRegistry

__all__ = [
    "AbstractStaticExtension",
    "AbstractProvider",
    "HookContext",
    "HookTiming",
    "hook",
    "ExtensionRegistry",
]
