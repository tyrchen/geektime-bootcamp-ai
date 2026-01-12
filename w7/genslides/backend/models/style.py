"""Style domain model."""

from dataclasses import dataclass


@dataclass
class Style:
    """Style configuration for image generation."""

    prompt: str
    image: str
