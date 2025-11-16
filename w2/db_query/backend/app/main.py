"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.api.v1 import databases, queries
from app.services.db_connection import close_all_connection_pools

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(
    title="Database Query Tool API",
    description="REST API for managing PostgreSQL database connections and executing queries",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(databases.router)
app.include_router(queries.router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize database on startup."""
    init_db()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Cleanup resources on shutdown."""
    await close_all_connection_pools()
