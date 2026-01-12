"""Slide business logic service."""

from datetime import datetime, timezone

from models.slide import Slide
from repositories.image_repository import ImageRepository
from repositories.slide_repository import SlideRepository


class SlideService:
    """Service for slide business logic."""

    def __init__(
        self, slide_repo: SlideRepository, image_repo: ImageRepository
    ):
        """
        Initialize slide service.

        Args:
            slide_repo: Slide repository instance
            image_repo: Image repository instance
        """
        self.slide_repo = slide_repo
        self.image_repo = image_repo

    def get_project(self, slug: str):
        """
        Get project with all slides.

        Args:
            slug: Project identifier

        Returns:
            Project object

        Raises:
            ValueError: If project does not exist
        """
        project = self.slide_repo.get_project(slug)
        if not project:
            raise ValueError(f"Project '{slug}' not found")
        return project

    def create_slide(
        self, slug: str, content: str, title: str | None = None, position: int | None = None
    ) -> Slide:
        """
        Create a new slide.

        Args:
            slug: Project identifier
            content: Slide content
            title: Project title (for new projects)
            position: Position to insert slide (0-based index)

        Returns:
            Newly created Slide object
        """
        if not self.slide_repo.project_exists(slug):
            if not title:
                raise ValueError("Title is required when creating a new project")
            self.slide_repo.create_project(slug, title)

        project = self.slide_repo.get_project(slug)
        if not project:
            raise ValueError(f"Failed to create/retrieve project '{slug}'")

        now = datetime.now(timezone.utc)
        new_slide = Slide(
            sid=self.slide_repo.generate_slide_id(),
            content=content,
            created_at=now,
            updated_at=now,
        )

        if position is not None and 0 <= position <= len(project.slides):
            project.slides.insert(position, new_slide)
        else:
            project.slides.append(new_slide)

        self.slide_repo.save_project(slug, project)
        return new_slide

    def update_slide(self, slug: str, sid: str, content: str) -> Slide:
        """
        Update a slide's content.

        Args:
            slug: Project identifier
            sid: Slide ID
            content: New content

        Returns:
            Updated Slide object

        Raises:
            ValueError: If project or slide not found
        """
        project = self.get_project(slug)

        slide_found = False
        for slide in project.slides:
            if slide.sid == sid:
                slide.content = content
                slide.updated_at = datetime.now(timezone.utc)
                slide_found = True
                updated_slide = slide
                break

        if not slide_found:
            raise ValueError(f"Slide '{sid}' not found in project '{slug}'")

        self.slide_repo.save_project(slug, project)
        return updated_slide

    def delete_slide(self, slug: str, sid: str) -> None:
        """
        Delete a slide.

        Args:
            slug: Project identifier
            sid: Slide ID

        Raises:
            ValueError: If project or slide not found
        """
        project = self.get_project(slug)

        original_length = len(project.slides)
        project.slides = [s for s in project.slides if s.sid != sid]

        if len(project.slides) == original_length:
            raise ValueError(f"Slide '{sid}' not found in project '{slug}'")

        self.slide_repo.save_project(slug, project)

    def reorder_slides(self, slug: str, slide_ids: list[str]) -> list[Slide]:
        """
        Reorder slides.

        Args:
            slug: Project identifier
            slide_ids: List of slide IDs in new order

        Returns:
            List of reordered slides

        Raises:
            ValueError: If project not found or slide IDs don't match
        """
        project = self.get_project(slug)

        if len(slide_ids) != len(project.slides):
            raise ValueError("Number of slide IDs must match number of slides")

        slide_map = {slide.sid: slide for slide in project.slides}

        if set(slide_ids) != set(slide_map.keys()):
            raise ValueError("Slide IDs do not match project slides")

        project.slides = [slide_map[sid] for sid in slide_ids]
        self.slide_repo.save_project(slug, project)

        return project.slides

    def update_title(self, slug: str, title: str) -> str:
        """
        Update project title.

        Args:
            slug: Project identifier
            title: New title

        Returns:
            Updated title

        Raises:
            ValueError: If project not found
        """
        project = self.get_project(slug)
        project.title = title
        self.slide_repo.save_project(slug, project)
        return title

    def get_slide_with_images(self, slug: str, sid: str):
        """
        Get slide with image metadata.

        Args:
            slug: Project identifier
            sid: Slide ID

        Returns:
            Tuple of (Slide, has_matching_image, image_count, latest_image)

        Raises:
            ValueError: If slide not found
        """
        slide = self.slide_repo.get_slide(slug, sid)
        if not slide:
            raise ValueError(f"Slide '{sid}' not found in project '{slug}'")

        images = self.image_repo.list_images(slug, sid)
        content_hash = slide.content_hash
        has_matching = any(img.content_hash == content_hash for img in images)

        # Get the most recent image (images are sorted by mtime)
        latest_image = images[-1].filename if images else None

        return slide, has_matching, len(images), latest_image

    def set_default_image(self, slug: str, sid: str, filename: str) -> str:
        """
        Set the default image for a slide.

        Args:
            slug: Project identifier
            sid: Slide ID
            filename: Image filename to set as default

        Returns:
            The filename of the default image

        Raises:
            ValueError: If project or slide not found
        """
        project = self.get_project(slug)

        for slide in project.slides:
            if slide.sid == sid:
                slide.default_image = filename
                self.slide_repo.save_project(slug, project)
                return filename

        raise ValueError(f"Slide '{sid}' not found in project '{slug}'")
