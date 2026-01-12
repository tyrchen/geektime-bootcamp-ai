# GenSlides Backend

AI-powered image slideshow generator backend built with FastAPI.

## Features

- FastAPI-based REST API
- Google Gemini AI for image generation
- File-based storage (YAML + images)
- Layered architecture (API -> Services -> Repositories)
- Blake3 content hashing for efficient image caching
- Style-based image generation

## Prerequisites

- Python 3.11 or higher
- uv package manager
- Google Gemini API key

## Installation

1. Install uv if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Install dependencies:
```bash
cd backend
uv sync
```

3. Create a `.env` file from the example:
```bash
cp .env.example .env
```

4. Edit `.env` and add your Google Gemini API key:
```
GEMINI_API_KEY=your_actual_api_key_here
```

## Running the Server

### Development Mode

```bash
uv run uvicorn main:app --reload --port 3003
```

Or use the convenience script:

```bash
uv run python main.py
```

The API will be available at `http://localhost:3003`

### API Documentation

Once the server is running, you can access:

- Swagger UI: `http://localhost:3003/docs`
- ReDoc: `http://localhost:3003/redoc`

## Project Structure

```
backend/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration management
├── api/                 # HTTP layer
│   ├── routes/          # Route handlers
│   ├── schemas/         # Pydantic request/response models
│   └── dependencies.py  # Dependency injection
├── services/            # Business logic layer
├── repositories/        # Data persistence layer
├── models/              # Domain models
├── clients/             # External service clients (Gemini)
└── utils/               # Utility functions
```

## API Endpoints

### Slides

- `GET /api/slides/{slug}` - Get project with all slides
- `POST /api/slides/{slug}` - Create new slide or project
- `PUT /api/slides/{slug}/{sid}` - Update slide content
- `DELETE /api/slides/{slug}/{sid}` - Delete slide
- `PUT /api/slides/{slug}/reorder` - Reorder slides
- `PUT /api/slides/{slug}/title` - Update project title

### Images

- `GET /api/slides/{slug}/{sid}/images` - Get all images for a slide
- `GET /api/slides/{slug}/{sid}/images/{filename}` - Get specific image
- `POST /api/slides/{slug}/{sid}/generate` - Generate new image

### Style

- `GET /api/slides/{slug}/style` - Get project style
- `POST /api/slides/{slug}/style/generate` - Generate style candidates
- `PUT /api/slides/{slug}/style` - Select and save style
- `GET /api/slides/{slug}/style/{filename}` - Get style image

### Cost

- `GET /api/cost/{slug}` - Get project cost statistics

## Architecture

The backend follows a layered architecture:

1. **API Layer** (`api/routes/`): Handles HTTP requests/responses, parameter validation
2. **Services Layer** (`services/`): Contains business logic, orchestrates operations
3. **Repositories Layer** (`repositories/`): Handles data persistence (YAML files, images)
4. **Clients Layer** (`clients/`): Interfaces with external services (Gemini API)

## Data Storage

Data is stored in the `./slides` directory (configurable):

```
slides/
└── {slug}/
    ├── outline.yml       # Project metadata and slides
    └── images/
        ├── style/        # Style reference images
        │   └── {hash}.jpg
        └── {sid}/        # Slide-specific images
            └── {content_hash}.jpg
```

## Development

### Code Style

The project uses Ruff for linting and formatting:

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Lint and fix
uv run ruff check --fix .
```

### Testing

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=. --cov-report=html
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `SLIDES_BASE_PATH` | Base directory for slides storage | `./slides` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `3003` |
| `CORS_ORIGINS` | Allowed CORS origins | `["http://localhost:5173"]` |

## License

MIT
