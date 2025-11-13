## Key Directives / Rules
### DO, ALWAYS:
- If functionality won't work without a parameter, it should be a required positional one without a default, not an optional one with a check.
- Any time you modify functionality in a file, ensure the accompanying `_test.py` file contains comprehensive tests for the modification WITHOUT MOCKS, as well as ensuring you update any relevant `.md` documentation in the same directory that references the code you changed.
- Write concise code (avoid obvious comments and use one-liners where possible).
- When requested to perform an implementation or refactor, critically analyze the requirements and ask any and all necessary clarifying questions to ensure your complete understanding of the goal.

### DO NOT, EVER, UNDER ANY CIRCUMSTANCE:
- Make assumptions, respond with "is likely", "probably" or "might be".
- Use frame-local or thread-local variables instead of passing data via parameters.
- Skip a failing test instead of fixing the root issue.
- Fix broken functionality and keep the broken functionality as a fallback instead of just implementing proper functionality.
- Re-implement existing functionality in a second location to bypass it instead of fixing the original implementation.
- Use bandaid fixes instead of fixing the core functionality.
- Mock functionality for testing instead of testing real functionality. Mocking functionality for testing is a cancer that needs to be excised - it defeats the entire point of tests.

### Python Syntax Guidelines:
- Always import the children of `datetime` I.E. `from datetime import date` - NEVER `import datetime` and `datetime.date`.
- All imports should be relative to ./src - this means NEVER `from src.x import y` - ALWAYS `from x import y`
- 
### Documentation Guidelines:
- Markdown documentation should be concise and written in a manner in which you could reconstruct the described code therefrom with 95% accuracy but with minimal snippets. It should be a clear architectural summary, not usage examples (that's what Swagger and Strawberry are for).

## Running Tests
When presented with a "_test" file, run the file using the command:

`source ./.venv.linux/bin/activate && python -m pytest (your test path) -v --lf` 

and repair any deficiencies starting with the easiest, most common or "lowest hanging fruit".

## Development Commands

### Basic Operations
- **Start the application**: `python src/app.py` (handles virtual environment setup automatically)
- **Run tests**: `pytest` (use specific test markers for targeted testing)
- **Format code**: `ruff src/` (configured with 88-character line length)
- **Type checking**: `mypy src/` (if available in dev dependencies)

### Testing
- **Test isolation**: Each test uses isolated database instances with proper cleanup

### Database Operations


## Architecture Overview

This is a **FastAPI-based server framework** with a layered architecture designed for scalability and modularity. The codebase follows strict separation of concerns with an extension-based plugin system.

### Core Architecture Layers



### Key Architectural Patterns

- **RORO Pattern**: All methods follow "Receive Object, Return Object" pattern


### Model Architecture

Each entity follows a three-model pattern:
- **Entity Model**: Core attributes and validation
- **Reference Model**: Relationships to other entities  
- **Network Model**: API schemas (POST, PUT, SEARCH, Response classes)


### Testing Framework

- **Abstract Test Classes**: Use provided abstract test base classes instead of creating new ones
- **Database Isolation**: Each test gets its own database instance with automatic cleanup
- **Hook Testing**: Comprehensive hook system testing with `@hook_bll` decorator
- **Parallel Execution**: Tests run in parallel by default using pytest-xdist
- **Never skip failing tests** - fix the root cause instead

### Authentication & Authorization

- **JWT-based authentication** with root API key for mutation of system entities
- **Role-based permissions** with team-scoped role heirarchies
- **System entities** require root API key authentication for write operations
- **User context** automatically injected into all BLL operations

### Key Development Principles

- Use UUID primary keys throughout (String type for SQLite, UUID for PostgreSQL)
- Handle errors at the beginning of functions with early raises, throwing FastAPI HTTPExceptions, as close to the database as possible
- All BLL managers support hook registration for extensibility
- Follow the existing search transformer pattern for custom search functionality
- Use the ModelRegistry system for proper Pydantic/SQLAlchemy integration
- Database migrations are automatically applied on startup

## Project-Specific Requirements: Photo-to-Line-Vectorizer

- **Privacy-First Processing**: Default to local processing. No cloud uploads by default. Any telemetry or remote calls must be opt-in and clearly disclosed.
- **Primary Output Style**: For portraits/animals, default to multi-stroke line drawings (avoid artificial connector lines). Offer optional single-path modes separately.
- **Canvas & Line Width Awareness**: `canvas_width_mm`, `canvas_height_mm`, and `line_width_mm` are required positional parameters wherever sizing or preview is computed. No hidden defaults.
- **Tech Stack (Hard Requirements)**:
  - Frontend: React + TypeScript + TailwindCSS + shadcn/ui; interactive SVG preview; professional UI (no Gradio/Streamlit look).
  - Backend: FastAPI (Python) with PyTorch (CUDA + Metal MPS support), OpenCV, vpype.
  - Vectorization: ImageTracerJS (public domain) preferred; Potrace only via isolated subprocess if used (GPL caution).
- **Hardware Acceleration**: Auto-detect device in this order: CUDA → MPS (Apple Metal) → CPU. Expose selected device in logs/response. Implement graceful CPU fallback.
- **Path Optimization Contract**: Always run `linemerge`, `linesimplify`, `linesort`, `dedupe` (vpype) before returning results. Ensure path count minimization without crossing artifacts.
- **Hatching/Shading**: Provide auto hatching for darker regions with spacing derived from `line_width_mm` (default 2×). Crosshatch for very dark regions. Must be toggleable.
- **Multi-Color Mode**: Support 3–5 color quantization → per-color layers → independent vector/optimize → ordered by brightness. Colors must be user-adjustable in advanced mode.
- **Export Formats**: Must support SVG (always) and provide HPGL and G-code options where applicable. Layer names should reflect pen colors.
- **Performance Targets**: 1080p image: CV path <5s; ML path (GPU) <15s; ML path (CPU) <45s. Return progress events over WebSocket for long jobs.
- **Licensing Guardrails**: Only use MIT/Apache/Unlicense in core. OpenRAIL-M (e.g., ControlNet LineArt) allowed with terms compliance and attribution. Avoid GPL linkage in-process; isolate if necessary.
- **API Discipline**: REST + WebSocket only. No hidden global state; pass all required parameters explicitly. Return deterministic, reproducible outputs for identical inputs + params.
- **UI/UX Constraints**: Modern, accessible (WCAG AA), responsive. Provide accurate line width visualization at true scale based on canvas size and `line_width_mm`.
- **Testing Expectations**: Include end-to-end tests for the pipeline (image → SVG) without mocks. Verify path count reduction, bounds fit to canvas, and deterministic outputs.
- **Error Handling**: Early validation with explicit messages for unsupported formats, oversized images, or missing required params. Never silently coerce units.
- **Image Format Support**: Must accept and decode at minimum: JPEG, PNG, TIFF, WebP, and Apple's HEIC/HEIF. Decoding must be local (e.g., Pillow + pillow-heif). Frontend file input must allow these MIME types. Clear errors for unsupported formats.