# Build Plan: Photo-to-Line-Vectorizer

**Goal**: Professional web app converting photos to plotter-ready SVG with precise canvas sizing, line width awareness, and path optimization.

---

## Architecture

### High-Level Flow
```
User Upload → ML/CV Processing → Vectorization → Optimization → Interactive Preview → Export
```

### Two-Tier System
- **Frontend**: React + TailwindCSS + shadcn/ui
- **Backend**: FastAPI + PyTorch (CUDA/Metal) + vpype

---

## Tech Stack

### Frontend
- **Framework**: React 18+ with TypeScript, Vite
- **UI**: TailwindCSS + shadcn/ui (Radix primitives)
- **Icons**: Lucide React
- **SVG**: svg.js or React SVG Pan Zoom
- **State**: Zustand + TanStack Query
- **Design**: Professional, modern (NOT default Gradio/Streamlit style)

### Backend
- **Framework**: FastAPI (Python 3.10+)
- **ML**: PyTorch 2.0+ with CUDA + Metal MPS support
- **Models**: U²-Net (Apache 2.0), Informative Drawings (MIT)
- **Vector**: vpype (MIT), ImageTracerJS (public domain)
- **CV**: OpenCV, Pillow, NumPy
- **Async**: FastAPI BackgroundTasks or Celery + Redis

### DevOps
- **Container**: Docker (multi-stage build)
- **Base Image**: `pytorch/pytorch:2.0-cuda11.8` or Python 3.10 slim
- **Native Wrapper** (future): Tauri for desktop app

---

## Processing Pipeline

### Stage 1: Preprocessing (Optional)
- **U²-Net Portrait**: Isolate subject from background (Apache 2.0)
- Fallback: Simple background removal

### Stage 2: Line Art Extraction
**Option A - ML (Auto Mode)**:
- Informative Drawings model (MIT, 2022)
- Or ControlNet LineArt preprocessor (OpenRAIL-M, 2023)

**Option B - Classical CV (Fast/Fallback)**:
- Bilateral filter → Canny edge detection
- Optional XDoG for stylized lines

**Auto Logic**: Try ML if GPU available, else fallback to CV

### Stage 3: Vectorization
- **Primary**: ImageTracerJS (public domain) via Node subprocess
- **Alternative**: Potrace (GPL, use subprocess isolation)
- Configurable line threshold, curve quality, min path length

### Stage 4: Path Optimization (vpype)
```python
doc = vpype.read_svg(svg_string)
doc = vpype.linemerge(doc, tolerance=0.5)      # Join close endpoints
doc = vpype.linesimplify(doc, tolerance=0.2)   # Reduce anchors
doc = vpype.linesort(doc)                       # TSP-like ordering
doc = vpype.dedupe(doc, tolerance=0.1)          # Remove duplicates
doc = vpype.scaleto(doc, width_mm, height_mm)  # Fit canvas
```

### Stage 5: Hatching (Dark Areas)
- **vpype-hatched plugin** OR custom scanline hatching
- Spacing = line_width × density_factor (default 2.0)
- Auto mode: 45° hatching for brightness < 100, crosshatch for < 50

### Stage 6: Multi-Color (3-5 colors)
- K-means color quantization
- Per-color layer extraction → vectorize → optimize
- Sort by brightness (lightest first for overprinting)

---

## User Interface

### Design Principles
- **Professional**: Neutral grays + subtle accent, Inter/Geist font
- **Clean**: 4px grid, consistent spacing
- **Modern**: shadcn/ui components, smooth transitions
- **Accessible**: WCAG AA compliance

### Layout
```
┌─────────────────────────────────────────────┐
│ Logo                         [Settings ⚙️]  │
├─────────────────────────────────────────────┤
│ ┌─────────────┐  ┌───────────────────────┐ │
│ │             │  │                       │ │
│ │   Upload    │  │   Interactive Preview │ │
│ │  Drag-Drop  │  │   (Pan/Zoom)          │ │
│ │             │  │   Line Width Visual   │ │
│ └─────────────┘  └───────────────────────┘ │
│ ┌─────────────┐                            │
│ │ Mode: Auto▼ │         [Process] [Export] │
│ │ Canvas: ... │                            │
│ │ Width: ...  │                            │
│ │ [Advanced▼] │                            │
│ └─────────────┘                            │
└─────────────────────────────────────────────┘
```

### Key Views
1. **Upload**: Drag-drop + preview
2. **Processing**: Progress bar + WebSocket updates
3. **Preview**: Interactive SVG, layer toggles, real-time line width rendering
4. **Export**: SVG/HPGL/G-code download

### Advanced Mode Controls
- Edge sensitivity, line weight, noise reduction
- Curve fitting, detail level, color count
- Merge tolerance, simplification, path sorting
- Hatching: enable, spacing, angle, crosshatch, threshold

---

## API Design

### REST Endpoints

**POST `/api/upload`**
```json
Request: { "image": "base64...", "filename": "photo.jpg" }
Response: { "job_id": "uuid", "image_url": "/temp/uuid.jpg" }
```

**POST `/api/process`**
```json
Request: { 
  "job_id": "uuid",
  "mode": "auto",
  "params": {
    "canvas_width": 300, "canvas_height": 200,
    "line_width": 0.3, "isolate_subject": true,
    "use_ml": true, "num_colors": 1, "hatching_enabled": true
  }
}
Response: { "job_id": "uuid", "status": "processing", "websocket_url": "..." }
```

**GET `/api/status/{job_id}`**
```json
Response: { 
  "job_id": "uuid", "status": "completed", "progress": 100,
  "result_url": "/results/uuid.svg",
  "stats": { "path_count": 1247, "total_length": 45230, "estimated_time": "8m 30s" }
}
```

**GET `/api/download/{job_id}?format=svg`** → File download

### WebSocket (`/ws/{job_id}`)
```json
Server → Client:
{ "type": "progress", "job_id": "uuid", "stage": "vectorizing", "percent": 45 }
{ "type": "complete", "job_id": "uuid", "result_url": "/results/..." }
{ "type": "error", "job_id": "uuid", "message": "..." }
```

---

## Auto Mode Presets

### Portrait
```python
{
  'isolate_subject': True, 'use_ml': True,
  'edge_threshold': (50, 150), 'line_threshold': 16,
  'merge_tolerance': 0.5, 'simplify_tolerance': 0.2,
  'hatching_enabled': True, 'hatch_density': 2.0,
  'hatch_angle': 45, 'darkness_threshold': 100
}
```

### Animal
```python
{
  'isolate_subject': True, 'use_ml': True,
  'edge_threshold': (30, 120),  # More sensitive for fur
  'line_threshold': 12, 'curve_quality': 1.2,
  'merge_tolerance': 0.3, 'simplify_tolerance': 0.15,
  'hatching_enabled': True, 'hatch_density': 1.5,
  'hatch_angle': 45, 'darkness_threshold': 80
}
```

---

## Build Phases

### Phase 1: MVP (Core Pipeline)
**Features**: Upload, CV line extraction (Canny), vectorize (ImageTracerJS), optimize (vpype), canvas sizing, SVG export  
**Stack**: React + FastAPI + OpenCV + vpype  
**Success**: Portrait → plotter-ready SVG in <10s

### Phase 2: ML Models + Presets
**Features**: U²-Net segmentation, Informative Drawings/ControlNet, GPU (CUDA/MPS), auto presets, progress indicators  
**Stack**: + PyTorch, WebSocket, Celery (optional)  
**Success**: Better quality, auto mode works for 80% portraits

### Phase 3: Hatching + Multi-Color
**Features**: Auto hatching for dark areas, K-means color quantization, per-color layers, layer visibility  
**Stack**: + vpype-hatched or custom, color clustering  
**Success**: Realistic shading, multi-color pen plotting

### Phase 4: Advanced Mode + Preview
**Features**: Full parameter controls, real-time preview, line width visualization, pan/zoom, path stats  
**Stack**: + React SVG Pan Zoom or Paper.js  
**Success**: Fine-tuning, accurate preview, iteration-friendly

### Phase 5: Export Formats + Presets
**Features**: HPGL, G-code export, save/load presets, material templates  
**Stack**: + vpype HPGL, G-code generator, localStorage  
**Success**: Works with AxiDraw, Cricut, lasers

### Phase 6: Polish + Deploy
**Features**: Error handling, loading states, mobile-responsive, Docker, docs  
**Stack**: Error boundaries, toast notifications, Compose  
**Success**: Production-ready, professional UX

---

## Directory Structure
```
photo-to-line-vectorizer/
├── frontend/
│   ├── src/
│   │   ├── components/ui/    # shadcn/ui
│   │   ├── components/       # Upload, Preview, Controls, Export
│   │   ├── lib/api.ts
│   │   └── App.tsx
│   ├── vite.config.ts
│   └── tailwind.config.js
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/              # upload, process, export
│   │   ├── models/           # u2net, informative_drawings, classical_cv
│   │   ├── pipeline/         # preprocess, line_extract, vectorize, optimize, hatching
│   │   └── utils/
│   ├── requirements.txt
│   └── Dockerfile
├── models/                    # Pre-trained weights
│   ├── u2net/
│   ├── informative-drawings/
│   └── docs/
│       ├── RESEARCH.md
│       └── PLAN.md
├── docker-compose.yml
└── README.md
```

---

## Hardware Acceleration

### PyTorch Device Detection
```python
device = (
    torch.device('cuda') if torch.cuda.is_available() else
    torch.device('mps') if torch.backends.mps.is_available() else
    torch.device('cpu')
)
```

### Optimization Paths
- **CUDA**: TensorRT for NVIDIA GPUs
- **Metal (MPS)**: Native M1/M2/M3 support (PyTorch 2.0+)
- **ONNX Runtime**: Cross-platform fallback
- **CoreML**: iOS/macOS (future)

---

## Performance Targets

### Processing Time
- Classical CV: <5s (1920×1080)
- ML (GPU): <15s
- ML (CPU): <45s

### Output Quality
- Path count: Optimize to <2000 for portraits
- Line merge: >80% duplicate removal
- Canvas sizing: Exact mm accuracy
- Pen travel: <20% of total path length

---

## Licensing Strategy

**Goal**: Commercial-friendly, open-source optional

**Core Stack** (all MIT/Apache/Public Domain):
- ImageTracerJS (Unlicense)
- vpype (MIT)
- U²-Net (Apache 2.0)
- Informative Drawings (MIT)
- OpenCV (Apache 2.0)
- React, FastAPI, TailwindCSS (MIT)

**Caution**:
- ControlNet LineArt (OpenRAIL-M): Review commercial terms
- Potrace (GPL): Use subprocess isolation to avoid contamination

**Result**: Full commercial use without restrictions

---

## Deployment

### Local Dev
```bash
# Frontend
cd frontend && npm install && npm run dev  # :5173

# Backend
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload  # :8000
```

### Docker
```bash
docker-compose up -d  # Frontend :3000, Backend :8000
```

### Native App (Phase 7)
```bash
cd frontend && npm install @tauri-apps/cli
npx tauri build  # .app (macOS), .exe (Windows), .AppImage (Linux)
```

---

## Next Steps

1. **Set up project structure** (frontend + backend dirs)
2. **Install dependencies** (package.json, requirements.txt)
3. **Phase 1 MVP**: Basic upload → CV → vectorize → optimize pipeline
4. **Test with sample portraits** (validate quality, timing)
5. **Iterate**: Add ML models, hatching, multi-color progressively

---

**End of Plan**
