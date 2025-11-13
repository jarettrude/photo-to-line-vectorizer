---
trigger: always_on
---

# Full-Stack Integration - Photo to Line Vectorizer

## Communication Flow
```
React Frontend (Vite)  ←→  FastAPI Backend
     Port 5173                Port 8000
```

## REST API Integration
- **Backend**: FastAPI with REST endpoints (`/api/*`)
- **Frontend**: Native `fetch()` API with TanStack Query for caching
- **Real-time**: Polling (currently), WebSocket progress (planned)
- **Type Safety**: Pydantic models (server) → TypeScript interfaces (client) → Zod schemas (to add)

## Data Model Synchronization
```
Backend (Python)                 Frontend (TypeScript)
├── Pydantic Models             ├── TypeScript Interfaces
│   └── ProcessingParams        │   └── ProcessParams
│   └── JobStatusResponse       │   └── JobStatusResponse
├── FastAPI Validators          ├── Zod Schemas (to be added)
└── Database (Redis/SQLite)     └── TanStack Query Cache
```

## Authentication Flow (Optional, Disabled by Default)
1. **Magic Link**: FastAPI-Users with Resend email
2. **Storage**: JWT in cookies
3. **Validation**: FastAPI dependency injection
4. **Enable**: Set `AUTH_ENABLED=true` in backend .env

## Development Workflow
1. Define Pydantic model in Backend (`app/api/models.py`)
2. Create matching TypeScript interface in Frontend (`lib/api.ts`)
3. Add Zod schema for runtime validation (to be implemented)
4. Use TanStack Query hooks for API calls
5. Components consume typed data

## Key Integration Points
- `POST /api/upload` - Image upload endpoint
- `POST /api/process` - Start processing with parameters
- `GET /api/status/{job_id}` - Poll for job status
- `GET /api/download/{job_id}?format=svg|hpgl|gcode` - Download result
- `WebSocket /ws/{job_id}` - Real-time progress (planned)

## Environment Configuration

### Frontend (.env)
```bash
VITE_API_URL=http://localhost:8000
```

### Backend (.env)
```bash
HOST=0.0.0.0
PORT=8000
DEBUG=True

# CORS
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Storage
REDIS_URL=redis://redis:6379/0  # None for in-memory fallback
UPLOAD_DIR=./temp/uploads
RESULTS_DIR=./temp/results
MAX_UPLOAD_SIZE_MB=50

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_UPLOADS=10/minute
RATE_LIMIT_PROCESSING=5/minute

# Authentication (Optional)
AUTH_ENABLED=false
SECRET_KEY=changeme-in-production
RESEND_API_KEY=re_xxxxx
RESEND_FROM_EMAIL=noreply@yourdomain.com
FRONTEND_URL=http://localhost:5173

# Models
U2NET_MODEL_PATH=../models/u2net/pytorch/u2netp.pth
INFORMATIVE_DRAWINGS_MODEL_PATH=../models/informative-drawings/checkpoints/netG_A_sketch.pth
```

## Type Safety Strategy
```
Pydantic (Backend) → OpenAPI Schema → TypeScript Types (Frontend) → Zod Runtime Validation
```

**Recommended**: Generate TypeScript types from OpenAPI spec using `openapi-typescript` or `fastapi-codegen`
