"""
Extension and provider registry with auto-discovery.

Scans the extensions directory and automatically discovers all
extensions (EXT_*.py) and their providers (PRV_*.py).
"""

from __future__ import annotations

import importlib.util
import inspect
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from extensions.base import AbstractProvider, AbstractStaticExtension

logger = logging.getLogger(__name__)


class ExtensionRegistry:
    """
    Registry for auto-discovering and managing extensions and providers.

    Scans the extensions directory for:
    - EXT_*.py files containing AbstractStaticExtension subclasses
    - PRV_*.py files containing AbstractProvider subclasses
    """

    _extensions: ClassVar[dict[str, type[AbstractStaticExtension]]] = {}
    _providers: ClassVar[dict[str, list[type[AbstractProvider]]]] = {}
    _discovered: ClassVar[bool] = False

    @classmethod
    def discover(cls, extensions_dir: Path | None = None) -> None:
        """
        Discover all extensions and providers.

        Args:
            extensions_dir: Root extensions directory (defaults to app/extensions)
        """
        if cls._discovered:
            return

        if extensions_dir is None:
            # Default to app/extensions directory
            extensions_dir = Path(__file__).parent

        logger.info(f"Discovering extensions in {extensions_dir}")

        # Scan for extension directories
        for ext_dir in extensions_dir.iterdir():
            if not ext_dir.is_dir() or ext_dir.name.startswith("_"):
                continue

            # Look for EXT_*.py file
            ext_files = list(ext_dir.glob("EXT_*.py"))
            if ext_files:
                cls._discover_extension(ext_files[0], ext_dir)

        cls._discovered = True
        logger.info(
            f"Discovered {len(cls._extensions)} extensions "
            f"with {sum(len(p) for p in cls._providers.values())} total providers"
        )

    @classmethod
    def _discover_extension(cls, ext_file: Path, ext_dir: Path) -> None:
        """
        Discover an extension and its providers.

        Args:
            ext_file: Path to EXT_*.py file
            ext_dir: Extension directory
        """
        from extensions.base import AbstractStaticExtension

        # Load extension module
        module = cls._load_module(ext_file)
        if module is None:
            return

        # Find AbstractStaticExtension subclasses
        for _name, obj in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(obj, AbstractStaticExtension)
                and obj is not AbstractStaticExtension
            ):
                cls._extensions[obj.name] = obj
                logger.debug("Discovered extension: %s", obj.name)

                # Discover providers for this extension
                providers = cls._discover_providers(ext_dir, obj.name)
                if providers:
                    cls._providers[obj.name] = providers
                    obj._providers = providers  # Intentionally setting class attribute
                    logger.debug(
                        "  Found %d providers for %s", len(providers), obj.name
                    )

    @classmethod
    def _discover_providers(
        cls, ext_dir: Path, ext_name: str
    ) -> list[type[AbstractProvider]]:
        """
        Discover all providers in an extension directory.

        Args:
            ext_dir: Extension directory
            ext_name: Extension name

        Returns:
            List of discovered provider classes
        """
        from extensions.base import AbstractProvider

        providers: list[type[AbstractProvider]] = []

        for prv_file in ext_dir.glob("PRV_*.py"):
            module = cls._load_module(prv_file)
            if module is None:
                continue

            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(obj, AbstractProvider)
                    and obj is not AbstractProvider
                    and obj.extension == ext_name
                ):
                    providers.append(obj)
                    logger.debug(f"    Provider: {obj.name}")

        return providers

    @classmethod
    def _load_module(cls, file_path: Path) -> Any:
        """
        Load a Python module from file path.

        Args:
            file_path: Path to .py file

        Returns:
            Loaded module or None if loading fails
        """
        try:
            spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
            if spec is None or spec.loader is None:
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module

        except Exception:
            logger.exception(f"Failed to load module: {file_path}")
            return None

    @classmethod
    def get_extension(cls, name: str) -> type[AbstractStaticExtension] | None:
        """
        Get extension by name.

        Args:
            name: Extension name

        Returns:
            Extension class or None if not found
        """
        if not cls._discovered:
            cls.discover()
        return cls._extensions.get(name)

    @classmethod
    def get_providers(cls, extension_name: str) -> list[type[AbstractProvider]]:
        """
        Get all providers for an extension.

        Args:
            extension_name: Extension name

        Returns:
            List of provider classes
        """
        if not cls._discovered:
            cls.discover()
        return cls._providers.get(extension_name, [])

    @classmethod
    def list_extensions(cls) -> list[str]:
        """
        List all discovered extension names.

        Returns:
            List of extension names
        """
        if not cls._discovered:
            cls.discover()
        return list(cls._extensions.keys())
