"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


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

    # Query configuration
    query_default_limit: int = 1000
    query_history_retention: int = 50

    # Database pool configuration
    db_pool_min_size: int = 1
    db_pool_max_size: int = 5
    db_pool_command_timeout: int = 60

    # Metadata cache configuration
    metadata_cache_hours: int = 24

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
