# GenSlides Backend - Development Guidelines

IMPORTANT: always use latest dependencies.

## Tech Stack

- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Package Manager**: uv
- **Image Generation**: Google AI SDK (Gemini)
- **Data Storage**: File system (YAML + images)

## Architecture Principles

### SOLID Principles

- **S - Single Responsibility**: Each module has one clear purpose
  - `api/routes/` - HTTP request handling only
  - `services/` - Business logic only
  - `repositories/` - Data persistence only
  - `clients/` - External API communication only

- **O - Open/Closed**: Use abstractions for extensibility
  - Define protocols/interfaces for services
  - New image generators can be added without modifying existing code

- **L - Liskov Substitution**: Subtypes must be substitutable
  - All repository implementations must honor the same contract

- **I - Interface Segregation**: Small, focused interfaces
  - Separate schemas for request/response
  - Don't force clients to depend on methods they don't use

- **D - Dependency Inversion**: Depend on abstractions
  - Services receive repositories via dependency injection
  - Use FastAPI's `Depends()` for DI

### YAGNI (You Aren't Gonna Need It)

- Don't add features until they're actually needed
- No premature abstractions
- Start simple, refactor when patterns emerge

### KISS (Keep It Simple, Stupid)

- Prefer straightforward solutions over clever ones
- Minimize layers of indirection
- Use standard library when possible

### DRY (Don't Repeat Yourself)

- Avoid duplicating code
- Use functions, classes, and modules to DRY code
- Use patterns and templates to DRY code

## Code Organization

```
backend/
├── main.py              # FastAPI app entry, router registration
├── config.py            # Settings via pydantic-settings
├── api/                 # HTTP layer
│   ├── routes/          # Route handlers (thin, delegate to services)
│   ├── schemas/         # Pydantic models for request/response
│   └── dependencies.py  # FastAPI dependencies (DI setup)
├── services/            # Business logic layer
├── repositories/        # Data access layer
├── models/              # Domain models (dataclasses)
├── clients/             # External service clients
└── utils/               # Pure utility functions
```

### Layer Responsibilities

| Layer        | Responsibility                | Can Call              |
|--------------|-------------------------------|-----------------------|
| Routes       | HTTP handling, validation     | Services              |
| Services     | Business logic, orchestration | Repositories, Clients |
| Repositories | Data persistence              | File system           |
| Clients      | External APIs                 | External services     |

### Import Rules

```python
# ALLOWED
from services.slide_service import SlideService  # routes -> services
from repositories.slide_repository import SlideRepository  # services -> repositories
from clients.gemini_client import GeminiClient  # services -> clients

# NOT ALLOWED
from api.routes.slides import router  # services should not import routes
from services.slide_service import SlideService  # repositories should not import services
```

## Concurrency

### Async/Await Best Practices

```python
# Use async for I/O-bound operations
async def generate_image(self, prompt: str) -> bytes:
    # Gemini API call is I/O-bound
    response = await self.client.models.generate_content_async(...)
    return response

# Use sync for CPU-bound operations
def compute_hash(content: str) -> str:
    # Blake3 hashing is CPU-bound, keep sync
    return blake3.blake3(content.encode()).hexdigest()[:16]
```

### File I/O

```python
# For file operations, use aiofiles or run_in_executor
import aiofiles

async def save_image(self, path: Path, data: bytes) -> None:
    async with aiofiles.open(path, 'wb') as f:
        await f.write(data)

# Or use run_in_executor for sync file ops
from functools import partial
import asyncio

async def read_yaml(self, path: Path) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(yaml.safe_load, path.read_text()))
```

### Parallel Image Generation

```python
# Generate multiple images concurrently
async def generate_style_candidates(self, prompt: str) -> list[bytes]:
    tasks = [
        self._generate_single(f"{prompt} (variant {i})")
        for i in range(2)
    ]
    return await asyncio.gather(*tasks)
```

## Error Handling

### Exception Hierarchy

```python
# models/exceptions.py
class GenSlidesError(Exception):
    """Base exception for all application errors"""
    pass

class ProjectNotFoundError(GenSlidesError):
    """Raised when project/slug doesn't exist"""
    pass

class SlideNotFoundError(GenSlidesError):
    """Raised when slide doesn't exist"""
    pass

class ImageGenerationError(GenSlidesError):
    """Raised when Gemini API fails"""
    pass

class ValidationError(GenSlidesError):
    """Raised for invalid input data"""
    pass
```

### HTTP Error Mapping

```python
# api/dependencies.py
from fastapi import HTTPException, status

def handle_service_error(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ProjectNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except SlideNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ImageGenerationError as e:
            raise HTTPException(status_code=502, detail=str(e))
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=str(e))
    return wrapper
```

### Error Response Format

```python
# Consistent error responses
{
    "detail": "Human-readable error message",
    "error_code": "PROJECT_NOT_FOUND",  # Optional: machine-readable code
    "context": {}  # Optional: additional context
}
```

## Logging

### Configuration

```python
# config.py
import logging
import sys

def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
```

### Usage Patterns

```python
import logging

logger = logging.getLogger(__name__)

class SlideService:
    async def create_slide(self, slug: str, content: str) -> Slide:
        logger.info("Creating slide", extra={"slug": slug, "content_length": len(content)})
        try:
            slide = await self._do_create(slug, content)
            logger.info("Slide created", extra={"slug": slug, "sid": slide.sid})
            return slide
        except Exception as e:
            logger.exception("Failed to create slide", extra={"slug": slug})
            raise
```

### Log Levels

| Level    | Usage                                                |
|----------|------------------------------------------------------|
| DEBUG    | Detailed diagnostic info (disabled in prod)          |
| INFO     | Normal operations (request received, task completed) |
| WARNING  | Unexpected but recoverable situations                |
| ERROR    | Failures that need attention                         |
| CRITICAL | System-wide failures                                 |

## Testing

### Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── unit/                # Unit tests (no I/O)
│   ├── test_services.py
│   └── test_utils.py
├── integration/         # Integration tests (with I/O)
│   ├── test_repositories.py
│   └── test_api.py
└── e2e/                 # End-to-end tests
    └── test_workflows.py
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=. --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_services.py -v
```

## Code Style

### Formatting & Linting

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Lint and fix
uv run ruff check --fix .
```

### Type Hints

Always use type hints:

```python
from typing import Optional
from pathlib import Path

async def get_slide(self, slug: str, sid: str) -> Optional[Slide]:
    ...

def compute_hash(content: str) -> str:
    ...
```

### Docstrings

Use Google-style docstrings for public APIs:

```python
def generate_image(self, prompt: str, style_image: Optional[bytes] = None) -> bytes:
    """Generate an image using Gemini API.

    Args:
        prompt: Text description for image generation.
        style_image: Optional reference image for style consistency.

    Returns:
        Generated image as PNG bytes.

    Raises:
        ImageGenerationError: If Gemini API fails.
    """
```

## FastAPI Best Practices

### Router Organization

```python
# api/routes/slides.py
from fastapi import APIRouter, Depends, status

router = APIRouter(prefix="/api/slides", tags=["slides"])

@router.get("/{slug}")
async def get_project(slug: str, service: SlideService = Depends(get_slide_service)):
    ...

@router.post("/{slug}", status_code=status.HTTP_201_CREATED)
async def create_slide(slug: str, request: CreateSlideRequest, ...):
    ...
```

### Dependency Injection

```python
# api/dependencies.py
from functools import lru_cache

@lru_cache
def get_settings() -> Settings:
    return Settings()

def get_slide_repository(settings: Settings = Depends(get_settings)) -> SlideRepository:
    return SlideRepository(settings.slides_base_path)

def get_slide_service(
    slide_repo: SlideRepository = Depends(get_slide_repository),
    image_repo: ImageRepository = Depends(get_image_repository),
) -> SlideService:
    return SlideService(slide_repo, image_repo)
```

### Response Models

```python
# Always specify response_model for documentation
@router.get("/{slug}", response_model=ProjectResponse)
async def get_project(slug: str, ...):
    ...

# Use status codes explicitly
@router.delete("/{slug}/{sid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_slide(slug: str, sid: str, ...):
    ...
```
