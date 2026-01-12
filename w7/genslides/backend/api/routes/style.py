"""Style API routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from api.dependencies import get_style_service
from api.schemas.style import (
    GenerateStyleRequest,
    GenerateStyleResponse,
    GetStyleResponse,
    SelectStyleRequest,
    SelectStyleResponse,
    StyleCandidate,
    StyleResponse,
)
from services.style_service import StyleService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/slides", tags=["style"])


@router.get("/{slug}/style", response_model=GetStyleResponse)
async def get_style(
    slug: str, service: StyleService = Depends(get_style_service)
):
    """
    Get project style configuration.

    Args:
        slug: Project identifier
        service: Style service instance

    Returns:
        Style configuration if exists

    Raises:
        HTTPException: 404 if project not found
    """
    try:
        style = service.get_style(slug)

        if style:
            return GetStyleResponse(
                has_style=True,
                style=StyleResponse(
                    prompt=style.prompt,
                    image=style.image,
                    image_url=f"/api/slides/{slug}/style/{style.image}",
                ),
            )
        else:
            return GetStyleResponse(has_style=False, style=None)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{slug}/style/generate", response_model=GenerateStyleResponse)
async def generate_style_candidates(
    slug: str,
    request: GenerateStyleRequest,
    service: StyleService = Depends(get_style_service),
):
    """
    Generate style candidate images.

    Args:
        slug: Project identifier
        request: Style generation request
        service: Style service instance

    Returns:
        Style candidate images and cost

    Raises:
        HTTPException: 404 if project not found, 500 if generation fails
    """
    try:
        candidates, cost = await service.generate_style_candidates(
            slug, request.prompt
        )

        candidate_responses = [
            StyleCandidate(
                filename=c.filename,
                url=f"/api/slides/{slug}/style/{c.filename}",
            )
            for c in candidates
        ]

        return GenerateStyleResponse(
            candidates=candidate_responses,
            generation_cost=cost,
        )
    except ValueError as e:
        logger.error(f"Style generation value error: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.exception(f"Style generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Style generation failed: {str(e)}",
        )


@router.put("/{slug}/style", response_model=SelectStyleResponse)
async def select_style(
    slug: str,
    request: SelectStyleRequest,
    service: StyleService = Depends(get_style_service),
):
    """
    Select and save a style for the project.

    Args:
        slug: Project identifier
        request: Style selection request
        service: Style service instance

    Returns:
        Selected style configuration

    Raises:
        HTTPException: 404 if project or image not found
    """
    try:
        style = service.select_style(slug, request.prompt, request.selected_image)

        return SelectStyleResponse(
            success=True,
            style=StyleResponse(
                prompt=style.prompt,
                image=style.image,
                image_url=f"/api/slides/{slug}/style/{style.image}",
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{slug}/style/{filename}")
async def get_style_image(
    slug: str, filename: str, service: StyleService = Depends(get_style_service)
):
    """
    Get a style image file.

    Args:
        slug: Project identifier
        filename: Image filename
        service: Style service instance

    Returns:
        Image file

    Raises:
        HTTPException: 404 if image not found
    """
    from repositories.image_repository import ImageRepository
    from config import Settings

    settings = Settings()
    image_repo = ImageRepository(settings.slides_base_path)

    image_path = image_repo.get_style_image_path(slug, filename)

    if not image_path or not image_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Style image not found"
        )

    return FileResponse(image_path, media_type="image/jpeg")
