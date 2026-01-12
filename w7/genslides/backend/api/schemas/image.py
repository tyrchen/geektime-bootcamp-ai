"""Image API schemas."""

from datetime import datetime

from pydantic import BaseModel


class ImageInfo(BaseModel):
    """Information about an image."""

    filename: str
    content_hash: str
    url: str
    is_current: bool
    created_at: datetime


class SlideImagesResponse(BaseModel):
    """Response model for slide images."""

    sid: str
    current_content_hash: str
    images: list[ImageInfo]


class GenerateImageRequest(BaseModel):
    """Request model for image generation."""

    prompt_override: str | None = None


class GenerateImageResponse(BaseModel):
    """Response model for image generation."""

    image: ImageInfo
    generation_cost: float
