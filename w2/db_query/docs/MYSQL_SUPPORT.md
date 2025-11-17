# MySQL Support Documentation

## Overview

The db_query backend now supports both PostgreSQL and MySQL databases. The system automatically detects the database type from the connection URL and routes operations to the appropriate service.

## Connection URL Formats

### PostgreSQL
```
postgresql://user:password@host:port/database
postgres://user:password@host:port/database
```

### MySQL
```
mysql://user:password@host:port/database
mysql+aiomysql://user:password@host:port/database
```

## Examples

### Connecting to MySQL

**Example: Local MySQL database**
```bash
curl -X PUT "http://localhost:8000/api/v1/dbs/my_todo_db" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "mysql://root@localhost:3306/todo_db",
    "description": "Local MySQL todo database"
  }'
```

**Example: Remote MySQL with password**
```bash
curl -X PUT "http://localhost:8000/api/v1/dbs/prod_db" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "mysql://user:password@db.example.com:3306/mydb",
    "dbType": "mysql",
    "description": "Production MySQL database"
  }'
```

### Database Type Detection

The system automatically detects the database type from the URL scheme:
- `postgresql://` or `postgres://` → PostgreSQL
- `mysql://` or `mysql+aiomysql://` → MySQL

You can also explicitly specify the `dbType` parameter (optional):
```json
{
  "url": "mysql://root@localhost:3306/todo_db",
  "dbType": "mysql"
}
```

## Features

### 1. Metadata Extraction

MySQL metadata extraction includes:
- Tables and views from all user schemas
- Column information (name, data type, nullable, primary key, unique)
- Row counts for tables
- Schema information

**Example: Get MySQL metadata**
```bash
curl "http://localhost:8000/api/v1/dbs/my_todo_db"
```

### 2. SQL Query Execution

Execute SQL SELECT queries against MySQL databases:

**Example: Query MySQL database**
```bash
curl -X POST "http://localhost:8000/api/v1/dbs/my_todo_db/query" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT * FROM todos WHERE completed = 0"
  }'
```

**MySQL-specific syntax support:**
- Backtick identifiers: `` `table_name` ``, `` `column_name` ``
- MySQL data types: INT, VARCHAR, DATETIME, etc.
- MySQL LIMIT syntax: `LIMIT 10`

### 3. Natural Language to SQL

Generate MySQL-specific SQL from natural language:

**Example: Chinese prompt**
```bash
curl -X POST "http://localhost:8000/api/v1/dbs/my_todo_db/query/natural" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "查询所有未完成的待办事项"
  }'
```

**Example: English prompt**
```bash
curl -X POST "http://localhost:8000/api/v1/dbs/my_todo_db/query/natural" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Find all incomplete todo items"
  }'
```

The generated SQL will use MySQL-specific syntax:
```sql
SELECT * FROM `todos` WHERE `completed` = 0 LIMIT 1000
```

## Technical Implementation

### Architecture

The implementation uses a factory pattern to route operations:

1. **Connection Factory** (`app/services/connection_factory.py`)
   - Routes connection operations based on `db_type`
   - Manages connection pools for both PostgreSQL and MySQL

2. **Metadata Factory** (`app/services/metadata.py`)
   - Routes metadata extraction to appropriate service
   - Caches metadata in SQLite

3. **Query Factory** (`app/services/query.py`)
   - Routes query execution based on database type
   - Validates SQL using appropriate dialect (postgres/mysql)

### Dependencies

- **aiomysql**: Async MySQL driver (similar to asyncpg for PostgreSQL)
- **PyMySQL**: Pure-Python MySQL client library
- **sqlglot**: SQL parser supporting multiple dialects

## Differences Between PostgreSQL and MySQL

### Identifiers
- **PostgreSQL**: Double quotes `"table_name"`
- **MySQL**: Backticks `` `table_name` ``

### Data Types
- **PostgreSQL**: `character varying`, `serial`, `timestamp with time zone`
- **MySQL**: `VARCHAR`, `AUTO_INCREMENT`, `DATETIME`

### Schema Qualification
- **PostgreSQL**: `schema.table` (multiple schemas common)
- **MySQL**: `database.table` (typically single database)

## Query History

All queries (manual and NL2SQL) are saved to query history with the database type:
```bash
curl "http://localhost:8000/api/v1/dbs/my_todo_db/history"
```

## Error Handling

MySQL-specific errors are properly handled:
- Connection timeouts
- Authentication failures
- Invalid syntax
- Permission errors

## Testing

### Manual Testing with your `todo_db`

1. **Create connection:**
```bash
curl -X PUT "http://localhost:8000/api/v1/dbs/todo_db" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "mysql://root@localhost:3306/todo_db",
    "description": "Test MySQL database"
  }'
```

2. **Get metadata:**
```bash
curl "http://localhost:8000/api/v1/dbs/todo_db"
```

3. **Execute query:**
```bash
curl -X POST "http://localhost:8000/api/v1/dbs/todo_db/query" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT * FROM todos LIMIT 10"
  }'
```

4. **Natural language query:**
```bash
curl -X POST "http://localhost:8000/api/v1/dbs/todo_db/query/natural" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "获取所有待办事项"
  }'
```

## Migration Notes

### Existing PostgreSQL Connections

Existing PostgreSQL connections will continue to work without any changes. The `db_type` field defaults to `postgresql` for backward compatibility.

### Database Schema Changes

The `DatabaseConnection` model now includes a `db_type` field:
```python
class DatabaseConnection(SQLModel, table=True):
    name: str
    url: str
    db_type: DatabaseType = Field(default=DatabaseType.POSTGRESQL)
    description: str | None
    ...
```

SQLModel will automatically handle the schema migration when the application starts.

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to MySQL
```
Connection test failed: Can't connect to MySQL server
```

**Solutions**:
1. Verify MySQL is running: `mysql -u root -p`
2. Check host/port: Use `localhost` or `127.0.0.1`
3. Verify credentials in connection URL
4. Check MySQL allows remote connections (if needed)

### Metadata Extraction Issues

**Problem**: Empty metadata returned
```json
{"tables": [], "views": []}
```

**Solutions**:
1. Verify database exists: `SHOW DATABASES;`
2. Check user permissions: `SHOW GRANTS;`
3. Ensure tables exist: `SHOW TABLES;`

### Query Execution Issues

**Problem**: SQL syntax errors
```
SQL parse error: ...
```

**Solutions**:
1. Use MySQL-specific syntax (backticks for identifiers)
2. Verify query with `mysql` CLI first
3. Check LIMIT clause is included (auto-added if missing)

## API Changes

### Request Schema

The `DatabaseConnectionInput` schema now supports optional `dbType`:

```typescript
{
  url: string;                    // Database connection URL
  dbType?: "postgresql" | "mysql"; // Optional, auto-detected from URL
  description?: string;            // Optional description
}
```

### Response Schema

The `DatabaseConnectionResponse` schema now includes `dbType`:

```typescript
{
  name: string;
  url: string;
  dbType: "postgresql" | "mysql"; // Database type
  description: string | null;
  createdAt: string;
  updatedAt: string;
  lastConnectedAt: string | null;
  status: string;
}
```

## Performance Considerations

### Connection Pooling

Both PostgreSQL and MySQL connections use connection pooling:
- **Min pool size**: 1
- **Max pool size**: 5
- **Command timeout**: 60 seconds (PostgreSQL)

### Metadata Caching

Metadata is cached in SQLite for 24 hours (configurable via `metadata_cache_hours` setting).

### Query Limits

All queries are automatically limited to 1000 rows to prevent performance issues.
