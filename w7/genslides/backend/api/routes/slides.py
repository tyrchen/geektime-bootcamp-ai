"""Slides API routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_slide_service
from api.schemas.slide import (
    CreateSlideRequest,
    DeleteResponse,
    ProjectResponse,
    ReorderResponse,
    ReorderSlidesRequest,
    SetDefaultImageRequest,
    SetDefaultImageResponse,
    SlideResponse,
    StyleInfo,
    UpdateSlideRequest,
    UpdateTitleRequest,
    UpdateTitleResponse,
)
from services.slide_service import SlideService

router = APIRouter(prefix="/api/slides", tags=["slides"])


@router.get("/{slug}", response_model=ProjectResponse)
async def get_project(
    slug: str, service: SlideService = Depends(get_slide_service)
):
    """
    Get project with all slides.

    Args:
        slug: Project identifier
        service: Slide service instance

    Returns:
        Project with all slides

    Raises:
        HTTPException: 404 if project not found
    """
    try:
        project = service.get_project(slug)

        style_info = None
        if project.style:
            style_info = StyleInfo(
                prompt=project.style.prompt,
                image=project.style.image,
            )

        slides = []
        for slide in project.slides:
            _, has_matching, image_count, latest_image = service.get_slide_with_images(
                slug, slide.sid
            )
            slides.append(
                SlideResponse(
                    sid=slide.sid,
                    content=slide.content,
                    content_hash=slide.content_hash,
                    created_at=slide.created_at,
                    updated_at=slide.updated_at,
                    has_matching_image=has_matching,
                    image_count=image_count,
                    default_image=slide.default_image,
                    latest_image=latest_image,
                )
            )

        return ProjectResponse(
            slug=slug,
            title=project.title,
            style=style_info,
            slides=slides,
            total_cost=project.total_cost,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{slug}", response_model=SlideResponse, status_code=status.HTTP_201_CREATED)
async def create_slide(
    slug: str,
    request: CreateSlideRequest,
    service: SlideService = Depends(get_slide_service),
):
    """
    Create a new slide or project.

    Args:
        slug: Project identifier
        request: Slide creation request
        service: Slide service instance

    Returns:
        Newly created slide

    Raises:
        HTTPException: 400 if validation fails
    """
    try:
        slide = service.create_slide(
            slug, request.content, request.title, request.position
        )

        _, has_matching, image_count, latest_image = service.get_slide_with_images(
            slug, slide.sid
        )

        return SlideResponse(
            sid=slide.sid,
            content=slide.content,
            content_hash=slide.content_hash,
            created_at=slide.created_at,
            updated_at=slide.updated_at,
            has_matching_image=has_matching,
            image_count=image_count,
            default_image=slide.default_image,
            latest_image=latest_image,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{slug}/title", response_model=UpdateTitleResponse)
async def update_title(
    slug: str,
    request: UpdateTitleRequest,
    service: SlideService = Depends(get_slide_service),
):
    """
    Update project title.

    Args:
        slug: Project identifier
        request: Title update request
        service: Slide service instance

    Returns:
        Updated title

    Raises:
        HTTPException: 404 if project not found
    """
    try:
        title = service.update_title(slug, request.title)
        return UpdateTitleResponse(success=True, title=title)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{slug}/reorder", response_model=ReorderResponse)
async def reorder_slides(
    slug: str,
    request: ReorderSlidesRequest,
    service: SlideService = Depends(get_slide_service),
):
    """
    Reorder slides.

    Args:
        slug: Project identifier
        request: Reorder request with slide IDs
        service: Slide service instance

    Returns:
        Reordered slides

    Raises:
        HTTPException: 400 if validation fails, 404 if project not found
    """
    try:
        slides = service.reorder_slides(slug, request.slide_ids)

        slide_responses = []
        for slide in slides:
            _, has_matching, image_count, latest_image = service.get_slide_with_images(
                slug, slide.sid
            )
            slide_responses.append(
                SlideResponse(
                    sid=slide.sid,
                    content=slide.content,
                    content_hash=slide.content_hash,
                    created_at=slide.created_at,
                    updated_at=slide.updated_at,
                    has_matching_image=has_matching,
                    image_count=image_count,
                    default_image=slide.default_image,
                    latest_image=latest_image,
                )
            )

        return ReorderResponse(success=True, slides=slide_responses)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{slug}/{sid}", response_model=SlideResponse)
async def update_slide(
    slug: str,
    sid: str,
    request: UpdateSlideRequest,
    service: SlideService = Depends(get_slide_service),
):
    """
    Update a slide's content.

    Args:
        slug: Project identifier
        sid: Slide ID
        request: Update request
        service: Slide service instance

    Returns:
        Updated slide

    Raises:
        HTTPException: 404 if project or slide not found
    """
    try:
        slide = service.update_slide(slug, sid, request.content)

        _, has_matching, image_count, latest_image = service.get_slide_with_images(
            slug, slide.sid
        )

        return SlideResponse(
            sid=slide.sid,
            content=slide.content,
            content_hash=slide.content_hash,
            created_at=slide.created_at,
            updated_at=slide.updated_at,
            has_matching_image=has_matching,
            image_count=image_count,
            default_image=slide.default_image,
            latest_image=latest_image,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{slug}/{sid}", response_model=DeleteResponse)
async def delete_slide(
    slug: str, sid: str, service: SlideService = Depends(get_slide_service)
):
    """
    Delete a slide.

    Args:
        slug: Project identifier
        sid: Slide ID
        service: Slide service instance

    Returns:
        Success response

    Raises:
        HTTPException: 404 if project or slide not found
    """
    try:
        service.delete_slide(slug, sid)
        return DeleteResponse(success=True, message="Slide deleted successfully")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{slug}/{sid}/default-image", response_model=SetDefaultImageResponse)
async def set_default_image(
    slug: str,
    sid: str,
    request: SetDefaultImageRequest,
    service: SlideService = Depends(get_slide_service),
):
    """
    Set the default image for a slide.

    Args:
        slug: Project identifier
        sid: Slide ID
        request: Request with image filename
        service: Slide service instance

    Returns:
        Success response with default image filename

    Raises:
        HTTPException: 404 if project or slide not found
    """
    try:
        filename = service.set_default_image(slug, sid, request.filename)
        return SetDefaultImageResponse(success=True, default_image=filename)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
