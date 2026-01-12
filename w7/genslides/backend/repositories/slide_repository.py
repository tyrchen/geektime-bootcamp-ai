"""Slide data persistence repository."""

import uuid
from datetime import datetime, timezone
from pathlib import Path

import yaml

from models.project import Project
from models.slide import Slide
from models.style import Style


class SlideRepository:
    """Repository for slide data persistence using YAML files."""

    def __init__(self, base_path: str = "./slides"):
        """
        Initialize slide repository.

        Args:
            base_path: Base directory for slides storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def get_project(self, slug: str) -> Project | None:
        """
        Get project by slug.

        Args:
            slug: Project identifier

        Returns:
            Project object if exists, None otherwise
        """
        outline_path = self.base_path / slug / "outline.yml"
        if not outline_path.exists():
            return None

        with open(outline_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        style = None
        if data.get("style"):
            style = Style(
                prompt=data["style"]["prompt"],
                image=data["style"]["image"],
            )

        slides = [
            Slide(
                sid=slide_data["sid"],
                content=slide_data["content"],
                created_at=datetime.fromisoformat(slide_data["created_at"]),
                updated_at=datetime.fromisoformat(slide_data["updated_at"]),
                default_image=slide_data.get("default_image"),
            )
            for slide_data in data.get("slides", [])
        ]

        return Project(
            title=data["title"],
            style=style,
            slides=slides,
            total_cost=data.get("total_cost", 0.0),
        )

    def save_project(self, slug: str, project: Project) -> None:
        """
        Save project to YAML file.

        Args:
            slug: Project identifier
            project: Project object to save
        """
        project_dir = self.base_path / slug
        project_dir.mkdir(parents=True, exist_ok=True)

        outline_path = project_dir / "outline.yml"

        slides_data = []
        for slide in project.slides:
            slide_dict = {
                "sid": slide.sid,
                "content": slide.content,
                "created_at": slide.created_at.isoformat(),
                "updated_at": slide.updated_at.isoformat(),
            }
            if slide.default_image:
                slide_dict["default_image"] = slide.default_image
            slides_data.append(slide_dict)

        data = {
            "title": project.title,
            "total_cost": project.total_cost,
            "slides": slides_data,
        }

        if project.style:
            data["style"] = {
                "prompt": project.style.prompt,
                "image": project.style.image,
            }

        with open(outline_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)

    def create_project(self, slug: str, title: str) -> Project:
        """
        Create a new project.

        Args:
            slug: Project identifier
            title: Project title

        Returns:
            Newly created Project object
        """
        project = Project(title=title)
        self.save_project(slug, project)
        return project

    def delete_project(self, slug: str) -> None:
        """
        Delete a project and all its files.

        Args:
            slug: Project identifier
        """
        import shutil

        project_dir = self.base_path / slug
        if project_dir.exists():
            shutil.rmtree(project_dir)

    def project_exists(self, slug: str) -> bool:
        """
        Check if a project exists.

        Args:
            slug: Project identifier

        Returns:
            True if project exists, False otherwise
        """
        outline_path = self.base_path / slug / "outline.yml"
        return outline_path.exists()

    def generate_slide_id(self) -> str:
        """
        Generate a unique slide ID.

        Returns:
            Unique slide ID string
        """
        return f"slide_{uuid.uuid4().hex[:8]}"

    def get_slide(self, slug: str, sid: str) -> Slide | None:
        """
        Get a specific slide from a project.

        Args:
            slug: Project identifier
            sid: Slide ID

        Returns:
            Slide object if found, None otherwise
        """
        project = self.get_project(slug)
        if not project:
            return None

        for slide in project.slides:
            if slide.sid == sid:
                return slide

        return None
