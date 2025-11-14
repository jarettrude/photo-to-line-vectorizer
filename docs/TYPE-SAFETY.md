# Type Safety Guide

This project maintains strict type safety between the Python backend (using Pydantic) and TypeScript frontend (using Zod).

## Architecture

**Backend (Source of Truth)**: Pydantic models in `backend/app/api/models.py`
**Frontend**: Zod schemas in `frontend/src/lib/schemas.ts`

## Keeping Types in Sync

### Manual Synchronization

When you modify Pydantic models, you **must** update the corresponding Zod schemas:

1. **Edit Pydantic model** in `backend/app/api/models.py`
2. **Update Zod schema** in `frontend/src/lib/schemas.ts` to match
3. **Run type checks** to verify:
   ```bash
   # Backend type check
   cd backend && uv run mypy app/

   # Frontend type check
   cd frontend && npm run type-check
   ```
4. **Run all tests**:
   ```bash
   # Backend tests
   cd backend && python -m pytest tests/

   # Frontend tests (if any)
   cd frontend && npm test
   ```

### Type Mapping Reference

| Pydantic | Zod | Notes |
|----------|-----|-------|
| `str` | `z.string()` | |
| `int` | `z.number().int()` | ⚠️ Must use `.int()` for integers |
| `float` | `z.number()` | |
| `bool` | `z.boolean()` | |
| `list[T]` | `z.array(T)` | |
| `dict[K, V]` | `z.record(K, V)` | |
| `T \| None` | `z.T().optional()` or `.nullable()` | Use `.nullable()` if backend sends `null` |
| `Literal["a", "b"]` | `z.enum(["a", "b"])` | |
| `Field(gt=0, le=100)` | `z.number().positive().max(100)` | Match all constraints |
| `tuple[int, int]` | `z.tuple([z.number().int(), z.number().int()])` | |

### Critical Validation Rules

1. **Integer vs Float**: Backend always uses `int` for counts/percentages → Frontend must use `.int()`
2. **Nullable Fields**: If Pydantic allows `None`, Zod must use `.nullable().optional()`
3. **URL Validation**: Backend may return paths, not full URLs → Use `z.string()` not `z.string().url()`
4. **Field Constraints**: All Pydantic `Field()` constraints must be replicated in Zod

## Pre-commit Hooks

All type checks run automatically before commits:

### Backend
- ✅ Ruff linting (`ruff check`)
- ✅ Ruff formatting (`ruff format`)
- ✅ MyPy type checking (`mypy app/`)
- ✅ Pytest tests (`pytest tests/`)

### Frontend
- ✅ ESLint (`eslint`)
- ✅ Prettier formatting (`prettier`)
- ✅ TypeScript type checking (`tsc --noEmit`)
- ✅ Build verification (`npm run build`)

## Current Type Schemas

### ProcessParams
**Required fields** (no defaults):
- `canvas_width_mm`: `0 < value ≤ 5000`
- `canvas_height_mm`: `0 < value ≤ 5000`
- `line_width_mm`: `0 < value ≤ 10`

**Optional fields** (with defaults):
- `isolate_subject`: boolean (default: false)
- `use_ml`: boolean (default: false)
- `edge_threshold`: tuple of (low, high) where `0 ≤ low < high ≤ 255` (default: [50, 150])
- `line_threshold`: `1 ≤ value ≤ 255` (default: 16)
- `merge_tolerance`: `0 ≤ value ≤ 10` (default: 0.5)
- `simplify_tolerance`: `0 ≤ value ≤ 10` (default: 0.2)
- `hatching_enabled`: boolean (default: false)
- `hatch_density`: `0 < value ≤ 10` (default: 2.0)
- `hatch_angle`: `-180 ≤ value ≤ 180` (default: 45)
- `darkness_threshold`: `0 ≤ value ≤ 255` (default: 100)

### Upload Response
```typescript
{
  job_id: string (UUID format)
  filename: string (min length 1)
  image_url: string (path, NOT full URL)
}
```

### Job Status Response
```typescript
{
  job_id: string (UUID)
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number (integer 0-100)
  result_url?: string (path, NOT full URL)
  stats?: {
    path_count: number (integer ≥ 0)
    total_length_mm: number (≥ 0)
    width_mm?: number | null (positive or null)
    height_mm?: number | null (positive or null)
  }
  error?: string
  device_used?: string
}
```

### WebSocket Message
```typescript
{
  type: 'progress' | 'complete' | 'error' | 'keepalive'
  job_id: string
  progress?: number (integer 0-100)
  stage?: string ('preprocessing' | 'line_extraction' | 'vectorizing' | 'optimizing' | 'export')
  message?: string
  result_url?: string
  stats?: JobStats
  error?: string
}
```

## Common Mistakes

### ❌ Wrong: Float for progress
```typescript
progress: z.number().min(0).max(100)  // Accepts 50.5
```

### ✅ Correct: Integer for progress
```typescript
progress: z.number().int().min(0).max(100)  // Only accepts 50
```

### ❌ Wrong: Rejecting null
```typescript
width_mm: z.number().positive().optional()  // Rejects null
```

### ✅ Correct: Accepting null
```typescript
width_mm: z.number().positive().nullable().optional()  // Accepts null
```

### ❌ Wrong: Strict URL validation
```typescript
image_url: z.string().url()  // Rejects "/api/uploads/..."
```

### ✅ Correct: Path string
```typescript
image_url: z.string().min(1)  // Accepts paths
```

## Testing Type Safety

### Manual Testing
```bash
# 1. Start backend
cd backend
uvicorn app.main:app --reload

# 2. Test API endpoints
curl -X POST http://localhost:8000/api/upload -F "file=@test.jpg"

# 3. Check response matches Zod schema (automatic via api.ts)
```

### Integration Tests
Create tests that validate actual API responses against Zod schemas:

```typescript
// frontend/src/lib/__tests__/api-validation.test.ts
import { describe, it, expect } from 'vitest'
import { JobStatusResponseSchema } from '../schemas'

describe('API Response Validation', () => {
  it('validates real backend response', async () => {
    const response = await fetch('http://localhost:8000/api/status/some-id')
    const data = await response.json()

    // This will throw if schema doesn't match
    const validated = JobStatusResponseSchema.parse(data)
    expect(validated).toBeDefined()
  })
})
```

## Future: Automated Type Generation

For fully automated type sync, consider:

1. **OpenAPI Schema Export** (Recommended)
   ```bash
   # Generate OpenAPI schema
   python -c "from app.main import app; import json; print(json.dumps(app.openapi()))" > openapi.json

   # Convert to TypeScript
   npx openapi-typescript openapi.json -o src/lib/generated-types.ts
   ```

2. **Pydantic to TypeScript Tools**
   - [`pydantic-to-typescript`](https://github.com/phillipdupuis/pydantic-to-typescript)
   - [`datamodel-code-generator`](https://github.com/koxudaxi/datamodel-code-generator)

## Troubleshooting

### "Invalid response from server"
- Check browser console for Zod validation errors
- Compare actual response with expected schema
- Verify Pydantic model matches Zod schema

### Type check failures
```bash
# Backend
cd backend && uv run mypy app/ --show-error-codes

# Frontend
cd frontend && npm run type-check
```

### Pre-commit hook failures
```bash
# Run all hooks manually
pre-commit run --all-files

# Run specific hook
pre-commit run backend-mypy --all-files
pre-commit run frontend-type-check --all-files
```

## Resources

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Zod Documentation](https://zod.dev/)
- [FastAPI OpenAPI](https://fastapi.tiangolo.com/advanced/extending-openapi/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
