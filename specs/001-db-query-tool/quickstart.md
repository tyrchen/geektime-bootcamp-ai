# Quick Start Guide: 数据库查询工具

**Feature**: 001-db-query-tool
**Date**: 2025-11-16
**Phase**: 1 - Quick Start & Integration Scenarios

## Overview

本文档提供快速开始指南和集成测试场景，帮助开发者快速设置开发环境并验证功能实现。

## Prerequisites

### Required Software

- **Backend**:
  - Python 3.12 or higher
  - uv (Python package manager): <https://astral.sh/uv>
  - PostgreSQL 14+ (for testing target database)

- **Frontend**:
  - Node.js 18+ or higher
  - npm or yarn

- **Tools**:
  - curl or httpie (for API testing)
  - git

### Environment Variables

Create a `.env` file in the backend directory:

```bash
# Backend (.env)
OPENAI_API_KEY=sk-your-api-key-here
DB_QUERY_DATA_DIR=~/.db_query  # Optional, defaults to this
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
CORS_ORIGINS=*  # Allow all origins for local development
```

---

## Quick Start: Backend

### 1. Clone and Setup

```bash
cd w2/db_query/backend

# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install project in development mode
uv pip install -e ".[dev]"
```

### 2. Initialize Database

```bash
# Create data directory
mkdir -p ~/.db_query

# Run migrations (creates SQLite schema)
alembic upgrade head
```

### 3. Run Backend Server

```bash
# Development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Server will be available at:
# - API: http://localhost:8000
# - Docs: http://localhost:8000/docs
# - OpenAPI: http://localhost:8000/openapi.json
```

### 4. Verify Backend

```bash
# Test health endpoint
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

## Quick Start: Frontend

### 1. Setup

```bash
cd w2/db_query/frontend

# Install dependencies
npm install  # or yarn install

# Create .env.local for local development
cat > .env.local << EOF
VITE_API_BASE_URL=http://localhost:8000/api/v1
EOF
```

### 2. Run Development Server

```bash
npm run dev

# Frontend will be available at:
# http://localhost:5173
```

### 3. Build for Production

```bash
npm run build

# Preview production build
npm run preview
```

---

## Integration Scenarios

### Scenario 1: Add Database Connection (P1)

**Purpose**: Verify user can add a PostgreSQL database connection and view metadata

**Prerequisites**:

- Backend running on port 8000
- PostgreSQL test database running and accessible

#### Step 1: Prepare Test Database

```bash
# Create test database (if needed)
createdb testdb

# Seed with test data
psql testdb << EOF
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    total DECIMAL(10, 2),
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO users (name, email, status) VALUES
    ('Alice', 'alice@example.com', 'active'),
    ('Bob', 'bob@example.com', 'active'),
    ('Charlie', 'charlie@example.com', 'inactive');

INSERT INTO orders (user_id, total, status) VALUES
    (1, 99.99, 'completed'),
    (1, 149.99, 'pending'),
    (2, 29.99, 'completed');
EOF
```

#### Step 2: Add Connection via API

```bash
# Add database connection
curl -X PUT http://localhost:8000/api/v1/dbs/testdb \
  -H "Content-Type: application/json" \
  -d '{
    "url": "postgresql://postgres:postgres@localhost:5432/testdb",
    "description": "Test database for development"
  }'

# Expected response (201 Created):
{
  "name": "testdb",
  "url": "postgresql://postgres:postgres@localhost:5432/testdb",
  "description": "Test database for development",
  "createdAt": "2025-11-16T10:00:00Z",
  "updatedAt": "2025-11-16T10:00:00Z",
  "lastConnectedAt": "2025-11-16T10:00:00Z",
  "status": "active"
}
```

#### Step 3: Retrieve Metadata

```bash
# Get database metadata
curl http://localhost:8000/api/v1/dbs/testdb

# Expected response:
{
  "databaseName": "testdb",
  "tables": [
    {
      "name": "users",
      "type": "table",
      "schemaName": "public",
      "rowCount": 3,
      "columns": [
        {
          "name": "id",
          "dataType": "integer",
          "nullable": false,
          "primaryKey": true,
          "defaultValue": "nextval('users_id_seq'::regclass)"
        },
        {
          "name": "name",
          "dataType": "character varying(100)",
          "nullable": false,
          "primaryKey": false
        },
        {
          "name": "email",
          "dataType": "character varying(100)",
          "nullable": false,
          "primaryKey": false,
          "unique": true
        },
        {
          "name": "status",
          "dataType": "character varying(20)",
          "nullable": true,
          "primaryKey": false,
          "defaultValue": "'active'::character varying"
        },
        {
          "name": "created_at",
          "dataType": "timestamp without time zone",
          "nullable": true,
          "primaryKey": false,
          "defaultValue": "now()"
        }
      ]
    },
    {
      "name": "orders",
      "type": "table",
      "schemaName": "public",
      "rowCount": 3,
      "columns": [...]
    }
  ],
  "views": [],
  "fetchedAt": "2025-11-16T10:00:05Z",
  "isStale": false
}
```

#### Step 4: Verify in Frontend

1. Open <http://localhost:5173>
2. Navigate to "Databases" page
3. Verify "testdb" appears in the list
4. Click on "testdb" to view metadata
5. Verify tables "users" and "orders" are displayed with columns

**Success Criteria**:

- ✅ Database connection saved and status is "active"
- ✅ Metadata fetched and cached within 5 seconds
- ✅ All tables and columns displayed correctly in UI

---

### Scenario 2: Execute SQL Query (P2)

**Purpose**: Verify user can execute SELECT queries and view results

#### Step 1: Execute Simple Query

```bash
curl -X POST http://localhost:8000/api/v1/dbs/testdb/query \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT * FROM users"
  }'

# Expected response:
{
  "columns": [
    {"name": "id", "dataType": "integer"},
    {"name": "name", "dataType": "character varying"},
    {"name": "email", "dataType": "character varying"},
    {"name": "status", "dataType": "character varying"},
    {"name": "created_at", "dataType": "timestamp without time zone"}
  ],
  "rows": [
    {
      "id": 1,
      "name": "Alice",
      "email": "alice@example.com",
      "status": "active",
      "created_at": "2025-11-16T10:00:00"
    },
    {
      "id": 2,
      "name": "Bob",
      "email": "bob@example.com",
      "status": "active",
      "created_at": "2025-11-16T10:00:01"
    },
    {
      "id": 3,
      "name": "Charlie",
      "email": "charlie@example.com",
      "status": "inactive",
      "created_at": "2025-11-16T10:00:02"
    }
  ],
  "rowCount": 3,
  "executionTimeMs": 15,
  "sql": "SELECT * FROM users LIMIT 1000"
}
```

#### Step 2: Test SQL Validation (Should Fail)

```bash
# Try to execute INSERT (should be rejected)
curl -X POST http://localhost:8000/api/v1/dbs/testdb/query \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "INSERT INTO users (name, email) VALUES ('\''Hacker'\'', '\''hack@example.com'\'')"
  }'

# Expected response (400 Bad Request):
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Only SELECT statements are allowed",
    "details": {
      "statementType": "INSERT",
      "line": 1,
      "column": 0
    }
  }
}
```

#### Step 3: Test Auto LIMIT

```bash
# Query without LIMIT (should auto-add LIMIT 1000)
curl -X POST http://localhost:8000/api/v1/dbs/testdb/query \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT name, email FROM users WHERE status = '\''active'\''"
  }'

# Expected response:
{
  "columns": [...],
  "rows": [...],
  "rowCount": 2,
  "executionTimeMs": 12,
  "sql": "SELECT name, email FROM users WHERE status = 'active' LIMIT 1000"
}
# Note: sql field shows LIMIT was auto-added
```

#### Step 4: Verify in Frontend

1. Navigate to "Query" page
2. Select "testdb" from database dropdown
3. Enter SQL: `SELECT * FROM users WHERE status = 'active'`
4. Click "Execute" button
5. Verify results appear in table
6. Try entering `DELETE FROM users` and verify error message

**Success Criteria**:

- ✅ Valid SELECT queries execute successfully
- ✅ Results display in table format within 3 seconds
- ✅ Non-SELECT queries are rejected with clear error
- ✅ LIMIT is auto-added when missing

---

### Scenario 3: Natural Language to SQL (P3)

**Purpose**: Verify natural language input generates valid SQL

#### Step 1: Generate SQL from Chinese

```bash
curl -X POST http://localhost:8000/api/v1/dbs/testdb/query/natural \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "查询所有活跃用户的姓名和邮箱"
  }'

# Expected response:
{
  "sql": "SELECT name, email FROM users WHERE status = 'active' LIMIT 1000",
  "explanation": "This query retrieves the name and email of all active users, limited to 1000 rows for safety."
}
```

#### Step 2: Generate SQL from English

```bash
curl -X POST http://localhost:8000/api/v1/dbs/testdb/query/natural \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Show total order amount by user, sorted by amount descending"
  }'

# Expected response:
{
  "sql": "SELECT u.name, SUM(o.total) as total_amount FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.name ORDER BY total_amount DESC LIMIT 1000",
  "explanation": "This query calculates the total order amount for each user and sorts them by amount in descending order."
}
```

#### Step 3: Verify Generated SQL

```bash
# Execute the generated SQL to verify it works
curl -X POST http://localhost:8000/api/v1/dbs/testdb/query \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT u.name, SUM(o.total) as total_amount FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.name ORDER BY total_amount DESC LIMIT 1000"
  }'

# Expected: Valid query results
```

#### Step 4: Verify in Frontend

1. Navigate to "Query" page with Natural Language tab
2. Enter: "显示每个用户的订单数量"
3. Click "Generate SQL"
4. Verify generated SQL appears in SQL editor
5. Click "Execute" to run the query
6. Verify results match expectation

**Success Criteria**:

- ✅ Natural language input generates syntactically valid SQL
- ✅ Generated SQL references actual tables and columns
- ✅ Explanation is clear and helpful
- ✅ User can edit generated SQL before execution

---

### Scenario 4: Query History (Included in P2)

**Purpose**: Verify query history is saved and retrievable

#### Step 1: Execute Multiple Queries

```bash
# Execute 3 different queries
curl -X POST http://localhost:8000/api/v1/dbs/testdb/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM users"}'

curl -X POST http://localhost:8000/api/v1/dbs/testdb/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM orders"}'

curl -X POST http://localhost:8000/api/v1/dbs/testdb/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT COUNT(*) FROM users WHERE status = '\''active'\''"}'
```

#### Step 2: Retrieve History

```bash
curl http://localhost:8000/api/v1/dbs/testdb/history

# Expected response:
{
  "history": [
    {
      "id": 3,
      "databaseName": "testdb",
      "sqlText": "SELECT COUNT(*) FROM users WHERE status = 'active' LIMIT 1000",
      "executedAt": "2025-11-16T10:05:00Z",
      "executionTimeMs": 8,
      "rowCount": 1,
      "success": true,
      "errorMessage": null,
      "querySource": "manual"
    },
    {
      "id": 2,
      "databaseName": "testdb",
      "sqlText": "SELECT * FROM orders LIMIT 1000",
      "executedAt": "2025-11-16T10:04:30Z",
      "executionTimeMs": 12,
      "rowCount": 3,
      "success": true,
      "errorMessage": null,
      "querySource": "manual"
    },
    {
      "id": 1,
      "databaseName": "testdb",
      "sqlText": "SELECT * FROM users LIMIT 1000",
      "executedAt": "2025-11-16T10:04:00Z",
      "executionTimeMs": 15,
      "rowCount": 3,
      "success": true,
      "errorMessage": null,
      "querySource": "manual"
    }
  ]
}
```

#### Step 3: Verify in Frontend

1. Open "Query History" panel
2. Verify last 3 queries are displayed
3. Click on a history entry
4. Verify SQL is loaded into editor
5. Execute to verify it still works

**Success Criteria**:

- ✅ All executed queries are saved to history
- ✅ History shows most recent queries first
- ✅ History includes execution time and row count
- ✅ Failed queries are also recorded with error messages

---

## Testing Checklist

### Backend Unit Tests

```bash
cd w2/db_query/backend

# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test categories
pytest tests/unit/           # Unit tests only
pytest tests/integration/    # Integration tests only
pytest tests/contract/       # Contract tests only

# Run specific test file
pytest tests/unit/test_sql_validator.py -v
```

**Expected Results**:

- ✅ SQL validator tests: 100% pass (critical for security)
- ✅ Overall coverage: >80%
- ✅ All contract tests pass (verifies camelCase format)

### Frontend Tests

```bash
cd w2/db_query/frontend

# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test suite
npm test -- SqlEditor
npm test -- ResultTable
```

### Manual UI Testing

**Database Management**:

- [ ] Can add new database connection
- [ ] Can view database metadata
- [ ] Can edit database connection
- [ ] Can delete database connection
- [ ] Can refresh metadata manually

**SQL Execution**:

- [ ] SQL editor provides syntax highlighting
- [ ] Autocomplete suggests table/column names
- [ ] Execute button runs query
- [ ] Results display in table
- [ ] Error messages are clear
- [ ] Query execution can be cancelled

**Natural Language**:

- [ ] Natural language input accepts Chinese and English
- [ ] Generate SQL button works
- [ ] Generated SQL appears in editor
- [ ] User can edit generated SQL
- [ ] Execute generated SQL works

**Query History**:

- [ ] History panel shows recent queries
- [ ] Click history entry loads SQL into editor
- [ ] History shows success/failure status
- [ ] History shows execution time

---

## Troubleshooting

### Backend Issues

**Problem**: `ModuleNotFoundError: No module named 'app'`

```bash
# Solution: Make sure you're in the right directory and venv is activated
cd w2/db_query/backend
source .venv/bin/activate
uv pip install -e ".[dev]"
```

**Problem**: `sqlalchemy.exc.OperationalError: unable to open database file`

```bash
# Solution: Create data directory
mkdir -p ~/.db_query
chmod 755 ~/.db_query
```

**Problem**: `openai.error.AuthenticationError`

```bash
# Solution: Set OPENAI_API_KEY environment variable
export OPENAI_API_KEY=sk-your-key-here
# Or add to .env file
```

### Frontend Issues

**Problem**: `Network Error` when calling API

```bash
# Solution: Verify backend is running and CORS is enabled
curl http://localhost:8000/health

# Check backend logs for CORS errors
# Verify VITE_API_BASE_URL in .env.local is correct
```

**Problem**: Monaco Editor not loading

```bash
# Solution: Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Database Connection Issues

**Problem**: `connection refused` when adding PostgreSQL database

```bash
# Solution: Verify PostgreSQL is running
pg_isready -h localhost -p 5432

# Check PostgreSQL is accepting connections
psql -h localhost -U postgres -c "SELECT 1"
```

**Problem**: `authentication failed`

```bash
# Solution: Verify username and password in connection URL
# Check pg_hba.conf allows password authentication
```

---

## API Documentation

Once backend is running, access interactive API documentation:

- **Swagger UI**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>
- **OpenAPI JSON**: <http://localhost:8000/openapi.json>

These provide:

- Interactive API testing
- Request/response schemas
- Example requests
- Error codes and descriptions

---

## Next Steps

After completing the quick start:

1. **Run `/speckit.tasks`**: Generate detailed implementation tasks
2. **Review `contracts/api-v1.yaml`**: Understand API specifications
3. **Read `data-model.md`**: Understand data structures
4. **Follow `research.md`**: Understand technology decisions

---

## Success Criteria Summary

✅ **Setup Complete** when:

- Backend starts without errors on port 8000
- Frontend starts without errors on port 5173
- Can access API documentation at /docs
- Test database is seeded with sample data

✅ **Integration Ready** when:

- All 4 scenarios pass successfully
- Unit tests achieve >80% coverage
- Contract tests verify camelCase format
- UI manual testing checklist is complete

✅ **Production Ready** when:

- All functional requirements (FR-001 to FR-016) are implemented
- All success criteria (SC-001 to SC-010) are met
- Security validation (SQL injection prevention) is verified
- Performance benchmarks are achieved

---

**Document Status**: Complete and ready for implementation phase.
