"""Database adapter registry (Factory pattern)."""

from typing import Dict, Type, List
import logging

from app.models.database import DatabaseType
from app.adapters.base import DatabaseAdapter, ConnectionConfig
from app.adapters.postgresql import PostgreSQLAdapter
from app.adapters.mysql import MySQLAdapter

logger = logging.getLogger(__name__)


class DatabaseAdapterRegistry:
    """Registry for database adapters (Factory pattern).

    This class maintains a mapping of database types to adapter classes.
    New database types can be registered without modifying existing code.

    Example:
        registry = DatabaseAdapterRegistry()
        config = ConnectionConfig(url="postgresql://...", name="mydb")
        adapter = registry.get_adapter(DatabaseType.POSTGRESQL, config)
        result = await adapter.execute_query("SELECT 1")
    """

    def __init__(self):
        """Initialize registry with built-in adapters."""
        self._adapters: Dict[DatabaseType, Type[DatabaseAdapter]] = {}
        self._instances: Dict[str, DatabaseAdapter] = {}

        # Register built-in adapters
        self.register(DatabaseType.POSTGRESQL, PostgreSQLAdapter)
        self.register(DatabaseType.MYSQL, MySQLAdapter)

        logger.info(f"Initialized adapter registry with {len(self._adapters)} adapters")

    def register(
        self, db_type: DatabaseType, adapter_class: Type[DatabaseAdapter]
    ) -> None:
        """Register a database adapter.

        Args:
            db_type: Database type enum value
            adapter_class: Adapter class (must inherit from DatabaseAdapter)

        Raises:
            TypeError: If adapter_class doesn't inherit from DatabaseAdapter

        Example:
            registry.register(DatabaseType.ORACLE, OracleAdapter)
        """
        if not issubclass(adapter_class, DatabaseAdapter):
            raise TypeError(
                f"{adapter_class.__name__} must inherit from DatabaseAdapter"
            )

        self._adapters[db_type] = adapter_class
        logger.info(f"Registered {adapter_class.__name__} for {db_type.value}")

    def get_adapter(
        self, db_type: DatabaseType, config: ConnectionConfig
    ) -> DatabaseAdapter:
        """Get or create database adapter instance.

        Args:
            db_type: Database type
            config: Connection configuration

        Returns:
            DatabaseAdapter instance

        Raises:
            ValueError: If database type is not registered

        Example:
            config = ConnectionConfig(url="mysql://...", name="mydb")
            adapter = registry.get_adapter(DatabaseType.MYSQL, config)
        """
        if db_type not in self._adapters:
            available = [t.value for t in self._adapters.keys()]
            raise ValueError(
                f"Unsupported database type: {db_type.value}. "
                f"Available types: {available}"
            )

        # Use connection name and type as cache key
        cache_key = f"{db_type.value}:{config.name}"

        if cache_key not in self._instances:
            adapter_class = self._adapters[db_type]
            self._instances[cache_key] = adapter_class(config)
            logger.info(f"Created new {adapter_class.__name__} instance for {config.name}")

        return self._instances[cache_key]

    async def close_adapter(self, db_type: DatabaseType, name: str) -> None:
        """Close and remove adapter instance.

        Args:
            db_type: Database type
            name: Connection name
        """
        cache_key = f"{db_type.value}:{name}"

        if cache_key in self._instances:
            adapter = self._instances.pop(cache_key)
            await adapter.close_connection_pool()
            logger.info(f"Closed adapter for {name}")

    async def close_all_adapters(self) -> None:
        """Close all adapter instances."""
        logger.info(f"Closing {len(self._instances)} adapter instances")
        for adapter in list(self._instances.values()):
            await adapter.close_connection_pool()
        self._instances.clear()

    def is_supported(self, db_type: DatabaseType) -> bool:
        """Check if database type is supported.

        Args:
            db_type: Database type to check

        Returns:
            True if supported, False otherwise
        """
        return db_type in self._adapters

    def get_supported_types(self) -> List[DatabaseType]:
        """Get list of supported database types.

        Returns:
            List of registered database types
        """
        return list(self._adapters.keys())


# Global registry instance
adapter_registry = DatabaseAdapterRegistry()
