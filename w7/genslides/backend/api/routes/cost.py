"""Cost API routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_cost_service
from api.schemas.cost import CostBreakdown, CostResponse
from services.cost_service import CostService

router = APIRouter(prefix="/api/cost", tags=["cost"])


@router.get("/{slug}", response_model=CostResponse)
async def get_cost_stats(
    slug: str, service: CostService = Depends(get_cost_service)
):
    """
    Get cost statistics for a project.

    Args:
        slug: Project identifier
        service: Cost service instance

    Returns:
        Cost statistics including breakdown

    Raises:
        HTTPException: 404 if project not found
    """
    try:
        stats = service.get_cost_stats(slug)

        return CostResponse(
            slug=stats["slug"],
            total_cost=stats["total_cost"],
            currency=stats["currency"],
            breakdown=CostBreakdown(
                slide_images=stats["breakdown"]["slide_images"],
                style_images=stats["breakdown"]["style_images"],
            ),
            image_count=stats["image_count"],
            cost_per_image=stats["cost_per_image"],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
