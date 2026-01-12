"""Images API routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from api.dependencies import get_image_service, get_slide_repository

logger = logging.getLogger(__name__)
from api.schemas.image import (
    GenerateImageRequest,
    GenerateImageResponse,
    ImageInfo,
    SlideImagesResponse,
)
from repositories.slide_repository import SlideRepository
from services.image_service import ImageService

router = APIRouter(prefix="/api/slides", tags=["images"])


@router.get("/{slug}/{sid}/images", response_model=SlideImagesResponse)
async def get_slide_images(
    slug: str,
    sid: str,
    service: ImageService = Depends(get_image_service),
    slide_repo: SlideRepository = Depends(get_slide_repository),
):
    """
    Get all images for a slide.

    Args:
        slug: Project identifier
        sid: Slide ID
        service: Image service instance
        slide_repo: Slide repository instance

    Returns:
        All images for the slide

    Raises:
        HTTPException: 404 if project or slide not found
    """
    try:
        slide = slide_repo.get_slide(slug, sid)
        if not slide:
            raise ValueError(f"Slide '{sid}' not found")

        images = service.get_slide_images(slug, sid)
        current_hash = slide.content_hash

        image_infos = [
            ImageInfo(
                filename=img.filename,
                content_hash=img.content_hash,
                url=f"/api/slides/{slug}/{sid}/images/{img.filename}",
                is_current=(img.content_hash == current_hash),
                created_at=img.created_at,
            )
            for img in images
        ]

        return SlideImagesResponse(
            sid=sid,
            current_content_hash=current_hash,
            images=image_infos,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{slug}/{sid}/images/{filename}")
async def get_image(
    slug: str,
    sid: str,
    filename: str,
    service: ImageService = Depends(get_image_service),
):
    """
    Get a specific image file.

    Args:
        slug: Project identifier
        sid: Slide ID
        filename: Image filename
        service: Image service instance

    Returns:
        Image file

    Raises:
        HTTPException: 404 if image not found
    """
    from repositories.image_repository import ImageRepository
    from config import Settings

    settings = Settings()
    image_repo = ImageRepository(settings.slides_base_path)

    content_hash = filename.rsplit(".", 1)[0]
    image_path = image_repo.get_image_path(slug, sid, content_hash)

    if not image_path or not image_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )

    return FileResponse(image_path, media_type="image/jpeg")


@router.post("/{slug}/{sid}/generate", response_model=GenerateImageResponse)
async def generate_image(
    slug: str,
    sid: str,
    request: GenerateImageRequest = GenerateImageRequest(),
    service: ImageService = Depends(get_image_service),
):
    """
    Generate a new image for a slide.

    Args:
        slug: Project identifier
        sid: Slide ID
        request: Image generation request
        service: Image service instance

    Returns:
        Generated image information

    Raises:
        HTTPException: 404 if project or slide not found, 500 if generation fails
    """
    try:
        image_info, cost = await service.generate_image(
            slug, sid, request.prompt_override
        )

        return GenerateImageResponse(
            image=ImageInfo(
                filename=image_info.filename,
                content_hash=image_info.content_hash,
                url=f"/api/slides/{slug}/{sid}/images/{image_info.filename}",
                is_current=True,
                created_at=image_info.created_at,
            ),
            generation_cost=cost,
        )
    except ValueError as e:
        logger.error(f"Image generation value error: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.exception(f"Image generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image generation failed: {str(e)}",
        )
