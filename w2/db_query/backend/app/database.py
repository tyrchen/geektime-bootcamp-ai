"""SQLite database setup and session management."""

from sqlmodel import SQLModel, create_engine, Session
from app.config import settings
from typing import Generator


# Create SQLite engine
engine = create_engine(
    f"sqlite:///{settings.db_path}",
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=False,  # Set to True for SQL query logging
)


def init_db() -> None:
    """Initialize database by creating all tables."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Dependency for FastAPI to get database session."""
    with Session(engine) as session:
        yield session
