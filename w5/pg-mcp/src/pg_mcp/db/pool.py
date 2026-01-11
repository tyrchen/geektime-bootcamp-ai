"""Database connection pool management.

This module provides utilities for creating and managing asyncpg connection
pools for PostgreSQL databases.
"""

import asyncpg
from asyncpg import Pool

from pg_mcp.config.settings import DatabaseConfig


async def create_pool(config: DatabaseConfig) -> Pool:
    """Create a connection pool for a single database.

    Args:
        config: Database configuration containing connection parameters
            and pool settings.

    Returns:
        Pool: An asyncpg connection pool instance.

    Raises:
        asyncpg.PostgresError: If connection to the database fails.

    Example:
        >>> config = DatabaseConfig(host="localhost", name="mydb")
        >>> pool = await create_pool(config)
        >>> async with pool.acquire() as conn:
        ...     result = await conn.fetch("SELECT 1")
    """
    pool = await asyncpg.create_pool(
        host=config.host,
        port=config.port,
        database=config.database,
        user=config.user,
        password=config.password,
        min_size=config.min_pool_size,
        max_size=config.max_pool_size,
        timeout=config.pool_timeout,
        command_timeout=config.command_timeout,
    )

    if pool is None:
        raise RuntimeError(f"Failed to create connection pool for {config.name}")

    return pool


async def create_pools(configs: list[DatabaseConfig]) -> dict[str, Pool]:
    """Create connection pools for multiple databases.

    This function creates pools concurrently for all provided database
    configurations.

    Args:
        configs: List of database configurations.

    Returns:
        dict[str, Pool]: Dictionary mapping database names to their pools.

    Raises:
        asyncpg.PostgresError: If any database connection fails.

    Example:
        >>> configs = [
        ...     DatabaseConfig(name="db1", host="localhost"),
        ...     DatabaseConfig(name="db2", host="localhost"),
        ... ]
        >>> pools = await create_pools(configs)
        >>> assert "db1" in pools and "db2" in pools
    """
    pools: dict[str, Pool] = {}

    for config in configs:
        pool = await create_pool(config)
        pools[config.name] = pool

    return pools


async def close_pools(pools: dict[str, Pool], timeout: float = 10.0) -> None:
    """Close all connection pools gracefully.

    This function closes all pools and waits for all connections to be
    released properly. If graceful shutdown takes too long, it will
    forcefully terminate the pools.

    Args:
        pools: Dictionary mapping database names to their pools.
        timeout: Maximum time in seconds to wait for graceful shutdown
            before forcing termination. Default: 10.0 seconds.

    Example:
        >>> pools = await create_pools(configs)
        >>> # ... use pools ...
        >>> await close_pools(pools, timeout=5.0)
    """
    import asyncio
    import logging

    logger = logging.getLogger(__name__)

    for db_name, pool in pools.items():
        try:
            # Try graceful close with timeout
            await asyncio.wait_for(pool.close(), timeout=timeout)
            logger.info(f"Connection pool for '{db_name}' closed gracefully")
        except asyncio.TimeoutError:
            # Force termination if graceful close times out
            logger.warning(
                f"Graceful close timed out for '{db_name}', forcing termination"
            )
            pool.terminate()
            logger.info(f"Connection pool for '{db_name}' terminated")
        except Exception as e:
            # Log error but continue closing other pools
            logger.error(f"Error closing pool for '{db_name}': {e!s}")
            # Force terminate on error
            pool.terminate()
