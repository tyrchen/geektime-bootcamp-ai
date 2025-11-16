# Data Model: 数据库查询工具

**Feature**: 001-db-query-tool
**Date**: 2025-11-16
**Phase**: 1 - Data Model Design

## Overview

本文档定义了数据库查询工具的核心数据模型。系统使用两种数据存储：

1. **本地 SQLite**: 存储数据库连接信息、元数据缓存和查询历史
2. **远程 PostgreSQL**: 用户要查询的目标数据库（只读访问）

所有 API 响应使用 camelCase 格式（符合宪法原则 III）。

## Entity Relationship Diagram

```
DatabaseConnection (1) ──┬──> (N) DatabaseMetadata
                          │
                          └──> (N) QueryHistory

DatabaseMetadata (1) ────> (N) TableMetadata

TableMetadata (1) ───────> (N) ColumnMetadata
```

## Core Entities

### 1. DatabaseConnection

表示一个已保存的数据库连接。

**Purpose**: 存储用户添加的数据库连接信息，支持多个数据库切换。

**Storage**: Local SQLite

**Fields**:

| Field Name          | Type     | Required | Description              | Validation                         |
|---------------------|----------|----------|--------------------------|------------------------------------|
| `name`              | string   | Yes      | 数据库连接的唯一标识名称 | 主键，2-50字符，允许字母数字和短横线 |
| `url`               | string   | Yes      | PostgreSQL 连接字符串    | 必须是有效的 PostgreSQL URL 格式   |
| `description`       | string   | No       | 可选的连接描述           | 最多 200 字符                      |
| `created_at`        | datetime | Yes      | 创建时间                 | 自动设置为当前时间                 |
| `updated_at`        | datetime | Yes      | 最后更新时间             | 自动更新                           |
| `last_connected_at` | datetime | No       | 最后成功连接时间         | 连接成功后更新                     |
| `status`            | enum     | Yes      | 连接状态                 | active, inactive, error            |

**Validation Rules**:

- `name`: 必须唯一，匹配正则 `^[a-zA-Z0-9-_]+$`
- `url`: 必须符合格式 `postgresql://[user[:password]@]host[:port][/database]`
- `status`: 默认为 "active"

**Example (SQLModel)**:

```python
from sqlmodel import SQLModel, Field
from datetime import datetime
from enum import Enum

class ConnectionStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"

class DatabaseConnection(SQLModel, table=True):
    __tablename__ = "database_connections"

    name: str = Field(primary_key=True, regex="^[a-zA-Z0-9-_]+$")
    url: str = Field(index=True)
    description: str | None = Field(default=None, max_length=200)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_connected_at: datetime | None = None
    status: ConnectionStatus = Field(default=ConnectionStatus.ACTIVE)
```

**API Response (camelCase)**:

```json
{
  "name": "my-postgres",
  "url": "postgresql://user:pass@localhost:5432/mydb",
  "description": "Production database",
  "createdAt": "2025-11-16T10:00:00Z",
  "updatedAt": "2025-11-16T15:30:00Z",
  "lastConnectedAt": "2025-11-16T15:30:00Z",
  "status": "active"
}
```

---

### 2. DatabaseMetadata

表示数据库的元数据（表、视图、列信息）缓存。

**Purpose**: 缓存从 PostgreSQL 系统表提取的 schema 信息，避免重复查询，提升性能。

**Storage**: Local SQLite (JSON 字段存储结构化数据)

**Fields**:

| Field Name      | Type     | Required | Description           | Validation                      |
|-----------------|----------|----------|-----------------------|---------------------------------|
| `id`            | integer  | Yes      | 自增主键              | 自动生成                        |
| `database_name` | string   | Yes      | 关联的数据库连接名称  | 外键 -> DatabaseConnection.name |
| `metadata_json` | text     | Yes      | JSON 格式的完整元数据 | 有效的 JSON 字符串              |
| `fetched_at`    | datetime | Yes      | 元数据获取时间        | 自动设置                        |
| `table_count`   | integer  | Yes      | 表和视图总数          | >= 0                            |
| `is_stale`      | boolean  | Yes      | 是否过期（超过24小时）  | 自动计算                        |

**Validation Rules**:

- `database_name`: 必须引用存在的 DatabaseConnection
- `metadata_json`: 必须是有效的 JSON，遵循 TableMetadata 结构
- `is_stale`: 当 `fetched_at` 距离现在超过 24 小时时为 true

**Metadata JSON Structure**:

```json
{
  "tables": [
    {
      "name": "users",
      "type": "table",
      "columns": [
        {
          "name": "id",
          "dataType": "integer",
          "nullable": false,
          "primaryKey": true,
          "defaultValue": "nextval('users_id_seq'::regclass)"
        },
        {
          "name": "email",
          "dataType": "character varying(100)",
          "nullable": false,
          "primaryKey": false,
          "unique": true
        }
      ],
      "rowCount": 1523
    }
  ],
  "views": [
    {
      "name": "active_users",
      "type": "view",
      "columns": [...]
    }
  ]
}
```

**Example (SQLModel)**:

```python
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Text
from datetime import datetime, timedelta

class DatabaseMetadata(SQLModel, table=True):
    __tablename__ = "database_metadata"

    id: int | None = Field(default=None, primary_key=True)
    database_name: str = Field(foreign_key="database_connections.name")
    metadata_json: str = Field(sa_column=Column(Text))
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    table_count: int = Field(default=0)

    @property
    def is_stale(self) -> bool:
        return datetime.utcnow() - self.fetched_at > timedelta(hours=24)
```

---

### 3. TableMetadata

表或视图的元数据（在 DatabaseMetadata.metadata_json 中）。

**Purpose**: 描述单个表或视图的结构。

**Storage**: 嵌套在 DatabaseMetadata 的 JSON 字段中

**Fields**:

| Field Name   | Type    | Required | Description                      |
|--------------|---------|----------|----------------------------------|
| `name`       | string  | Yes      | 表/视图名称                      |
| `type`       | enum    | Yes      | "table" 或 "view"                |
| `columns`    | array   | Yes      | 列定义数组                       |
| `rowCount`   | integer | No       | 估计行数（仅表）                   |
| `schemaName` | string  | No       | PostgreSQL schema（默认 "public"） |

**Example (Pydantic Model)**:

```python
from pydantic import BaseModel, Field
from typing import Literal

class TableMetadata(BaseModel):
    name: str = Field(min_length=1, max_length=63)
    type: Literal["table", "view"]
    columns: list["ColumnMetadata"]
    row_count: int | None = Field(default=None, alias="rowCount")
    schema_name: str = Field(default="public", alias="schemaName")
```

---

### 4. ColumnMetadata

列的元数据（在 TableMetadata.columns 中）。

**Purpose**: 描述表/视图中的单个列。

**Storage**: 嵌套在 TableMetadata 的 columns 数组中

**Fields**:

| Field Name     | Type    | Required | Description         |
|----------------|---------|----------|---------------------|
| `name`         | string  | Yes      | 列名称              |
| `dataType`     | string  | Yes      | PostgreSQL 数据类型 |
| `nullable`     | boolean | Yes      | 是否可为 NULL       |
| `primaryKey`   | boolean | Yes      | 是否为主键          |
| `unique`       | boolean | No       | 是否有唯一约束      |
| `defaultValue` | string  | No       | 默认值表达式        |
| `comment`      | string  | No       | 列注释              |

**Example (Pydantic Model)**:

```python
from pydantic import BaseModel, Field

class ColumnMetadata(BaseModel):
    name: str = Field(min_length=1, max_length=63)
    data_type: str = Field(alias="dataType")
    nullable: bool
    primary_key: bool = Field(alias="primaryKey")
    unique: bool = False
    default_value: str | None = Field(default=None, alias="defaultValue")
    comment: str | None = None
```

---

### 5. QueryHistory

查询历史记录。

**Purpose**: 保存用户执行过的 SQL 查询，支持快速重新执行。

**Storage**: Local SQLite

**Fields**:

| Field Name          | Type     | Required | Description         | Validation                      |
|---------------------|----------|----------|---------------------|---------------------------------|
| `id`                | integer  | Yes      | 自增主键            | 自动生成                        |
| `database_name`     | string   | Yes      | 执行查询的数据库    | 外键 -> DatabaseConnection.name |
| `sql_text`          | text     | Yes      | 完整的 SQL 查询语句 | 非空                            |
| `executed_at`       | datetime | Yes      | 执行时间            | 自动设置                        |
| `execution_time_ms` | integer  | No       | 执行耗时（毫秒）      | >= 0                            |
| `row_count`         | integer  | No       | 返回行数            | >= 0                            |
| `success`           | boolean  | Yes      | 是否成功执行        | true/false                      |
| `error_message`     | text     | No       | 错误信息（如果失败）  | success=false 时必须            |
| `query_source`      | enum     | Yes      | 查询来源            | manual, natural_language        |

**Validation Rules**:

- 保留最近 50 条记录（自动清理旧记录）
- `execution_time_ms`: 如果成功则必须有值
- `row_count`: 如果成功则必须有值
- `error_message`: 仅在 `success = false` 时有值

**Example (SQLModel)**:

```python
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Text
from datetime import datetime
from enum import Enum

class QuerySource(str, Enum):
    MANUAL = "manual"
    NATURAL_LANGUAGE = "natural_language"

class QueryHistory(SQLModel, table=True):
    __tablename__ = "query_history"

    id: int | None = Field(default=None, primary_key=True)
    database_name: str = Field(foreign_key="database_connections.name")
    sql_text: str = Field(sa_column=Column(Text))
    executed_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    execution_time_ms: int | None = None
    row_count: int | None = None
    success: bool
    error_message: str | None = Field(default=None, sa_column=Column(Text))
    query_source: QuerySource = Field(default=QuerySource.MANUAL)
```

**API Response (camelCase)**:

```json
{
  "id": 123,
  "databaseName": "my-postgres",
  "sqlText": "SELECT * FROM users WHERE status = 'active' LIMIT 100",
  "executedAt": "2025-11-16T15:45:00Z",
  "executionTimeMs": 125,
  "rowCount": 87,
  "success": true,
  "errorMessage": null,
  "querySource": "manual"
}
```

---

### 6. QueryResult (Transient)

查询执行结果（不持久化，仅 API 响应）。

**Purpose**: 返回查询结果给前端展示。

**Storage**: 不存储，仅在内存中构建

**Fields**:

| Field Name        | Type    | Required | Description                |
|-------------------|---------|----------|----------------------------|
| `columns`         | array   | Yes      | 列定义数组                 |
| `rows`            | array   | Yes      | 数据行数组                 |
| `rowCount`        | integer | Yes      | 总行数                     |
| `executionTimeMs` | integer | Yes      | 执行耗时（毫秒）             |
| `sql`             | string  | Yes      | 实际执行的 SQL（可能被修改） |

**Column Definition**:

```typescript
interface QueryColumn {
  name: string;
  dataType: string;
}
```

**Row Format**:

```typescript
type QueryRow = Record<string, any>;  // 键为列名，值为数据
```

**Example (Pydantic Model)**:

```python
from pydantic import BaseModel, Field

class QueryColumn(BaseModel):
    name: str
    data_type: str = Field(alias="dataType")

class QueryResult(BaseModel):
    columns: list[QueryColumn]
    rows: list[dict[str, any]]
    row_count: int = Field(alias="rowCount")
    execution_time_ms: int = Field(alias="executionTimeMs")
    sql: str
```

**API Response Example**:

```json
{
  "columns": [
    {"name": "id", "dataType": "integer"},
    {"name": "name", "dataType": "character varying"},
    {"name": "email", "dataType": "character varying"}
  ],
  "rows": [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "email": "bob@example.com"}
  ],
  "rowCount": 2,
  "executionTimeMs": 45,
  "sql": "SELECT id, name, email FROM users LIMIT 1000"
}
```

---

## Data Access Patterns

### Pattern 1: Add Database Connection

**Flow**:

```
1. User submits connection info (name, URL)
2. Validate URL format
3. Test connection (connect and disconnect immediately)
4. Insert into DatabaseConnection table
5. Return connection details
```

**SQL**:

```sql
INSERT INTO database_connections (name, url, description, status)
VALUES (?, ?, ?, 'active')
ON CONFLICT (name) DO UPDATE SET
    url = EXCLUDED.url,
    description = EXCLUDED.description,
    updated_at = CURRENT_TIMESTAMP;
```

### Pattern 2: Fetch and Cache Metadata

**Flow**:

```
1. Check if cached metadata exists and is not stale
2. If fresh cache exists, return from SQLite
3. Otherwise:
   a. Connect to PostgreSQL
   b. Query system tables (pg_tables, information_schema.columns)
   c. Transform to JSON structure
   d. Insert/update in database_metadata table
   e. Return metadata
```

**PostgreSQL Queries**:

```sql
-- Get all tables and views
SELECT schemaname, tablename, 'table' AS type
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
UNION ALL
SELECT schemaname, viewname, 'view' AS type
FROM pg_views
WHERE schemaname NOT IN ('pg_catalog', 'information_schema');

-- Get columns for each table
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = ? AND table_name = ?
ORDER BY ordinal_position;

-- Get primary keys
SELECT kcu.column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
WHERE tc.table_schema = ?
    AND tc.table_name = ?
    AND tc.constraint_type = 'PRIMARY KEY';
```

### Pattern 3: Execute Query

**Flow**:

```
1. Validate SQL with sqlglot
2. Check if SELECT statement
3. Add LIMIT 1000 if missing
4. Execute query against PostgreSQL
5. Convert result to QueryResult format
6. Save to QueryHistory
7. Return QueryResult
```

**Query Execution**:

```python
async def execute_query(db_name: str, sql: str) -> QueryResult:
    # Validate
    validated_sql = validate_and_transform_sql(sql)

    # Execute
    start = time.time()
    result = await asyncpg_pool.fetch(validated_sql)
    execution_time = int((time.time() - start) * 1000)

    # Transform
    columns = [{"name": col, "dataType": type} for col, type in result.keys()]
    rows = [dict(row) for row in result]

    # Save history
    await save_query_history(db_name, validated_sql, len(rows), execution_time, True)

    return QueryResult(
        columns=columns,
        rows=rows,
        rowCount=len(rows),
        executionTimeMs=execution_time,
        sql=validated_sql
    )
```

---

## State Transitions

### DatabaseConnection Status

```
[Initial] → active (default)
active → inactive (user disables)
active → error (connection test fails)
inactive → active (user re-enables)
error → active (connection restored)
```

### Metadata Freshness

```
[Not Cached] → fresh (first fetch)
fresh → stale (after 24 hours)
stale → fresh (manual refresh)
```

---

## Performance Considerations

### Indexes

**database_connections**:

- Primary key: `name`
- Index on: `url` (for duplicate detection)

**database_metadata**:

- Primary key: `id`
- Foreign key: `database_name` → `database_connections.name`
- Index on: `database_name, fetched_at` (for cache lookup)

**query_history**:

- Primary key: `id`
- Foreign key: `database_name` → `database_connections.name`
- Index on: `executed_at DESC` (for recent queries)
- Auto-cleanup: Keep only last 50 records per database

### Caching Strategy

1. **Metadata**: 24-hour cache in SQLite
2. **Connections**: In-memory asyncpg connection pool
3. **Query Results**: No caching (always fresh)

---

## Data Migration

### Initial Schema (Alembic Migration)

```python
# alembic/versions/001_initial_schema.py
def upgrade():
    op.create_table(
        'database_connections',
        sa.Column('name', sa.String(50), primary_key=True),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('description', sa.String(200)),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('last_connected_at', sa.DateTime),
        sa.Column('status', sa.String(20), nullable=False),
    )

    op.create_table(
        'database_metadata',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('database_name', sa.String(50), sa.ForeignKey('database_connections.name')),
        sa.Column('metadata_json', sa.Text, nullable=False),
        sa.Column('fetched_at', sa.DateTime, nullable=False),
        sa.Column('table_count', sa.Integer, nullable=False),
    )

    op.create_table(
        'query_history',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('database_name', sa.String(50), sa.ForeignKey('database_connections.name')),
        sa.Column('sql_text', sa.Text, nullable=False),
        sa.Column('executed_at', sa.DateTime, nullable=False),
        sa.Column('execution_time_ms', sa.Integer),
        sa.Column('row_count', sa.Integer),
        sa.Column('success', sa.Boolean, nullable=False),
        sa.Column('error_message', sa.Text),
        sa.Column('query_source', sa.String(20), nullable=False),
    )

    op.create_index('idx_query_history_executed_at', 'query_history', ['executed_at'])
```

---

## Validation Summary

### Backend (Python/Pydantic)

- ✅ All models use Pydantic BaseModel or SQLModel
- ✅ Strict type annotations on all fields
- ✅ Automatic validation via Pydantic validators
- ✅ camelCase aliases configured globally

### Frontend (TypeScript)

- ✅ TypeScript interfaces mirror backend models
- ✅ Strict type checking enabled
- ✅ Runtime validation with zod or similar (optional)

### Database Constraints

- ✅ Primary keys, foreign keys, unique constraints
- ✅ NOT NULL constraints on required fields
- ✅ Indexes on frequently queried columns

---

## Conclusion

数据模型设计完成，满足以下要求：

- ✅ 符合项目宪法（Pydantic, camelCase, 类型安全）
- ✅ 支持所有用户故事（P1-P4）
- ✅ 性能优化（缓存、索引）
- ✅ 数据完整性（外键、约束）
- ✅ 易于测试和维护

准备进入 API Contract 设计阶段。
