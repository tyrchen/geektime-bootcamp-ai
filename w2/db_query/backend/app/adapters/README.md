# Database Adapter Development Guide

## Overview

This guide explains how to add support for new database types to the system. The adapter pattern makes it easy to extend the system without modifying existing code.

## Quick Start: Adding a New Database

### Step 1: Create Adapter File

Create a new file in `app/adapters/` for your database:

```
app/adapters/
├── base.py              # Abstract base class (DO NOT MODIFY)
├── postgresql.py        # PostgreSQL implementation (reference)
├── mysql.py             # MySQL implementation (reference)
└── your_database.py     # Your new adapter (CREATE THIS)
```

### Step 2: Implement DatabaseAdapter

```python
# app/adapters/your_database.py

from typing import Tuple, Optional
from app.adapters.base import DatabaseAdapter, ConnectionConfig, QueryResult, MetadataResult

class YourDatabaseAdapter(DatabaseAdapter):
    """Adapter for YourDatabase."""

    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test database connection."""
        try:
            # TODO: Implement connection test
            # Example: conn = await your_db_driver.connect(self.config.url)
            # await conn.close()
            return True, None
        except Exception as e:
            return False, str(e)

    async def get_connection_pool(self):
        """Get or create connection pool."""
        if self._pool is None:
            # TODO: Create connection pool
            # Example: self._pool = await your_db_driver.create_pool(...)
            pass
        return self._pool

    async def close_connection_pool(self) -> None:
        """Close connection pool."""
        if self._pool is not None:
            # TODO: Close pool
            # Example: await self._pool.close()
            self._pool = None

    async def extract_metadata(self) -> MetadataResult:
        """Extract database metadata."""
        # TODO: Query database catalog/schema
        # Return MetadataResult with tables and views
        tables = []
        views = []
        return MetadataResult(tables=tables, views=views)

    async def execute_query(self, sql: str) -> QueryResult:
        """Execute SQL query."""
        # TODO: Execute query and return results
        # Return QueryResult with columns, rows, row_count
        columns = []
        rows = []
        return QueryResult(columns=columns, rows=rows, row_count=len(rows))

    def get_dialect_name(self) -> str:
        """Get SQL dialect name for sqlglot."""
        # TODO: Return dialect name
        # Examples: 'postgres', 'mysql', 'oracle', 'sqlite'
        return "your_database"

    def get_identifier_quote_char(self) -> str:
        """Get identifier quote character."""
        # TODO: Return quote character
        # Examples: '"' (PostgreSQL), '`' (MySQL), '[' (SQL Server)
        return '"'
```

### Step 3: Register Adapter

Add your adapter to the registry:

```python
# app/adapters/registry.py

from app.adapters.your_database import YourDatabaseAdapter

class DatabaseAdapterRegistry:
    def __init__(self):
        # ... existing code ...

        # Register your adapter
        self.register(DatabaseType.YOUR_DATABASE, YourDatabaseAdapter)
```

### Step 4: Update Database Type Enum

```python
# app/models/database.py

class DatabaseType(str, Enum):
    """Database type."""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    YOUR_DATABASE = "your_database"  # Add this
```

### Step 5: Update URL Parser (Optional)

If your database uses a custom URL scheme:

```python
# app/utils/db_parser.py

def detect_database_type(url: str) -> DatabaseType:
    """Detect database type from URL scheme."""
    url_lower = url.lower()

    if url_lower.startswith(("your_db://", "your_database://")):
        return DatabaseType.YOUR_DATABASE
    # ... other databases ...
```

### Step 6: Test Your Adapter

```python
# tests/adapters/test_your_database.py

import pytest
from app.adapters.your_database import YourDatabaseAdapter
from app.adapters.base import ConnectionConfig

@pytest.mark.asyncio
async def test_connection():
    config = ConnectionConfig(
        url="your_database://localhost/test",
        name="test"
    )
    adapter = YourDatabaseAdapter(config)

    success, error = await adapter.test_connection()
    assert success or error is not None

@pytest.mark.asyncio
async def test_query_execution():
    # ... test query execution
    pass
```

## Detailed Implementation Guide

### Connection Management

#### Connection Pool Pattern

Your adapter should cache the connection pool in `self._pool`:

```python
async def get_connection_pool(self):
    if self._pool is None:
        # Create pool ONCE
        self._pool = await your_driver.create_pool(
            url=self.config.url,
            min_size=self.config.min_pool_size,
            max_size=self.config.max_pool_size,
        )
    return self._pool  # Return cached pool on subsequent calls
```

#### URL Parsing

If your database URL requires custom parsing:

```python
from urllib.parse import urlparse

def _parse_url(self, url: str) -> dict:
    """Parse database-specific URL format."""
    parsed = urlparse(url)
    return {
        'host': parsed.hostname or 'localhost',
        'port': parsed.port or 5432,  # default port
        'user': parsed.username,
        'password': parsed.password,
        'database': parsed.path.lstrip('/'),
    }
```

### Metadata Extraction

#### Tables and Views

Query your database's metadata catalog:

```python
async def extract_metadata(self) -> MetadataResult:
    pool = await self.get_connection_pool()

    async with pool.acquire() as conn:
        # Query for tables
        tables_query = """
            SELECT table_name, table_type
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """
        tables_rows = await conn.fetch(tables_query)

        tables = []
        views = []

        for row in tables_rows:
            table_name = row['table_name']
            table_type = 'table' if row['table_type'] == 'BASE TABLE' else 'view'

            # Get columns for this table
            columns = await self._get_columns(conn, table_name)

            # Get row count (for tables only)
            row_count = None
            if table_type == 'table':
                row_count = await self._get_row_count(conn, table_name)

            table_meta = {
                "name": table_name,
                "type": table_type,
                "schemaName": "public",
                "columns": columns,
            }
            if row_count is not None:
                table_meta["rowCount"] = row_count

            if table_type == 'table':
                tables.append(table_meta)
            else:
                views.append(table_meta)

        return MetadataResult(tables=tables, views=views)
```

#### Column Information

Extract column metadata:

```python
async def _get_columns(self, conn, table_name: str):
    """Get column metadata for a table."""
    columns_query = """
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns
        WHERE table_name = $1
        ORDER BY ordinal_position
    """
    columns_rows = await conn.fetch(columns_query, table_name)

    columns = []
    for col_row in columns_rows:
        data_type = col_row['data_type']
        if col_row['character_maximum_length']:
            data_type = f"{data_type}({col_row['character_maximum_length']})"

        columns.append({
            "name": col_row['column_name'],
            "dataType": data_type,
            "nullable": col_row['is_nullable'] == 'YES',
            "primaryKey": False,  # Determine from constraints
            "unique": False,      # Determine from constraints
            "defaultValue": col_row['column_default'],
        })

    return columns
```

### Query Execution

#### Execute and Format Results

```python
async def execute_query(self, sql: str) -> QueryResult:
    """Execute SQL query and return standardized results."""
    pool = await self.get_connection_pool()

    async with pool.acquire() as conn:
        # Execute query
        rows = await conn.fetch(sql)

        # Build columns from cursor metadata
        columns = []
        if rows:
            first_row = rows[0]
            for key, value in first_row.items():
                columns.append({
                    "name": key,
                    "dataType": self._infer_type(value)
                })

        # Convert rows to list of dicts
        result_rows = [dict(row) for row in rows]

        return QueryResult(
            columns=columns,
            rows=result_rows,
            row_count=len(result_rows)
        )
```

#### Type Inference

Map database types to standard names:

```python
@staticmethod
def _infer_type(value) -> str:
    """Infer database type from Python value."""
    if value is None:
        return "unknown"
    elif isinstance(value, bool):
        return "boolean"
    elif isinstance(value, int):
        return "integer"
    elif isinstance(value, float):
        return "numeric"
    elif isinstance(value, str):
        return "text"
    elif isinstance(value, datetime):
        return "timestamp"
    elif isinstance(value, date):
        return "date"
    else:
        return str(type(value).__name__)
```

### Dialect Configuration

#### SQL Dialect Name

This is used by sqlglot for SQL validation:

```python
def get_dialect_name(self) -> str:
    """Get SQL dialect name for sqlglot."""
    # Supported dialects: postgres, mysql, sqlite, oracle, mssql, etc.
    # See: https://github.com/tobymao/sqlglot#dialects
    return "postgres"  # Change to your database's dialect
```

#### Identifier Quoting

Different databases use different quote characters:

```python
def get_identifier_quote_char(self) -> str:
    """Get character used for quoting identifiers."""
    # PostgreSQL, Oracle: double quotes (")
    # MySQL: backticks (`)
    # SQL Server: brackets ([])
    return '"'
```

## Examples from Existing Adapters

### PostgreSQL Adapter

**Connection**:
```python
import asyncpg

async def get_connection_pool(self) -> asyncpg.Pool:
    if self._pool is None:
        self._pool = await asyncpg.create_pool(
            self.config.url,
            min_size=self.config.min_pool_size,
            max_size=self.config.max_pool_size,
            command_timeout=self.config.command_timeout,
        )
    return self._pool
```

**Metadata**:
```python
# Query pg_catalog and information_schema
tables_query = """
    SELECT schemaname, tablename, 'table' AS type
    FROM pg_tables
    WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
"""
```

**Query Execution**:
```python
async with pool.acquire() as conn:
    rows = await conn.fetch(sql)
    # asyncpg returns Record objects
    result_rows = [dict(row) for row in rows]
```

### MySQL Adapter

**Connection**:
```python
import aiomysql
from urllib.parse import urlparse

def _parse_url(self, url: str):
    parsed = urlparse(url)
    return {
        'host': parsed.hostname or 'localhost',
        'port': parsed.port or 3306,
        'user': parsed.username or 'root',
        'password': parsed.password or '',
        'db': parsed.path.lstrip('/') if parsed.path else None,
    }

async def get_connection_pool(self):
    if self._pool is None:
        params = self._parse_url(self.config.url)
        self._pool = await aiomysql.create_pool(**params)
    return self._pool
```

**Metadata**:
```python
# Query INFORMATION_SCHEMA
async with conn.cursor(aiomysql.DictCursor) as cursor:
    await cursor.execute("""
        SELECT TABLE_NAME, TABLE_TYPE
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = %s
    """, (db_name,))
    rows = await cursor.fetchall()
```

**Query Execution**:
```python
async with conn.cursor(aiomysql.DictCursor) as cursor:
    await cursor.execute(sql)
    rows = await cursor.fetchall()
    # aiomysql returns dicts when using DictCursor
```

## Common Patterns

### Async Context Manager

Use connection pools with async context managers:

```python
pool = await self.get_connection_pool()
async with pool.acquire() as conn:
    # Use connection
    result = await conn.execute(query)
```

### Error Handling

Wrap database-specific errors:

```python
from app.exceptions import DatabaseError, QueryExecutionError

async def execute_query(self, sql: str):
    try:
        # Execute query
        pass
    except YourDatabaseError as e:
        raise QueryExecutionError(f"Query failed: {e}") from e
```

### Resource Cleanup

Always cleanup resources:

```python
async def close_connection_pool(self):
    if self._pool is not None:
        await self._pool.close()
        await self._pool.wait_closed()  # if needed
        self._pool = None
```

## Testing Your Adapter

### Unit Tests

Test each method independently:

```python
@pytest.mark.asyncio
async def test_test_connection_success():
    """Test successful connection."""
    config = ConnectionConfig(url="valid_url", name="test")
    adapter = YourDatabaseAdapter(config)

    success, error = await adapter.test_connection()

    assert success is True
    assert error is None

@pytest.mark.asyncio
async def test_test_connection_failure():
    """Test failed connection."""
    config = ConnectionConfig(url="invalid_url", name="test")
    adapter = YourDatabaseAdapter(config)

    success, error = await adapter.test_connection()

    assert success is False
    assert error is not None
    assert "connection" in error.lower()
```

### Integration Tests

Test with real database:

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_execution_with_real_db():
    """Test query execution against real database."""
    config = ConnectionConfig(
        url=os.getenv("YOUR_DB_URL"),
        name="test"
    )
    adapter = YourDatabaseAdapter(config)

    result = await adapter.execute_query("SELECT 1 as num")

    assert result.row_count == 1
    assert result.columns[0]["name"] == "num"
    assert result.rows[0]["num"] == 1
```

### Contract Tests

Ensure adapter implements all required methods:

```python
def test_adapter_implements_all_methods():
    """Verify adapter implements DatabaseAdapter contract."""
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
        assert hasattr(YourDatabaseAdapter, method)
        assert callable(getattr(YourDatabaseAdapter, method))
```

## Checklist

Before submitting your adapter:

- [ ] Implements all abstract methods from `DatabaseAdapter`
- [ ] Handles connection errors gracefully
- [ ] Properly manages connection pool lifecycle
- [ ] Extracts complete metadata (tables, views, columns)
- [ ] Executes queries and returns standardized results
- [ ] Returns correct SQL dialect name
- [ ] Returns correct identifier quote character
- [ ] Includes unit tests (90%+ coverage)
- [ ] Includes integration tests
- [ ] Passes contract tests
- [ ] Documented with docstrings
- [ ] Registered in `DatabaseAdapterRegistry`
- [ ] Added to `DatabaseType` enum
- [ ] Updated URL parser (if needed)

## Support

For questions or issues:
1. Review existing adapters (PostgreSQL, MySQL) as reference
2. Check the main architecture document: `ARCHITECTURE_REDESIGN.md`
3. Look at base class documentation in `app/adapters/base.py`
4. Consult with the team

## FAQ

**Q: How do I handle database-specific features?**
A: Add optional methods to your adapter class. The base contract only requires common functionality.

**Q: What if my database doesn't support connection pooling?**
A: Implement connection management however your driver supports it. The interface just requires a `get_connection_pool()` method.

**Q: Can I add custom configuration options?**
A: Yes, extend `ConnectionConfig` or create a database-specific config class.

**Q: How do I handle different metadata structures?**
A: Transform your database's metadata into the standard `MetadataResult` format defined in `base.py`.

**Q: What about transactions?**
A: The base adapter doesn't require transaction support, but you can add it as an optional feature.

**Q: How do I support special data types?**
A: Implement custom type mapping in your `_infer_type()` method.
