"""DatabaseConnection SQLModel entity."""

from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from enum import Enum


class ConnectionStatus(str, Enum):
    """Database connection status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class DatabaseConnection(SQLModel, table=True):
    """Database connection entity stored in SQLite."""

    __tablename__ = "databaseconnections"

    name: str = Field(primary_key=True, max_length=50)
    url: str = Field(index=True, max_length=500)
    description: str | None = Field(default=None, max_length=200)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_connected_at: datetime | None = None
    status: ConnectionStatus = Field(default=ConnectionStatus.ACTIVE)
