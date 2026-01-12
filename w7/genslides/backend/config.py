"""Application configuration management."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    gemini_api_key: str = ""
    slides_base_path: str = "./slides"
    host: str = "0.0.0.0"
    port: int = 3003
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = {"env_file": ".env"}

    def get_slides_path(self) -> Path:
        """Get absolute path to slides directory."""
        path = Path(self.slides_base_path)
        if not path.is_absolute():
            # Resolve relative to the backend directory
            backend_dir = Path(__file__).parent
            path = backend_dir / path
        path.mkdir(parents=True, exist_ok=True)
        return path.resolve()
