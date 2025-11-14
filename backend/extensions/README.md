# Extension System - Developer Guide

## Overview

The photo-to-line-vectorizer now uses a modular, extensible architecture inspired by ServerFramework. Each pipeline stage (preprocessing, vectorization, optimization) is implemented as an **extension** that can have multiple **providers**.

## Key Concepts

### Extensions
Extensions represent pipeline stages (e.g., vectorization, optimization). They:
- Are static classes (no instantiation)
- Coordinate multiple providers
- Execute hooks before/after operations
- Auto-discover their providers

### Providers
Providers implement specific algorithms or tools. They:
- Implement one approach to a pipeline stage
- Check availability (dependencies installed?)
- Execute the actual processing
- Are auto-discovered from PRV_*.py files

### Hooks
Hooks allow adding functionality without modifying core code:
- Execute before/after pipeline stages
- Run in priority order (1-100)
- Used for logging, metrics, validation
- Registered via decorator

## Quick Start

### 1. Using an Existing Extension

```python
from extensions.registry import ExtensionRegistry
from extensions.vectorize.EXT_Vectorize import EXT_Vectorize
import numpy as np

# Auto-discover all extensions and providers
ExtensionRegistry.discover()

# Create test image
image = np.zeros((100, 100), dtype=np.uint8)
image[25:75, 25:75] = 255

# Vectorize with provider preferences
svg = EXT_Vectorize.vectorize(
    image,
    provider_preferences=["imagetracer", "potrace"],  # Try imagetracer first
    line_threshold=128,
    qtres=1.0,
    pathomit=8
)
```

### 2. Adding a Hook

```python
from extensions.hooks import hook, HookTiming
from extensions.vectorize.EXT_Vectorize import EXT_Vectorize
import logging

logger = logging.getLogger(__name__)

@hook(EXT_Vectorize, "vectorize", HookTiming.BEFORE, priority=10)
def validate_input_image(context):
    """Validate image before vectorization."""
    if context.input_data is None:
        raise ValueError("Input image cannot be None")
    logger.info("Vectorizing image with shape: %s", context.input_data.shape)

@hook(EXT_Vectorize, "vectorize", HookTiming.AFTER, priority=20)
def log_vectorization_stats(context):
    """Log statistics after vectorization."""
    svg = context.output_data
    path_count = svg.count('<path')
    logger.info("Generated %d SVG paths", path_count)
```

### 3. Creating a New Provider

Just create a new file in the extension directory:

```python
# app/extensions/vectorize/PRV_Vtracer.py
from extensions.base import AbstractProvider
import subprocess
from typing import ClassVar, Any
from numpy.typing import NDArray
import numpy as np

class PRV_Vtracer(AbstractProvider):
    """vtracer vectorization provider (MIT license)."""
    
    name: ClassVar[str] = "vtracer"
    extension: ClassVar[str] = "vectorize"
    description: ClassVar[str] = "vtracer vectorization"
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if vtracer binary is available."""
        try:
            result = subprocess.run(
                ["vtracer", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    @classmethod
    def execute(cls, input_data: NDArray[np.uint8], **params: Any) -> str:
        """Vectorize using vtracer."""
        # Implementation here
        # Call vtracer binary with subprocess
        # Return SVG string
        pass
```

**That's it!** The provider is automatically discovered and can be used immediately:

```python
svg = EXT_Vectorize.vectorize(
    image,
    provider_preferences=["vtracer", "imagetracer"],  # Try vtracer first
    **params
)
```

## Creating a New Extension

### 1. Create Extension Directory

```bash
mkdir -p app/extensions/my_new_stage
touch app/extensions/my_new_stage/__init__.py
```

### 2. Create Extension Class

```python
# app/extensions/my_new_stage/EXT_MyNewStage.py
from typing import ClassVar
from extensions.base import AbstractStaticExtension, HookContext
from extensions.hooks import HookTiming
import logging

logger = logging.getLogger(__name__)

class EXT_MyNewStage(AbstractStaticExtension):
    """My new pipeline stage extension."""
    
    name: ClassVar[str] = "my_new_stage"
    version: ClassVar[str] = "1.0.0"
    description: ClassVar[str] = "Description of what this stage does"
    
    @classmethod
    def process(cls, input_data, provider_preferences=None, **params):
        """Main processing method with hook support."""
        
        # Execute before hooks
        context = HookContext(
            extension=cls.name,
            stage="process",
            method_name="process",
            timing=HookTiming.BEFORE.value,
            input_data=input_data,
            params=params
        )
        cls.execute_hooks("process", HookTiming.BEFORE.value, context)
        
        # Select and execute provider
        provider = cls.select_provider(provider_preferences)
        logger.info("Using provider: %s", provider.name)
        result = provider.execute(input_data, **params)
        
        # Execute after hooks
        context.output_data = result
        context.timing = HookTiming.AFTER.value
        cls.execute_hooks("process", HookTiming.AFTER.value, context)
        
        return context.output_data or result
```

### 3. Create First Provider

```python
# app/extensions/my_new_stage/PRV_MyFirstProvider.py
from extensions.base import AbstractProvider
from typing import ClassVar, Any

class PRV_MyFirstProvider(AbstractProvider):
    """First provider for my new stage."""
    
    name: ClassVar[str] = "my_first_provider"
    extension: ClassVar[str] = "my_new_stage"
    description: ClassVar[str] = "Description"
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if this provider can be used."""
        # Check for dependencies, binaries, etc.
        return True
    
    @classmethod
    def execute(cls, input_data: Any, **params: Any) -> Any:
        """Execute the processing."""
        # Implement your algorithm
        result = input_data  # Process it
        return result
```

### 4. Use Your New Extension

```python
from extensions.registry import ExtensionRegistry
from extensions.my_new_stage.EXT_MyNewStage import EXT_MyNewStage

ExtensionRegistry.discover()

result = EXT_MyNewStage.process(
    my_input_data,
    provider_preferences=["my_first_provider"],
    param1=value1,
    param2=value2
)
```

## Hook Priority Guidelines

Use these priority ranges for consistent behavior:

- **1-20**: Critical validation, security checks
  - Fail fast on invalid input
  - Security validation
  - Required parameter checks

- **21-50**: Business logic, data transformation
  - Data enrichment
  - Format conversion
  - Business rule enforcement

- **51-80**: Logging, metrics, non-critical
  - Performance logging
  - Metrics collection
  - Informational logging

- **81-100**: Cleanup, finalization
  - Cache updates
  - Cleanup operations
  - Final notifications

## Testing Extensions and Providers

### Test Extension Discovery

```python
def test_my_extension_discovered():
    from extensions.registry import ExtensionRegistry
    
    ExtensionRegistry.discover()
    extensions = ExtensionRegistry.list_extensions()
    assert "my_new_stage" in extensions
```

### Test Provider Discovery

```python
def test_my_provider_discovered():
    from extensions.registry import ExtensionRegistry
    
    ExtensionRegistry.discover()
    providers = ExtensionRegistry.get_providers("my_new_stage")
    provider_names = [p.name for p in providers]
    assert "my_first_provider" in provider_names
```

### Test Provider Execution (No Mocks!)

```python
def test_provider_execution():
    """Test real provider with real data."""
    from extensions.my_new_stage.PRV_MyFirstProvider import PRV_MyFirstProvider
    
    # Use real test data
    test_input = create_real_test_data()
    
    # Execute real provider
    result = PRV_MyFirstProvider.execute(test_input, param1=value1)
    
    # Verify real output
    assert result is not None
    assert verify_output_quality(result)
```

### Test Hooks

```python
def test_hooks_execute():
    from extensions.hooks import hook, HookTiming
    from extensions.my_new_stage.EXT_MyNewStage import EXT_MyNewStage
    
    hook_called = {"value": False}
    
    @hook(EXT_MyNewStage, "test", HookTiming.BEFORE, priority=10)
    def test_hook(context):
        hook_called["value"] = True
    
    from extensions.base import HookContext
    context = HookContext(
        extension="my_new_stage",
        stage="test",
        method_name="test",
        timing="before"
    )
    
    EXT_MyNewStage.execute_hooks("test", "before", context)
    assert hook_called["value"]
```

## File Naming Conventions

**IMPORTANT**: Follow these naming patterns for auto-discovery:

- Extension files: `EXT_*.py` (e.g., `EXT_Vectorize.py`)
- Provider files: `PRV_*.py` (e.g., `PRV_ImageTracer.py`)
- Extension class: `EXT_ExtensionName` (matches file name)
- Provider class: `PRV_ProviderName` (matches file name)

## Directory Structure

```
app/extensions/
├── __init__.py              # Framework exports
├── base.py                  # Abstract base classes
├── hooks.py                 # Hook system
├── registry.py              # Auto-discovery
│
├── vectorize/               # Vectorization extension
│   ├── __init__.py
│   ├── EXT_Vectorize.py    # Extension definition
│   ├── PRV_ImageTracer.py  # ImageTracer provider
│   ├── PRV_Potrace.py      # Potrace provider (future)
│   └── PRV_Vtracer.py      # vtracer provider (future)
│
├── optimize/                # Optimization extension (future)
│   ├── __init__.py
│   ├── EXT_Optimize.py
│   └── PRV_Vpype.py
│
└── export/                  # Export extension (future)
    ├── __init__.py
    ├── EXT_Export.py
    ├── PRV_SVG.py
    ├── PRV_HPGL.py
    └── PRV_GCode.py
```

## Benefits

### For Development
- ✅ Add new providers without modifying core code
- ✅ Test providers in isolation
- ✅ Clear separation of concerns
- ✅ Easy to understand and maintain

### For Users
- ✅ Choose preferred algorithms
- ✅ Automatic failover if provider unavailable
- ✅ Consistent API across all providers
- ✅ Easy to extend with custom providers

### For Testing
- ✅ No mocks - test real implementations
- ✅ Each provider independently testable
- ✅ Hook system allows comprehensive integration testing
- ✅ Parallel test execution

## Common Patterns

### Provider Selection with Fallback

```python
# Try providers in order until one works
svg = EXT_Vectorize.vectorize(
    image,
    provider_preferences=["vtracer", "imagetracer", "potrace"]
)
```

### Conditional Provider Parameters

```python
@classmethod
def execute(cls, input_data, **params):
    # Extract provider-specific params with defaults
    quality = params.get("quality", "high")
    timeout = params.get("timeout", 60)
    
    # Your implementation
    pass
```

### Hook-based Metrics Collection

```python
metrics = {}

@hook(EXT_Vectorize, "vectorize", HookTiming.BEFORE, priority=1)
def start_timer(context):
    context.metadata["start_time"] = time.time()

@hook(EXT_Vectorize, "vectorize", HookTiming.AFTER, priority=99)
def collect_metrics(context):
    duration = time.time() - context.metadata["start_time"]
    metrics["vectorize_duration"] = duration
    metrics["path_count"] = context.output_data.count("<path")
```

## Troubleshooting

### Provider Not Discovered

1. Check file naming: Must be `PRV_*.py`
2. Check class name: Must match file (e.g., `PRV_MyProvider`)
3. Check `extension` attribute: Must match parent extension name
4. Check inheritance: Must inherit from `AbstractProvider`

### Extension Not Discovered

1. Check file naming: Must be `EXT_*.py`
2. Check class name: Must match file (e.g., `EXT_MyExtension`)
3. Check inheritance: Must inherit from `AbstractStaticExtension`
4. Check `name` attribute: Must be set

### Hooks Not Executing

1. Check hook registration: Decorator must be `@hook(...)`
2. Check stage name: Must match what's passed to `execute_hooks()`
3. Check timing: BEFORE or AFTER must match
4. Check extension class: Must match the extension you're using

## Next Steps

1. **Study existing extensions**: Look at `extensions/vectorize/` for examples
2. **Run tests**: `pytest tests/test_extension_system.py -v`
3. **Create your own**: Follow the patterns above
4. **Add hooks**: Enhance pipeline with cross-cutting concerns
5. **Contribute**: Add new providers for existing extensions

## Resources

- **Architecture Doc**: `/backend/ARCHITECTURE.md`
- **Implementation Plan**: `/backend/docs/implementation-plan.md`
- **Completion Summary**: `/EXTENSION_SYSTEM_COMPLETE.md`
- **Tests**: `/backend/tests/test_extension_system.py`

---

**Happy extending!** 🚀
