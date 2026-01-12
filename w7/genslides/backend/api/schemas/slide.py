"""Slide API schemas."""

from datetime import datetime

from pydantic import BaseModel


class SlideResponse(BaseModel):
    """Response model for a single slide."""

    sid: str
    content: str
    content_hash: str
    created_at: datetime
    updated_at: datetime
    has_matching_image: bool
    image_count: int
    default_image: str | None = None
    latest_image: str | None = None  # Most recent image filename


class StyleInfo(BaseModel):
    """Style information."""

    prompt: str
    image: str


class ProjectResponse(BaseModel):
    """Response model for project with all slides."""

    slug: str
    title: str
    style: StyleInfo | None
    slides: list[SlideResponse]
    total_cost: float = 0.0


class CreateSlideRequest(BaseModel):
    """Request model for creating a new slide."""

    title: str | None = None
    content: str
    position: int | None = None


class UpdateSlideRequest(BaseModel):
    """Request model for updating a slide."""

    content: str


class ReorderSlidesRequest(BaseModel):
    """Request model for reordering slides."""

    slide_ids: list[str]


class UpdateTitleRequest(BaseModel):
    """Request model for updating project title."""

    title: str


class DeleteResponse(BaseModel):
    """Response model for delete operations."""

    success: bool
    message: str


class ReorderResponse(BaseModel):
    """Response model for reorder operation."""

    success: bool
    slides: list[SlideResponse]


class UpdateTitleResponse(BaseModel):
    """Response model for title update."""

    success: bool
    title: str


class SetDefaultImageRequest(BaseModel):
    """Request model for setting default image."""

    filename: str


class SetDefaultImageResponse(BaseModel):
    """Response model for setting default image."""

    success: bool
    default_image: str
