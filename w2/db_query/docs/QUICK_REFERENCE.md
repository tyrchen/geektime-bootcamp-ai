# Quick Reference: Database Adapter Architecture

## Adding a New Database (5 Steps)

### 1. Create Adapter
```python
# app/adapters/yourdb.py
from app.adapters.base import DatabaseAdapter, ConnectionConfig, QueryResult, MetadataResult

class YourDBAdapter(DatabaseAdapter):
    async def test_connection(self):
        # Test connection, return (True, None) or (False, error_msg)
        pass

    async def get_connection_pool(self):
        # Create and cache connection pool
        if self._pool is None:
            self._pool = await your_driver.create_pool(self.config.url)
        return self._pool

    async def close_connection_pool(self):
        # Close pool
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def extract_metadata(self):
        # Query database catalog, return MetadataResult
        return MetadataResult(tables=[], views=[])

    async def execute_query(self, sql: str):
        # Execute SQL, return QueryResult
        return QueryResult(columns=[], rows=[], row_count=0)

    def get_dialect_name(self):
        return "yourdb"  # For SQL validation

    def get_identifier_quote_char(self):
        return '"'  # or '`' or '['
```

### 2. Add Database Type
```python
# app/models/database.py
class DatabaseType(str, Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    YOURDB = "yourdb"  # ADD THIS
```

### 3. Register Adapter
```python
# app/adapters/registry.py
from app.adapters.yourdb import YourDBAdapter

class DatabaseAdapterRegistry:
    def __init__(self):
        # ... existing code ...
        self.register(DatabaseType.YOURDB, YourDBAdapter)  # ADD THIS
```

### 4. Update URL Parser (Optional)
```python
# app/utils/db_parser.py
def detect_database_type(url: str) -> DatabaseType:
    if url.startswith("yourdb://"):
        return DatabaseType.YOURDB
    # ... other databases ...
```

### 5. Test
```python
# tests/adapters/test_yourdb.py
@pytest.mark.asyncio
async def test_yourdb_adapter():
    config = ConnectionConfig(url="yourdb://localhost/test", name="test")
    adapter = YourDBAdapter(config)

    success, error = await adapter.test_connection()
    assert success or error is not None
```

## Common Patterns

### Connection Pool Management
```python
async def get_connection_pool(self):
    if self._pool is None:
        # CREATE ONCE, reuse on subsequent calls
        self._pool = await driver.create_pool(
            self.config.url,
            min_size=self.config.min_pool_size,
            max_size=self.config.max_pool_size,
        )
    return self._pool
```

### URL Parsing
```python
from urllib.parse import urlparse

def _parse_url(self, url: str):
    parsed = urlparse(url)  # yourdb://user:pass@host:port/database
    return {
        'host': parsed.hostname or 'localhost',
        'port': parsed.port or 5432,
        'user': parsed.username,
        'password': parsed.password,
        'database': parsed.path.lstrip('/'),
    }
```

### Metadata Extraction
```python
async def extract_metadata(self):
    pool = await self.get_connection_pool()

    async with pool.acquire() as conn:
        # Get tables
        tables = await self._get_tables(conn)
        # Get views
        views = await self._get_views(conn)

    return MetadataResult(tables=tables, views=views)

async def _get_tables(self, conn):
    rows = await conn.fetch("SELECT table_name FROM information_schema.tables")
    tables = []
    for row in rows:
        columns = await self._get_columns(conn, row['table_name'])
        tables.append({
            "name": row['table_name'],
            "type": "table",
            "schemaName": "public",
            "columns": columns,
        })
    return tables
```

### Query Execution
```python
async def execute_query(self, sql: str):
    pool = await self.get_connection_pool()

    async with pool.acquire() as conn:
        rows = await conn.fetch(sql)

        # Extract columns from first row
        columns = []
        if rows:
            for key, value in rows[0].items():
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

### Type Inference
```python
@staticmethod
def _infer_type(value):
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
    else:
        return str(type(value).__name__)
```

## Data Structures

### ConnectionConfig
```python
@dataclass
class ConnectionConfig:
    url: str              # Database connection URL
    name: str             # Connection identifier
    min_pool_size: int = 1
    max_pool_size: int = 5
    command_timeout: int = 60
```

### QueryResult
```python
@dataclass
class QueryResult:
    columns: List[Dict[str, str]]    # [{"name": "id", "dataType": "integer"}]
    rows: List[Dict[str, Any]]       # [{"id": 1, "name": "Alice"}]
    row_count: int                    # 1
```

### MetadataResult
```python
@dataclass
class MetadataResult:
    tables: List[Dict[str, Any]]  # Table metadata
    views: List[Dict[str, Any]]   # View metadata

# Table structure:
{
    "name": "users",
    "type": "table",
    "schemaName": "public",
    "rowCount": 100,
    "columns": [
        {
            "name": "id",
            "dataType": "integer",
            "nullable": False,
            "primaryKey": True,
            "unique": False,
            "defaultValue": None
        }
    ]
}
```

## Using the Service

### Execute Query
```python
from app.services.database_service import database_service
from app.models.database import DatabaseType

result, time_ms = await database_service.execute_query(
    db_type=DatabaseType.POSTGRESQL,
    name="mydb",
    url="postgresql://localhost/mydb",
    sql="SELECT * FROM users",
    limit=1000
)

print(f"Returned {result.row_count} rows in {time_ms}ms")
for row in result.rows:
    print(row)
```

### Extract Metadata
```python
metadata = await database_service.extract_metadata(
    db_type=DatabaseType.MYSQL,
    name="mydb",
    url="mysql://localhost/mydb"
)

print(f"Tables: {len(metadata.tables)}")
for table in metadata.tables:
    print(f"  {table['name']}: {len(table['columns'])} columns")
```

### Test Connection
```python
success, error = await database_service.test_connection(
    db_type=DatabaseType.POSTGRESQL,
    url="postgresql://localhost/test"
)

if success:
    print("Connection successful!")
else:
    print(f"Connection failed: {error}")
```

## Database-Specific Examples

### PostgreSQL
```python
import asyncpg

async def get_connection_pool(self):
    if self._pool is None:
        self._pool = await asyncpg.create_pool(self.config.url)
    return self._pool

async def execute_query(self, sql):
    pool = await self.get_connection_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(sql)  # Returns List[Record]
        return QueryResult(...)
```

### MySQL
```python
import aiomysql

async def get_connection_pool(self):
    if self._pool is None:
        params = self._parse_url(self.config.url)
        self._pool = await aiomysql.create_pool(**params)
    return self._pool

async def execute_query(self, sql):
    pool = await self.get_connection_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(sql)
            rows = await cursor.fetchall()  # Returns List[Dict]
            return QueryResult(...)
```

### SQLite
```python
import aiosqlite

async def get_connection_pool(self):
    # SQLite doesn't have pools, create connection
    if self._pool is None:
        self._pool = await aiosqlite.connect(self.config.url)
    return self._pool

async def execute_query(self, sql):
    conn = await self.get_connection_pool()
    cursor = await conn.execute(sql)
    rows = await cursor.fetchall()  # Returns List[Tuple]
    # Convert to list of dicts...
    return QueryResult(...)
```

## Debugging

### Enable Logging
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('app.adapters')
```

### Check Registered Adapters
```python
from app.adapters.registry import adapter_registry

print(adapter_registry.get_supported_types())
# [DatabaseType.POSTGRESQL, DatabaseType.MYSQL, ...]
```

### Test Adapter Directly
```python
from app.adapters.postgresql import PostgreSQLAdapter
from app.adapters.base import ConnectionConfig

config = ConnectionConfig(url="postgresql://localhost/test", name="test")
adapter = PostgreSQLAdapter(config)

# Test connection
success, error = await adapter.test_connection()
print(f"Connection: {success}, Error: {error}")

# Test query
result = await adapter.execute_query("SELECT 1 as num")
print(f"Result: {result.rows}")
```

## Common Issues

### Issue: "Unsupported database type"
**Cause**: Adapter not registered
**Fix**: Add to `DatabaseAdapterRegistry.__init__()`
```python
self.register(DatabaseType.YOURDB, YourDBAdapter)
```

### Issue: Pool already closed
**Cause**: Connection pool closed prematurely
**Fix**: Ensure pool lifecycle managed by registry
```python
# Don't manually close pools, let registry handle it
await adapter_registry.close_adapter(db_type, name)
```

### Issue: Type inference returns "unknown"
**Cause**: Value is None or unhandled type
**Fix**: Add type mapping in `_infer_type()`
```python
elif isinstance(value, Decimal):
    return "decimal"
```

### Issue: Metadata extraction fails
**Cause**: Database catalog queries incorrect
**Fix**: Check your database's information schema structure
```python
# PostgreSQL: information_schema.tables
# MySQL: INFORMATION_SCHEMA.TABLES
# Oracle: user_tables
# SQLite: sqlite_master
```

## Checklist for New Adapters

- [ ] Implement all 7 abstract methods
- [ ] Handle connection errors gracefully
- [ ] Manage connection pool lifecycle
- [ ] Extract metadata (tables, views, columns)
- [ ] Execute queries and return results
- [ ] Return correct SQL dialect name
- [ ] Return correct identifier quote char
- [ ] Add unit tests (90%+ coverage)
- [ ] Add integration tests
- [ ] Pass contract tests
- [ ] Add docstrings
- [ ] Register in registry
- [ ] Update DatabaseType enum
- [ ] Update URL parser (if needed)

## Resources

- **Full Architecture**: `ARCHITECTURE_REDESIGN.md`
- **Implementation Guide**: `IMPLEMENTATION_GUIDE.md`
- **Adapter Guide**: `app/adapters/README.md`
- **Summary**: `ARCHITECTURE_SUMMARY.md`
- **Examples**: `app/adapters/postgresql.py`, `app/adapters/mysql.py`
