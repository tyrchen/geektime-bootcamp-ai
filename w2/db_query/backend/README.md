# Database Query Tool Backend

FastAPI backend for the Database Query Tool application.

## Setup

1. Install dependencies:
```bash
uv sync
```

2. Create `.env` file from `.env.example`:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

3. Run database migrations:
```bash
alembic upgrade head
```

4. Start the development server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

## Project Structure

- `app/` - Application code
  - `main.py` - FastAPI application entry point
  - `config.py` - Configuration using Pydantic Settings
  - `database.py` - SQLite database setup
  - `models/` - SQLModel entities and Pydantic schemas
  - `services/` - Business logic services
  - `api/v1/` - API route handlers
- `tests/` - Test files
- `alembic/` - Database migrations

## Development

- Python 3.12+
- Uses `uv` for package management
- Uses `ruff` for linting
- Uses `mypy` for type checking
- Uses `pytest` for testing
