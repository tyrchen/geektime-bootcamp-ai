"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import os


class Settings(BaseSettings):
    """Application settings."""

    # OpenAI API
    openai_api_key: str

    # Data directory
    db_query_data_dir: str = str(Path.home() / ".db_query")

    # Logging
    log_level: str = "INFO"

    # CORS
    cors_origins: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins string into list."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def db_path(self) -> Path:
        """Get SQLite database path."""
        data_dir = Path(self.db_query_data_dir).expanduser()
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "db_query.db"


settings = Settings()
