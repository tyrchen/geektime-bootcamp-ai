# Implementation Guide: Architecture Redesign

## Overview

This guide provides step-by-step instructions for implementing the new architecture. The implementation is designed to be incremental and non-breaking.

## Prerequisites

- Understanding of the current codebase
- Familiarity with Python async programming
- Knowledge of ABC (Abstract Base Classes)
- Understanding of dependency injection pattern

## Implementation Phases

### Phase 1: Create Adapter Infrastructure (Week 1)

#### Task 1.1: Create Base Adapter Module

**File**: `app/adapters/base.py`

```python
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
```

**Validation**:
```bash
# Test that the module can be imported
python -c "from app.adapters.base import DatabaseAdapter, ConnectionConfig"
```

#### Task 1.2: Create PostgreSQL Adapter

**File**: `app/adapters/postgresql.py`

Extract the PostgreSQL-specific logic from:
- `app/services/db_connection.py` → connection pool management
- `app/services/metadata.py` → metadata extraction (extract_postgres_metadata)
- `app/services/query.py` → query execution (PostgreSQL branch)

```python
"""PostgreSQL database adapter."""

import asyncpg
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime

from app.adapters.base import (
    DatabaseAdapter,
    ConnectionConfig,
    QueryResult,
    MetadataResult,
)


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL database adapter using asyncpg."""

    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test PostgreSQL connection."""
        try:
            conn = await asyncpg.connect(self.config.url)
            await conn.close()
            return True, None
        except Exception as e:
            return False, str(e)

    async def get_connection_pool(self) -> asyncpg.Pool:
        """Get or create asyncpg connection pool."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                self.config.url,
                min_size=self.config.min_pool_size,
                max_size=self.config.max_pool_size,
                command_timeout=self.config.command_timeout,
            )
        return self._pool

    async def close_connection_pool(self) -> None:
        """Close PostgreSQL connection pool."""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def extract_metadata(self) -> MetadataResult:
        """Extract PostgreSQL metadata from pg_catalog."""
        pool = await self.get_connection_pool()

        async with pool.acquire() as conn:
            # Get all tables and views
            tables_query = """
                SELECT
                    schemaname,
                    tablename,
                    'table' AS type
                FROM pg_tables
                WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                UNION ALL
                SELECT
                    schemaname,
                    viewname AS tablename,
                    'view' AS type
                FROM pg_views
                WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                ORDER BY schemaname, tablename
            """
            tables_rows = await conn.fetch(tables_query)

            tables: List[Dict[str, Any]] = []
            views: List[Dict[str, Any]] = []

            for row in tables_rows:
                schema_name = row["schemaname"]
                table_name = row["tablename"]
                table_type = row["type"]

                # Get columns for this table/view
                columns = await self._get_columns(conn, schema_name, table_name)

                # Get row count for tables (not views)
                row_count = None
                if table_type == "table":
                    row_count = await self._get_row_count(conn, schema_name, table_name)

                table_meta = {
                    "name": table_name,
                    "type": table_type,
                    "schemaName": schema_name,
                    "columns": columns,
                }
                if row_count is not None:
                    table_meta["rowCount"] = row_count

                if table_type == "table":
                    tables.append(table_meta)
                else:
                    views.append(table_meta)

        return MetadataResult(tables=tables, views=views)

    async def _get_columns(
        self, conn: asyncpg.Connection, schema_name: str, table_name: str
    ) -> List[Dict[str, Any]]:
        """Get column metadata for a table/view."""
        columns_query = """
            SELECT
                c.column_name,
                c.data_type,
                c.character_maximum_length,
                c.is_nullable,
                c.column_default,
                c.ordinal_position,
                CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END AS is_primary_key,
                CASE WHEN uq.column_name IS NOT NULL THEN true ELSE false END AS is_unique
            FROM information_schema.columns c
            LEFT JOIN (
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                    AND tc.table_name = kcu.table_name
                WHERE tc.table_schema = $1
                    AND tc.table_name = $2
                    AND tc.constraint_type = 'PRIMARY KEY'
            ) pk ON c.column_name = pk.column_name
            LEFT JOIN (
                SELECT DISTINCT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                    AND tc.table_name = kcu.table_name
                WHERE tc.table_schema = $1
                    AND tc.table_name = $2
                    AND tc.constraint_type = 'UNIQUE'
            ) uq ON c.column_name = uq.column_name
            WHERE c.table_schema = $1
                AND c.table_name = $2
            ORDER BY c.ordinal_position
        """
        columns_rows = await conn.fetch(columns_query, schema_name, table_name)

        columns: List[Dict[str, Any]] = []
        for col_row in columns_rows:
            data_type = col_row["data_type"]
            if col_row["character_maximum_length"]:
                data_type = f"{data_type}({col_row['character_maximum_length']})"

            column_meta = {
                "name": col_row["column_name"],
                "dataType": data_type,
                "nullable": col_row["is_nullable"] == "YES",
                "primaryKey": col_row["is_primary_key"],
                "unique": col_row["is_unique"],
                "defaultValue": col_row["column_default"],
            }
            columns.append(column_meta)

        return columns

    async def _get_row_count(
        self, conn: asyncpg.Connection, schema_name: str, table_name: str
    ) -> Optional[int]:
        """Get row count for a table."""
        try:
            count_query = f'SELECT COUNT(*) FROM "{schema_name}"."{table_name}"'
            count_result = await conn.fetchrow(count_query)
            if count_result:
                return count_result[0]
        except Exception:
            # If count fails, return None
            pass
        return None

    async def execute_query(self, sql: str) -> QueryResult:
        """Execute query against PostgreSQL."""
        pool = await self.get_connection_pool()

        async with pool.acquire() as conn:
            rows = await conn.fetch(sql)

            # Convert to standard format
            columns: List[Dict[str, str]] = []
            result_rows: List[Dict[str, Any]] = []

            if rows:
                # Get column names and types from first row
                first_row = rows[0]
                for key, value in first_row.items():
                    data_type = self._infer_type(value)
                    columns.append({"name": key, "dataType": data_type})

                # Convert all rows
                for row in rows:
                    result_rows.append(dict(row))

            return QueryResult(
                columns=columns,
                rows=result_rows,
                row_count=len(result_rows)
            )

    def get_dialect_name(self) -> str:
        """Get PostgreSQL dialect name."""
        return "postgres"

    def get_identifier_quote_char(self) -> str:
        """PostgreSQL uses double quotes."""
        return '"'

    @staticmethod
    def _infer_type(value: Any) -> str:
        """Infer PostgreSQL type from Python value."""
        if value is None:
            return "unknown"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "double precision"
        elif isinstance(value, str):
            return "character varying"
        elif isinstance(value, datetime):
            return "timestamp"
        else:
            return str(type(value).__name__)
```

**Validation**:
```bash
# Run pytest for adapter tests
pytest tests/adapters/test_postgresql.py -v
```

#### Task 1.3: Create MySQL Adapter

**File**: `app/adapters/mysql.py`

Similar to PostgreSQL adapter, extract from:
- `app/services/mysql_connection.py`
- `app/services/mysql_metadata.py`
- `app/services/mysql_query.py`

```python
"""MySQL database adapter."""

import aiomysql
from typing import Dict, List, Any, Tuple, Optional
from urllib.parse import urlparse
from datetime import datetime

from app.adapters.base import (
    DatabaseAdapter,
    ConnectionConfig,
    QueryResult,
    MetadataResult,
)


class MySQLAdapter(DatabaseAdapter):
    """MySQL database adapter using aiomysql."""

    def _parse_url(self, url: str) -> Dict[str, Any]:
        """Parse MySQL connection URL."""
        parsed = urlparse(url)
        return {
            'host': parsed.hostname or 'localhost',
            'port': parsed.port or 3306,
            'user': parsed.username or 'root',
            'password': parsed.password or '',
            'db': parsed.path.lstrip('/') if parsed.path else None,
        }

    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test MySQL connection."""
        try:
            params = self._parse_url(self.config.url)
            conn = await aiomysql.connect(**params)
            await conn.ensure_closed()
            return True, None
        except Exception as e:
            return False, str(e)

    async def get_connection_pool(self) -> aiomysql.Pool:
        """Get or create aiomysql connection pool."""
        if self._pool is None:
            params = self._parse_url(self.config.url)
            self._pool = await aiomysql.create_pool(
                host=params['host'],
                port=params['port'],
                user=params['user'],
                password=params['password'],
                db=params['db'],
                minsize=self.config.min_pool_size,
                maxsize=self.config.max_pool_size,
                autocommit=True,
            )
        return self._pool

    async def close_connection_pool(self) -> None:
        """Close MySQL connection pool."""
        if self._pool is not None:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None

    # ... implement extract_metadata() similar to mysql_metadata.py
    # ... implement execute_query() similar to mysql_query.py

    def get_dialect_name(self) -> str:
        """Get MySQL dialect name."""
        return "mysql"

    def get_identifier_quote_char(self) -> str:
        """MySQL uses backticks."""
        return "`"
```

#### Task 1.4: Create Adapter Registry

**File**: `app/adapters/registry.py`

```python
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
```

**Validation**:
```bash
python -c "from app.adapters.registry import adapter_registry; print(adapter_registry.get_supported_types())"
```

### Phase 2: Create Service Layer (Week 2)

#### Task 2.1: Create Database Service

**File**: `app/services/database_service.py`

```python
"""High-level database service (Facade pattern)."""

import time
from typing import Tuple, Optional
import logging

from app.models.database import DatabaseType
from app.adapters.base import ConnectionConfig, QueryResult, MetadataResult
from app.adapters.registry import DatabaseAdapterRegistry, adapter_registry
from app.services.sql_validator import validate_and_transform_sql, SqlValidationError

logger = logging.getLogger(__name__)


class DatabaseService:
    """High-level service for database operations (Facade pattern).

    This class provides a simplified interface to database operations,
    coordinating between adapters, validators, and other components.

    Example:
        service = DatabaseService(adapter_registry)
        result = await service.execute_query(
            DatabaseType.POSTGRESQL,
            "mydb",
            "postgresql://...",
            "SELECT * FROM users"
        )
    """

    def __init__(self, registry: DatabaseAdapterRegistry):
        """Initialize service with adapter registry.

        Args:
            registry: Database adapter registry
        """
        self.registry = registry
        logger.info("Initialized DatabaseService")

    async def test_connection(
        self, db_type: DatabaseType, url: str
    ) -> Tuple[bool, Optional[str]]:
        """Test database connection.

        Args:
            db_type: Database type
            url: Connection URL

        Returns:
            Tuple of (success, error_message)

        Example:
            success, error = await service.test_connection(
                DatabaseType.POSTGRESQL,
                "postgresql://localhost/test"
            )
        """
        config = ConnectionConfig(url=url, name="test")
        adapter = self.registry.get_adapter(db_type, config)
        return await adapter.test_connection()

    async def execute_query(
        self,
        db_type: DatabaseType,
        name: str,
        url: str,
        sql: str,
        limit: int = 1000,
    ) -> Tuple[QueryResult, int]:
        """Execute SQL query.

        Args:
            db_type: Database type
            name: Connection name
            url: Connection URL
            sql: SQL query (will be validated)
            limit: Maximum rows to return

        Returns:
            Tuple of (QueryResult, execution_time_ms)

        Raises:
            SqlValidationError: If SQL is invalid
            Exception: If query execution fails

        Example:
            result, time_ms = await service.execute_query(
                DatabaseType.MYSQL,
                "mydb",
                "mysql://...",
                "SELECT * FROM users"
            )
        """
        # Validate SQL
        validated_sql = validate_and_transform_sql(sql, limit=limit, db_type=db_type)

        # Get adapter
        config = ConnectionConfig(url=url, name=name)
        adapter = self.registry.get_adapter(db_type, config)

        # Execute query with timing
        start_time = time.time()
        try:
            result = await adapter.execute_query(validated_sql)
            execution_time_ms = int((time.time() - start_time) * 1000)

            logger.info(
                f"Query executed successfully on {name}: "
                f"{result.row_count} rows in {execution_time_ms}ms"
            )

            return result, execution_time_ms

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Query failed on {name} after {execution_time_ms}ms: {e}")
            raise

    async def extract_metadata(
        self,
        db_type: DatabaseType,
        name: str,
        url: str,
    ) -> MetadataResult:
        """Extract database metadata.

        Args:
            db_type: Database type
            name: Connection name
            url: Connection URL

        Returns:
            MetadataResult

        Example:
            metadata = await service.extract_metadata(
                DatabaseType.POSTGRESQL,
                "mydb",
                "postgresql://..."
            )
        """
        config = ConnectionConfig(url=url, name=name)
        adapter = self.registry.get_adapter(db_type, config)

        logger.info(f"Extracting metadata for {name}")
        metadata = await adapter.extract_metadata()
        logger.info(
            f"Extracted metadata for {name}: "
            f"{len(metadata.tables)} tables, {len(metadata.views)} views"
        )

        return metadata

    async def close_connection(
        self,
        db_type: DatabaseType,
        name: str,
    ) -> None:
        """Close database connection.

        Args:
            db_type: Database type
            name: Connection name
        """
        await self.registry.close_adapter(db_type, name)
        logger.info(f"Closed connection for {name}")


# Global service instance
database_service = DatabaseService(adapter_registry)
```

**Validation**:
```bash
pytest tests/services/test_database_service.py -v
```

### Phase 3: Update API Layer (Week 3)

#### Task 3.1: Update Query API

**File**: `app/api/v1/queries.py` (modified)

```python
"""Query execution API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.models.database import DatabaseConnection
from app.models.query import QuerySource
from app.models.schemas import QueryInput, QueryResult as QueryResultSchema
from app.services.database_service import database_service
from app.services.sql_validator import SqlValidationError
from app.services.query_history import save_query_history

router = APIRouter(prefix="/api/v1/dbs", tags=["queries"])


@router.post("/{name}/query", response_model=QueryResultSchema)
async def execute_sql_query(
    name: str,
    input_data: QueryInput,
    session: Session = Depends(get_session),
) -> QueryResultSchema:
    """Execute SQL query against a database."""
    # Get connection
    statement = select(DatabaseConnection).where(DatabaseConnection.name == name)
    connection = session.exec(statement).first()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database connection '{name}' not found",
        )

    # Execute query using new service
    try:
        result, execution_time_ms = await database_service.execute_query(
            db_type=connection.db_type,
            name=name,
            url=connection.url,
            sql=input_data.sql,
        )

        # Save successful query to history
        await save_query_history(
            session=session,
            database_name=name,
            sql=input_data.sql,
            row_count=result.row_count,
            execution_time_ms=execution_time_ms,
            success=True,
            error_message=None,
            query_source=QuerySource.MANUAL,
        )

        # Convert to API schema
        return QueryResultSchema(
            columns=result.columns,
            rows=result.rows,
            rowCount=result.row_count,
            executionTimeMs=execution_time_ms,
            sql=input_data.sql,
        )

    except SqlValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query execution failed: {str(e)}",
        )
```

#### Task 3.2: Update Database API

**File**: `app/api/v1/databases.py` (modified)

Update to use `database_service` instead of `connection_factory`.

### Phase 4: Testing (Week 4)

#### Task 4.1: Unit Tests

Create tests for each adapter:

```python
# tests/adapters/test_postgresql.py

import pytest
from app.adapters.postgresql import PostgreSQLAdapter
from app.adapters.base import ConnectionConfig

@pytest.mark.asyncio
async def test_postgresql_adapter_connection():
    config = ConnectionConfig(
        url="postgresql://localhost/test",
        name="test"
    )
    adapter = PostgreSQLAdapter(config)

    success, error = await adapter.test_connection()
    assert success is True or isinstance(error, str)

@pytest.mark.asyncio
async def test_postgresql_adapter_query():
    # ... implementation
    pass
```

#### Task 4.2: Integration Tests

```python
# tests/integration/test_database_service.py

@pytest.mark.asyncio
async def test_service_with_postgres():
    from app.services.database_service import database_service
    from app.models.database import DatabaseType

    result, time_ms = await database_service.execute_query(
        DatabaseType.POSTGRESQL,
        "test",
        "postgresql://localhost/test",
        "SELECT 1 as num"
    )

    assert result.row_count == 1
    assert time_ms > 0
```

#### Task 4.3: Contract Tests

Ensure all adapters implement the contract:

```python
# tests/adapters/test_adapter_contract.py

import pytest
from app.adapters.postgresql import PostgreSQLAdapter
from app.adapters.mysql import MySQLAdapter
from app.adapters.base import DatabaseAdapter

@pytest.mark.parametrize("adapter_class", [
    PostgreSQLAdapter,
    MySQLAdapter,
])
def test_adapter_implements_contract(adapter_class):
    """Verify all adapters implement DatabaseAdapter contract."""
    assert issubclass(adapter_class, DatabaseAdapter)

    # Check all methods exist
    required_methods = [
        'test_connection',
        'get_connection_pool',
        'close_connection_pool',
        'extract_metadata',
        'execute_query',
        'get_dialect_name',
        'get_identifier_quote_char',
    ]

    for method in required_methods:
        assert hasattr(adapter_class, method)
```

### Phase 5: Cleanup and Documentation (Week 5)

#### Task 5.1: Remove Old Code

Once all tests pass:

1. Delete old service files:
```bash
rm app/services/connection_factory.py
rm app/services/db_connection.py
rm app/services/mysql_connection.py
rm app/services/mysql_metadata.py
rm app/services/mysql_query.py
```

2. Update imports throughout codebase

#### Task 5.2: Update Documentation

Update:
- README.md
- API documentation
- Create ADAPTER_DEVELOPMENT_GUIDE.md

## Rollback Strategy

If issues arise during implementation:

1. **Phase 1-2**: Simply delete `app/adapters/` directory
2. **Phase 3**: Revert API changes (git revert)
3. **Phase 4**: No rollback needed (tests don't affect production)
4. **Phase 5**: Restore deleted files from git

## Monitoring During Rollout

Monitor these metrics:
- Response times (should not increase)
- Error rates (should not increase)
- Connection pool utilization
- Memory usage (should decrease slightly due to less duplication)

## Success Criteria

- All existing tests pass
- New adapter tests have 90%+ coverage
- API response times within 5% of baseline
- No increase in error rates
- Documentation updated

## Timeline

- Week 1: Adapter infrastructure
- Week 2: Service layer
- Week 3: API updates
- Week 4: Testing
- Week 5: Cleanup and documentation

**Total: 5 weeks for complete migration**
