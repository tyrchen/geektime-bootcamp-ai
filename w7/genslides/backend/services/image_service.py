"""Image generation business logic service."""

from clients.gemini_client import GeminiClient
from repositories.image_repository import ImageInfo, ImageRepository
from repositories.slide_repository import SlideRepository


class ImageService:
    """Service for image generation and management."""

    def __init__(
        self,
        gemini_client: GeminiClient,
        image_repo: ImageRepository,
        slide_repo: SlideRepository,
    ):
        """
        Initialize image service.

        Args:
            gemini_client: Gemini client instance
            image_repo: Image repository instance
            slide_repo: Slide repository instance
        """
        self.gemini_client = gemini_client
        self.image_repo = image_repo
        self.slide_repo = slide_repo

    async def generate_image(
        self, slug: str, sid: str, prompt_override: str | None = None
    ) -> tuple[ImageInfo, float]:
        """
        Generate an image for a slide.

        Args:
            slug: Project identifier
            sid: Slide ID
            prompt_override: Optional prompt override

        Returns:
            Tuple of (ImageInfo, generation_cost)

        Raises:
            ValueError: If project or slide not found
        """
        project = self.slide_repo.get_project(slug)
        if not project:
            raise ValueError(f"Project '{slug}' not found")

        slide = self.slide_repo.get_slide(slug, sid)
        if not slide:
            raise ValueError(f"Slide '{sid}' not found in project '{slug}'")

        prompt = prompt_override if prompt_override else slide.content

        style_image_data = None
        if project.style:
            style_image_path = self.image_repo.get_style_image_path(
                slug, project.style.image
            )
            if style_image_path:
                with open(style_image_path, "rb") as f:
                    style_image_data = f.read()

        image_data = await self.gemini_client.generate_image(prompt, style_image_data)

        filename = self.image_repo.save_image(
            slug, sid, slide.content_hash, image_data
        )

        images = self.image_repo.list_images(slug, sid)
        image_info = next(
            (img for img in images if img.filename == filename), None
        )

        if not image_info:
            raise ValueError("Failed to retrieve saved image")

        project.total_cost += GeminiClient.COST_PER_IMAGE
        self.slide_repo.save_project(slug, project)

        return image_info, GeminiClient.COST_PER_IMAGE

    def get_slide_images(self, slug: str, sid: str) -> list[ImageInfo]:
        """
        Get all images for a slide.

        Args:
            slug: Project identifier
            sid: Slide ID

        Returns:
            List of ImageInfo objects

        Raises:
            ValueError: If project or slide not found
        """
        project = self.slide_repo.get_project(slug)
        if not project:
            raise ValueError(f"Project '{slug}' not found")

        slide = self.slide_repo.get_slide(slug, sid)
        if not slide:
            raise ValueError(f"Slide '{sid}' not found in project '{slug}'")

        return self.image_repo.list_images(slug, sid)

    def get_matching_image(
        self, slug: str, sid: str, content_hash: str
    ) -> ImageInfo | None:
        """
        Get image matching a specific content hash.

        Args:
            slug: Project identifier
            sid: Slide ID
            content_hash: Blake3 hash to match

        Returns:
            ImageInfo if matching image exists, None otherwise
        """
        images = self.image_repo.list_images(slug, sid)
        return next(
            (img for img in images if img.content_hash == content_hash), None
        )
