# Implementation Plan: 数据库查询工具

**Branch**: `001-db-query-tool` | **Date**: 2025-11-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-db-query-tool/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

构建一个数据库查询工具，允许用户添加PostgreSQL数据库连接，查看数据库元数据，执行SQL查询（仅SELECT），并通过自然语言生成SQL。系统使用FastAPI后端和React+Refine前端，数据存储在本地SQLite数据库中，支持查询结果导出。

技术方案：

- 后端：Python 3.12+ with FastAPI, sqlglot for SQL parsing, OpenAI SDK for NL2SQL
- 前端：React 18 with TypeScript, Refine 5, Ant Design, Monaco Editor for SQL editing
- 存储：SQLite (本地) for connections/metadata, PostgreSQL (remote) for querying
- 安全：sqlglot验证SQL，仅允许SELECT，自动添加LIMIT 1000

## Technical Context

**Language/Version**:

- Backend: Python 3.12+
- Frontend: TypeScript 5.0+ (React 19+)

**Primary Dependencies**:

- Backend: FastAPI 0.104+, Pydantic v2, sqlglot, OpenAI SDK, asyncpg (PostgreSQL driver), SQLAlchemy/SQLModel (SQLite ORM)
- Frontend: React 19, Refine 5, Ant Design 5, Monaco Editor, Tailwind CSS 4, Vite

**Storage**:

- Local: SQLite (~/.db_query/db_query.db) for database connections and metadata cache
- Remote: PostgreSQL (user-provided) for query execution

**Testing**:

- Backend: pytest, pytest-asyncio, httpx (for FastAPI testing)
- Frontend: Vitest, React Testing Library

**Target Platform**:

- Backend: Cross-platform (Linux/macOS/Windows), runs as local web server
- Frontend: Modern browsers (Chrome, Firefox, Safari, Edge)

**Project Type**: Web application (frontend + backend)

**Performance Goals**:

- Metadata fetch: <5 seconds for typical database (100 tables)
- Query execution: <3 seconds for simple SELECT with <1000 rows
- Natural language to SQL: <10 seconds (LLM API call)
- UI responsiveness: <100ms for user interactions

**Constraints**:

- No authentication required (local tool)
- SQL safety: Only SELECT statements allowed
- Result set limit: Auto-apply LIMIT 1000 if not specified
- Local storage: All connections stored in ~/.db_query/
- CORS: Backend must allow all origins for local development

**Scale/Scope**:

- Support: 5-10 concurrent database connections
- Metadata cache: Up to 1000 tables per database
- Query history: Store last 50 queries
- Result display: Handle up to 10,000 rows in UI (with pagination)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ I. Ergonomic Python with Strict Typing

- **Compliance**: All backend code will use Python 3.12+ with full type annotations
- **Implementation**: Use `typing` module, type hints on all functions/methods/classes
- **Validation**: mypy type checking in CI/CD

### ✅ II. Pydantic for Data Models

- **Compliance**: All API models and configuration use Pydantic BaseModel
- **Implementation**:
  - Request/Response models: Pydantic BaseModel
  - Database models: SQLModel (Pydantic + SQLAlchemy)
  - Config: Pydantic Settings
- **Validation**: Automatic via Pydantic validators

### ✅ III. camelCase JSON API Convention

- **Compliance**: All API responses use camelCase field names
- **Implementation**: Configure Pydantic `alias_generator=to_camel` globally
- **Validation**: API contract tests verify camelCase format

### ✅ IV. TypeScript with Strict Type Safety

- **Compliance**: All frontend code uses TypeScript with `strict: true`
- **Implementation**:
  - tsconfig.json with strict mode enabled
  - Define interfaces for all API responses
  - No `any` types without justification
- **Validation**: TypeScript compiler in strict mode

### ✅ V. No Authentication Required

- **Compliance**: No user authentication or authorization
- **Implementation**: All endpoints publicly accessible, connections stored locally
- **Note**: Production deployment should use network-level access control

### ✅ VI. SQL Safety and Query Validation

- **Compliance**: Strict SQL validation using sqlglot
- **Implementation**:
  - Parse SQL with sqlglot before execution
  - Block all non-SELECT statements
  - Auto-add LIMIT 1000 if missing
  - Return detailed parse errors
- **Validation**: Comprehensive test suite for SQL validation logic

### ✅ VII. Test-Driven Development (Recommended)

- **Compliance**: Key features have test coverage
- **Implementation**:
  - SQL validation: Unit tests (>95% coverage)
  - API endpoints: Integration tests
  - Data models: Serialization tests
  - Frontend: Component tests for critical flows
- **Validation**: pytest coverage >80% for backend critical paths

### Constitution Compliance Summary

✅ **All principles satisfied** - No violations or justifications required.

## Project Structure

### Documentation (this feature)

```text
specs/001-db-query-tool/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── api-v1.yaml      # OpenAPI specification
├── checklists/
│   └── requirements.md  # Already created
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
w2/db_query/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application entry
│   │   ├── config.py            # Pydantic Settings configuration
│   │   ├── models/              # Pydantic models & SQLModel entities
│   │   │   ├── __init__.py
│   │   │   ├── database.py      # DatabaseConnection entity
│   │   │   ├── metadata.py      # DatabaseMetadata entity
│   │   │   ├── query.py         # QueryHistory entity
│   │   │   └── schemas.py       # Request/Response Pydantic models
│   │   ├── services/            # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── db_connection.py # Database connection management
│   │   │   ├── metadata.py      # Metadata extraction service
│   │   │   ├── query.py         # Query execution service
│   │   │   ├── sql_validator.py # SQL parsing & validation (sqlglot)
│   │   │   └── nl2sql.py        # Natural language to SQL (OpenAI)
│   │   ├── api/                 # FastAPI routers
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── databases.py # /api/v1/dbs endpoints
│   │   │   │   └── queries.py   # /api/v1/dbs/{name}/query endpoints
│   │   ├── database.py          # SQLite database setup
│   │   └── dependencies.py      # FastAPI dependencies
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py          # pytest fixtures
│   │   ├── unit/
│   │   │   ├── test_sql_validator.py
│   │   │   ├── test_metadata.py
│   │   │   └── test_models.py
│   │   ├── integration/
│   │   │   ├── test_api_databases.py
│   │   │   └── test_api_queries.py
│   │   └── contract/
│   │       └── test_api_contracts.py
│   ├── pyproject.toml           # uv dependencies & project config
│   ├── README.md
│   └── .python-version          # Python 3.12
│
└── frontend/
    ├── src/
    │   ├── App.tsx              # Main application component
    │   ├── main.tsx             # Vite entry point
    │   ├── types/               # TypeScript type definitions
    │   │   ├── database.ts      # Database connection types
    │   │   ├── metadata.ts      # Metadata types
    │   │   ├── query.ts         # Query & result types
    │   │   └── api.ts           # API response types
    │   ├── services/            # API client & data providers
    │   │   ├── api.ts           # Axios instance & interceptors
    │   │   └── dataProvider.ts  # Refine data provider
    │   ├── pages/               # Refine resource pages
    │   │   ├── databases/
    │   │   │   ├── list.tsx     # Database list view
    │   │   │   ├── create.tsx   # Add new database
    │   │   │   ├── show.tsx     # Database metadata view
    │   │   │   └── edit.tsx     # Edit database connection
    │   │   └── queries/
    │   │       └── execute.tsx  # Query execution page
    │   ├── components/          # Reusable React components
    │   │   ├── SqlEditor.tsx    # Monaco-based SQL editor
    │   │   ├── ResultTable.tsx  # Query result display
    │   │   ├── MetadataTree.tsx # Database schema tree
    │   │   └── NaturalLanguageInput.tsx
    │   ├── hooks/               # Custom React hooks
    │   │   ├── useQueryExecution.ts
    │   │   └── useMetadata.ts
    │   └── styles/
    │       └── index.css        # Tailwind imports
    ├── public/
    ├── package.json
    ├── tsconfig.json            # Strict TypeScript config
    ├── vite.config.ts
    ├── tailwind.config.js
    └── README.md
```

**Structure Decision**: Web application structure (Option 2) selected because this is a full-stack application with distinct frontend (React SPA) and backend (FastAPI REST API) components. The backend serves as a REST API server, and the frontend is a standalone SPA that communicates via HTTP. This separation enables independent development, testing, and potential future deployment strategies.

The project is located at `w2/db_query/` to align with the course week structure.

## Complexity Tracking

No constitution violations. All principles are satisfied with standard patterns and technologies.
