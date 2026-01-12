"""Style management business logic service."""

import uuid

from clients.gemini_client import GeminiClient
from models.style import Style
from repositories.image_repository import ImageRepository
from repositories.slide_repository import SlideRepository


class StyleCandidate:
    """Style candidate information."""

    def __init__(self, filename: str):
        """
        Initialize style candidate.

        Args:
            filename: Candidate image filename
        """
        self.filename = filename


class StyleService:
    """Service for style management."""

    def __init__(
        self,
        gemini_client: GeminiClient,
        image_repo: ImageRepository,
        slide_repo: SlideRepository,
    ):
        """
        Initialize style service.

        Args:
            gemini_client: Gemini client instance
            image_repo: Image repository instance
            slide_repo: Slide repository instance
        """
        self.gemini_client = gemini_client
        self.image_repo = image_repo
        self.slide_repo = slide_repo

    async def generate_style_candidates(
        self, slug: str, prompt: str
    ) -> tuple[list[StyleCandidate], float]:
        """
        Generate style candidate images.

        Args:
            slug: Project identifier
            prompt: Style description prompt

        Returns:
            Tuple of (list of StyleCandidate, total_cost)

        Raises:
            ValueError: If project not found
        """
        project = self.slide_repo.get_project(slug)
        if not project:
            raise ValueError(f"Project '{slug}' not found")

        candidates_data = await self.gemini_client.generate_style_candidates(prompt)

        candidates = []
        for i, image_data in enumerate(candidates_data):
            filename = f"candidate_{i + 1}_{uuid.uuid4().hex[:8]}.jpg"
            self.image_repo.save_style_image(slug, image_data, filename)
            candidates.append(StyleCandidate(filename=filename))

        cost = len(candidates_data) * GeminiClient.COST_PER_IMAGE

        return candidates, cost

    def select_style(
        self, slug: str, prompt: str, image_filename: str
    ) -> Style:
        """
        Select and save a style for the project.

        Args:
            slug: Project identifier
            prompt: Style description prompt
            image_filename: Selected candidate image filename

        Returns:
            Selected Style object

        Raises:
            ValueError: If project not found or image doesn't exist
        """
        project = self.slide_repo.get_project(slug)
        if not project:
            raise ValueError(f"Project '{slug}' not found")

        image_path = self.image_repo.get_style_image_path(slug, image_filename)
        if not image_path:
            raise ValueError(f"Style image '{image_filename}' not found")

        final_filename = f"style_{uuid.uuid4().hex[:8]}.jpg"

        with open(image_path, "rb") as f:
            image_data = f.read()

        self.image_repo.save_style_image(slug, image_data, final_filename)

        style = Style(prompt=prompt, image=final_filename)
        project.style = style
        self.slide_repo.save_project(slug, project)

        return style

    def get_style(self, slug: str) -> Style | None:
        """
        Get the style for a project.

        Args:
            slug: Project identifier

        Returns:
            Style object if set, None otherwise

        Raises:
            ValueError: If project not found
        """
        project = self.slide_repo.get_project(slug)
        if not project:
            raise ValueError(f"Project '{slug}' not found")

        return project.style
