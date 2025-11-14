# Implementation Plan - Extension System Migration

## Phase 1: Core Infrastructure (Days 1-2)

### Abstract Base Classes
Create foundation classes:
- `AbstractStaticExtension`: Base for all extensions
- `AbstractProvider`: Base for all providers
- `HookRegistry`: Hook management system
- `ExtensionRegistry`: Auto-discovery system

### Hook System
- Decorator pattern for hook registration
- Priority-based execution
- Before/after timing support
- Context passing between hooks

## Phase 2: Extension Migration (Days 3-5)

### Migrate Existing Pipeline Stages
1. **EXT_Preprocess** (from `pipeline/preprocess.py`)
   - PRV_ClassicalCV_Preprocess
   - PRV_U2Net_Preprocess

2. **EXT_LineExtraction** (from `pipeline/line_extraction.py`)
   - PRV_Canny_LineExtraction
   - PRV_HED_LineExtraction (future)

3. **EXT_Vectorize** (from `pipeline/vectorize.py`)
   - PRV_ImageTracer_Vectorize
   - PRV_Potrace_Vectorize
   - PRV_Vtracer_Vectorize (future)

4. **EXT_Optimize** (from `pipeline/optimize.py`)
   - PRV_Vpype_Optimize

5. **EXT_Export** (from `pipeline/export.py`)
   - PRV_SVG_Export
   - PRV_HPGL_Export (future)
   - PRV_GCode_Export (future)

## Phase 3: Testing Infrastructure (Days 6-7)

### Abstract Test Classes
- `AbstractExtensionTest`: Base for extension tests
- `AbstractProviderTest`: Base for provider tests
- `AbstractPipelineTest`: End-to-end tests

### Test Strategy
- No mocks - use real implementations
- Isolated test environments
- Parallel execution with pytest-xdist
- 90%+ coverage target

## Quick Start Implementation

### Step 1: Create Base Classes
```python
# app/extensions/base.py
from abc import ABC, abstractmethod
from typing import ClassVar, Dict, Any, List, Type

class AbstractStaticExtension(ABC):
    name: ClassVar[str]
    version: ClassVar[str] = "1.0.0"
    _providers: ClassVar[List[Type]] = []
    
    @classmethod
    def providers(cls) -> List[Type]:
        return cls._providers
```

### Step 2: First Extension (EXT_Vectorize)
Convert existing vectorizer to extension pattern.

### Step 3: Add Hook Points
Add hooks to PhotoToLineProcessor for each stage.

## Success Metrics
- All existing tests pass
- Can add new vectorizer without changing core code
- Hook system functional with logging hooks
- Provider auto-discovery working
