"""Image file persistence repository."""

from datetime import datetime, timezone
from pathlib import Path


class ImageInfo:
    """Information about a stored image."""

    def __init__(
        self,
        filename: str,
        content_hash: str,
        created_at: datetime,
    ):
        """
        Initialize image info.

        Args:
            filename: Image filename
            content_hash: Blake3 hash of the content that generated this image
            created_at: Image creation timestamp
        """
        self.filename = filename
        self.content_hash = content_hash
        self.created_at = created_at


class ImageRepository:
    """Repository for image file storage."""

    def __init__(self, base_path: str = "./slides"):
        """
        Initialize image repository.

        Args:
            base_path: Base directory for slides storage
        """
        self.base_path = Path(base_path)

    def save_image(
        self, slug: str, sid: str, content_hash: str, image_data: bytes
    ) -> str:
        """
        Save an image file.

        Args:
            slug: Project identifier
            sid: Slide ID
            content_hash: Blake3 hash of the slide content
            image_data: Image binary data

        Returns:
            Path to saved image file (relative to project root)
        """
        image_dir = self.base_path / slug / "images" / sid
        image_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{content_hash}.jpg"
        image_path = image_dir / filename

        with open(image_path, "wb") as f:
            f.write(image_data)

        return filename

    def get_image_path(
        self, slug: str, sid: str, content_hash: str
    ) -> Path | None:
        """
        Get the path to an image file.

        Args:
            slug: Project identifier
            sid: Slide ID
            content_hash: Blake3 hash of the slide content

        Returns:
            Path to image file if exists, None otherwise
        """
        filename = f"{content_hash}.jpg"
        image_path = self.base_path / slug / "images" / sid / filename

        if image_path.exists():
            return image_path
        return None

    def list_images(self, slug: str, sid: str) -> list[ImageInfo]:
        """
        List all images for a slide.

        Args:
            slug: Project identifier
            sid: Slide ID

        Returns:
            List of ImageInfo objects
        """
        image_dir = self.base_path / slug / "images" / sid
        if not image_dir.exists():
            return []

        images = []
        for image_file in sorted(image_dir.glob("*.jpg"), key=lambda p: p.stat().st_mtime):
            content_hash = image_file.stem
            created_at = datetime.fromtimestamp(
                image_file.stat().st_mtime, tz=timezone.utc
            )
            images.append(
                ImageInfo(
                    filename=image_file.name,
                    content_hash=content_hash,
                    created_at=created_at,
                )
            )

        return images

    def delete_image(self, slug: str, sid: str, content_hash: str) -> None:
        """
        Delete an image file.

        Args:
            slug: Project identifier
            sid: Slide ID
            content_hash: Blake3 hash of the slide content
        """
        image_path = self.get_image_path(slug, sid, content_hash)
        if image_path and image_path.exists():
            image_path.unlink()

    def save_style_image(self, slug: str, image_data: bytes, filename: str) -> str:
        """
        Save a style image.

        Args:
            slug: Project identifier
            image_data: Image binary data
            filename: Filename for the style image

        Returns:
            Filename of saved image
        """
        style_dir = self.base_path / slug / "images" / "style"
        style_dir.mkdir(parents=True, exist_ok=True)

        image_path = style_dir / filename

        with open(image_path, "wb") as f:
            f.write(image_data)

        return filename

    def get_style_image_path(self, slug: str, filename: str) -> Path | None:
        """
        Get the path to a style image.

        Args:
            slug: Project identifier
            filename: Style image filename

        Returns:
            Path to style image if exists, None otherwise
        """
        image_path = self.base_path / slug / "images" / "style" / filename

        if image_path.exists():
            return image_path
        return None

    def list_style_images(self, slug: str) -> list[str]:
        """
        List all style images for a project.

        Args:
            slug: Project identifier

        Returns:
            List of style image filenames
        """
        style_dir = self.base_path / slug / "images" / "style"
        if not style_dir.exists():
            return []

        return [f.name for f in style_dir.glob("*.jpg")]
