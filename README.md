# Photo to Line Vectorizer

Professional web application for converting photographs to plotter-ready line art SVG. Designed for laser engravers, pen plotters, paint plotters, and vinyl cutters.

## Features

- **Privacy-First**: All processing happens locally, no cloud uploads required
- **Hardware Acceleration**: Auto-detects CUDA (NVIDIA), MPS (Apple Metal), or CPU
- **Canvas-Aware**: Precise canvas sizing in millimeters with line width consideration
- **Path Optimization**: Uses vpype for line merging, simplification, and TSP-like sorting
- **Hatching Support**: Automatic hatching for dark regions with configurable density
- **Multiple Formats**: Supports JPEG, PNG, TIFF, WebP, HEIC/HEIF input
- **Professional UI**: Modern React + TailwindCSS + shadcn/ui interface
- **Real-Time Processing**: Background processing with status polling

## Tech Stack

### Frontend
- **Framework**: React 18 + TypeScript + Vite
- **UI Library**: TailwindCSS + shadcn/ui (Radix primitives)
- **Icons**: Lucide React
- **State Management**: TanStack Query + Zustand
- **Responsive**: Mobile-friendly, WCAG AA accessible

### Backend
- **Framework**: FastAPI (Python 3.13)
- **ML/CV**: PyTorch 2.0+ (CUDA/MPS support), OpenCV
- **Models**: U²-Net (Apache 2.0) for subject segmentation
- **Vectorization**: ImageTracerJS (public domain), Potrace fallback
- **Optimization**: vpype (MIT) for path optimization

## Architecture

```
User Upload → Preprocessing → Line Extraction (CV/ML) →
Vectorization (ImageTracerJS) → Optimization (vpype) →
Canvas Scaling → SVG Export
```

### Processing Pipeline

1. **Preprocessing** (Optional)
   - Subject isolation using U²-Net
   - Contrast enhancement with CLAHE
   - Image resizing

2. **Line Extraction**
   - **Classical CV**: Canny edge detection, bilateral filtering, XDoG
   - **ML** (future): Informative Drawings, ControlNet LineArt

3. **Vectorization**
   - ImageTracerJS for raster-to-vector conversion
   - Configurable quality and simplification

4. **Optimization**
   - Line merging (join close endpoints)
   - Path simplification (reduce anchors)
   - Line sorting (minimize pen travel)
   - Deduplication (remove overlaps)
   - Canvas scaling to exact dimensions

5. **Hatching** (Optional)
   - Scanline hatching for dark regions
   - Crosshatch for very dark areas
   - Spacing based on line width

## Installation

### Prerequisites

- Python 3.13
- Node.js 18+
- (Optional) CUDA for NVIDIA GPUs
- (Optional) Apple Silicon for MPS acceleration

### Quick Start with Docker

```bash
# Clone repository
git clone https://github.com/yourusername/photo-to-line-vectorizer.git
cd photo-to-line-vectorizer

# Start services
docker-compose up -d

# Access application
# Frontend: http://localhost:5173
# Backend: http://localhost:8000
```

### Manual Installation

#### Backend

```bash
cd backend

# Install uv (once per machine)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create and activate virtual environment
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt

# Install ImageTracerJS
npm install -g imagetracerjs

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Usage

### Web Interface

1. **Upload Image**
   - Drag and drop or click to browse
   - Supports JPEG, PNG, TIFF, WebP, HEIC/HEIF

2. **Configure Parameters**
   - **Canvas Size**: Width and height in millimeters (required)
   - **Line Width**: Pen/laser width in millimeters (required)
   - **Subject Isolation**: Remove background
   - **Hatching**: Add shading to dark areas
   - **Advanced Options**: Edge thresholds, merge/simplify tolerances

3. **Process**
   - Click "Process Image"
   - Monitor real-time progress
   - View device used (CUDA/MPS/CPU)

4. **Download**
   - Preview SVG in browser
   - View path statistics
   - Download SVG file

### API Usage

#### Upload Image

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@photo.jpg"
```

Response:
```json
{
  "job_id": "uuid",
  "filename": "photo.jpg",
  "image_url": "/api/uploads/uuid.jpg"
}
```

#### Process Image

```bash
curl -X POST http://localhost:8000/api/process \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "uuid",
    "mode": "auto",
    "params": {
      "canvas_width_mm": 300,
      "canvas_height_mm": 200,
      "line_width_mm": 0.3,
      "isolate_subject": true,
      "hatching_enabled": true
    }
  }'
```

#### Check Status

```bash
curl http://localhost:8000/api/status/uuid
```

#### Download Result

```bash
curl http://localhost:8000/api/download/uuid > result.svg
```

## Configuration

### Backend Environment Variables

Create `backend/.env`:

```env
HOST=0.0.0.0
PORT=8000
DEBUG=True

UPLOAD_DIR=./temp/uploads
RESULTS_DIR=./temp/results
MAX_UPLOAD_SIZE_MB=50

U2NET_MODEL_PATH=../models/u2net/pytorch/u2netp.pth
INFORMATIVE_DRAWINGS_MODEL_PATH=../models/informative-drawings/checkpoints/netG_A_sketch.pth
```

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest -v

# With coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_device.py -v
```

### Linting & Formatting

```bash
# Backend
cd backend
ruff check app/ --fix
ruff format app/

# Frontend
cd frontend
npm run lint
npm run format
```

### Project Structure

```
photo-to-line-vectorizer/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints and models
│   │   ├── models/           # ML models (U²-Net, CV)
│   │   ├── pipeline/         # Processing pipeline
│   │   ├── utils/            # Device management, helpers
│   │   ├── config.py         # Configuration
│   │   └── main.py           # FastAPI application
│   ├── tests/                # Pytest test suite
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── lib/              # API client, utilities
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── Dockerfile
├── models/                   # Pre-trained model weights
│   ├── u2net/
│   ├── informative-drawings/
│   └── docs/
│       ├── RESEARCH.md       # Technology research
│       └── PLAN.md           # Implementation plan
├── docker-compose.yml
└── README.md
```

## Performance

### Target Processing Times (1920×1080 image)

- **Classical CV**: < 5 seconds
- **ML with GPU (CUDA/MPS)**: < 15 seconds
- **ML with CPU**: < 45 seconds

### Output Quality

- Path count optimization: < 2000 paths for typical portraits
- Line merge efficiency: > 80% duplicate removal
- Canvas sizing: Exact mm accuracy
- Pen travel: < 20% of total path length

## Licensing

### Core Components (MIT/Apache/Public Domain)

- ImageTracerJS: Unlicense (Public Domain)
- vpype: MIT
- U²-Net: Apache 2.0
- OpenCV: Apache 2.0
- React, FastAPI, TailwindCSS: MIT

### Commercial Use

Fully commercial-friendly. All core dependencies use permissive licenses.

### GPL Caution

Potrace (GPL v2) is isolated via subprocess to avoid license contamination.

## Troubleshooting

### ImageTracerJS Not Found

```bash
npm install -g imagetracerjs
```

### PyTorch CUDA Not Detected

```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Install CUDA-enabled PyTorch
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### MPS (Apple Silicon) Not Working

```bash
# Check MPS availability
python -c "import torch; print(torch.backends.mps.is_available())"

# Ensure PyTorch 2.0+
uv pip install --upgrade torch torchvision
```

### Vectorization Fails

- Ensure Node.js is installed
- Check ImageTracerJS is globally available
- Verify image is not too large (< 50MB)

## Roadmap

- [ ] Additional ML models (ControlNet, Informative Drawings)
- [ ] Multi-color layer support (3-5 colors)
- [ ] HPGL and G-code export
- [ ] WebSocket progress updates
- [ ] Preset management (save/load)
- [ ] Batch processing
- [ ] Desktop app (Tauri wrapper)

## Contributing

Contributions welcome! Please read AGENTS.md for development guidelines.

Key principles:
- No mocks in tests - use real data and processes
- Required parameters must be positional, not optional
- Clean code with comprehensive docstrings
- No inline comments if docstrings are well-written

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- U²-Net by Xuebin Qin et al.
- ImageTracerJS by András Jankovics
- vpype by Antoine Beyeler
- shadcn/ui component library
- FastAPI and React communities

---

**Built with ❤️ for the plotter and maker community**
