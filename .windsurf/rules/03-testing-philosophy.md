---
trigger: always_on
---

# Testing Philosophy

## No-Mock Testing Approach
- Use real implementations with proper isolation
- Each test gets isolated database instance with automatic cleanup
- Test end-to-end workflows as they run in production
- Tests run in parallel by default (pytest-xdist)

## Test Execution Commands

### ServerFramework (Python/FastAPI)
```bash
source ./.venv/bin/activate && python -m pytest (path) -v --lf
```

### Test Markers

- `pytest -m unit` – Unit tests (fast, focused, narrow scope)
- `pytest -m integration` – Integration tests (real HTTP endpoints and pipeline)
- `pytest -m "integration and real_images"` – Integration tests that use real test image files
- `pytest -m slow` – Slow tests (long-running, e.g. larger images or full pipelines)
- `pytest -m requires_ml` – Tests that require ML model weights to be available
- `pytest -m requires_redis` – Tests that require a running Redis instance
- `pytest -m requires_potrace` – Tests that require the Potrace binary to be installed
- `pytest -m requires_imagetracerjs` – Tests that require the imagetracerjs npm package
- `pytest -n auto` – Parallel execution (pytest-xdist)

## Test Requirements
- Minimum 90% code coverage across all layers
- 100% coverage for authentication and permission systems
- Comprehensive edge case and boundary testing
- Integration testing for end-to-end workflows

## When Modifying Code
- Update accompanying `*_test.py` file with comprehensive tests
- Update relevant `.md` documentation in same directory
- NO mocks - test real functionality
- Fix failing tests, never skip them