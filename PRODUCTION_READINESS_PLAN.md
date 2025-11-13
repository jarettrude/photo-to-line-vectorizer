# Production Readiness Plan
**Date**: 2025-11-13
**Status**: Comprehensive audit and refactoring plan
**Goal**: Production-ready code with security, modularity, testing, and documentation

---

## Executive Summary

After comprehensive review of the codebase against industry best practices and `.windsurf/rules`, I've identified critical areas requiring refactoring and enhancement to achieve production quality. This is a **full production-readiness** transformation, not shortcuts.

**Current Status**: ~65% production-ready (security done, features 70% complete, tests 0%, frontend untested)
**Target**: 95%+ production-ready (modular backend, comprehensive tests, Storybook, full documentation)
**Estimated Time**: 16-24 hours of focused development

---

## Critical Findings

### ✅ STRENGTHS (What's Working Well)
1. **Security**: CORS, rate limiting, input validation, Redis storage all properly implemented
2. **Architecture**: Clean separation of concerns in pipeline modules
3. **Code Quality**: Ruff linting passes with zero errors
4. **Documentation**: Comprehensive markdown docs for features and architecture
5. **Privacy-First**: Local processing, no cloud uploads by default

### ⚠️ CRITICAL ISSUES (Must Fix)
1. **No Backend Tests Running**: Dependencies not installed, 0% test coverage
2. **No Frontend Tests**: Zero test files, no Storybook, untested components
3. **No Type Safety on Frontend**: TypeScript interfaces without Zod runtime validation
4. **Monolithic Endpoints**: Business logic mixed with API layer (violates clean architecture)
5. **Global State in Endpoints**: Module-level `_processor` singleton (not testable)
6. **Incomplete Documentation**: Some rules outdated (GraphQL references fixed)

### ⚡ MODERATE ISSUES (Should Fix)
7. **No Service Layer**: Missing separation between controllers and business logic
8. **No Repository Pattern**: Storage access scattered across endpoint code
9. **Missing WebSocket Progress**: Still using polling (on roadmap)
10. **ML Model Not Implemented**: Informative Drawings model unused
11. **No Multi-Color Support**: K-means color quantization missing
12. **No Component Documentation**: Missing Storybook stories

---

## Architecture Refactoring Plan

### Current Architecture (Problematic)
```
┌──────────────────┐
│   API Endpoint   │  ← Business logic mixed in
│  (endpoints.py)  │  ← Direct storage access
│                  │  ← Global singleton processor
└──────────────────┘
         ↓
┌──────────────────┐
│    Pipeline      │  ← Tightly coupled
│   (processor.py) │
└──────────────────┘
```

### Target Architecture (Clean & Modular)
```
┌──────────────────┐
│   API Endpoint   │  ← Only request/response handling
│  (endpoints.py)  │  ← Dependency injection
└────────┬─────────┘
         ↓
┌──────────────────┐
│  Service Layer   │  ← Business logic & orchestration
│ (services/*.py)  │  ← Transaction management
└────────┬─────────┘
         ↓
┌──────────────────┐
│   Repository     │  ← Data access abstraction
│ (repositories/*) │  ← Storage interface
└────────┬─────────┘
         ↓
┌──────────────────┐
│   Pipeline       │  ← Domain logic only
│ (pipeline/*.py)  │  ← No external dependencies
└──────────────────┘
```

### Benefits of Refactoring
- **Testability**: Each layer independently testable
- **Maintainability**: Clear separation of concerns
- **Scalability**: Easy to add features without breaking existing code
- **Dependency Injection**: No global state, better for testing

---

## Detailed Refactoring Tasks

### 1. Backend Service Layer & Repository Pattern

#### 1.1 Create Service Layer
```python
# backend/app/services/job_service.py
class JobService:
    def __init__(self, job_repo: JobRepository, processor: PhotoToLineProcessor):
        self.job_repo = job_repo
        self.processor = processor

    async def create_job(self, file: UploadFile) -> Job:
        """Create job with validation"""
        # Business logic here

    async def process_job(self, job_id: str, params: ProcessingParams) -> None:
        """Process job with error handling"""
        # Orchestration logic here
```

#### 1.2 Create Repository Layer
```python
# backend/app/repositories/job_repository.py
class JobRepository(ABC):
    @abstractmethod
    async def create(self, job: JobCreate) -> Job:
        pass

    @abstractmethod
    async def get_by_id(self, job_id: str) -> Job | None:
        pass

    # ... other CRUD methods

# backend/app/repositories/redis_job_repository.py
class RedisJobRepository(JobRepository):
    """Redis implementation"""

# backend/app/repositories/memory_job_repository.py
class InMemoryJobRepository(JobRepository):
    """In-memory fallback"""
```

#### 1.3 Dependency Injection
```python
# backend/app/dependencies.py
from fastapi import Depends

def get_job_repository() -> JobRepository:
    if settings.redis_url:
        return RedisJobRepository(settings.redis_url)
    return InMemoryJobRepository()

def get_processor() -> PhotoToLineProcessor:
    return PhotoToLineProcessor(
        u2net_model_path=settings.u2net_model_path
    )

def get_job_service(
    repo: JobRepository = Depends(get_job_repository),
    processor: PhotoToLineProcessor = Depends(get_processor)
) -> JobService:
    return JobService(repo, processor)
```

#### 1.4 Refactored Endpoint
```python
# backend/app/api/endpoints.py (after refactoring)
@router.post("/process")
async def process_image(
    body: ProcessRequest,
    job_service: JobService = Depends(get_job_service)
) -> ProcessResponse:
    """Process image - now just delegates to service"""
    return await job_service.process_image(body.job_id, body.params)
```

### 2. Frontend Type Safety with Zod

#### 2.1 Add Zod Schemas
```typescript
// frontend/src/lib/schemas.ts
import { z } from 'zod'

export const ProcessParamsSchema = z.object({
  canvas_width_mm: z.number().positive(),
  canvas_height_mm: z.number().positive(),
  line_width_mm: z.number().positive(),
  isolate_subject: z.boolean().optional(),
  use_ml: z.boolean().optional(),
  // ... rest of fields
})

export const JobStatusResponseSchema = z.object({
  job_id: z.string().uuid(),
  status: z.enum(['pending', 'processing', 'completed', 'failed']),
  progress: z.number().min(0).max(100),
  result_url: z.string().url().optional(),
  // ... rest of fields
})

export type ProcessParams = z.infer<typeof ProcessParamsSchema>
export type JobStatusResponse = z.infer<typeof JobStatusResponseSchema>
```

#### 2.2 Validate API Responses
```typescript
// frontend/src/lib/api.ts (with Zod)
export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  const response = await fetch(`${API_BASE}/status/${jobId}`)

  if (!response.ok) {
    throw new Error('Failed to get status')
  }

  const data = await response.json()

  // Runtime validation
  return JobStatusResponseSchema.parse(data)
}
```

### 3. Frontend Testing & Storybook

#### 3.1 Install Dependencies
```bash
npm install -D @storybook/react @storybook/blocks @storybook/test
npm install -D @storybook/addon-essentials @storybook/addon-a11y
npm install -D vitest @vitest/ui @testing-library/react
npm install -D @testing-library/jest-dom @testing-library/user-event
npm install -D msw  # Mock Service Worker for API mocking
npm install zod  # Runtime validation
```

#### 3.2 Storybook Configuration
```typescript
// .storybook/main.ts
import type { StorybookConfig } from '@storybook/react-vite'

const config: StorybookConfig = {
  stories: ['../src/**/*.stories.@(js|jsx|ts|tsx)'],
  addons: [
    '@storybook/addon-essentials',
    '@storybook/addon-a11y',
    '@storybook/addon-interactions',
  ],
  framework: '@storybook/react-vite',
}

export default config
```

#### 3.3 Component Tests
```typescript
// frontend/src/components/Upload.test.tsx
import { describe, it, expect } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Upload } from './Upload'

describe('Upload Component', () => {
  it('renders upload area', () => {
    render(<Upload onUploadComplete={() => {}} />)
    expect(screen.getByText(/drag.*drop/i)).toBeInTheDocument()
  })

  it('handles file upload', async () => {
    const onUploadComplete = vi.fn()
    render(<Upload onUploadComplete={onUploadComplete} />)

    const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
    const input = screen.getByLabelText(/upload/i)

    await userEvent.upload(input, file)
    await waitFor(() => expect(onUploadComplete).toHaveBeenCalled())
  })

  it('rejects invalid file types', async () => {
    render(<Upload onUploadComplete={() => {}} />)

    const file = new File(['test'], 'test.txt', { type: 'text/plain' })
    const input = screen.getByLabelText(/upload/i)

    await userEvent.upload(input, file)
    expect(screen.getByText(/unsupported/i)).toBeInTheDocument()
  })
})
```

#### 3.4 Storybook Stories
```typescript
// frontend/src/components/Upload.stories.tsx
import type { Meta, StoryObj } from '@storybook/react'
import { Upload } from './Upload'

const meta: Meta<typeof Upload> = {
  title: 'Components/Upload',
  component: Upload,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj<typeof Upload>

export const Default: Story = {
  args: {
    onUploadComplete: () => console.log('Upload complete'),
  },
}

export const WithError: Story = {
  args: {
    onUploadComplete: () => console.log('Upload complete'),
  },
  play: async ({ canvasElement }) => {
    // Test interactions
  },
}
```

### 4. Backend Testing Setup

#### 4.1 Install Dependencies
```bash
cd backend
pip install pytest pytest-asyncio pytest-cov httpx
pip install -r requirements.txt  # All production dependencies
```

#### 4.2 Test Configuration
```ini
# backend/pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
```

#### 4.3 Test Structure
```
backend/tests/
├── conftest.py              # Fixtures
├── unit/
│   ├── test_services.py     # Service layer tests
│   ├── test_repositories.py # Repository tests
│   └── test_pipeline.py     # Pipeline logic tests
├── integration/
│   ├── test_api.py          # API endpoint tests
│   └── test_processor.py    # End-to-end pipeline tests
└── fixtures/
    └── sample_images/       # Test images
```

#### 4.4 Example Service Test
```python
# backend/tests/unit/test_job_service.py
import pytest
from app.services.job_service import JobService
from app.repositories.memory_job_repository import InMemoryJobRepository

@pytest.fixture
def job_service():
    repo = InMemoryJobRepository()
    processor = Mock(spec=PhotoToLineProcessor)
    return JobService(repo, processor)

async def test_create_job_validates_file_size(job_service):
    large_file = create_large_file(size_mb=100)  # Over limit

    with pytest.raises(ValueError, match="File too large"):
        await job_service.create_job(large_file)

async def test_process_job_updates_status(job_service):
    job = await job_service.create_job(valid_file)

    await job_service.process_job(job.id, default_params)

    updated_job = await job_service.get_job(job.id)
    assert updated_job.status == ProcessingStatus.COMPLETED
```

### 5. Documentation Requirements

#### 5.1 Backend Module Documentation
Each module needs a `.md` file:
```
backend/app/services/README.md
backend/app/repositories/README.md
backend/app/pipeline/README.md
```

#### 5.2 Docstring Standards
```python
def process_image(
    image_path: Path,
    canvas_width_mm: float,
    canvas_height_mm: float,
    line_width_mm: float,
) -> ProcessingResult:
    """
    Process image through complete pipeline.

    Executes preprocessing, line extraction, vectorization, optimization,
    and optional hatching to produce plotter-ready SVG output.

    Args:
        image_path: Path to input image file (JPEG, PNG, TIFF, WebP, HEIC)
        canvas_width_mm: Target canvas width in millimeters (required)
        canvas_height_mm: Target canvas height in millimeters (required)
        line_width_mm: Pen/laser line width in millimeters (required)

    Returns:
        ProcessingResult containing:
            - svg_content: Optimized SVG string
            - stats: Path count, total length, dimensions
            - device_used: GPU/CPU device name

    Raises:
        ValueError: If required parameters missing or invalid
        RuntimeError: If processing fails at any stage

    Example:
        >>> result = processor.process_image(
        ...     Path("photo.jpg"),
        ...     canvas_width_mm=300.0,
        ...     canvas_height_mm=200.0,
        ...     line_width_mm=0.3,
        ... )
        >>> print(f"Created {result.stats['path_count']} paths")

    Note:
        Canvas dimensions are required positional parameters.
        No default values to prevent silent unit coercion errors.
    """
```

---

## Implementation Priority

### Phase 1: Critical Infrastructure (8-10 hours)
1. ✅ Update .windsurf/rules (DONE)
2. Install all dependencies (backend + frontend)
3. Refactor backend: Service layer + Repository pattern
4. Add Zod schemas to frontend
5. Set up Vitest + React Testing Library
6. Set up Storybook

### Phase 2: Comprehensive Testing (6-8 hours)
7. Write backend unit tests (services, repositories)
8. Write backend integration tests (API endpoints)
9. Write frontend component tests (Upload, Controls, Preview)
10. Create Storybook stories for all components
11. Achieve 90%+ test coverage

### Phase 3: Missing Features (4-6 hours)
12. Implement WebSocket progress updates
13. Implement Informative Drawings ML model
14. Implement K-means multi-color support

### Phase 4: Documentation & Polish (2-3 hours)
15. Add comprehensive docstrings
16. Create module-level documentation
17. Update README with testing instructions
18. Pre-commit hooks and final quality checks

---

## Quality Gates

### Before Merge to Main
- [ ] All tests passing (backend + frontend)
- [ ] Test coverage > 90% (backend), > 80% (frontend)
- [ ] Ruff linting passes with zero errors
- [ ] ESLint + Prettier passes with zero errors
- [ ] All Storybook stories render correctly
- [ ] Pre-commit hooks configured and passing
- [ ] Documentation complete (docstrings + .md files)
- [ ] No TODO comments remaining
- [ ] Environment variables documented
- [ ] Docker build succeeds
- [ ] Manual smoke test of full pipeline

### Security Checklist
- [x] CORS properly configured
- [x] Rate limiting enabled
- [x] Input validation (UUID, file size, file types)
- [x] Subprocess injection prevented
- [x] No secrets in code
- [ ] Environment variables validation
- [ ] Error messages don't leak internals
- [ ] File cleanup on errors

### Performance Targets
- Classical CV: < 5s (1920×1080 image)
- ML with GPU: < 15s
- ML with CPU: < 45s
- Path count: < 2000 for portraits
- Line merge efficiency: > 80%

---

## Testing Coverage Goals

### Backend
- **Services**: 95%+ coverage (business logic critical)
- **Repositories**: 90%+ coverage (data access layer)
- **Pipeline**: 90%+ coverage (domain logic)
- **API Endpoints**: 85%+ coverage (integration tests)
- **Models**: 100%+ coverage (data validation)

### Frontend
- **Components**: 80%+ coverage (UI interactions)
- **Hooks**: 90%+ coverage (state management)
- **API Client**: 95%+ coverage (external calls)
- **Utils**: 100%+ coverage (helper functions)

---

## Success Criteria

### Technical
- Clean architecture with proper separation of concerns
- Comprehensive test suite with high coverage
- All components documented and in Storybook
- Zero linting errors
- All critical security issues resolved

### User Experience
- Professional UI with Storybook documentation
- Clear error messages
- Responsive design
- Accessible (WCAG AA)
- Fast processing times within targets

### Deployment
- Docker Compose works out of the box
- Environment variables well-documented
- Health checks functional
- Graceful error handling
- Production-ready configuration

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Begin Phase 1** (Critical Infrastructure)
3. **Daily progress updates** via commit messages
4. **Code reviews** after each phase
5. **Final production deployment** after all quality gates pass

---

**This is production code. No shortcuts, no hacks. We're building the best photo-to-line vectorizer ever made.**
