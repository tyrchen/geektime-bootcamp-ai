"""Cost calculation business logic service."""

from repositories.image_repository import ImageRepository
from repositories.slide_repository import SlideRepository


class CostService:
    """Service for cost calculation and statistics."""

    def __init__(
        self,
        slide_repo: SlideRepository,
        image_repo: ImageRepository,
    ):
        """
        Initialize cost service.

        Args:
            slide_repo: Slide repository instance
            image_repo: Image repository instance
        """
        self.slide_repo = slide_repo
        self.image_repo = image_repo

    def get_cost_stats(self, slug: str):
        """
        Get cost statistics for a project.

        Args:
            slug: Project identifier

        Returns:
            Dictionary with cost breakdown

        Raises:
            ValueError: If project not found
        """
        project = self.slide_repo.get_project(slug)
        if not project:
            raise ValueError(f"Project '{slug}' not found")

        total_slide_images = 0
        for slide in project.slides:
            images = self.image_repo.list_images(slug, slide.sid)
            total_slide_images += len(images)

        style_images = len(self.image_repo.list_style_images(slug))

        total_images = total_slide_images + style_images

        from clients.gemini_client import GeminiClient

        cost_per_image = GeminiClient.COST_PER_IMAGE

        slide_images_cost = total_slide_images * cost_per_image
        style_images_cost = style_images * cost_per_image

        return {
            "slug": slug,
            "total_cost": project.total_cost,
            "currency": "USD",
            "breakdown": {
                "slide_images": slide_images_cost,
                "style_images": style_images_cost,
            },
            "image_count": total_images,
            "cost_per_image": cost_per_image,
        }
