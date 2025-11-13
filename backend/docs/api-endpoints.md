# API Endpoints

**Location:** `app/api/endpoints.py`

## Overview

RESTful API endpoints for the photo-to-line-vectorizer service. Follows clean architecture principles with HTTP concerns separated from business logic.

## Architecture

```
HTTP Layer (endpoints.py)
    ↓ Depends on
Service Layer (job_service.py)
    ↓ Uses
Storage Layer (jobs.py) + Processor (processor.py)
```

**Key Principles:**
- Endpoints only handle HTTP concerns (validation, serialization, rate limiting)
- Business logic delegated to `JobService`
- Dependency injection via FastAPI `Depends()`
- Rate limiting on upload/process endpoints
- Comprehensive error handling with appropriate status codes

## Base URL

```
http://localhost:8000/api
```

## Authentication

Currently no authentication required. Auth module exists (`app/auth/`) but is not enforced on these endpoints.

## Rate Limiting

Configured via environment variables:
- `RATE_LIMIT_UPLOADS` - Upload endpoint (default: "10/minute")
- `RATE_LIMIT_PROCESS` - Process endpoint (default: "5/minute")

Rate limits are per IP address using `slowapi`.

## Endpoints

### POST `/api/upload`

Upload an image file for processing.

**Request:**
- **Method:** POST
- **Content-Type:** `multipart/form-data`
- **Body:**
  - `file`: Image file (max 50MB)

**Supported Formats:**
- JPEG (.jpg, .jpeg)
- PNG (.png)
- TIFF (.tiff, .tif)
- WebP (.webp)
- HEIC/HEIF (.heic, .heif) - iPhone native format

**Response (200 OK):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "photo.jpg",
  "image_url": "/api/uploads/550e8400-e29b-41d4-a716-446655440000.jpg"
}
```

**Error Responses:**

**400 Bad Request** - Invalid file format:
```json
{
  "detail": "Unsupported file format: .bmp. Supported: .jpg, .jpeg, .png, ..."
}
```

**413 Payload Too Large** - File exceeds size limit:
```json
{
  "detail": "File too large (75.5 MB). Maximum size: 50 MB"
}
```

**429 Too Many Requests** - Rate limit exceeded:
```json
{
  "detail": "Rate limit exceeded: 10 per 1 minute"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@photo.jpg"
```

---

### POST `/api/process/{job_id}`

Start processing a previously uploaded image.

**Request:**
- **Method:** POST
- **Path Parameter:** `job_id` (UUID)
- **Content-Type:** `application/json`
- **Body:** Processing parameters (all required)

```json
{
  "canvas_width_mm": 300,
  "canvas_height_mm": 200,
  "line_width_mm": 0.3,
  "isolate_subject": false,
  "use_ml": false,
  "edge_threshold": [50, 150],
  "line_threshold": 16,
  "merge_tolerance": 0.5,
  "simplify_tolerance": 0.2,
  "hatching_enabled": false,
  "hatch_density": 2.0,
  "hatch_angle": 45,
  "darkness_threshold": 100
}
```

**Parameter Validation:**

| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `canvas_width_mm` | float | 10-2000 | 300 | Output width in mm |
| `canvas_height_mm` | float | 10-2000 | 200 | Output height in mm |
| `line_width_mm` | float | 0.1-5 | 0.3 | Stroke width in mm |
| `isolate_subject` | bool | - | false | Use U²-Net background removal |
| `use_ml` | bool | - | false | ML-assisted vectorization (future) |
| `edge_threshold` | [int, int] | [0-255, 0-255] | [50, 150] | Canny thresholds |
| `line_threshold` | int | 0-255 | 16 | Hough line sensitivity |
| `merge_tolerance` | float | 0-5 | 0.5 | Endpoint merge distance (mm) |
| `simplify_tolerance` | float | 0-5 | 0.2 | Path simplification (mm) |
| `hatching_enabled` | bool | - | false | Enable cross-hatching |
| `hatch_density` | float | 0.5-5 | 2.0 | Hatch line spacing |
| `hatch_angle` | int | 0-360 | 45 | Hatch angle in degrees |
| `darkness_threshold` | int | 0-255 | 100 | Hatching threshold |

**Response (202 Accepted):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Processing started"
}
```

**Error Responses:**

**400 Bad Request** - Invalid job ID format:
```json
{
  "detail": "Invalid job ID format"
}
```

**404 Not Found** - Job doesn't exist:
```json
{
  "detail": "Job not found"
}
```

**422 Validation Error** - Invalid parameters:
```json
{
  "detail": [
    {
      "loc": ["body", "canvas_width_mm"],
      "msg": "ensure this value is greater than or equal to 10",
      "type": "value_error.number.not_ge"
    }
  ]
}
```

**429 Too Many Requests** - Rate limit exceeded:
```json
{
  "detail": "Rate limit exceeded: 5 per 1 minute"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/process/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -d '{
    "canvas_width_mm": 300,
    "canvas_height_mm": 200,
    "line_width_mm": 0.3,
    "isolate_subject": false,
    "use_ml": false,
    "edge_threshold": [50, 150],
    "line_threshold": 16,
    "merge_tolerance": 0.5,
    "simplify_tolerance": 0.2,
    "hatching_enabled": false,
    "hatch_density": 2.0,
    "hatch_angle": 45,
    "darkness_threshold": 100
  }'
```

---

### GET `/api/status/{job_id}`

Get current status and progress of a processing job.

**Request:**
- **Method:** GET
- **Path Parameter:** `job_id` (UUID)

**Response (200 OK):**

**Status: pending** (not yet processed):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "progress": 0,
  "result_url": null,
  "stats": null,
  "error": null,
  "device_used": null
}
```

**Status: processing** (in progress):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 45,
  "result_url": null,
  "stats": null,
  "error": null,
  "device_used": "cuda"
}
```

**Status: completed** (success):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "result_url": "/api/uploads/550e8400-e29b-41d4-a716-446655440000.svg",
  "stats": {
    "path_count": 42,
    "total_length_mm": 1234.56,
    "width_mm": 200.0,
    "height_mm": 150.0
  },
  "error": null,
  "device_used": "cuda"
}
```

**Status: failed** (error occurred):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "progress": 0,
  "result_url": null,
  "stats": null,
  "error": "Out of memory: Image resolution too high",
  "device_used": "cuda"
}
```

**Error Responses:**

**400 Bad Request** - Invalid job ID format:
```json
{
  "detail": "Invalid job ID format"
}
```

**404 Not Found** - Job doesn't exist:
```json
{
  "detail": "Job not found"
}
```

**Example:**
```bash
curl http://localhost:8000/api/status/550e8400-e29b-41d4-a716-446655440000
```

**Polling Recommendation:**
- Poll every 1-2 seconds during processing
- Use exponential backoff if needed
- Stop polling once status is "completed" or "failed"

---

### GET `/api/download/{job_id}`

Download the processed SVG file.

**Request:**
- **Method:** GET
- **Path Parameter:** `job_id` (UUID)
- **Query Parameters:**
  - `format` (optional): "svg" (default), "gcode" (future)

**Response (200 OK):**
- **Content-Type:** `image/svg+xml`
- **Content-Disposition:** `attachment; filename="result_{job_id}.svg"`
- **Body:** SVG file content

**Error Responses:**

**400 Bad Request** - Invalid job ID or job not completed:
```json
{
  "detail": "Job not completed or result not available"
}
```

**404 Not Found** - Job or result file not found:
```json
{
  "detail": "Job not found"
}
```

**Example:**
```bash
curl http://localhost:8000/api/download/550e8400-e29b-41d4-a716-446655440000 \
  -o result.svg
```

---

### GET `/api/uploads/{job_id}.{ext}`

Serve uploaded images and processed SVG files (static file serving).

**Request:**
- **Method:** GET
- **Path:** `/api/uploads/{job_id}.{ext}`

**Response (200 OK):**
- **Content-Type:** Appropriate MIME type based on extension
- **Body:** File content

**Error Responses:**

**404 Not Found** - File doesn't exist:
```json
{
  "detail": "File not found"
}
```

**Example:**
```bash
# View uploaded image
curl http://localhost:8000/api/uploads/550e8400-e29b-41d4-a716-446655440000.jpg

# View processed SVG
curl http://localhost:8000/api/uploads/550e8400-e29b-41d4-a716-446655440000.svg
```

## Complete Workflow Example

### 1. Upload Image
```bash
JOB_ID=$(curl -X POST http://localhost:8000/api/upload \
  -F "file=@photo.jpg" | jq -r '.job_id')

echo "Job ID: $JOB_ID"
```

### 2. Start Processing
```bash
curl -X POST http://localhost:8000/api/process/$JOB_ID \
  -H "Content-Type: application/json" \
  -d '{
    "canvas_width_mm": 300,
    "canvas_height_mm": 200,
    "line_width_mm": 0.3,
    "isolate_subject": false,
    "use_ml": false,
    "edge_threshold": [50, 150],
    "line_threshold": 16,
    "merge_tolerance": 0.5,
    "simplify_tolerance": 0.2,
    "hatching_enabled": false,
    "hatch_density": 2.0,
    "hatch_angle": 45,
    "darkness_threshold": 100
  }'
```

### 3. Poll Status
```bash
while true; do
  STATUS=$(curl -s http://localhost:8000/api/status/$JOB_ID | jq -r '.status')
  echo "Status: $STATUS"

  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    break
  fi

  sleep 2
done
```

### 4. Download Result
```bash
if [ "$STATUS" = "completed" ]; then
  curl http://localhost:8000/api/download/$JOB_ID -o result.svg
  echo "Downloaded result.svg"
fi
```

## Error Handling Best Practices

### Client-Side
1. **Validate files before upload** - Check format and size client-side
2. **Handle rate limits gracefully** - Implement exponential backoff
3. **Show progress during processing** - Poll status endpoint
4. **Handle all status codes** - 400, 404, 413, 422, 429, 500

### Server-Side
- All errors include descriptive `detail` field
- Uses appropriate HTTP status codes
- Logs errors with full context for debugging
- Returns validation errors in structured format (Pydantic)

## Testing

```bash
# Test upload endpoint
pytest tests/test_api.py::test_upload_image -v

# Test process endpoint
pytest tests/test_api.py::test_process_image -v

# Test status endpoint
pytest tests/test_api.py::test_job_status -v

# Test complete workflow
pytest tests/integration/test_real_images.py::test_complete_pipeline_jpeg -v
```

## Performance Considerations

### Upload Endpoint
- **Streaming uploads** - Files not loaded entirely into memory
- **Format validation** - Early rejection of unsupported formats
- **File size limits** - Prevents DoS via large uploads

### Process Endpoint
- **Background processing** - Uses FastAPI `BackgroundTasks`
- **Non-blocking** - Returns 202 immediately, processes asynchronously
- **Progress updates** - Real-time progress tracking (future: WebSocket)

### Status Endpoint
- **Fast lookups** - Redis-backed storage (with in-memory fallback)
- **No computation** - Simply returns stored status
- **Cacheable** - Can add HTTP caching headers for completed jobs

### Download Endpoint
- **Direct file serving** - Uses FastAPI `FileResponse` for streaming
- **Sendfile optimization** - Kernel-level file transfer when available

## Security Considerations

### Input Validation
- **UUID format validation** - Prevents path traversal
- **File format validation** - Uses extension + magic bytes (future)
- **Parameter range validation** - Pydantic models enforce constraints

### Rate Limiting
- **Per-IP limits** - Prevents abuse
- **Different limits per endpoint** - Upload vs process
- **Configurable** - Via environment variables

### File Storage
- **Secure filenames** - Uses UUIDs, not user-provided names
- **Separate directories** - Uploads isolated from application code
- **Cleanup jobs** - Automatic deletion of old files (future)

## Future Enhancements

### WebSocket Support
```python
@router.websocket("/ws/status/{job_id}")
async def websocket_status(websocket: WebSocket, job_id: str):
    """Real-time progress updates via WebSocket."""
    await websocket.accept()
    # Stream progress updates...
```

### Batch Processing
```python
@router.post("/batch/upload")
async def batch_upload(files: list[UploadFile]):
    """Upload multiple images for batch processing."""
    # Create jobs for all files...
```

### G-code Export
```python
@router.get("/download/{job_id}")
async def download(job_id: str, format: str = "svg"):
    """Download result in SVG or G-code format."""
    if format == "gcode":
        # Generate G-code for CNC plotters...
```

## Related Documentation

- [`job-service.md`](./job-service.md) - Business logic layer
- [`storage.md`](./storage.md) - Job storage and state management
- [`processor.md`](./processor.md) - Image processing pipeline
