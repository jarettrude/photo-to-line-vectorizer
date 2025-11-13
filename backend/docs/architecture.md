# System Architecture

## Overview

Photo-to-line-vectorizer is a full-stack application that converts photographs into single-line SVG drawings optimized for pen plotters and CNC machines.

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                            │
│  React + TypeScript + Vite + TailwindCSS + shadcn/ui       │
│                                                             │
│  Components:                                                │
│  ├── Upload (drag-drop, format validation)                 │
│  ├── Controls (parameter configuration)                    │
│  └── Preview (status, SVG display, download)               │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP REST API
                          │ (Future: WebSocket)
┌─────────────────────────┴───────────────────────────────────┐
│                         Backend                             │
│       FastAPI + Python 3.14 + PyTorch + OpenCV             │
│                                                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │           API Layer (endpoints.py)                 │    │
│  │  - HTTP request handling                           │    │
│  │  - Rate limiting                                   │    │
│  │  - Input validation                                │    │
│  └──────────────┬─────────────────────────────────────┘    │
│                 │ Depends()                                 │
│  ┌──────────────┴─────────────────────────────────────┐    │
│  │         Service Layer (job_service.py)             │    │
│  │  - Business logic orchestration                    │    │
│  │  - Job lifecycle management                        │    │
│  │  - Error handling & validation                     │    │
│  └──────────┬───────────────────────┬─────────────────┘    │
│             │                       │                       │
│  ┌──────────┴──────────┐  ┌────────┴───────────────┐       │
│  │  Storage (jobs.py)  │  │ Processor (pipeline/)  │       │
│  │  - Redis/In-memory  │  │ - Image preprocessing  │       │
│  │  - Job state        │  │ - Line extraction      │       │
│  │  - File management  │  │ - Vectorization        │       │
│  └─────────────────────┘  │ - Optimization         │       │
│                            │ - SVG export           │       │
│                            └────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## Architecture Patterns

### Clean Architecture

The system follows clean architecture principles with clear separation of concerns:

**Layer 1: HTTP/Presentation** (`api/endpoints.py`)
- Handles HTTP protocol concerns
- Rate limiting, CORS, authentication (future)
- Request/response serialization
- Minimal logic, delegates to service layer

**Layer 2: Business Logic** (`services/job_service.py`)
- Orchestrates business workflows
- Enforces business rules
- Handles errors and edge cases
- Independent of HTTP and storage details

**Layer 3: Data Access** (`storage/jobs.py`)
- Abstract storage interface
- Supports multiple backends (Redis, in-memory)
- Single source of truth for job state
- No business logic

**Layer 4: Domain/Pipeline** (`pipeline/`)
- Core image processing algorithms
- Pure functions where possible
- No knowledge of jobs, HTTP, or storage
- Reusable across different contexts

**Benefits:**
- Testable (each layer can be unit tested in isolation)
- Maintainable (clear boundaries, single responsibility)
- Extensible (add new storage backends, API endpoints, etc.)
- Independent (layers don't depend on implementation details)

### Dependency Injection

Uses FastAPI's built-in dependency injection:

```python
# Define dependencies
@lru_cache
def get_processor() -> PhotoToLineProcessor:
    return PhotoToLineProcessor()

def get_job_service(
    storage: JobStorage = Depends(get_job_storage),
    processor: PhotoToLineProcessor = Depends(get_processor),
) -> JobService:
    return JobService(storage=storage, processor=processor)

# Inject into endpoints
@router.post("/process/{job_id}")
async def process_image(
    job_id: str,
    job_service: JobService = Depends(get_job_service),
):
    # Use injected service...
```

**Benefits:**
- Testable (inject mocks during testing)
- Singleton management (via `@lru_cache`)
- Clear dependency graph
- No global state

### Async/Background Processing

```
┌─────────┐          ┌─────────┐         ┌──────────┐
│ Client  │          │  API    │         │ Worker   │
└────┬────┘          └────┬────┘         └────┬─────┘
     │ POST /upload       │                   │
     │───────────────────>│                   │
     │ 200 {job_id}       │                   │
     │<───────────────────│                   │
     │                    │                   │
     │ POST /process      │                   │
     │───────────────────>│                   │
     │ 202 Accepted       │ BackgroundTask    │
     │<───────────────────│──────────────────>│
     │                    │                   │ (Processing)
     │ GET /status        │                   │
     │───────────────────>│                   │
     │ {status:processing}│                   │
     │<───────────────────│                   │
     │                    │                   │
     │ GET /status        │                   │
     │───────────────────>│                   │
     │ {status:completed} │                   │
     │<───────────────────│<──────────────────│
     │                    │                   │
     │ GET /download      │                   │
     │───────────────────>│                   │
     │ SVG file           │                   │
     │<───────────────────│                   │
```

**Key Points:**
- Non-blocking: API responds immediately with 202 Accepted
- Background tasks: FastAPI `BackgroundTasks` for async processing
- Progress tracking: Polling `/status` for real-time updates
- Future: WebSocket for push-based progress updates

## Data Flow

### Upload → Process → Download Flow

**1. Upload Phase**
```
Client File → API Validation → Storage (disk + Redis) → job_id
```

**2. Process Phase**
```
job_id → Load Image → Preprocessing → Line Extraction
                                            ↓
                                    Vectorization
                                            ↓
                                    Optimization
                                            ↓
                                    Export SVG
                                            ↓
                                Storage (disk + Redis stats)
```

**3. Status Phase**
```
job_id → Redis lookup → Job state + progress → Client
```

**4. Download Phase**
```
job_id → File path lookup → Stream SVG file → Client
```

### Processing Pipeline Detail

```
Photo (JPEG/PNG/HEIC)
        ↓
┌───────────────────┐
│  Preprocessing    │  - Load image (PIL + pillow-heif)
│  preprocess.py    │  - Convert to RGB numpy array
│                   │  - Optional: U²-Net subject isolation
└─────────┬─────────┘
          ↓
┌───────────────────┐
│ Line Extraction   │  - Bilateral filtering or Gaussian blur
│ line_extraction.py│  - Canny edge detection
│ classical_cv.py   │  - OR XDoG for stylized lines
└─────────┬─────────┘
          ↓
     Binary Line Art (255 = line, 0 = bg)
          ↓
┌───────────────────┐
│  Vectorization    │  - Save to temp PNG
│  vectorize.py     │  - Call ImageTracerJS via Node.js
│                   │  - Parse SVG output
└─────────┬─────────┘
          ↓
     SVG Paths (unoptimized)
          ↓
┌───────────────────┐
│  Optimization     │  - Load into vpype Document
│  optimize.py      │  - Merge close endpoints
│                   │  - Simplify paths (Douglas-Peucker)
│                   │  - Reorder for plotting (TSP)
│                   │  - Filter short paths
└─────────┬─────────┘
          ↓
┌───────────────────┐
│  Hatching         │  - Analyze grayscale image
│  hatching.py      │  - Generate parallel hatch lines
│  (optional)       │  - Clip to dark regions
└─────────┬─────────┘
          ↓
┌───────────────────┐
│  Export           │  - Set canvas dimensions
│  export.py        │  - Calculate statistics
│                   │  - Generate SVG string
│                   │  - Add metadata
└─────────┬─────────┘
          ↓
   Optimized SVG (ready for plotting)
```

## Storage Architecture

### Job State Management

**Storage Interface:** Abstract interface supporting multiple backends

```python
class JobStorage(ABC):
    @abstractmethod
    def create_job(self, job_id: str, filename: str, file_path: Path): ...

    @abstractmethod
    def get_job(self, job_id: str) -> dict | None: ...

    @abstractmethod
    def set_status(self, job_id: str, status: str, progress: int): ...

    @abstractmethod
    def set_result(self, job_id: str, result_url: str, stats: dict): ...
```

**Implementations:**
1. **RedisJobStorage** (production)
   - High performance in-memory storage
   - Persistence to disk (RDB + AOF)
   - TTL support for automatic cleanup
   - Pub/Sub for real-time updates (future)

2. **InMemoryJobStorage** (development/testing)
   - Python dict-based storage
   - No external dependencies
   - Ephemeral (lost on restart)
   - Good for unit tests

**Job State Schema:**
```python
{
    "job_id": str,           # UUID
    "filename": str,         # Original filename
    "file_path": str,        # Path to uploaded file
    "status": str,           # "pending" | "processing" | "completed" | "failed"
    "progress": int,         # 0-100
    "result_url": str | None, # "/api/uploads/{job_id}.svg"
    "stats": {               # Processing statistics
        "path_count": int,
        "total_length_mm": float,
        "width_mm": float | None,
        "height_mm": float | None,
    } | None,
    "error": str | None,     # Error message if failed
    "device_used": str | None, # "cuda" | "mps" | "cpu"
}
```

### File Storage

**Directory Structure:**
```
backend/uploads/
├── {job_id}.jpg          # Original upload
├── {job_id}.svg          # Processed result
└── {job_id}.gcode        # Future: G-code export
```

**File Naming:**
- Uses job_id (UUID) as filename
- Prevents path traversal attacks
- Easy cleanup by job_id
- Supports multiple formats per job

**Cleanup Strategy (Future):**
- TTL in Redis (e.g., 24 hours)
- Cron job to delete expired files
- Archive old results to S3/object storage

## Device Management

### Hardware Acceleration

```python
Priority Order:
1. CUDA (NVIDIA GPUs) → Best for ML inference
2. MPS (Apple Metal) → Good for M1/M2/M3 Macs
3. CPU (fallback) → Always available, slower

Auto-detection at startup:
INFO: Using device: cuda (NVIDIA GeForce RTX 3080)
```

**Device Manager:**
- Singleton pattern (`device_manager`)
- Lazy model loading
- Automatic device placement
- Fallback on OOM errors

**Models Using GPU:**
- U²-Net (subject isolation) - ~500MB VRAM
- Future: Informative Drawings ML model

**CPU-Only Operations:**
- OpenCV (Canny, bilateral filtering)
- ImageTracerJS (Node.js subprocess)
- Vpype optimization (Python)

## Security Architecture

### Input Validation

**File Upload:**
- Extension whitelist (.jpg, .png, .tiff, .webp, .heic, .heif)
- File size limit (50MB default)
- Future: Magic byte validation
- Filename sanitization (UUIDs)

**API Parameters:**
- Pydantic models for request validation
- Range constraints (e.g., canvas 10-2000mm)
- Type safety (TypeScript → Pydantic → processor)

**Job IDs:**
- UUID format validation
- Regex pattern matching
- Prevents path traversal (no `../` possible)

### Rate Limiting

**Per-Endpoint Limits:**
- `/upload`: 10/minute (configurable)
- `/process`: 5/minute (configurable)
- Per IP address using `slowapi`

**Protection Against:**
- Brute force attacks
- Resource exhaustion
- DoS via large uploads

### Future: Authentication

Auth module exists (`app/auth/`) but not yet enforced:
- User registration/login
- JWT tokens
- Role-based access control
- Per-user rate limits
- Job ownership validation

## Scalability Considerations

### Current Limitations

**Single Instance:**
- One FastAPI process
- Background tasks in same process
- Limited to one server's resources

**Bottlenecks:**
1. CPU-bound: ImageTracerJS, vpype optimization
2. GPU-bound: U²-Net inference (if enabled)
3. I/O-bound: File uploads/downloads
4. Memory: Large images (>4K resolution)

### Future: Horizontal Scaling

```
┌─────────┐     ┌────────────┐
│ Client  │────>│ Load       │
└─────────┘     │ Balancer   │
                └──────┬─────┘
                       │
         ┌─────────────┼─────────────┐
         ↓             ↓             ↓
   ┌─────────┐   ┌─────────┐   ┌─────────┐
   │ API     │   │ API     │   │ API     │
   │ Server 1│   │ Server 2│   │ Server 3│
   └────┬────┘   └────┬────┘   └────┬────┘
        │             │             │
        └─────────────┼─────────────┘
                      ↓
           ┌──────────────────┐
           │  Shared Redis    │
           │  (job state)     │
           └──────────────────┘
                      ↓
           ┌──────────────────┐
           │  Shared Storage  │
           │  (S3/NFS)        │
           └──────────────────┘
                      ↓
           ┌──────────────────┐
           │  Worker Pool     │
           │  (Celery/RQ)     │
           └──────────────────┘
```

**Required Changes:**
1. Replace FastAPI `BackgroundTasks` with Celery/RQ
2. Shared file storage (S3, NFS, or object storage)
3. Redis for shared state (already supported)
4. Load balancer (nginx, HAProxy)
5. WebSocket sticky sessions

## Technology Stack

### Backend

**Core Framework:**
- FastAPI - Modern async web framework
- Python 3.14 - Free-threaded execution
- Pydantic v2 - Validation and serialization
- Uvicorn - ASGI server

**Image Processing:**
- PyTorch - ML inference (U²-Net)
- OpenCV - Classical CV operations
- NumPy - Numerical operations
- Pillow - Image I/O
- pillow-heif - HEIC/HEIF support

**Vectorization:**
- ImageTracerJS - Raster to vector (via Node.js)
- vpype - Path optimization, plotting preparation

**Storage:**
- Redis - Job state (production)
- File system - Image/SVG storage

**Testing:**
- pytest - Test framework
- pytest-asyncio - Async test support
- pytest-cov - Coverage reporting

### Frontend

**Core Framework:**
- React 18 - UI library
- TypeScript - Type safety
- Vite - Build tool and dev server

**UI Components:**
- shadcn/ui - Component library
- Radix UI - Accessible primitives
- TailwindCSS - Utility-first styling
- Lucide React - Icon library

**State Management:**
- React hooks (useState, useEffect)
- Future: Zustand or Redux for complex state

**Testing:**
- Vitest - Test runner
- React Testing Library - Component testing
- Storybook - Component documentation

**HTTP Client:**
- Fetch API - Native browser API
- Future: React Query for caching

## Development Workflow

### Local Development

**Backend:**
```bash
cd backend
uv pip install -r requirements-dev.in
python -m app.main  # or uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev  # Vite dev server on :5173
```

**Full Stack:**
```bash
# Terminal 1: Backend
cd backend && python -m app.main

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Redis (if using)
redis-server
```

### Testing

**Backend:**
```bash
# Unit tests (fast, mocked)
pytest tests/unit/ -v

# Integration tests (slow, real images)
pytest tests/integration/ -v -m "not requires_ml"

# With ML model
pytest tests/integration/ -v

# Coverage
pytest --cov=app --cov-report=html
```

**Frontend:**
```bash
# Unit tests
npm run test

# Watch mode
npm run test:watch

# Coverage
npm run test:coverage
```

### Code Quality

**Backend:**
```bash
# Linting
ruff check app/ tests/

# Formatting
ruff format app/ tests/

# Type checking
mypy app/

# All checks
pre-commit run --all-files
```

**Frontend:**
```bash
# Linting
npm run lint

# Type checking
npm run type-check

# Formatting
npm run format
```

## Deployment

### Production Build

**Backend:**
```bash
# Compile requirements
uv pip compile requirements.in -o requirements.txt

# Install dependencies
pip install -r requirements.txt

# Run with production server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

**Frontend:**
```bash
# Build for production
npm run build

# Preview build
npm run preview

# Deploy to CDN/static hosting
```

### Environment Variables

**Backend (.env):**
```bash
# Server
PORT=8000
HOST=0.0.0.0

# Storage
REDIS_URL=redis://localhost:6379/0
UPLOAD_DIR=./uploads

# Processing
U2NET_MODEL_PATH=./models/u2net.pth
MAX_UPLOAD_SIZE_MB=50

# Rate Limiting
RATE_LIMIT_UPLOADS=10/minute
RATE_LIMIT_PROCESS=5/minute

# CORS
CORS_ORIGINS=http://localhost:5173,https://example.com
```

**Frontend (.env):**
```bash
VITE_API_URL=http://localhost:8000/api
```

### Docker Deployment (Future)

```dockerfile
# Multi-stage build for small image size
FROM python:3.14-slim AS backend
# ... install dependencies, copy code

FROM node:20-alpine AS frontend
# ... build frontend

FROM nginx:alpine
# ... serve frontend, proxy to backend
```

## Monitoring & Observability (Future)

### Logging

**Current:**
- Python `logging` module
- Console output with timestamps
- Log levels: DEBUG, INFO, WARNING, ERROR

**Future:**
- Structured JSON logging (structlog)
- Log aggregation (ELK stack, Datadog)
- Request ID tracing

### Metrics

**Future Metrics:**
- Request latency (p50, p95, p99)
- Processing time per stage
- Success/failure rates
- Queue depth (if using Celery)
- GPU utilization
- File storage usage

**Tools:**
- Prometheus for metrics collection
- Grafana for visualization
- Alert Manager for notifications

### Tracing

**Future:**
- OpenTelemetry for distributed tracing
- Trace requests across API → Service → Processor
- Identify bottlenecks in pipeline

## Related Documentation

- [`processor.md`](./processor.md) - Processing pipeline details
- [`api-endpoints.md`](./api-endpoints.md) - REST API reference
- [`../README.md`](../README.md) - Project overview and setup
