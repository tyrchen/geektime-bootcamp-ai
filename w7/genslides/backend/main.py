"""FastAPI application entry point."""

import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import cost, images, slides, style
from config import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

settings = Settings()

app = FastAPI(
    title="GenSlides API",
    description="AI-powered image slideshow generator",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes in order of specificity (most specific first)
# style and images have paths like /{slug}/style/... and /{slug}/{sid}/images
# which must match before the generic /{slug}/{sid} in slides
app.include_router(style.router)
app.include_router(images.router)
app.include_router(cost.router)
app.include_router(slides.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "GenSlides API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
