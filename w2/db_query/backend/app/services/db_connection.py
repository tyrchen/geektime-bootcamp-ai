"""Database connection service for managing PostgreSQL connections."""

import asyncpg
from typing import Dict
from datetime import datetime
from app.models.database import DatabaseConnection, ConnectionStatus


# Global connection pool cache
_connection_pools: Dict[str, asyncpg.Pool] = {}


async def test_connection(url: str) -> tuple[bool, str | None]:
    """
    Test PostgreSQL database connection.

    Args:
        url: PostgreSQL connection URL

    Returns:
        Tuple of (success, error_message)
    """
    try:
        conn = await asyncpg.connect(url)
        await conn.close()
        return True, None
    except Exception as e:
        return False, str(e)


async def get_connection_pool(
    name: str, url: str, min_size: int = 1, max_size: int = 5
) -> asyncpg.Pool:
    """
    Get or create asyncpg connection pool for a database.

    Args:
        name: Database connection name
        url: PostgreSQL connection URL
        min_size: Minimum pool size
        max_size: Maximum pool size

    Returns:
        asyncpg connection pool
    """
    if name not in _connection_pools:
        pool = await asyncpg.create_pool(
            url,
            min_size=min_size,
            max_size=max_size,
            command_timeout=60,
        )
        _connection_pools[name] = pool
    return _connection_pools[name]


async def close_connection_pool(name: str) -> None:
    """
    Close connection pool for a database.

    Args:
        name: Database connection name
    """
    if name in _connection_pools:
        pool = _connection_pools.pop(name)
        await pool.close()


async def close_all_connection_pools() -> None:
    """Close all connection pools."""
    for name in list(_connection_pools.keys()):
        await close_connection_pool(name)
