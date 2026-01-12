"""Cost API schemas."""

from pydantic import BaseModel


class CostBreakdown(BaseModel):
    """Cost breakdown by category."""

    slide_images: float
    style_images: float


class CostResponse(BaseModel):
    """Response model for cost statistics."""

    slug: str
    total_cost: float
    currency: str
    breakdown: CostBreakdown
    image_count: int
    cost_per_image: float
