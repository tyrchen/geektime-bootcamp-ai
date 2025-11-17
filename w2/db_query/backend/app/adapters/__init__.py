"""Database adapters package."""

from app.adapters.base import (
    DatabaseAdapter,
    ConnectionConfig,
    QueryResult,
    MetadataResult,
)

__all__ = [
    "DatabaseAdapter",
    "ConnectionConfig",
    "QueryResult",
    "MetadataResult",
]
