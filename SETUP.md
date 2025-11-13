# Installation and Setup Guide

## Python 3.13 Notes

This project targets Python 3.13. Tooling emphasizes strict typing (MyPy), Ruff, and Pydantic v2.

## Prerequisites

- **Python 3.13** (required)
- **Node.js 20+** (required)
- **npm 10+** (required)
- Git 2.40+
- (Optional) CUDA 12.0+ for NVIDIA GPUs
- (Optional) Apple Silicon for MPS acceleration

## Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/photo-to-line-vectorizer.git
cd photo-to-line-vectorizer
```

### 2. Install Pre-commit Hooks

```bash
# Install uv (once per machine)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install pre-commit package (if not already installed)
uv pip install pre-commit

# Install the git hooks
pre-commit install

# Test the hooks (optional)
pre-commit run --all-files
```

### 3. Backend Setup

```bash
cd backend

# Ensure uv is installed
command -v uv >/dev/null 2>&1 || curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment with Python 3.13
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt

# Install ImageTracerJS globally
npm install -g imagetracerjs

# Copy environment file
cp .env.example .env

# Run tests to verify installation
pytest -v

# Run type checking
mypy app/ --strict

# Run linting
ruff check app/ tests/
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies (uses latest versions)
npm install

# Run linting
npm run lint

# Run type checking
npm run type-check

# Test build
npm run build
```

## Development Workflow

### Pre-commit Hooks

Every commit automatically runs:

**Backend:**
- ✅ Ruff linting (code quality)
- ✅ Ruff formatting (code style)
- ✅ MyPy type checking (strict mode)
- ✅ Pytest (all tests must pass)

**Frontend:**
- ✅ ESLint (code quality)
- ✅ Prettier (code formatting)
- ✅ TypeScript type checking
- ✅ Build verification (must compile)

**General:**
- ✅ No trailing whitespace
- ✅ End-of-file fixers
- ✅ YAML/JSON validation
- ✅ Large file prevention
- ✅ Merge conflict detection

### Running Development Servers

**Backend:**
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

Access the application:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Manual Pre-commit Check

```bash
# Run all pre-commit checks manually
pre-commit run --all-files

# Run specific hook
pre-commit run backend-pytest --all-files
pre-commit run frontend-build --all-files
```

### Bypassing Hooks (NOT RECOMMENDED)

```bash
git commit --no-verify -m "Emergency commit"
```

## Type Checking

### Backend (MyPy)

Strict type checking is enforced:

```bash
cd backend
mypy app/ --strict
```

All code must have:
- Type annotations for all functions
- No implicit `Any` types
- Strict equality checks
- No untyped definitions

### Frontend (TypeScript)

```bash
cd frontend
npm run type-check
```

TypeScript configuration:
- Strict mode enabled
- No implicit any
- No unused locals/parameters
- No fallthrough cases

## Code Quality Standards

### Backend (Python 3.13)

**Required:**
- Type hints with `from __future__ import annotations`
- Pydantic v2 models with strict validation
- Docstrings for all public functions/classes
- No mocks in tests (use real data)
- Use pattern matching (`match`/`case`) where appropriate
- Use `StrEnum` for string enums

**Example:**
```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from torch import nn

def process(model: nn.Module, device: str) -> torch.Tensor:
    """
    Process model on specified device.

    Args:
        model: PyTorch model to process
        device: Device name (cuda/mps/cpu)

    Returns:
        Processed tensor output
    """
    match device:
        case "cuda":
            return model.cuda()
        case "mps":
            return model.to("mps")
        case _:
            return model.cpu()
```

### Frontend (React 18 + TypeScript)

**Required:**
- Functional components with hooks
- Proper TypeScript interfaces for all props
- No `any` types
- Use React 18 features (concurrent rendering, automatic batching)
- Accessible components (ARIA labels)

**Example:**
```typescript
interface UploadProps {
  onComplete: (result: UploadResponse) => void
  maxSizeMB?: number
}

export function Upload({ onComplete, maxSizeMB = 50 }: UploadProps): JSX.Element {
  // Component implementation
}
```

## Troubleshooting

### Pre-commit Hook Fails

```bash
# Update pre-commit hooks
pre-commit autoupdate

# Clean pre-commit cache
pre-commit clean

# Reinstall hooks
pre-commit uninstall
pre-commit install
```

### Python 3.13 Not Found

```bash
# Install Python 3.13 using pyenv
pyenv install 3.13.0
pyenv local 3.13.0

# Or download from python.org
# https://www.python.org/downloads/
```

### MyPy Errors

```bash
# Update type stubs
uv pip install --upgrade types-aiofiles types-pillow

# Check specific module
mypy app/models/u2net.py --strict
```

### Frontend Build Fails

```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf node_modules/.vite
```

## Docker Development

```bash
# Build with Python 3.13
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Run tests in container
docker-compose exec backend pytest -v
```

## CI/CD Integration

The pre-commit hooks can be integrated into CI/CD:

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install uv and dependencies
        run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          uv pip install pre-commit
          pre-commit install
      - name: Run pre-commit
        run: pre-commit run --all-files
```

## Performance Tips

### Free-Threading (experimental)

Enable free-threaded mode if your interpreter supports it:
```bash
export PYTHON_GIL=0
python app/main.py
```

### Frontend Build Optimization

```bash
# Production build with optimization
npm run build

# Analyze bundle size
npm run build -- --mode analyze
```

## License

MIT License - see LICENSE file for details.
