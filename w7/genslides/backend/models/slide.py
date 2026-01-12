"""Slide domain model."""

from dataclasses import dataclass
from datetime import datetime

from utils.hash import compute_blake3


@dataclass
class Slide:
    """Represents a single slide in a presentation."""

    sid: str
    content: str
    created_at: datetime
    updated_at: datetime
    default_image: str | None = None  # Filename of the selected default image

    @property
    def content_hash(self) -> str:
        """
        Compute blake3 hash based on content.

        Returns:
            The blake3 hash of the slide content (16 characters)
        """
        return compute_blake3(self.content)
