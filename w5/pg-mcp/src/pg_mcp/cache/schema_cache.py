"""Schema caching layer.

This module provides caching functionality for database schemas to avoid
repeated introspection queries and improve performance.
"""

import asyncio
import contextlib
import logging
from datetime import UTC, datetime

from asyncpg import Pool

from pg_mcp.config.settings import CacheConfig
from pg_mcp.db.introspection import SchemaIntrospector
from pg_mcp.models.schema import DatabaseSchema
from pg_mcp.observability.metrics import metrics

logger = logging.getLogger(__name__)


class SchemaCache:
    """Schema cache manager with TTL and auto-refresh capabilities.

    This class manages cached database schemas with configurable TTL and
    supports automatic background refresh.

    Attributes:
        config: Cache configuration.

    Example:
        >>> cache = SchemaCache(CacheConfig(schema_ttl=3600))
        >>> schema = await cache.load("mydb", pool)
        >>> cached = cache.get("mydb")  # Returns cached schema
        >>> await cache.start_auto_refresh(60, pools)  # Refresh every 60 minutes
    """

    def __init__(self, config: CacheConfig):
        """Initialize schema cache.

        Args:
            config: Cache configuration with TTL and size limits.
        """
        self.config = config
        self._cache: dict[str, DatabaseSchema] = {}
        self._cache_timestamps: dict[str, datetime] = {}
        self._refresh_task: asyncio.Task[None] | None = None
        self._stop_refresh = False

    def get(self, database_name: str) -> DatabaseSchema | None:
        """Get cached schema if available and not expired.

        Args:
            database_name: Name of the database.

        Returns:
            DatabaseSchema | None: Cached schema if available and valid,
                None otherwise.

        Example:
            >>> schema = cache.get("mydb")
            >>> if schema is None:
            ...     schema = await cache.load("mydb", pool)
        """
        if not self.config.enabled:
            return None

        if database_name not in self._cache:
            return None

        # Check if cache is expired
        cache_age = self.get_cache_age(database_name)
        if cache_age is None or cache_age > self.config.schema_ttl:
            # Cache expired, remove it
            self._cache.pop(database_name, None)
            self._cache_timestamps.pop(database_name, None)
            return None

        # Update cache age metric
        metrics.set_schema_cache_age(database_name, cache_age)

        return self._cache[database_name]

    async def load(
        self,
        database_name: str,
        pool: Pool,
    ) -> DatabaseSchema:
        """Load and cache database schema.

        This method performs schema introspection and stores the result
        in cache with current timestamp.

        Args:
            database_name: Name of the database to introspect.
            pool: Connection pool for the database.

        Returns:
            DatabaseSchema: Loaded database schema.

        Raises:
            asyncpg.PostgresError: If database connection or introspection fails.

        Example:
            >>> schema = await cache.load("mydb", pool)
            >>> print(f"Loaded {len(schema.tables)} tables")
        """
        introspector = SchemaIntrospector(pool, database_name)
        schema = await introspector.introspect()

        if self.config.enabled:
            self._cache[database_name] = schema
            self._cache_timestamps[database_name] = datetime.now(UTC)
            # Reset cache age metric to 0 after reload
            metrics.set_schema_cache_age(database_name, 0.0)

        return schema

    async def refresh(
        self,
        database_name: str,
        pool: Pool,
    ) -> None:
        """Refresh schema cache for a specific database.

        This method reloads the schema and updates the cache.

        Args:
            database_name: Name of the database to refresh.
            pool: Connection pool for the database.

        Example:
            >>> await cache.refresh("mydb", pool)
        """
        await self.load(database_name, pool)

    async def start_auto_refresh(
        self,
        interval_minutes: int,
        pools: dict[str, Pool],
    ) -> None:
        """Start automatic background schema refresh.

        This method starts a background task that periodically refreshes
        all cached schemas.

        Args:
            interval_minutes: Refresh interval in minutes.
            pools: Dictionary mapping database names to connection pools.

        Example:
            >>> pools = {"db1": pool1, "db2": pool2}
            >>> await cache.start_auto_refresh(60, pools)
        """
        if not self.config.enabled:
            return

        if self._refresh_task is not None and not self._refresh_task.done():
            # Task already running
            return

        self._stop_refresh = False
        self._refresh_task = asyncio.create_task(self._auto_refresh_loop(interval_minutes, pools))

    async def stop_auto_refresh(self) -> None:
        """Stop automatic refresh task.

        This method immediately cancels the background refresh task if running.

        Example:
            >>> await cache.stop_auto_refresh()
        """
        self._stop_refresh = True

        if self._refresh_task is not None and not self._refresh_task.done():
            # Immediately cancel the task
            self._refresh_task.cancel()
            # Wait for cancellation to complete
            with contextlib.suppress(asyncio.CancelledError):
                await self._refresh_task
            logger.debug("Auto-refresh task cancelled")

    async def _auto_refresh_loop(
        self,
        interval_minutes: int,
        pools: dict[str, Pool],
    ) -> None:
        """Background loop for automatic schema refresh.

        Args:
            interval_minutes: Refresh interval in minutes.
            pools: Dictionary mapping database names to connection pools.
        """
        interval_seconds = interval_minutes * 60

        while not self._stop_refresh:
            try:
                # Wait for the interval
                await asyncio.sleep(interval_seconds)

                if self._stop_refresh:
                    break

                # Refresh all cached schemas
                for database_name, pool in pools.items():
                    if database_name in self._cache:
                        with contextlib.suppress(Exception):
                            await self.refresh(database_name, pool)

            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue
                logger.exception("Error during schema refresh: %s", e)

    def get_cache_age(self, database_name: str) -> float | None:
        """Get cache age in seconds.

        Args:
            database_name: Name of the database.

        Returns:
            float | None: Age in seconds if cached, None otherwise.

        Example:
            >>> age = cache.get_cache_age("mydb")
            >>> if age and age > 3600:
            ...     print("Cache is stale")
        """
        if database_name not in self._cache_timestamps:
            return None

        timestamp = self._cache_timestamps[database_name]
        age = datetime.now(UTC) - timestamp
        return age.total_seconds()

    def clear(self, database_name: str | None = None) -> None:
        """Clear cache for a specific database or all databases.

        Args:
            database_name: Name of the database to clear. If None, clears all.

        Example:
            >>> cache.clear("mydb")  # Clear specific database
            >>> cache.clear()  # Clear all
        """
        if database_name is None:
            self._cache.clear()
            self._cache_timestamps.clear()
        else:
            self._cache.pop(database_name, None)
            self._cache_timestamps.pop(database_name, None)

    def get_cached_databases(self) -> list[str]:
        """Get list of currently cached database names.

        Returns:
            list[str]: List of database names with valid cache entries.

        Example:
            >>> databases = cache.get_cached_databases()
            >>> print(f"Cached: {', '.join(databases)}")
        """
        return list(self._cache.keys())
