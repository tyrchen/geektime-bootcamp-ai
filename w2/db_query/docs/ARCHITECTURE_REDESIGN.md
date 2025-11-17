# Database Query Backend - Architecture Redesign

## Executive Summary

This document presents a comprehensive architecture redesign for the database query backend to follow SOLID principles, particularly the Open-Closed Principle (OCP). The proposed architecture uses abstract base classes, factory pattern, and dependency injection to make the system extensible for adding new database types without modifying existing code.

## Current Architecture Analysis

### 1. Current Structure

The current implementation supports PostgreSQL and MySQL through:

```
app/
├── services/
│   ├── connection_factory.py      # Routes based on db_type
│   ├── db_connection.py            # PostgreSQL connection pool
│   ├── mysql_connection.py         # MySQL connection pool
│   ├── metadata.py                 # Routes metadata extraction
│   ├── mysql_metadata.py           # MySQL metadata extraction
│   ├── query.py                    # Routes query execution
│   ├── mysql_query.py              # MySQL query execution
│   ├── nl2sql.py                   # NL to SQL conversion
│   └── sql_validator.py            # SQL validation
```

### 2. Identified Problems

#### 2.1 Violation of Open-Closed Principle

**Problem**: Adding a new database requires modifying existing code in multiple places.

**Current Code Example** (`connection_factory.py`):
```python
async def test_connection(db_type: DatabaseType, url: str) -> tuple[bool, str | None]:
    if db_type == DatabaseType.POSTGRESQL:
        return await pg_connection.test_connection(url)
    elif db_type == DatabaseType.MYSQL:
        return await mysql_connection.test_connection(url)
    else:
        return False, f"Unsupported database type: {db_type}"
```

**Impact**: To add Oracle/SQLite/MongoDB support, you must:
1. Modify `connection_factory.py` (add new if-elif branch)
2. Modify `metadata.py` (add new if-elif branch)
3. Modify `query.py` (add new if-elif branch)
4. Modify `DatabaseType` enum
5. Risk breaking existing functionality

#### 2.2 Code Duplication

**Problem**: Each database has separate but structurally identical modules:
- `db_connection.py` vs `mysql_connection.py` (99% identical structure)
- PostgreSQL metadata extraction in `metadata.py` vs MySQL in `mysql_metadata.py`

**Example**:
```python
# db_connection.py
_connection_pools: Dict[str, asyncpg.Pool] = {}

async def get_connection_pool(name: str, url: str, min_size: int = 1, max_size: int = 5):
    if name not in _connection_pools:
        pool = await asyncpg.create_pool(url, min_size=min_size, max_size=max_size)
        _connection_pools[name] = pool
    return _connection_pools[name]

# mysql_connection.py - IDENTICAL LOGIC, different driver
_connection_pools: Dict[str, aiomysql.Pool] = {}

async def get_connection_pool(name: str, url: str, min_size: int = 1, max_size: int = 5):
    if name not in _connection_pools:
        # Parse MySQL URL... (extra complexity)
        pool = await aiomysql.create_pool(host=host, port=port, ...)
        _connection_pools[name] = pool
    return _connection_pools[name]
```

#### 2.3 Tight Coupling

**Problem**: Services directly import specific database modules:
```python
# query.py
from app.services import db_connection as pg_connection
from app.services import mysql_query
```

This creates tight coupling and prevents dependency injection.

#### 2.4 No Interface Abstraction

**Problem**: No defined contracts (interfaces) for database operations.
- Each database implements functions independently
- No guarantee of consistent behavior
- Difficult to test with mocks

#### 2.5 Global State Management

**Problem**: Connection pools managed in global dictionaries:
```python
_connection_pools: Dict[str, asyncpg.Pool] = {}
```

Issues:
- Hard to test
- No lifecycle management
- Difficult to mock
- Not thread-safe in some edge cases

---

## Proposed Architecture

### 1. Design Principles

The redesign follows these principles:

1. **Single Responsibility Principle (SRP)**: Each class has one reason to change
2. **Open-Closed Principle (OCP)**: Open for extension, closed for modification
3. **Liskov Substitution Principle (LSP)**: Database adapters are interchangeable
4. **Interface Segregation Principle (ISP)**: Small, focused interfaces
5. **Dependency Inversion Principle (DIP)**: Depend on abstractions, not concrete implementations

### 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     API Layer (FastAPI)                      │
│                  (databases.py, queries.py)                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Dependency Injection
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Service Layer (Facade)                     │
│              DatabaseService (coordinates operations)        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Uses
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Database Adapter Registry                   │
│         (Factory pattern - returns appropriate adapter)      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Returns
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Abstract Base Class (Protocol/ABC)              │
│                    DatabaseAdapter                           │
│   ┌───────────────────────────────────────────────────────┐ │
│   │ - test_connection()                                   │ │
│   │ - get_connection_pool()                               │ │
│   │ - close_connection_pool()                             │ │
│   │ - extract_metadata()                                  │ │
│   │ - execute_query()                                     │ │
│   │ - get_dialect_name()                                  │ │
│   └───────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┬──────────────┐
         │               │               │              │
         ▼               ▼               ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────┐ ┌──────────┐
│ PostgreSQL   │ │    MySQL     │ │  Oracle  │ │  SQLite  │
│   Adapter    │ │   Adapter    │ │  Adapter │ │  Adapter │
└──────────────┘ └──────────────┘ └──────────┘ └──────────┘
```

### 3. Core Components

#### 3.1 Abstract Base Class: `DatabaseAdapter`

Defines the contract all database adapters must implement:

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

@dataclass
class ConnectionConfig:
    """Configuration for database connection."""
    url: str
    name: str
    min_pool_size: int = 1
    max_pool_size: int = 5
    command_timeout: int = 60

@dataclass
class QueryResult:
    """Standardized query result."""
    columns: List[Dict[str, str]]
    rows: List[Dict[str, Any]]
    row_count: int

@dataclass
class MetadataResult:
    """Standardized metadata result."""
    tables: List[Dict[str, Any]]
    views: List[Dict[str, Any]]


class DatabaseAdapter(ABC):
    """Abstract base class for database adapters.

    All database implementations must inherit from this class and
    implement all abstract methods. This ensures consistent behavior
    across different database types.
    """

    def __init__(self, config: ConnectionConfig):
        """Initialize adapter with connection configuration."""
        self.config = config
        self._pool = None

    @abstractmethod
    async def test_connection(self) -> Tuple[bool, str | None]:
        """Test database connection.

        Returns:
            Tuple of (success, error_message)
        """
        pass

    @abstractmethod
    async def get_connection_pool(self):
        """Get or create connection pool.

        Returns:
            Database-specific connection pool object
        """
        pass

    @abstractmethod
    async def close_connection_pool(self) -> None:
        """Close connection pool and cleanup resources."""
        pass

    @abstractmethod
    async def extract_metadata(self) -> MetadataResult:
        """Extract database metadata (tables, columns, etc.).

        Returns:
            MetadataResult with tables and views
        """
        pass

    @abstractmethod
    async def execute_query(self, sql: str) -> QueryResult:
        """Execute SQL query.

        Args:
            sql: SQL query string (already validated)

        Returns:
            QueryResult with columns and rows
        """
        pass

    @abstractmethod
    def get_dialect_name(self) -> str:
        """Get SQL dialect name for this database (for sqlglot).

        Returns:
            Dialect name (e.g., 'postgres', 'mysql', 'oracle')
        """
        pass

    @abstractmethod
    def get_identifier_quote_char(self) -> str:
        """Get character used for quoting identifiers.

        Returns:
            Quote character (e.g., '"' for PostgreSQL, '`' for MySQL)
        """
        pass
```

#### 3.2 Concrete Implementations

##### PostgreSQL Adapter

```python
from typing import Tuple
import asyncpg
from app.adapters.base import DatabaseAdapter, ConnectionConfig, QueryResult, MetadataResult

class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL database adapter."""

    async def test_connection(self) -> Tuple[bool, str | None]:
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
        """Extract PostgreSQL metadata."""
        pool = await self.get_connection_pool()

        async with pool.acquire() as conn:
            # Query pg_catalog for tables and views
            tables_query = """
                SELECT schemaname, tablename, 'table' AS type
                FROM pg_tables
                WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                UNION ALL
                SELECT schemaname, viewname AS tablename, 'view' AS type
                FROM pg_views
                WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                ORDER BY schemaname, tablename
            """
            tables_rows = await conn.fetch(tables_query)

            # Process tables and views...
            # (Implementation similar to current extract_postgres_metadata)

            return MetadataResult(tables=tables, views=views)

    async def execute_query(self, sql: str) -> QueryResult:
        """Execute query against PostgreSQL."""
        pool = await self.get_connection_pool()

        async with pool.acquire() as conn:
            rows = await conn.fetch(sql)

            # Convert to standard format
            columns = []
            result_rows = []

            if rows:
                first_row = rows[0]
                for key, value in first_row.items():
                    data_type = self._infer_type(value)
                    columns.append({"name": key, "dataType": data_type})

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
    def _infer_type(value) -> str:
        """Infer PostgreSQL type from Python value."""
        if value is None:
            return "unknown"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "double precision"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, str):
            return "character varying"
        elif isinstance(value, datetime):
            return "timestamp"
        else:
            return str(type(value).__name__)
```

##### MySQL Adapter

```python
from typing import Tuple
import aiomysql
from urllib.parse import urlparse
from app.adapters.base import DatabaseAdapter, ConnectionConfig, QueryResult, MetadataResult

class MySQLAdapter(DatabaseAdapter):
    """MySQL database adapter."""

    def _parse_url(self, url: str) -> dict:
        """Parse MySQL connection URL."""
        parsed = urlparse(url)
        return {
            'host': parsed.hostname or 'localhost',
            'port': parsed.port or 3306,
            'user': parsed.username or 'root',
            'password': parsed.password or '',
            'db': parsed.path.lstrip('/') if parsed.path else None,
        }

    async def test_connection(self) -> Tuple[bool, str | None]:
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

    async def extract_metadata(self) -> MetadataResult:
        """Extract MySQL metadata."""
        pool = await self.get_connection_pool()

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                # Query INFORMATION_SCHEMA
                # (Implementation similar to current mysql_metadata.extract_metadata)

                return MetadataResult(tables=tables, views=views)

    async def execute_query(self, sql: str) -> QueryResult:
        """Execute query against MySQL."""
        pool = await self.get_connection_pool()

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql)
                rows = await cursor.fetchall()

                # Build columns from cursor description
                columns = []
                if cursor.description:
                    for desc in cursor.description:
                        columns.append({
                            "name": desc[0],
                            "dataType": self._map_mysql_type(desc[1])
                        })

                # Process rows
                result_rows = []
                for row in rows:
                    processed_row = {}
                    for key, value in row.items():
                        if isinstance(value, datetime):
                            processed_row[key] = value.isoformat()
                        else:
                            processed_row[key] = value
                    result_rows.append(processed_row)

                return QueryResult(
                    columns=columns,
                    rows=result_rows,
                    row_count=len(result_rows)
                )

    def get_dialect_name(self) -> str:
        """Get MySQL dialect name."""
        return "mysql"

    def get_identifier_quote_char(self) -> str:
        """MySQL uses backticks."""
        return "`"

    @staticmethod
    def _map_mysql_type(type_code: int) -> str:
        """Map MySQL type codes to names."""
        # Implementation from current mysql_query.py
        type_map = {
            0: "DECIMAL", 1: "TINY", 2: "SHORT", 3: "LONG",
            # ... full mapping
        }
        return type_map.get(type_code, f"UNKNOWN({type_code})")
```

#### 3.3 Adapter Registry (Factory Pattern)

```python
from typing import Dict, Type
from app.models.database import DatabaseType
from app.adapters.base import DatabaseAdapter, ConnectionConfig
from app.adapters.postgresql import PostgreSQLAdapter
from app.adapters.mysql import MySQLAdapter

class DatabaseAdapterRegistry:
    """Registry for database adapters (Factory pattern).

    This class maintains a mapping of database types to adapter classes.
    New database types can be registered without modifying existing code.
    """

    def __init__(self):
        self._adapters: Dict[DatabaseType, Type[DatabaseAdapter]] = {}
        self._instances: Dict[str, DatabaseAdapter] = {}

        # Register built-in adapters
        self.register(DatabaseType.POSTGRESQL, PostgreSQLAdapter)
        self.register(DatabaseType.MYSQL, MySQLAdapter)

    def register(self, db_type: DatabaseType, adapter_class: Type[DatabaseAdapter]) -> None:
        """Register a database adapter.

        Args:
            db_type: Database type enum value
            adapter_class: Adapter class (must inherit from DatabaseAdapter)

        Raises:
            TypeError: If adapter_class doesn't inherit from DatabaseAdapter
        """
        if not issubclass(adapter_class, DatabaseAdapter):
            raise TypeError(f"{adapter_class} must inherit from DatabaseAdapter")

        self._adapters[db_type] = adapter_class

    def get_adapter(self, db_type: DatabaseType, config: ConnectionConfig) -> DatabaseAdapter:
        """Get or create database adapter instance.

        Args:
            db_type: Database type
            config: Connection configuration

        Returns:
            DatabaseAdapter instance

        Raises:
            ValueError: If database type is not registered
        """
        if db_type not in self._adapters:
            raise ValueError(f"Unsupported database type: {db_type}. "
                           f"Available types: {list(self._adapters.keys())}")

        # Use connection name as cache key
        cache_key = f"{db_type.value}:{config.name}"

        if cache_key not in self._instances:
            adapter_class = self._adapters[db_type]
            self._instances[cache_key] = adapter_class(config)

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

    async def close_all_adapters(self) -> None:
        """Close all adapter instances."""
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

#### 3.4 Service Layer (Facade)

```python
from sqlmodel import Session
from app.models.database import DatabaseType
from app.adapters.base import ConnectionConfig
from app.adapters.registry import adapter_registry

class DatabaseService:
    """High-level service for database operations (Facade pattern).

    This class provides a simplified interface to database operations,
    coordinating between adapters, validators, and other components.
    """

    def __init__(self, registry: DatabaseAdapterRegistry):
        """Initialize service with adapter registry."""
        self.registry = registry

    async def test_connection(
        self,
        db_type: DatabaseType,
        url: str
    ) -> Tuple[bool, str | None]:
        """Test database connection.

        Args:
            db_type: Database type
            url: Connection URL

        Returns:
            Tuple of (success, error_message)
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
    ) -> QueryResult:
        """Execute SQL query.

        Args:
            db_type: Database type
            name: Connection name
            url: Connection URL
            sql: SQL query (will be validated)

        Returns:
            QueryResult

        Raises:
            SqlValidationError: If SQL is invalid
        """
        # Get adapter
        config = ConnectionConfig(url=url, name=name)
        adapter = self.registry.get_adapter(db_type, config)

        # Validate SQL using adapter's dialect
        from app.services.sql_validator import validate_and_transform_sql
        validated_sql = validate_and_transform_sql(
            sql,
            limit=1000,
            db_type=db_type
        )

        # Execute query
        result = await adapter.execute_query(validated_sql)
        return result

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
        """
        config = ConnectionConfig(url=url, name=name)
        adapter = self.registry.get_adapter(db_type, config)
        return await adapter.extract_metadata()

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


# Global service instance
database_service = DatabaseService(adapter_registry)
```

#### 3.5 Dependency Injection in API Layer

```python
# app/api/v1/queries.py (updated)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.database import get_session
from app.services.database_service import database_service
from app.models.schemas import QueryInput, QueryResult

router = APIRouter(prefix="/api/v1/dbs", tags=["queries"])

@router.post("/{name}/query", response_model=QueryResult)
async def execute_sql_query(
    name: str,
    input_data: QueryInput,
    session: Session = Depends(get_session),
) -> QueryResult:
    """Execute SQL query against a database."""
    # Get connection from database
    statement = select(DatabaseConnection).where(DatabaseConnection.name == name)
    connection = session.exec(statement).first()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database connection '{name}' not found",
        )

    # Execute query using service
    try:
        result = await database_service.execute_query(
            db_type=connection.db_type,
            name=name,
            url=connection.url,
            sql=input_data.sql,
        )

        # Save to history
        await save_query_history(session, name, result, success=True)

        return result
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

---

## New Directory Structure

```
app/
├── adapters/                      # NEW: Database adapters
│   ├── __init__.py
│   ├── base.py                   # Abstract base class + data classes
│   ├── registry.py               # Adapter registry (factory)
│   ├── postgresql.py             # PostgreSQL adapter
│   ├── mysql.py                  # MySQL adapter
│   └── README.md                 # Guide for adding new adapters
│
├── services/
│   ├── __init__.py
│   ├── database_service.py       # NEW: High-level service (facade)
│   ├── sql_validator.py          # SQL validation (unchanged)
│   ├── nl2sql.py                 # NL to SQL (unchanged)
│   └── query_history.py          # NEW: Extracted from query.py
│
├── api/
│   └── v1/
│       ├── databases.py          # UPDATED: Use database_service
│       └── queries.py            # UPDATED: Use database_service
│
├── models/
│   ├── database.py               # Database models
│   ├── schemas.py                # API schemas
│   └── ...
│
└── utils/
    ├── db_parser.py              # URL parsing utilities
    └── ...

# REMOVED (functionality moved to adapters):
# - services/connection_factory.py
# - services/db_connection.py
# - services/mysql_connection.py
# - services/mysql_metadata.py
# - services/mysql_query.py
# - services/metadata.py (most logic moved to adapters)
```

---

## How to Add a New Database

### Example: Adding Oracle Support

#### Step 1: Add Database Type to Enum

```python
# app/models/database.py

class DatabaseType(str, Enum):
    """Database type."""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    ORACLE = "oracle"  # NEW
```

#### Step 2: Create Oracle Adapter

```python
# app/adapters/oracle.py

from typing import Tuple
import cx_Oracle_async
from app.adapters.base import DatabaseAdapter, ConnectionConfig, QueryResult, MetadataResult

class OracleAdapter(DatabaseAdapter):
    """Oracle database adapter."""

    async def test_connection(self) -> Tuple[bool, str | None]:
        """Test Oracle connection."""
        try:
            # Parse Oracle connection string
            dsn = cx_Oracle_async.makedsn(...)
            conn = await cx_Oracle_async.connect(dsn=dsn)
            await conn.close()
            return True, None
        except Exception as e:
            return False, str(e)

    async def get_connection_pool(self):
        """Get or create Oracle connection pool."""
        if self._pool is None:
            self._pool = await cx_Oracle_async.create_pool(
                user=...,
                password=...,
                dsn=...,
                min=self.config.min_pool_size,
                max=self.config.max_pool_size,
            )
        return self._pool

    async def close_connection_pool(self) -> None:
        """Close Oracle connection pool."""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def extract_metadata(self) -> MetadataResult:
        """Extract Oracle metadata from USER_TABLES, USER_VIEWS."""
        pool = await self.get_connection_pool()

        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Query Oracle data dictionary
                await cursor.execute("""
                    SELECT table_name, 'table' as type
                    FROM user_tables
                    UNION ALL
                    SELECT view_name as table_name, 'view' as type
                    FROM user_views
                    ORDER BY table_name
                """)

                # ... process results

                return MetadataResult(tables=tables, views=views)

    async def execute_query(self, sql: str) -> QueryResult:
        """Execute query against Oracle."""
        pool = await self.get_connection_pool()

        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(sql)
                rows = await cursor.fetchall()

                # Build columns from description
                columns = [
                    {"name": desc[0], "dataType": self._map_oracle_type(desc[1])}
                    for desc in cursor.description
                ]

                # Convert rows to list of dicts
                result_rows = [
                    {desc[0]: value for desc, value in zip(cursor.description, row)}
                    for row in rows
                ]

                return QueryResult(
                    columns=columns,
                    rows=result_rows,
                    row_count=len(result_rows)
                )

    def get_dialect_name(self) -> str:
        """Get Oracle dialect name."""
        return "oracle"

    def get_identifier_quote_char(self) -> str:
        """Oracle uses double quotes."""
        return '"'

    @staticmethod
    def _map_oracle_type(type_code) -> str:
        """Map Oracle type codes to names."""
        # Implementation specific to cx_Oracle
        return "VARCHAR2"  # Example
```

#### Step 3: Register Oracle Adapter

```python
# app/adapters/registry.py (updated)

from app.adapters.oracle import OracleAdapter  # NEW

class DatabaseAdapterRegistry:
    def __init__(self):
        self._adapters: Dict[DatabaseType, Type[DatabaseAdapter]] = {}
        self._instances: Dict[str, DatabaseAdapter] = {}

        # Register built-in adapters
        self.register(DatabaseType.POSTGRESQL, PostgreSQLAdapter)
        self.register(DatabaseType.MYSQL, MySQLAdapter)
        self.register(DatabaseType.ORACLE, OracleAdapter)  # NEW
```

#### Step 4: Update URL Parser (Optional)

```python
# app/utils/db_parser.py

def detect_database_type(url: str) -> DatabaseType:
    """Detect database type from URL scheme."""
    url_lower = url.lower()

    if url_lower.startswith(("postgresql://", "postgres://")):
        return DatabaseType.POSTGRESQL
    elif url_lower.startswith(("mysql://", "mysql+aiomysql://")):
        return DatabaseType.MYSQL
    elif url_lower.startswith(("oracle://", "oracle+cx://")):  # NEW
        return DatabaseType.ORACLE
    else:
        raise ValueError(f"Unknown database type in URL: {url}")
```

#### Step 5: That's It!

**No other code changes required:**
- API endpoints automatically work with Oracle
- SQL validation uses "oracle" dialect
- NL2SQL generates Oracle-specific SQL
- Query history tracks Oracle queries
- Metadata extraction works automatically

---

## Migration Path from Current Code

### Phase 1: Create New Structure (Non-Breaking)

1. Create `app/adapters/` directory
2. Implement `base.py`, `registry.py`
3. Implement `postgresql.py`, `mysql.py` adapters
4. Create `database_service.py`
5. Add comprehensive tests

**At this point, old code still works**

### Phase 2: Update API Layer

1. Update `queries.py` to use `database_service`
2. Update `databases.py` to use `database_service`
3. Test thoroughly

**Old services still exist but are no longer used**

### Phase 3: Cleanup

1. Remove old service files:
   - `connection_factory.py`
   - `db_connection.py`
   - `mysql_connection.py`
   - `mysql_metadata.py`
   - `mysql_query.py`
   - Most of `metadata.py` (keep caching logic)

2. Update imports
3. Remove dead code

### Phase 4: Documentation

1. Update README.md
2. Create adapter development guide
3. Update API documentation

---

## Benefits of New Architecture

### 1. Open-Closed Principle Compliance

**Adding SQLite support:**

```python
# app/adapters/sqlite.py
class SQLiteAdapter(DatabaseAdapter):
    # Implement abstract methods
    pass

# app/adapters/registry.py
adapter_registry.register(DatabaseType.SQLITE, SQLiteAdapter)
```

**No modifications to existing code required!**

### 2. Easy Testing

**Mock adapter for testing:**

```python
class MockAdapter(DatabaseAdapter):
    def __init__(self, config):
        super().__init__(config)
        self.test_data = {"tables": [], "views": []}

    async def execute_query(self, sql: str) -> QueryResult:
        return QueryResult(columns=[], rows=[], row_count=0)

    # ... implement other methods

# In tests
adapter_registry.register(DatabaseType.TEST, MockAdapter)
```

### 3. Clear Contracts

All adapters must implement:
- `test_connection()`
- `get_connection_pool()`
- `close_connection_pool()`
- `extract_metadata()`
- `execute_query()`
- `get_dialect_name()`
- `get_identifier_quote_char()`

**No ambiguity about what needs to be implemented**

### 4. Single Responsibility

- **Adapters**: Database-specific operations
- **Registry**: Adapter lifecycle management
- **Service**: Coordination and orchestration
- **API**: HTTP request/response handling
- **Validators**: SQL validation
- **NL2SQL**: Natural language processing

### 5. Dependency Injection

```python
# Can swap implementations easily
test_service = DatabaseService(test_registry)
prod_service = DatabaseService(prod_registry)
```

### 6. Better Error Messages

```python
# Before
ValueError: Unsupported database type: oracle

# After
ValueError: Unsupported database type: oracle.
Available types: [DatabaseType.POSTGRESQL, DatabaseType.MYSQL]
Did you forget to register the adapter?
```

---

## Advanced Features (Future Enhancements)

### 1. Plugin System

```python
# External plugin
# my_plugin/adapters/mongodb.py

class MongoDBAdapter(DatabaseAdapter):
    # Implementation
    pass

# Register at runtime
from my_plugin.adapters.mongodb import MongoDBAdapter
adapter_registry.register(DatabaseType.MONGODB, MongoDBAdapter)
```

### 2. Adapter Capabilities

```python
class DatabaseAdapter(ABC):
    @property
    def capabilities(self) -> Set[str]:
        """Return set of supported capabilities."""
        return {"query", "metadata", "transactions"}

    def supports(self, capability: str) -> bool:
        """Check if adapter supports a capability."""
        return capability in self.capabilities

# Usage
if adapter.supports("transactions"):
    await adapter.begin_transaction()
```

### 3. Connection Pooling Strategy

```python
class PoolingStrategy(ABC):
    @abstractmethod
    async def get_connection(self, pool):
        pass

class SimplePooling(PoolingStrategy):
    async def get_connection(self, pool):
        return await pool.acquire()

class LoadBalancedPooling(PoolingStrategy):
    async def get_connection(self, pool):
        # Implement load balancing
        pass
```

### 4. Metrics and Monitoring

```python
class InstrumentedAdapter(DatabaseAdapter):
    """Adapter wrapper that adds metrics."""

    def __init__(self, adapter: DatabaseAdapter):
        self._adapter = adapter
        self._metrics = MetricsCollector()

    async def execute_query(self, sql: str) -> QueryResult:
        start = time.time()
        try:
            result = await self._adapter.execute_query(sql)
            self._metrics.record_success(time.time() - start)
            return result
        except Exception as e:
            self._metrics.record_failure(time.time() - start)
            raise
```

---

## Testing Strategy

### 1. Unit Tests

```python
# tests/adapters/test_postgresql.py

@pytest.mark.asyncio
async def test_postgresql_adapter_query():
    config = ConnectionConfig(
        url="postgresql://localhost/test",
        name="test"
    )
    adapter = PostgreSQLAdapter(config)

    result = await adapter.execute_query("SELECT 1 as num")

    assert result.row_count == 1
    assert result.columns == [{"name": "num", "dataType": "integer"}]
    assert result.rows == [{"num": 1}]
```

### 2. Integration Tests

```python
# tests/integration/test_database_service.py

@pytest.mark.asyncio
async def test_service_with_multiple_databases():
    service = DatabaseService(adapter_registry)

    # Test PostgreSQL
    pg_result = await service.execute_query(
        DatabaseType.POSTGRESQL,
        "test_pg",
        "postgresql://localhost/test",
        "SELECT 1"
    )

    # Test MySQL
    mysql_result = await service.execute_query(
        DatabaseType.MYSQL,
        "test_mysql",
        "mysql://localhost/test",
        "SELECT 1"
    )

    assert pg_result.row_count == 1
    assert mysql_result.row_count == 1
```

### 3. Contract Tests

```python
# tests/adapters/test_adapter_contract.py

@pytest.mark.parametrize("adapter_class", [
    PostgreSQLAdapter,
    MySQLAdapter,
    OracleAdapter,
])
@pytest.mark.asyncio
async def test_adapter_implements_contract(adapter_class):
    """Verify all adapters implement the required contract."""

    # Check all abstract methods are implemented
    assert hasattr(adapter_class, 'test_connection')
    assert hasattr(adapter_class, 'get_connection_pool')
    assert hasattr(adapter_class, 'close_connection_pool')
    assert hasattr(adapter_class, 'extract_metadata')
    assert hasattr(adapter_class, 'execute_query')
    assert hasattr(adapter_class, 'get_dialect_name')
    assert hasattr(adapter_class, 'get_identifier_quote_char')

    # Check method signatures match
    # ... signature validation
```

---

## Performance Considerations

### 1. Connection Pool Reuse

The registry caches adapter instances by connection name, ensuring connection pools are reused:

```python
# First call: creates adapter and pool
adapter1 = registry.get_adapter(DatabaseType.POSTGRESQL, config)

# Second call with same name: returns cached adapter
adapter2 = registry.get_adapter(DatabaseType.POSTGRESQL, config)

assert adapter1 is adapter2  # Same instance
```

### 2. Lazy Initialization

Connection pools are created only when first needed:

```python
class DatabaseAdapter:
    async def get_connection_pool(self):
        if self._pool is None:
            self._pool = await self._create_pool()
        return self._pool
```

### 3. Metadata Caching

Metadata caching remains in the service layer (SQLite cache):

```python
class DatabaseService:
    async def extract_metadata(self, ...):
        # Check cache first
        cached = await get_cached_metadata(session, name)
        if cached and not cached.is_stale:
            return cached.to_metadata_result()

        # Fetch fresh metadata via adapter
        result = await adapter.extract_metadata()

        # Cache it
        await cache_metadata(session, name, result)

        return result
```

---

## Code Quality Improvements

### 1. Type Safety

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class DatabaseAdapter(Protocol):
    """Protocol for type checking (alternative to ABC)."""

    async def test_connection(self) -> Tuple[bool, str | None]: ...
    async def execute_query(self, sql: str) -> QueryResult: ...

# Type checker ensures all methods are implemented
def use_adapter(adapter: DatabaseAdapter):
    # Type-safe
    result = adapter.execute_query("SELECT 1")
```

### 2. Error Handling

```python
class DatabaseError(Exception):
    """Base exception for database operations."""
    pass

class ConnectionError(DatabaseError):
    """Connection-related errors."""
    pass

class QueryExecutionError(DatabaseError):
    """Query execution errors."""
    pass

class MetadataExtractionError(DatabaseError):
    """Metadata extraction errors."""
    pass

# In adapters
async def execute_query(self, sql: str) -> QueryResult:
    try:
        # ... execution
    except asyncpg.PostgresError as e:
        raise QueryExecutionError(f"PostgreSQL error: {e}") from e
```

### 3. Logging

```python
import logging

class DatabaseAdapter:
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self._pool = None
        self.logger = logging.getLogger(f"{self.__class__.__name__}:{config.name}")

    async def execute_query(self, sql: str) -> QueryResult:
        self.logger.info(f"Executing query: {sql[:100]}...")
        start = time.time()

        try:
            result = await self._do_execute(sql)
            self.logger.info(f"Query completed in {time.time() - start:.2f}s")
            return result
        except Exception as e:
            self.logger.error(f"Query failed: {e}")
            raise
```

---

## Comparison: Before vs After

### Adding a New Database Type

#### Before (Current Architecture)

1. Create `newdb_connection.py` (100 lines)
2. Create `newdb_metadata.py` (150 lines)
3. Create `newdb_query.py` (80 lines)
4. Modify `connection_factory.py` (add if-elif branch)
5. Modify `metadata.py` (add if-elif branch)
6. Modify `query.py` (add if-elif branch)
7. Modify `nl2sql.py` (add dialect rules)
8. Modify `sql_validator.py` (add dialect)
9. Update `DatabaseType` enum
10. Test all modified files

**Total: 330+ lines of new code, 6 files modified**

#### After (New Architecture)

1. Create `newdb.py` adapter (200 lines implementing DatabaseAdapter)
2. Register in `registry.py` (1 line)
3. Update `DatabaseType` enum (1 line)
4. Update `db_parser.py` detection (3 lines)

**Total: 200 lines of new code, 3 files modified (trivially)**

### Query Execution Flow

#### Before

```
API → query.py → connection_factory.py → if POSTGRESQL → db_connection.py
                                       → if MYSQL → mysql_connection.py
                                       → if ORACLE → Error!
```

#### After

```
API → database_service.py → adapter_registry.get_adapter() → OracleAdapter
                                                            → PostgreSQLAdapter
                                                            → MySQLAdapter
                                                            → Any registered adapter
```

---

## Conclusion

The proposed architecture redesign:

1. **Follows SOLID Principles**
   - Single Responsibility: Each class has one job
   - Open-Closed: Add databases without modifying existing code
   - Liskov Substitution: All adapters are interchangeable
   - Interface Segregation: Focused DatabaseAdapter interface
   - Dependency Inversion: Depend on abstractions (DatabaseAdapter)

2. **Improves Maintainability**
   - Clear contracts via abstract base class
   - Reduced code duplication
   - Centralized adapter management
   - Better error handling

3. **Enhances Extensibility**
   - Add new databases with 1 new file + 1 line registration
   - No modifications to existing code
   - Plugin system possible
   - Easy to add capabilities

4. **Better Testing**
   - Mock adapters for unit tests
   - Contract tests ensure compliance
   - Isolated components

5. **Production Ready**
   - Connection pool reuse
   - Lazy initialization
   - Proper resource cleanup
   - Comprehensive logging

The migration can be done incrementally without breaking existing functionality, making this a safe and practical path forward.
