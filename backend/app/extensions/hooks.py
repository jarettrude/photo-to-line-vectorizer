"""
Hook system for cross-cutting concerns.

Provides decorator-based hook registration with priority-based
execution order and before/after timing support.
"""

from __future__ import annotations

from enum import Enum
from functools import wraps
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from extensions.base import AbstractStaticExtension, HookContext


class HookTiming(str, Enum):
    """Hook execution timing."""

    BEFORE = "before"
    AFTER = "after"


def hook(
    extension_class: type[AbstractStaticExtension],
    stage: str,
    timing: HookTiming,
    priority: int = 50,
) -> Callable[[Callable], Callable]:
    """
    Decorator to register a hook for an extension stage.

    Hooks execute in priority order (lower priority = earlier execution).
    Priority ranges:
        1-20:   Critical validation, security checks
        21-50:  Business logic, data transformation
        51-80:  Logging, metrics, non-critical
        81-100: Cleanup, finalization

    Args:
        extension_class: Extension class to register hook for
        stage: Stage name (e.g., "vectorize", "optimize")
        timing: When to execute (BEFORE or AFTER)
        priority: Execution priority (lower = earlier)

    Returns:
        Decorated function

    Example:
        @hook(EXT_Vectorize, "vectorize", HookTiming.BEFORE, priority=10)
        def validate_input(context: HookContext):
            if context.input_data is None:
                raise ValueError("Input cannot be None")
    """

    def decorator(func: Callable[[HookContext], Any]) -> Callable:
        hook_key = (stage, timing.value)

        # Initialize hooks dict if needed
        if not hasattr(extension_class, "_hooks"):
            extension_class._hooks = {}

        if hook_key not in extension_class._hooks:
            extension_class._hooks[hook_key] = []

        # Register hook with priority
        extension_class._hooks[hook_key].append((priority, func))

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return wrapper

    return decorator
