# Processor Module

**Location:** `app/pipeline/processor.py`

## Overview

Main processing pipeline coordinator that orchestrates the complete photo-to-line-vectorizer pipeline from image upload through preprocessing, line extraction, vectorization, optimization, and export.

## Architecture

The processor follows a clean, modular architecture with clear separation of concerns:

```
PhotoToLineProcessor
├── ImagePreprocessor (subject isolation, format conversion)
├── LineExtractor (edge detection, line art extraction)
├── VpypeOptimizer (path optimization, merging, simplification)
├── HatchGenerator (optional cross-hatching for shading)
└── PlotterExporter (SVG generation, statistics)
```

## Key Classes

### `ProcessingParams`

Dataclass containing all parameters for the processing pipeline.

**Required Parameters:**
- `canvas_width_mm: float` - Output canvas width in millimeters
- `canvas_height_mm: float` - Output canvas height in millimeters
- `line_width_mm: float` - Stroke width for paths in millimeters

**Optional Parameters:**
- `isolate_subject: bool = False` - Use U²-Net for background removal
- `use_ml: bool = False` - Enable ML-assisted vectorization (future)
- `edge_threshold: tuple[int, int] = (50, 150)` - Canny edge detection thresholds
- `line_threshold: int = 16` - Hough line detection sensitivity
- `merge_tolerance: float = 0.5` - Distance threshold for merging endpoints (mm)
- `simplify_tolerance: float = 0.2` - Path simplification aggressiveness (mm)
- `hatching_enabled: bool = False` - Enable cross-hatching for shading
- `hatch_density: float = 2.0` - Spacing between hatch lines
- `hatch_angle: int = 45` - Angle of hatch lines in degrees
- `darkness_threshold: int = 100` - Pixel intensity threshold for hatching

### `ProcessingResult`

Dataclass containing the results of processing.

**Attributes:**
- `svg_content: str` - Optimized SVG string ready for download
- `stats: Mapping` - Dictionary with processing statistics:
  - `path_count: int` - Number of paths in final SVG
  - `total_length_mm: float` - Total length of all paths
  - `width_mm: float | None` - Canvas width
  - `height_mm: float | None` - Canvas height
  - `bounds: tuple | None` - Bounding box (minx, miny, maxx, maxy)
- `device_used: str` - Computing device used ("cuda", "mps", or "cpu")

### `PhotoToLineProcessor`

Main pipeline coordinator providing a unified interface for the complete processing pipeline.

**Initialization:**
```python
processor = PhotoToLineProcessor(
    u2net_model_path=Path("models/u2net.pth")  # Optional
)
```

**Key Methods:**

#### `process(image_path: Path, params: ProcessingParams) -> ProcessingResult`

Asynchronous processing (recommended for production).

**Args:**
- `image_path: Path` - Path to input image file
- `params: ProcessingParams` - Processing configuration

**Returns:**
- `ProcessingResult` - Contains SVG content, statistics, and device info

**Process Flow:**
1. **Preprocessing** - Load image, optional subject isolation
2. **Line Extraction** - Canny edge detection or XDoG
3. **Raster to Vector** - ImageTracerJS conversion
4. **Optimization** - Merge endpoints, simplify paths, reorder for plotting
5. **Hatching** (optional) - Add cross-hatching for depth
6. **Export** - Generate SVG with statistics

#### `process_sync(image_path: Path, params: ProcessingParams) -> ProcessingResult`

Synchronous processing (for testing/CLI usage).

## Pipeline Stages

### Stage 1: Preprocessing

**Module:** `app/pipeline/preprocess.py`

**Responsibilities:**
- Load images from multiple formats (JPEG, PNG, TIFF, WebP, HEIC/HEIF)
- Convert all images to RGB numpy arrays
- Optional U²-Net subject isolation (background removal)
- Normalize image dimensions

**Output:** RGB numpy array `(H, W, 3)`

### Stage 2: Line Extraction

**Module:** `app/pipeline/line_extraction.py`

**Methods Available:**
- **BILATERAL_CANNY** (default) - Bilateral filtering + Canny edge detection
- **CANNY** - Standard Canny edge detection
- **AUTO_CANNY** - Automatic threshold selection via median
- **XDOG** - Extended Difference of Gaussians (stylized lines)

**Output:** Binary line art image (255 = line, 0 = background)

### Stage 3: Raster to Vector

**Module:** `app/pipeline/vectorize.py`

Uses ImageTracerJS (Node.js subprocess) to convert raster line art to SVG paths.

**Configuration:**
- `line_threshold: int` - Threshold for line vs background
- `qtres: float` - Quality/resolution (lower = more detail)
- `pathomit: int` - Minimum path length to keep
- `scale: float` - Output scaling factor

**Output:** SVG string with unoptimized paths

### Stage 4: Optimization

**Module:** `app/pipeline/optimize.py`

Uses vpype for path optimization:
1. **Merge Close Endpoints** - Reduce fragmented paths
2. **Simplify Paths** - Remove redundant points (Douglas-Peucker)
3. **Reorder Paths** - Traveling salesman optimization for plotting
4. **Filter Short Paths** - Remove tiny artifacts

**Output:** Optimized vpype Document

### Stage 5: Hatching (Optional)

**Module:** `app/pipeline/hatching.py`

Adds cross-hatching lines to represent darker areas:
- Analyzes original grayscale image
- Generates parallel hatch lines at specified angle
- Clips lines to dark regions based on threshold
- Controls density via spacing parameter

**Output:** vpype Document with hatching layers added

### Stage 6: Export

**Module:** `app/pipeline/export.py`

Generates final SVG with metadata:
- Sets canvas dimensions
- Calculates path statistics
- Adds metadata (path count, total length)
- Formats SVG for web display and plotting

**Output:** SVG string with statistics

## Device Management

The processor automatically detects and uses the best available compute device:

1. **CUDA** - NVIDIA GPUs (fastest for U²-Net)
2. **MPS** - Apple Silicon Metal (M1/M2/M3)
3. **CPU** - Fallback (always available)

Device selection is logged at initialization:
```
INFO: Using device: cuda (NVIDIA GeForce RTX 3080)
```

## Usage Examples

### Basic Processing

```python
from pipeline.processor import PhotoToLineProcessor, ProcessingParams
from pathlib import Path

# Initialize processor
processor = PhotoToLineProcessor()

# Configure processing
params = ProcessingParams(
    canvas_width_mm=300,
    canvas_height_mm=200,
    line_width_mm=0.3,
)

# Process image
result = processor.process_sync(
    Path("photo.jpg"),
    params
)

# Access results
print(f"Generated {result.stats['path_count']} paths")
print(f"Total length: {result.stats['total_length_mm']:.2f}mm")
print(f"Device: {result.device_used}")

# Save SVG
Path("output.svg").write_text(result.svg_content)
```

### Advanced Processing with All Features

```python
params = ProcessingParams(
    # Canvas
    canvas_width_mm=400,
    canvas_height_mm=300,
    line_width_mm=0.25,

    # ML Features
    isolate_subject=True,  # Requires U²-Net model
    use_ml=False,  # Reserved for future ML models

    # Edge Detection
    edge_threshold=(30, 150),  # Lower = more edges
    line_threshold=12,  # Lower = more lines detected

    # Optimization
    merge_tolerance=0.75,  # Merge endpoints within 0.75mm
    simplify_tolerance=0.15,  # Aggressive simplification

    # Hatching for shading
    hatching_enabled=True,
    hatch_density=1.5,  # Closer spacing
    hatch_angle=45,
    darkness_threshold=80,  # More area hatched
)

result = processor.process_sync(Path("portrait.heic"), params)
```

### Production Usage (Async)

```python
import asyncio

async def process_job(image_path: Path):
    processor = PhotoToLineProcessor()
    params = ProcessingParams(
        canvas_width_mm=300,
        canvas_height_mm=200,
        line_width_mm=0.3,
    )

    # Non-blocking processing
    result = await asyncio.to_thread(
        processor.process_sync,
        image_path,
        params
    )

    return result

# Use with FastAPI background tasks
result = await process_job(Path("image.jpg"))
```

## Performance Characteristics

### Processing Time (300x200mm canvas)

- **CPU Only:** ~5-10 seconds
- **With U²-Net (CUDA):** ~2-4 seconds
- **With U²-Net (MPS):** ~3-6 seconds

### Bottlenecks

1. **ImageTracerJS** - Node.js subprocess overhead (~1-2s)
2. **U²-Net Inference** - GPU required for acceptable speed
3. **Vpype Optimization** - Linear time complexity with path count

### Optimization Tips

- Use lower `edge_threshold` values for simpler images (fewer paths)
- Increase `simplify_tolerance` to reduce path complexity
- Disable `isolate_subject` if background is already clean
- Use `merge_tolerance` to consolidate fragmented edges

## Error Handling

The processor provides detailed error messages for common failures:

### File Not Found
```python
FileNotFoundError: Image not found: /path/to/image.jpg
```

### Unsupported Format
```python
ValueError: Unsupported format: .bmp
```

### U²-Net Model Missing
```python
WARNING: U²-Net model not found, subject isolation unavailable
# Processing continues without isolation
```

### Node.js Not Available
```python
WARNING: Node.js not found, vectorization will not work
RuntimeError: Vectorization failed: Node.js not available
```

### Out of Memory
```python
RuntimeError: CUDA out of memory
# Falls back to CPU automatically for subsequent processing
```

## Testing

The processor has comprehensive test coverage:

```bash
# Unit tests (mocked dependencies)
pytest tests/unit/test_job_service.py -v

# Integration tests (real images)
pytest tests/integration/test_real_images.py -v

# Skip tests requiring ML model
pytest -m "not requires_ml"
```

## Dependencies

**Core:**
- `torch` - Device management and U²-Net inference
- `opencv-python` - Image processing, Canny edge detection
- `pillow` - Image loading, format support
- `pillow-heif` - HEIC/HEIF format support
- `numpy` - Numerical operations

**Vectorization:**
- `vpype` - Path optimization and plotting preparation
- Node.js + ImageTracerJS - Raster to vector conversion

**Optional:**
- U²-Net model weights (for subject isolation)

## Future Enhancements

Planned features referenced in the code:

1. **`use_ml` Parameter** - ML-assisted vectorization via Informative Drawings model
2. **WebSocket Progress** - Real-time progress updates during processing
3. **K-means Multi-Color** - Support for color layer separation
4. **Batch Processing** - Process multiple images efficiently
5. **Result Caching** - Cache processed results by content hash

## Related Modules

- [`preprocess.md`](./preprocess.md) - Image preprocessing details
- [`line_extraction.md`](./line_extraction.md) - Edge detection algorithms
- [`optimize.md`](./optimize.md) - Path optimization strategies
- [`hatching.md`](./hatching.md) - Cross-hatching implementation
- [`export.md`](./export.md) - SVG generation and statistics
