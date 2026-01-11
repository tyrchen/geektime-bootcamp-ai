"""Mock asyncpg pool and connection for testing."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock


class MockRecord(dict):
    """Mock asyncpg.Record that behaves like a dict."""

    pass


class MockConnection:
    """Mock asyncpg connection."""

    def __init__(self, records: list[dict] | None = None):
        """Initialize mock connection.

        Args:
            records: Optional list of records to return from fetch() calls.
        """
        self.records = records or []
        self.executed_sql: list[str] = []
        self.closed = False

    async def fetch(self, sql: str, *args, **kwargs) -> list[MockRecord]:
        """Mock fetch method."""
        self.executed_sql.append(sql)
        return [MockRecord(record) for record in self.records]

    async def fetchrow(self, sql: str, *args, **kwargs) -> MockRecord | None:
        """Mock fetchrow method."""
        self.executed_sql.append(sql)
        if self.records:
            return MockRecord(self.records[0])
        return None

    async def execute(self, sql: str, *args, **kwargs) -> str:
        """Mock execute method."""
        self.executed_sql.append(sql)
        return "SELECT 1"

    async def close(self) -> None:
        """Mock close method."""
        self.closed = True

    def transaction(self, *, readonly: bool = False):
        """Mock transaction context manager."""
        return MockTransaction()


class MockTransaction:
    """Mock asyncpg transaction."""

    async def __aenter__(self):
        """Enter transaction."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit transaction."""
        return False


class MockPool:
    """Mock asyncpg connection pool."""

    def __init__(self, records: list[dict] | None = None):
        """Initialize mock pool.

        Args:
            records: Optional list of records to return from connections.
        """
        self.records = records or []
        self._size = 10
        self._idle_size = 8
        self.closed = False

    def acquire(self):
        """Mock acquire context manager."""
        return MockPoolAcquire(self.records)

    def get_size(self) -> int:
        """Get pool size."""
        return self._size

    def get_idle_size(self) -> int:
        """Get idle connection count."""
        return self._idle_size

    async def close(self) -> None:
        """Close the pool."""
        self.closed = True

    def terminate(self) -> None:
        """Terminate the pool immediately."""
        self.closed = True


class MockPoolAcquire:
    """Mock pool acquire context manager."""

    def __init__(self, records: list[dict] | None = None):
        """Initialize acquire context.

        Args:
            records: Optional list of records for the connection.
        """
        self.records = records or []
        self.connection: MockConnection | None = None

    async def __aenter__(self) -> MockConnection:
        """Acquire connection."""
        self.connection = MockConnection(self.records)
        return self.connection

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release connection."""
        return False


def create_mock_pool(records: list[dict] | None = None) -> MockPool:
    """Create a mock asyncpg pool.

    Args:
        records: Optional list of records to return from queries.

    Returns:
        MockPool instance.

    Example:
        >>> pool = create_mock_pool([{"id": 1, "name": "Test"}])
        >>> async with pool.acquire() as conn:
        ...     results = await conn.fetch("SELECT * FROM users")
        ...     assert len(results) == 1
    """
    return MockPool(records)
