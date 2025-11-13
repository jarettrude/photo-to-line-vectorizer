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
- `pytest -m db` - Database tests only
- `pytest -m bll` - Business logic tests
- `pytest -m ep` - Endpoint tests
- `pytest -m auth` - Authentication tests
- `pytest -n auto` - Parallel execution

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
