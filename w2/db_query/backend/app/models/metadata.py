"""DatabaseMetadata SQLModel entity."""

from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Text, DateTime
from datetime import datetime, timedelta


class DatabaseMetadata(SQLModel, table=True):
    """Database metadata cache stored in SQLite."""

    __tablename__ = "databasemetadata"

    id: int | None = Field(default=None, primary_key=True)
    database_name: str = Field(foreign_key="databaseconnections.name", index=True)
    metadata_json: str = Field(sa_column=Column(Text))
    fetched_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=False)),
    )
    table_count: int = Field(default=0)

    @property
    def is_stale(self) -> bool:
        """Check if metadata is stale (older than 24 hours)."""
        return datetime.utcnow() - self.fetched_at > timedelta(hours=24)
