"""FastAPI dependency injection configuration."""

from functools import lru_cache

from clients.gemini_client import GeminiClient
from config import Settings
from repositories.image_repository import ImageRepository
from repositories.slide_repository import SlideRepository
from services.cost_service import CostService
from services.image_service import ImageService
from services.slide_service import SlideService
from services.style_service import StyleService


@lru_cache
def get_settings() -> Settings:
    """
    Get application settings (cached).

    Returns:
        Settings instance
    """
    return Settings()


def get_slide_repository(settings: Settings = None) -> SlideRepository:
    """
    Get slide repository instance.

    Args:
        settings: Application settings

    Returns:
        SlideRepository instance
    """
    if settings is None:
        settings = get_settings()
    return SlideRepository(str(settings.get_slides_path()))


def get_image_repository(settings: Settings = None) -> ImageRepository:
    """
    Get image repository instance.

    Args:
        settings: Application settings

    Returns:
        ImageRepository instance
    """
    if settings is None:
        settings = get_settings()
    return ImageRepository(str(settings.get_slides_path()))


def get_gemini_client(settings: Settings = None) -> GeminiClient:
    """
    Get Gemini client instance.

    Args:
        settings: Application settings

    Returns:
        GeminiClient instance
    """
    if settings is None:
        settings = get_settings()
    # Pass api_key only if it's set, otherwise let client use env var
    api_key = settings.gemini_api_key if settings.gemini_api_key else None
    return GeminiClient(api_key)


def get_slide_service() -> SlideService:
    """
    Get slide service instance.

    Returns:
        SlideService instance
    """
    slide_repo = get_slide_repository()
    image_repo = get_image_repository()
    return SlideService(slide_repo, image_repo)


def get_image_service() -> ImageService:
    """
    Get image service instance.

    Returns:
        ImageService instance
    """
    gemini_client = get_gemini_client()
    image_repo = get_image_repository()
    slide_repo = get_slide_repository()
    return ImageService(gemini_client, image_repo, slide_repo)


def get_style_service() -> StyleService:
    """
    Get style service instance.

    Returns:
        StyleService instance
    """
    gemini_client = get_gemini_client()
    image_repo = get_image_repository()
    slide_repo = get_slide_repository()
    return StyleService(gemini_client, image_repo, slide_repo)


def get_cost_service() -> CostService:
    """
    Get cost service instance.

    Returns:
        CostService instance
    """
    slide_repo = get_slide_repository()
    image_repo = get_image_repository()
    return CostService(slide_repo, image_repo)
