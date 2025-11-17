"""Base classes and data structures for database adapters."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ConnectionConfig:
    """Configuration for database connection.

    Attributes:
        url: Database connection URL
        name: Connection identifier
        min_pool_size: Minimum number of connections in pool
        max_pool_size: Maximum number of connections in pool
        command_timeout: Timeout for commands in seconds
    """
    url: str
    name: str
    min_pool_size: int = 1
    max_pool_size: int = 5
    command_timeout: int = 60


@dataclass
class QueryResult:
    """Standardized query result.

    Attributes:
        columns: List of column definitions with name and dataType
        rows: List of row dictionaries
        row_count: Number of rows returned
    """
    columns: List[Dict[str, str]]
    rows: List[Dict[str, Any]]
    row_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "columns": self.columns,
            "rows": self.rows,
            "rowCount": self.row_count,
        }


@dataclass
class MetadataResult:
    """Standardized metadata result.

    Attributes:
        tables: List of table metadata dictionaries
        views: List of view metadata dictionaries
    """
    tables: List[Dict[str, Any]]
    views: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "tables": self.tables,
            "views": self.views,
        }


class DatabaseAdapter(ABC):
    """Abstract base class for database adapters.

    All database implementations must inherit from this class and
    implement all abstract methods. This ensures consistent behavior
    across different database types.

    The adapter is responsible for:
    - Connection management (pooling)
    - Query execution
    - Metadata extraction
    - Database-specific type conversions

    Example:
        class PostgreSQLAdapter(DatabaseAdapter):
            async def test_connection(self):
                # Implementation
                pass
    """

    def __init__(self, config: ConnectionConfig):
        """Initialize adapter with connection configuration.

        Args:
            config: Connection configuration
        """
        self.config = config
        self._pool: Optional[Any] = None

    @abstractmethod
    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test database connection.

        This method should attempt to connect to the database and
        verify that the connection works.

        Returns:
            Tuple of (success, error_message)
            - success: True if connection successful, False otherwise
            - error_message: Error message if failed, None if successful

        Example:
            success, error = await adapter.test_connection()
            if not success:
                print(f"Connection failed: {error}")
        """
        pass

    @abstractmethod
    async def get_connection_pool(self) -> Any:
        """Get or create connection pool.

        This method should create a connection pool on first call and
        return the cached pool on subsequent calls.

        Returns:
            Database-specific connection pool object

        Example:
            pool = await adapter.get_connection_pool()
            async with pool.acquire() as conn:
                # Use connection
        """
        pass

    @abstractmethod
    async def close_connection_pool(self) -> None:
        """Close connection pool and cleanup resources.

        This method should close all connections in the pool and
        release any resources.

        Example:
            await adapter.close_connection_pool()
        """
        pass

    @abstractmethod
    async def extract_metadata(self) -> MetadataResult:
        """Extract database metadata (tables, columns, etc.).

        This method should query the database's metadata catalogs
        (e.g., information_schema, pg_catalog) to get schema information.

        Returns:
            MetadataResult with tables and views

        Example:
            metadata = await adapter.extract_metadata()
            for table in metadata.tables:
                print(f"Table: {table['name']}")
        """
        pass

    @abstractmethod
    async def execute_query(self, sql: str) -> QueryResult:
        """Execute SQL query.

        This method should execute the given SQL query and return
        results in a standardized format.

        Args:
            sql: SQL query string (already validated)

        Returns:
            QueryResult with columns and rows

        Raises:
            Exception: If query execution fails

        Example:
            result = await adapter.execute_query("SELECT * FROM users")
            for row in result.rows:
                print(row)
        """
        pass

    @abstractmethod
    def get_dialect_name(self) -> str:
        """Get SQL dialect name for this database (for sqlglot).

        Returns:
            Dialect name (e.g., 'postgres', 'mysql', 'oracle')

        Example:
            dialect = adapter.get_dialect_name()  # 'postgres'
        """
        pass

    @abstractmethod
    def get_identifier_quote_char(self) -> str:
        """Get character used for quoting identifiers.

        Returns:
            Quote character (e.g., '"' for PostgreSQL, '`' for MySQL)

        Example:
            quote = adapter.get_identifier_quote_char()  # '"'
            table_name = f'{quote}my_table{quote}'  # "my_table"
        """
        pass

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        await self.close_connection_pool()
