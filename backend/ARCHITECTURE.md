# Photo-to-Line-Vectorizer Architecture

**Inspired by ServerFramework's extensibility patterns**

## Overview

This FastAPI-based application converts photos to line art using an extensible, modular pipeline architecture. Each stage (preprocessing, line extraction, vectorization, optimization) is plugin-based, allowing new implementations to be added without modifying core code.

## Core Architecture Patterns (from ServerFramework)

### Extension System
- **Static Classes**: Extensions implemented as static/abstract classes
- **Auto-Discovery**: Filesystem-based provider discovery
- **Hook System**: Before/after hooks for cross-cutting concerns
- **No Instantiation**: All functionality through class methods and static properties

### Provider System
- **Multiple Implementations**: Each pipeline stage can have multiple providers
- **Automatic Failover**: Rotation system for provider selection
- **Isolation**: Each provider is self-contained and testable
- **Configuration**: Environment-based provider configuration

### Testing Philosophy
- **No Mocks**: Real implementations with isolated environments
- **Parallel Execution**: Tests run concurrently with isolation
- **Abstract Base Classes**: Consistent test patterns across all layers
- **90%+ Coverage**: Comprehensive testing at all levels

## Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     API Layer (FastAPI)                      │
│  - REST endpoints for upload, process, status                │
│  - WebSocket for real-time progress                          │
│  - Pydantic models for request/response validation           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Pipeline Orchestration                     │
│  - PhotoToLineProcessor (main coordinator)                   │
│  - Hook execution (before/after each stage)                  │
│  - Progress tracking and WebSocket notifications             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Extension Layer (EXT_*)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ EXT_Preprocess│  │EXT_Vectorize │  │ EXT_Optimize │      │
│  │              │  │              │  │              │      │
│  │  Providers:  │  │  Providers:  │  │  Providers:  │      │
│  │  - Classical │  │  - ImageTracer│  │  - Vpype     │      │
│  │  - U2Net     │  │  - Potrace   │  │  - Custom    │      │
│  │              │  │  - vtracer   │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Provider Layer (PRV_*)                     │
│  - ImageTracerVectorizer (public domain)                     │
│  - PotraceVectorizer (GPL-isolated subprocess)               │
│  - VtracerVectorizer (MIT - future implementation)           │
│  - ClassicalCVProcessor                                      │
│  - U2NetProcessor                                            │
│  - VpypeOptimizer                                            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Utility Layer (utils/)                     │
│  - Device management (CUDA/MPS/CPU detection)                │
│  - Job storage and tracking                                  │
│  - Image format handling (HEIC/HEIF support)                 │
└─────────────────────────────────────────────────────────────┘
```

## Extension System Design

### Abstract Extension Pattern

```python
from abc import ABC, abstractmethod
from typing import ClassVar, Dict, Any, Set, List, Type

class AbstractStaticExtension(ABC):
    """Base class for all extensions."""
    
    name: ClassVar[str]
    version: ClassVar[str]
    description: ClassVar[str]
    
    # Auto-discovered providers
    _providers: ClassVar[List[Type]] = []
    
    # Hook registry
    _hooks: ClassVar[Dict[str, List[callable]]] = {}
    
    @classmethod
    @abstractmethod
    def get_providers(cls) -> List[Type]:
        """Return all discovered providers for this extension."""
        pass
    
    @classmethod
    def execute_hooks(cls, hook_name: str, context: Dict[str, Any]) -> None:
        """Execute all registered hooks for a given hook point."""
        pass
```

### Provider Pattern

```python
class AbstractProvider(ABC):
    """Base class for all providers."""
    
    name: ClassVar[str]
    extension: ClassVar[str]  # Parent extension name
    
    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        """Check if provider is available (dependencies installed)."""
        pass
    
    @classmethod
    @abstractmethod
    def execute(cls, input_data: Any, **params) -> Any:
        """Execute provider-specific processing."""
        pass
```

## Pipeline Stages as Extensions

### 1. EXT_Preprocess (Background Removal & Enhancement)

**Responsibilities:**
- Load image from various formats (JPEG, PNG, HEIC, etc.)
- Resize if needed
- Isolate subject from background (optional)
- Enhance contrast (optional)

**Providers:**
- `PRV_ClassicalCV_Preprocess`: Basic OpenCV preprocessing
- `PRV_U2Net_Preprocess`: ML-based subject isolation
- `PRV_RemBG_Preprocess`: Alternative ML model (future)

**Hook Points:**
- `before_load`: Validate file format
- `after_load`: Log image dimensions
- `before_isolate_subject`: Prepare for segmentation
- `after_isolate_subject`: Validate mask quality
- `after_preprocess`: Final validation

### 2. EXT_LineExtraction (Edge Detection & Line Art)

**Responsibilities:**
- Extract edges/lines from preprocessed image
- Support classical CV and ML approaches
- Generate clean binary edge map

**Providers:**
- `PRV_CannyEdge_LineExtraction`: Canny edge detection
- `PRV_HED_LineExtraction`: ML-based edge detection (future)
- `PRV_ControlNet_LineExtraction`: ControlNet LineArt (future)

**Hook Points:**
- `before_extract`: Log extraction method
- `after_extract`: Validate edge quality
- `before_hatching`: Prepare for hatching
- `after_hatching`: Verify hatching coverage

### 3. EXT_Vectorize (Raster to Vector Conversion)

**Responsibilities:**
- Convert raster edge map to SVG paths
- Support multiple vectorization engines
- Generate optimized path structures

**Providers:**
- `PRV_ImageTracer_Vectorize`: ImageTracerJS (public domain)
- `PRV_Potrace_Vectorize`: Potrace (GPL-isolated)
- `PRV_Vtracer_Vectorize`: vtracer (MIT - future)
- `PRV_AutoTrace_Vectorize`: autotrace (future)

**Hook Points:**
- `before_vectorize`: Log vectorizer selection
- `after_vectorize`: Parse SVG statistics
- `before_path_generation`: Validate bitmap
- `after_path_generation`: Count paths

### 4. EXT_Optimize (Path Optimization)

**Responsibilities:**
- Merge nearby paths
- Simplify path geometry
- Sort paths for plotting efficiency
- Deduplicate paths
- Fit to canvas dimensions

**Providers:**
- `PRV_Vpype_Optimize`: vpype-based optimization
- `PRV_Custom_Optimize`: Custom optimization logic (future)
- `PRV_Clipper_Optimize`: Clipper library (future)

**Hook Points:**
- `before_optimize`: Log initial path count
- `after_linemerge`: Log merge statistics
- `after_simplify`: Log simplification ratio
- `after_linesort`: Log path ordering
- `after_optimize`: Final statistics

### 5. EXT_Export (Format Conversion)

**Responsibilities:**
- Export to various formats (SVG, HPGL, G-code)
- Layer management for multi-color output
- Per-format optimization

**Providers:**
- `PRV_SVG_Export`: SVG export
- `PRV_HPGL_Export`: HPGL plotter format
- `PRV_GCode_Export`: CNC G-code format

**Hook Points:**
- `before_export`: Validate output format
- `after_export`: Verify file integrity

## Hook System Architecture

### Hook Registration

```python
from enum import Enum
from typing import Callable, Dict, Any
from dataclasses import dataclass

class HookTiming(Enum):
    BEFORE = "before"
    AFTER = "after"

@dataclass
class HookContext:
    """Context passed to hook handlers."""
    extension: str
    stage: str
    method_name: str
    timing: HookTiming
    input_data: Any
    output_data: Any = None
    params: Dict[str, Any] = None
    metadata: Dict[str, Any] = None

def hook(extension: str, stage: str, timing: HookTiming, priority: int = 50):
    """Decorator to register hooks."""
    def decorator(func: Callable):
        # Register hook in global registry
        HookRegistry.register(extension, stage, timing, priority, func)
        return func
    return decorator

# Usage example:
@hook("EXT_Vectorize", "vectorize", HookTiming.BEFORE, priority=10)
def validate_bitmap(context: HookContext):
    """Validate bitmap before vectorization."""
    if context.input_data is None:
        raise ValueError("Input bitmap cannot be None")
```

### Hook Execution

Hooks execute in priority order (lower priority = earlier execution):

```
BEFORE hooks (priority 1-100):
  1-20:   Critical validation, security checks
  21-50:  Business logic, data transformation
  51-80:  Logging, metrics, non-critical
  81-100: Cleanup, finalization

Original method executes here

AFTER hooks (priority 1-100):
  1-20:   Critical post-processing
  21-50:  Result transformation
  51-80:  Logging, notifications
  81-100: Cleanup, cache updates
```

## Provider Discovery System

### File Structure

```
app/
├── extensions/
│   ├── __init__.py
│   ├── preprocess/
│   │   ├── __init__.py
│   │   ├── EXT_Preprocess.py          # Extension definition
│   │   ├── PRV_ClassicalCV.py         # Classical CV provider
│   │   └── PRV_U2Net.py               # ML-based provider
│   │
│   ├── line_extraction/
│   │   ├── __init__.py
│   │   ├── EXT_LineExtraction.py
│   │   ├── PRV_Canny.py
│   │   └── PRV_HED.py
│   │
│   ├── vectorize/
│   │   ├── __init__.py
│   │   ├── EXT_Vectorize.py
│   │   ├── PRV_ImageTracer.py
│   │   ├── PRV_Potrace.py
│   │   └── PRV_Vtracer.py
│   │
│   ├── optimize/
│   │   ├── __init__.py
│   │   ├── EXT_Optimize.py
│   │   └── PRV_Vpype.py
│   │
│   └── export/
│       ├── __init__.py
│       ├── EXT_Export.py
│       ├── PRV_SVG.py
│       ├── PRV_HPGL.py
│       └── PRV_GCode.py
│
└── pipeline/
    ├── __init__.py
    └── processor.py                   # Main orchestrator
```

### Auto-Discovery Implementation

```python
import importlib
import inspect
from pathlib import Path
from typing import List, Type

class ExtensionRegistry:
    """Auto-discover and register extensions and providers."""
    
    _extensions: Dict[str, Type[AbstractStaticExtension]] = {}
    _providers: Dict[str, List[Type[AbstractProvider]]] = {}
    
    @classmethod
    def discover_extensions(cls, extensions_dir: Path) -> None:
        """Scan extensions directory and register all extensions."""
        for ext_dir in extensions_dir.iterdir():
            if not ext_dir.is_dir() or ext_dir.name.startswith('_'):
                continue
            
            # Load EXT_*.py file
            ext_file = ext_dir / f"EXT_{ext_dir.name.title()}.py"
            if ext_file.exists():
                module = cls._load_module(ext_file)
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, AbstractStaticExtension) and obj != AbstractStaticExtension:
                        cls._extensions[obj.name] = obj
            
            # Discover providers in PRV_*.py files
            cls._discover_providers(ext_dir, ext_dir.name)
    
    @classmethod
    def _discover_providers(cls, ext_dir: Path, ext_name: str) -> None:
        """Discover all providers for an extension."""
        providers = []
        for prv_file in ext_dir.glob("PRV_*.py"):
            module = cls._load_module(prv_file)
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, AbstractProvider) and obj != AbstractProvider:
                    providers.append(obj)
        
        cls._providers[ext_name] = providers
```

## Testing Architecture

### No-Mock Testing Philosophy

Every test uses real implementations with proper isolation:

```python
import pytest
from pathlib import Path

class AbstractProcessorTest:
    """Abstract base class for processor tests."""
    
    @pytest.fixture
    def test_image(self, tmp_path: Path) -> Path:
        """Create test image in isolated directory."""
        # Generate real test image, not a mock
        pass
    
    @pytest.fixture
    def isolated_temp_dir(self, tmp_path: Path) -> Path:
        """Provide isolated temp directory for test."""
        return tmp_path
    
    def test_complete_pipeline(self, test_image: Path):
        """Test complete pipeline with real data."""
        # No mocks - use actual implementations
        processor = PhotoToLineProcessor()
        result = processor.process(test_image, ProcessingParams(...))
        
        # Verify real output
        assert result.svg_content.startswith('<?xml')
        assert result.stats['path_count'] > 0
```

### Test Markers

```python
# pytest.ini configuration
pytest_markers = [
    "unit: Unit tests (fast, focused, narrow scope)",
    "integration: Integration tests (real HTTP endpoints and pipeline)",
    "real_images: Tests using real test image files",
    "slow: Slow tests (long-running, e.g. larger images)",
    "requires_ml: Tests requiring ML model weights",
    "requires_imagetracer: Tests requiring imagetracerjs npm package",
    "requires_potrace: Tests requiring Potrace binary",
]

# Run specific test categories:
# pytest -m unit                      # Fast unit tests
# pytest -m integration               # Integration tests
# pytest -m "integration and real_images"  # Integration with real images
# pytest -m "not slow"                # Skip slow tests
```

### Test Structure

```
tests/
├── __init__.py
├── conftest.py                       # Shared fixtures
├── abstract_tests.py                 # Abstract base classes
│
├── unit/                             # Unit tests (no I/O)
│   ├── __init__.py
│   ├── test_models.py
│   └── test_utils.py
│
├── integration/                      # Integration tests (real I/O)
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_pipeline.py
│   ├── test_extensions.py
│   ├── test_providers.py
│   └── test_real_images.py
│
└── fixtures/                         # Test data
    ├── images/
    │   ├── portrait_test.jpg
    │   ├── animal_test.jpg
    │   └── simple_shape.png
    └── expected/
        ├── portrait_expected.svg
        └── animal_expected.svg
```

## Migration Strategy

### Phase 1: Create Extension Infrastructure (Week 1)
1. ✅ Create abstract base classes (AbstractStaticExtension, AbstractProvider)
2. ✅ Implement extension discovery system
3. ✅ Implement hook system with decorator pattern
4. ✅ Create ExtensionRegistry for auto-discovery
5. ✅ Add comprehensive unit tests

### Phase 2: Migrate Existing Code to Extensions (Week 2)
1. ✅ Create EXT_Preprocess with existing ImagePreprocessor
2. ✅ Create EXT_LineExtraction with existing LineExtractor
3. ✅ Create EXT_Vectorize with ImageTracerVectorizer
4. ✅ Create EXT_Optimize with VpypeOptimizer
5. ✅ Create EXT_Export with SVG export
6. ✅ Update PhotoToLineProcessor to use extension system
7. ✅ Maintain backward compatibility

### Phase 3: Add New Providers (Week 3)
1. Add PRV_Vtracer_Vectorize (vtracer implementation)
2. Add PRV_HED_LineExtraction (ML-based edge detection)
3. Add PRV_HPGL_Export (HPGL plotter format)
4. Add PRV_GCode_Export (CNC G-code format)

### Phase 4: Advanced Features (Week 4)
1. Implement provider rotation/failover
2. Add performance metrics hooks
3. Implement multi-color layer support
4. Add advanced optimization strategies

## Configuration Management

### Environment Variables

```bash
# Extension Control
ENABLED_EXTENSIONS=preprocess,line_extraction,vectorize,optimize,export

# Provider Selection (comma-separated priority order)
VECTORIZE_PROVIDERS=imagetracer,vtracer,potrace
OPTIMIZE_PROVIDERS=vpype,custom

# ML Model Paths
U2NET_MODEL_PATH=./models/u2net/u2net.pth
HED_MODEL_PATH=./models/hed/hed.pth

# Provider-Specific Settings
IMAGETRACER_NODE_PATH=./node_modules
POTRACE_BINARY_PATH=/usr/local/bin/potrace
VTRACER_BINARY_PATH=/usr/local/bin/vtracer

# Hardware
DEVICE=auto  # auto, cuda, mps, cpu
```

### Runtime Configuration

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    enabled_extensions: str = "preprocess,line_extraction,vectorize,optimize,export"
    vectorize_providers: str = "imagetracer,potrace"
    optimize_providers: str = "vpype"
    
    u2net_model_path: Path | None = None
    device: str = "auto"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

## Performance Considerations

### Lazy Loading
- Extensions loaded only when first accessed
- Providers initialized on demand
- ML models loaded once and cached

### Caching
- Processed results cached by job_id
- Provider availability cached
- Extension discovery cached

### Parallel Processing
- Independent pipeline stages can run in parallel (future)
- Multiple jobs processed concurrently
- Tests run in parallel with pytest-xdist

## Security Considerations

### GPL Isolation
- Potrace runs in isolated subprocess
- No GPL code linked in main process
- Clear license boundaries documented

### Input Validation
- File format validation before processing
- Image size limits enforced
- Parameter validation with Pydantic
- Path traversal prevention

### Resource Limits
- Maximum image dimensions
- Processing timeout limits
- Disk space monitoring
- Memory usage limits

## Monitoring & Observability

### Logging Strategy
```python
import logging

# Extension-specific loggers
logger = logging.getLogger(f"extensions.{extension_name}")

# Hook execution logging
logger.debug(f"Executing hook: {hook_name} (priority: {priority})")

# Provider selection logging
logger.info(f"Selected provider: {provider_name} for {extension_name}")
```

### Metrics (Future)
- Pipeline stage duration
- Provider success/failure rates
- Resource usage per job
- Cache hit rates

## Benefits of This Architecture

### Extensibility
- Add new vectorizers without modifying core code
- Add new optimization strategies as providers
- Add new export formats easily

### Maintainability
- Clear separation of concerns
- Each provider is independent and testable
- Hook system for cross-cutting concerns

### Testability
- No mocks - real implementations
- Isolated test environments
- Comprehensive test coverage

### Performance
- Lazy loading reduces startup time
- Provider rotation enables failover
- Parallel test execution

### Developer Experience
- Clear extension patterns
- Auto-discovery reduces boilerplate
- Type-safe with Pydantic models
- Comprehensive documentation

---

**Document Version:** 1.0  
**Last Updated:** 2025-01-13  
**Status:** Implementation Ready
