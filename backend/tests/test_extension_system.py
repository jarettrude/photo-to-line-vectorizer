"""
Tests for extension system infrastructure.

Verifies that the extension system, hooks, and auto-discovery work correctly.
"""

import logging

import numpy as np
import pytest

logger = logging.getLogger(__name__)


def test_extension_registry_discovery():
    """Test that extension registry discovers extensions."""
    from extensions.registry import ExtensionRegistry

    # Discover extensions
    ExtensionRegistry.discover()

    # Check that vectorize extension was discovered
    extensions = ExtensionRegistry.list_extensions()
    assert "vectorize" in extensions, "Vectorize extension should be discovered"

    # Get the extension
    ext = ExtensionRegistry.get_extension("vectorize")
    assert ext is not None, "Should be able to get vectorize extension"
    assert ext.name == "vectorize"


def test_provider_discovery():
    """Test that providers are auto-discovered for extensions."""
    from extensions.registry import ExtensionRegistry

    ExtensionRegistry.discover()

    # Get providers for vectorize extension
    providers = ExtensionRegistry.get_providers("vectorize")
    assert len(providers) > 0, "Should discover at least one provider"

    # Check that ImageTracer provider was discovered
    provider_names = [p.name for p in providers]
    assert "imagetracer" in provider_names, "ImageTracer provider should be discovered"


def test_provider_availability():
    """Test provider availability checking."""
    from extensions.registry import ExtensionRegistry

    ExtensionRegistry.discover()

    providers = ExtensionRegistry.get_providers("vectorize")
    imagetracer = next(p for p in providers if p.name == "imagetracer")

    # Availability depends on Node.js installation
    # This test just verifies the method exists and returns a boolean
    available = imagetracer.is_available()
    assert isinstance(available, bool)


def test_hook_registration():
    """Test that hooks can be registered and executed."""
    from extensions.hooks import HookTiming, hook
    from extensions.registry import ExtensionRegistry
    from extensions.vectorize.EXT_Vectorize import EXT_Vectorize

    ExtensionRegistry.discover()

    # Track hook execution
    hook_called = {"before": False, "after": False}

    @hook(EXT_Vectorize, "test_stage", HookTiming.BEFORE, priority=10)
    def test_before_hook(context):
        hook_called["before"] = True
        logger.info("Before hook called")

    @hook(EXT_Vectorize, "test_stage", HookTiming.AFTER, priority=20)
    def test_after_hook(context):
        hook_called["after"] = True
        logger.info("After hook called")

    # Create a test context
    from extensions.base import HookContext

    context = HookContext(
        extension="vectorize",
        stage="test_stage",
        method_name="test",
        timing="before",
    )

    # Execute hooks
    EXT_Vectorize.execute_hooks("test_stage", "before", context)
    assert hook_called["before"], "Before hook should have been called"

    context.timing = "after"
    EXT_Vectorize.execute_hooks("test_stage", "after", context)
    assert hook_called["after"], "After hook should have been called"


@pytest.mark.integration
@pytest.mark.requires_imagetracer
def test_vectorize_extension_end_to_end():
    """
    Test complete vectorization through extension system.

    Requires Node.js and imagetracerjs to be installed.
    """
    from extensions.registry import ExtensionRegistry
    from extensions.vectorize.EXT_Vectorize import EXT_Vectorize

    ExtensionRegistry.discover()

    # Create a simple test image (white square on black background)
    test_image = np.zeros((100, 100), dtype=np.uint8)
    test_image[25:75, 25:75] = 255

    # Vectorize using extension
    try:
        svg = EXT_Vectorize.vectorize(
            test_image,
            provider_preferences=["imagetracer"],
            line_threshold=128,
            qtres=1.0,
            pathomit=8,
        )

        # Verify SVG output
        assert svg.startswith("<?xml") or svg.startswith("<svg")
        assert "<path" in svg
        logger.info("Vectorization successful, SVG generated")

    except RuntimeError as e:
        if "No available providers" in str(e):
            pytest.skip("ImageTracerJS not available")
        raise


def test_hook_priority_ordering():
    """Test that hooks execute in priority order."""
    from extensions.hooks import HookTiming, hook
    from extensions.registry import ExtensionRegistry
    from extensions.vectorize.EXT_Vectorize import EXT_Vectorize

    ExtensionRegistry.discover()

    execution_order = []

    @hook(EXT_Vectorize, "priority_test", HookTiming.BEFORE, priority=50)
    def medium_priority(context):
        execution_order.append("medium")

    @hook(EXT_Vectorize, "priority_test", HookTiming.BEFORE, priority=10)
    def high_priority(context):
        execution_order.append("high")

    @hook(EXT_Vectorize, "priority_test", HookTiming.BEFORE, priority=90)
    def low_priority(context):
        execution_order.append("low")

    from extensions.base import HookContext

    context = HookContext(
        extension="vectorize",
        stage="priority_test",
        method_name="test",
        timing="before",
    )

    EXT_Vectorize.execute_hooks("priority_test", "before", context)

    # Verify execution order: high (10) -> medium (50) -> low (90)
    assert execution_order == [
        "high",
        "medium",
        "low",
    ], "Hooks should execute in priority order"
