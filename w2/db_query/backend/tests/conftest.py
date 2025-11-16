"""Pytest configuration and shared fixtures."""

import pytest


# Import all models at test collection time to ensure SQLModel metadata is populated
def pytest_configure(config):
    """Pytest configuration hook - runs before test collection."""
    # Import all models to register them with SQLModel.metadata
    from app.models.database import DatabaseConnection
    from app.models.metadata import DatabaseMetadata
    from app.models.query import QueryHistory
