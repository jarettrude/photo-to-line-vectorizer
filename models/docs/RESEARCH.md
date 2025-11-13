# Research: Photo-to-Line-Vectorizer Solutions

**Last Updated**: November 12, 2025  
**Purpose**: Comprehensive survey of technologies, models, and libraries for converting photographs (portraits/animals) into plotter-friendly single-line SVG drawings.

---

## Problem Statement

Convert photographs → detailed line art SVG suitable for:
- Laser engravers
- Pen plotters
- Paint plotters  
- Cricut/vinyl cutters

**Key Requirements**:
- Adjustable canvas size (material dimensions)
- Line width awareness (pen/brush/laser beam size)
- Path optimization (reduce duplicates, minimize pen-up travel)
- Hatching/shading for dark areas
- Multi-color support (3-5 colors)
- Privacy-first (no cloud upload required)
- Commercial-friendly licensing

---

## AI Models for Line Art Extraction

### 1. Informative Drawings (2022, MIT License)
**Source**: https://github.com/carolineec/informative-drawings  
**Paper**: "Learning to generate line drawings that convey geometry and semantics" (CVPR 2022)  
**License**: MIT ✅ Commercial-friendly

**Capabilities**:
- Generates semantically meaningful line drawings from photos
- Preserves geometric and semantic information
- Unpaired learning (doesn't require paired training data)
- Trained on portraits/faces primarily

**Technology**:
- PyTorch-based
- Uses depth maps + edge detection + learned model
- Output: raster line art (needs vectorization)

**Pros**:
- MIT license = unrestricted commercial use
- Produces clean, artistic line drawings
- Good for portraits
- Has HuggingFace demo

**Cons**:
- Released 2022 (potentially dated)
- Requires GPU for inference
- Output is raster (512x512), needs vectorization step
- Setup complexity (PyTorch, dependencies)

**Commercial Viability**: ⭐⭐⭐⭐⭐

---

### 2. ControlNet LineArt (v1.1, 2023, OpenRAIL-M)
**Source**: https://huggingface.co/lllyasviel/control_v11p_sd15_lineart  
**Paper**: "Adding Conditional Control to Text-to-Image Diffusion Models"  
**License**: CreativeML OpenRAIL-M ✅ Commercial with conditions

**Capabilities**:
- Extracts line art from images as conditioning for Stable Diffusion
- Very high quality line detection
- Can work as standalone line extractor
- Multiple variants (lineart, lineart_anime, etc.)

**Technology**:
- Built on Stable Diffusion 1.5
- Uses dedicated line art detection preprocessor
- PyTorch + Diffusers library
- Can leverage ONNX/TensorRT for optimization

**Pros**:
- State-of-the-art quality (2023)
- Active ecosystem (HuggingFace, Diffusers)
- Multiple preprocessor options
- Hardware acceleration support

**Cons**:
- Heavy model (GPU required)
- OpenRAIL-M has usage restrictions (must review for commercial)
- Primarily designed for generative workflow
- Output is raster

**Commercial Viability**: ⭐⭐⭐⭐ (review license carefully)

---

### 3. U²-Net / U²-Net Portrait (2020, Apache 2.0)
**Source**: https://github.com/xuebinqin/U-2-Net  
**Paper**: "U²-Net: Going Deeper with Nested U-Structure for Salient Object Detection"  
**License**: Apache 2.0 ✅ Commercial-friendly

**Capabilities**:
- Portrait segmentation/matting
- Salient object detection
- Subject isolation from background
- Produces clean masks

**Technology**:
- PyTorch-based
- Lightweight compared to transformers
- `u2net_portrait.pth` model for portraits
- 512x512 input/output

**Pros**:
- Apache 2.0 = unrestricted commercial use
- Fast inference
- Good for preprocessing (subject isolation)
- Active repo, good documentation

**Cons**:
- Not a line art generator (produces masks)
- Needs to be paired with edge detection
- Quality depends on background complexity

**Use Case**: Preprocessing step to isolate subject before line extraction

**Commercial Viability**: ⭐⭐⭐⭐⭐

---

### 4. Classical Computer Vision Approaches

#### Canny Edge Detection (OpenCV)
**License**: Apache 2.0 ✅

**Capabilities**:
- Fast, deterministic edge detection
- Adjustable thresholds
- Well-understood, predictable

**Pros**:
- No ML required
- Fast (CPU)
- Local processing
- Highly controllable

**Cons**:
- Can be noisy on complex images
- Needs significant tuning per image
- Less semantic understanding

#### XDoG (Extended Difference of Gaussians)
**License**: Public domain / research ✅

**Capabilities**:
- Stylized line art from photos
- Adjustable line thickness
- Good for artistic effects

**Pros**:
- No ML required
- Fast
- Artistic control

**Cons**:
- Less detail preservation
- Parameter-sensitive

**Commercial Viability**: ⭐⭐⭐⭐⭐ (implementation-dependent)

---

## Vectorization Libraries

### 1. ImageTracerJS (Unlicense/Public Domain)
**Source**: https://github.com/jankovicsandras/imagetracerjs  
**License**: Unlicense ✅ Public domain

**Capabilities**:
- Raster → vector tracing
- Multi-color support with color quantization
- Path simplification
- Browser and Node.js compatible
- SVG output

**Technology**:
- Pure JavaScript
- Runs client-side (privacy-friendly)
- Configurable tracing options
- Color palette extraction

**Pros**:
- Public domain = zero restrictions
- Client-side capable (privacy)
- Active maintenance
- Used by 575+ projects
- Good color handling
- InkScape extension available

**Cons**:
- JavaScript performance limits for large images
- Less precise than Potrace for monochrome

**Commercial Viability**: ⭐⭐⭐⭐⭐

---

### 2. Potrace (GPL v2)
**Source**: https://potrace.sourceforge.net/  
**License**: GPL v2 ⚠️ Restrictive for proprietary software

**Capabilities**:
- High-quality bitmap → vector
- Smooth curves (Bézier)
- Monochrome tracing
- Industry standard

**Technology**:
- C implementation
- Python/JS/Ruby/etc. bindings available
- WebAssembly ports exist

**Pros**:
- Highest quality monochrome tracing
- Very fast
- Well-tested (20+ years)
- Multiple language bindings

**Cons**:
- **GPL = must open-source derived work if statically linked**
- Monochrome only (no color support)
- Licensing complexity for commercial apps

**Commercial Viability**: ⭐⭐ (GPL complications; consider WASM with dynamic linking or separate process)

---

### 3. Vectorizer.AI (Proprietary SaaS)
**Source**: https://vectorizer.ai/  
**License**: Proprietary (API/web service)

**Capabilities**:
- AI-powered vectorization
- Full-color support
- Best-in-class quality
- Symmetry detection

**Pros**:
- Excellent quality
- No local compute needed
- Handles complex images

**Cons**:
- **Not privacy-friendly (cloud upload)**
- Proprietary/paid service
- No local processing option
- API dependency

**Commercial Viability**: ⭐⭐⭐ (pricing + privacy concerns)

---

### 4. Linedraw by LingDong
**Source**: https://github.com/LingDong-/linedraw  
**License**: Not explicitly stated (appears permissive)

**Capabilities**:
- Image → line drawing vectors
- Optimized for plotters
- Contour and hatch modes
- Stroke order optimization
- SVG output

**Technology**:
- Python 2/3
- OpenCV (optional for performance)
- NumPy, PIL

**Pros**:
- Purpose-built for plotters
- Path optimization included
- Simple interface
- Contour + hatch options

**Cons**:
- Older project (maintenance unclear)
- Limited documentation
- License ambiguity

**Commercial Viability**: ⭐⭐⭐ (verify license)

---

## Vector Optimization Tools

### vpype (MIT License)
**Source**: https://vpype.readthedocs.io/ | https://pypi.org/project/vpype/  
**License**: MIT ✅ Commercial-friendly

**Capabilities**:
- **Swiss Army knife for plotter vector graphics**
- Path optimization (line merge, line sort)
- Duplicate line removal
- Multi-layer support (for multi-color)
- Scaling and page layout
- HPGL and SVG I/O
- Plugin ecosystem

**Key Commands**:
- `linemerge`: join paths with close endpoints
- `linesort`: minimize pen-up travel (TSP-like)
- `crop`: canvas trimming
- `scaleto`: precise sizing
- `splitall`: break paths for optimization
- `reloop`: optimize closed path starting points

**Plugins** (extend functionality):
- `vpype-gcode`: G-code export
- `vpype-pixelart`: pixel art rendering
- `hatched`: crosshatch/stipple fills
- Many community plugins

**Technology**:
- Python library + CLI
- Hardware-accelerated viewer
- Can be embedded in other tools

**Pros**:
- MIT = unrestricted commercial use
- Purpose-built for plotters
- Active development
- Excellent documentation
- Extensible via plugins
- Multi-layer/multi-color workflows

**Cons**:
- Python-based (not browser-native)
- CLI-first design (needs wrapper for GUI)

**Commercial Viability**: ⭐⭐⭐⭐⭐

---

## Hatching & Shading Techniques

### 1. Eggbot Hatch Fill (Inkscape Extension)
**Source**: Evil Mad Scientist Laboratories  
**License**: Open source ✅

**Capabilities**:
- Convert filled regions → hatched lines
- Adjustable spacing and angle
- Crosshatch support
- Inset/spiral fill modes

**Technology**:
- Python extension for Inkscape
- Can be adapted/ported

---

### 2. vpype-hatched Plugin
**License**: MIT-compatible

**Capabilities**:
- Parametric hatching
- Multiple hatch patterns
- Tone-based density

---

### 3. Manual Implementation Options
- **Scanline hatching**: horizontal/diagonal lines at density based on pixel darkness
- **Concentric insets**: spiral inward for solid fills
- **Stippling**: dots with density mapping
- **Parallel line fills**: adjustable spacing and angle

---

## Single-Path / TSP Art Techniques

### TSP Art (Traveling Salesman Problem Art)
**Source**: https://wiki.evilmadscientist.com/TSP_art  
**License**: Open algorithms

**Capabilities**:
- Converts stippled image → single continuous path
- Minimizes pen-up travel to zero (one stroke)
- Uses TSP solvers (Concorde, LKH)

**Technology**:
- Stipple generation (weighted Voronoi, halftoning)
- TSP solver (Concorde LKH recommended)
- Python tooling (StippleGen, tspart.py)

**Pros**:
- True single-stroke output
- Artistic style
- Plotter-optimal

**Cons**:
- Computationally expensive (TSP is NP-hard)
- Long solve times for >5000 points
- Less photorealistic
- Stippled aesthetic (not line drawing)

**Use Case**: Alternative output mode for specific artistic style

---

## Color Handling & Quantization

### Color Quantization Algorithms
1. **Median Cut** (fast, decent quality)
2. **K-means clustering** (better quality, slower)
3. **Octree** (balanced)

### Color → Layer Workflow
1. Quantize image to N colors (e.g., 3-5)
2. Extract mask per color
3. Vectorize each mask independently
4. Assign SVG layer/group per color
5. Optimize paths per layer
6. Sort layers by brightness (light → dark for overprinting)

**Tools**:
- ImageTracerJS: built-in color quantization
- PIL/Pillow: `Image.quantize()`
- scikit-learn: KMeans
- vpype: layer management

---

## Modern Alternatives & Emerging Tech

### Segment Anything Model (SAM) - Meta (2023)
**License**: Apache 2.0 ✅

**Use Case**: Subject segmentation (alternative to U²-Net)  
**Status**: Very large model, may be overkill

---

### DINOv2 + Edge Detection
**License**: Apache 2.0 ✅

**Use Case**: Feature extraction → edge-aware processing  
**Status**: Experimental

---

### Anime2Sketch / APDrawingGAN
**License**: Varies (check repo)

**Use Case**: Alternative line art generators  
**Status**: Older (2019-2020), less maintained

---

## Hardware Acceleration Options

### PyTorch Acceleration
1. **CUDA** (NVIDIA GPUs)
   - Best support, most mature
   - TensorRT for optimization

2. **Metal (MPS)** (Apple Silicon)
   - Native M1/M2/M3 support
   - PyTorch 2.0+ has `mps` device
   - Good performance for inference

3. **ROCm** (AMD GPUs)
   - Linux only
   - Growing support

### Model Optimization
- **ONNX Runtime**: cross-platform inference
- **CoreML**: Apple ecosystem (can convert PyTorch)
- **TensorRT**: NVIDIA optimization
- **OpenVINO**: Intel hardware

### Browser Acceleration
- **WebGPU**: emerging standard (limited browser support)
- **WebGL**: mature but less ML-optimized
- **WASM + SIMD**: CPU-bound but portable

---

## Recommended Pipeline Options

### Pipeline A: ML-First (High Quality)
1. **Input**: Photo upload
2. **Preprocessing**: U²-Net portrait segmentation (optional)
3. **Line extraction**: ControlNet LineArt OR Informative Drawings
4. **Vectorization**: ImageTracerJS (client) or Potrace (server)
5. **Optimization**: vpype (merge, sort, simplify)
6. **Hatching**: vpype-hatched or custom algorithm
7. **Output**: SVG with adjustable canvas size

**Pros**: Best quality, semantic understanding  
**Cons**: GPU required, slower, heavier stack

---

### Pipeline B: Hybrid (Balanced)
1. **Input**: Photo upload
2. **Preprocessing**: U²-Net (optional subject isolation)
3. **Line extraction**: Canny or XDoG (classical CV)
4. **Vectorization**: ImageTracerJS
5. **Optimization**: vpype or JS path optimizer
6. **Hatching**: Scanline algorithm
7. **Output**: SVG

**Pros**: Faster, lighter, still good quality  
**Cons**: Less "intelligent" line extraction

---

### Pipeline C: Lightweight Client-Side
1. **Input**: Photo (browser)
2. **Preprocessing**: Canvas API image processing
3. **Line extraction**: WebGL Canny edge detection
4. **Vectorization**: ImageTracerJS (WASM)
5. **Optimization**: JS path library (simplify-js, etc.)
6. **Hatching**: Client-side algorithm
7. **Output**: SVG

**Pros**: Full privacy, no server needed, fast  
**Cons**: Limited by browser compute, lower quality

---

## Tech Stack Recommendations

### Backend (if using ML models)
- **Framework**: FastAPI or Flask (Python)
- **ML**: PyTorch with MPS (Metal) and CUDA support
- **Vector tools**: vpype (Python native)
- **Task queue**: Celery or RQ (for async processing)
- **Storage**: Local filesystem or S3-compatible

### Frontend
- **Framework**: React or Svelte (modern, component-based)
- **Styling**: TailwindCSS (utility-first, professional look)
- **UI Components**: shadcn/ui (React) or Melt UI (Svelte)
- **Icons**: Lucide or Hero Icons
- **Canvas**: Fabric.js or Konva.js (interactive SVG preview)
- **SVG rendering**: svg.js or native SVG DOM

### Deployment
- **Web app**: Docker containerized
- **Native wrapper**: Electron or Tauri (for desktop app)
- **Compute**: Local server or cloud (AWS, GCP, Modal)

---

## Licensing Summary Table

| Tool/Model | License | Commercial Use | Privacy | Notes |
|------------|---------|----------------|---------|-------|
| Informative Drawings | MIT | ✅ Unrestricted | ✅ Local | GPU required |
| ControlNet LineArt | OpenRAIL-M | ✅ With conditions | ✅ Local | Review terms |
| U²-Net | Apache 2.0 | ✅ Unrestricted | ✅ Local | Good for preprocessing |
| ImageTracerJS | Unlicense | ✅ Public domain | ✅ Client-side | Best choice |
| Potrace | GPL v2 | ⚠️ Restricted | ✅ Local | Linking issues |
| vpype | MIT | ✅ Unrestricted | ✅ Local | Essential tool |
| OpenCV | Apache 2.0 | ✅ Unrestricted | ✅ Local | Classical CV |

**Legend**:
- ✅ = Good/Compatible
- ⚠️ = Caution/Review needed
- ❌ = Problematic

---

## Open Questions & Future Research

1. **Latest line art models (2024-2025)**:
   - Search for newer alternatives to Informative Drawings
   - Check ControlNet v2/SDXL variants
   - Investigate FLUX/SD3 line art capabilities

2. **Real-time preview**:
   - WebGL-based line width rendering
   - Interactive path editing

3. **Advanced optimizations**:
   - Duplicate stroke detection across overlapping regions
   - Intelligent path joining (avoid crossing)
   - Tool path physics (acceleration, jerk limits)

4. **Multi-material support**:
   - Laser power curves
   - Brush stroke dynamics
   - Vinyl cut settings

---

## References & Links

- [Drawingbots.net](https://drawingbots.net/knowledge/tools) - Comprehensive plotter tools directory
- [Evil Mad Scientist Wiki](https://wiki.evilmadscientist.com/) - Plotter tutorials and techniques
- [vpype Documentation](https://vpype.readthedocs.io/)
- [ControlNet Paper](https://arxiv.org/abs/2302.05543)
- [Informative Drawings Paper](https://arxiv.org/abs/2203.12691)
- [U²-Net Paper](https://arxiv.org/pdf/2005.09007.pdf)

---

**End of Research Document**
