"""Project domain model."""

from dataclasses import dataclass, field

from models.slide import Slide
from models.style import Style


@dataclass
class Project:
    """Represents a slides project with metadata and slides."""

    title: str
    slides: list[Slide] = field(default_factory=list)
    style: Style | None = None
    total_cost: float = 0.0
