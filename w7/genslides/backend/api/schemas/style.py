"""Style API schemas."""

from pydantic import BaseModel


class StyleCandidate(BaseModel):
    """Style candidate image information."""

    filename: str
    url: str


class GenerateStyleRequest(BaseModel):
    """Request model for generating style candidates."""

    prompt: str


class GenerateStyleResponse(BaseModel):
    """Response model for style generation."""

    candidates: list[StyleCandidate]
    generation_cost: float


class SelectStyleRequest(BaseModel):
    """Request model for selecting a style."""

    prompt: str
    selected_image: str


class StyleResponse(BaseModel):
    """Response model for style information."""

    prompt: str
    image: str
    image_url: str


class GetStyleResponse(BaseModel):
    """Response model for getting style."""

    has_style: bool
    style: StyleResponse | None


class SelectStyleResponse(BaseModel):
    """Response model for style selection."""

    success: bool
    style: StyleResponse
