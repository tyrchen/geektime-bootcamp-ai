# Research Document: 数据库查询工具

**Feature**: 001-db-query-tool
**Date**: 2025-11-16
**Phase**: 0 - Technology Research & Decisions

## Overview

本文档记录了数据库查询工具实现过程中的技术选型、最佳实践研究和设计决策。所有决策都基于项目宪法的原则和功能需求。

## Technology Stack Decisions

### Backend Framework: FastAPI

**Decision**: 使用 FastAPI 作为后端 Web 框架

**Rationale**:
- **自动化文档**: 自动生成 OpenAPI (Swagger) 文档，方便 API 测试和前端集成
- **Pydantic 集成**: 深度集成 Pydantic，自动进行请求/响应验证和序列化
- **性能优秀**: 基于 Starlette 和 Pydantic，性能接近 Node.js 和 Go
- **类型安全**: 完全支持 Python 类型提示，配合 mypy 实现编译时类型检查
- **异步支持**: 原生支持 async/await，适合 I/O 密集型操作（数据库查询）
- **成熟生态**: 丰富的中间件、依赖注入系统和测试工具

**Alternatives Considered**:
- **Flask**: 更简单但缺乏自动文档和类型验证，需要更多手动配置
- **Django**: 过于重量级，自带 ORM 和认证系统与需求不符
- **Starlette**: FastAPI 基于 Starlette，直接使用 FastAPI 获得更多开箱即用特性

### SQL Parser: sqlglot

**Decision**: 使用 sqlglot 进行 SQL 解析和验证

**Rationale**:
- **纯 Python 实现**: 无需额外系统依赖，易于安装和分发
- **多方言支持**: 支持 PostgreSQL、MySQL 等多种 SQL 方言
- **AST 解析**: 提供完整的抽象语法树，可以精确分析 SQL 语句结构
- **类型安全**: 可以识别 SELECT/INSERT/UPDATE/DELETE 等语句类型
- **SQL 转换**: 支持 SQL 重写（如自动添加 LIMIT 子句）
- **性能良好**: 对于单条查询解析速度 <10ms

**Alternatives Considered**:
- **sqlparse**: 功能较弱，只能做基本的格式化和 tokenization，无法深度分析语句类型
- **pglast (libpg_query)**: 使用 PostgreSQL 官方解析器，但依赖 C 库，安装复杂，且仅支持 PostgreSQL
- **手动正则表达式**: 不可靠，容易被绕过，维护困难

### PostgreSQL Driver: asyncpg

**Decision**: 使用 asyncpg 作为 PostgreSQL 数据库驱动

**Rationale**:
- **异步 I/O**: 原生支持 asyncio，与 FastAPI 异步模型完美配合
- **高性能**: 比 psycopg2/3 快 2-3 倍，使用 Cython 优化
- **类型转换**: 自动处理 PostgreSQL 类型到 Python 类型的转换
- **连接池**: 内置连接池管理，避免频繁建立连接
- **元数据查询**: 支持查询 PostgreSQL 系统表获取 schema 信息

**Alternatives Considered**:
- **psycopg3**: 支持同步和异步，但性能不如 asyncpg，且异步模式较新
- **SQLAlchemy**: ORM 层过重，不需要完整的 ORM 功能，只需执行原始 SQL

### Local Database: SQLite with SQLModel

**Decision**: 使用 SQLite + SQLModel 管理本地数据

**Rationale**:
- **零配置**: SQLite 无需安装和配置，文件即数据库
- **轻量级**: 适合存储少量元数据和连接信息
- **SQLModel 优势**:
  - 基于 Pydantic 和 SQLAlchemy，同时获得类型验证和 ORM 功能
  - 代码更简洁，一个类同时定义 Pydantic 模型和数据库表
  - 自动生成迁移（通过 Alembic）
- **本地存储**: ~/.db_query/db_query.db，用户数据不离开本地机器

**Alternatives Considered**:
- **纯 SQLAlchemy**: 需要分别定义 ORM 模型和 Pydantic 模型，代码冗余
- **JSON 文件**: 缺乏查询能力，数据完整性难以保证
- **Redis**: 过度设计，不需要缓存服务器

### LLM Integration: OpenAI SDK

**Decision**: 使用官方 OpenAI Python SDK 进行自然语言转 SQL

**Rationale**:
- **官方支持**: OpenAI 官方维护，API 稳定可靠
- **异步支持**: 支持 async/await，与 FastAPI 无缝集成
- **流式响应**: 支持 streaming，可以实时返回 LLM 生成的 SQL（未来功能）
- **简单易用**: API 设计清晰，文档完善
- **提示工程**: 可以灵活设计 system prompt 和 user prompt，注入元数据上下文

**Implementation Strategy**:
```python
# Prompt template structure
system_prompt = """
You are a SQL expert. Generate PostgreSQL SELECT queries based on natural language.

Database schema:
{metadata_json}

Rules:
- ONLY generate SELECT statements
- Include column names explicitly (no SELECT *)
- Add appropriate WHERE, ORDER BY, LIMIT clauses
- Return valid PostgreSQL syntax
"""

user_prompt = "User query: {natural_language_input}"
```

**Alternatives Considered**:
- **Langchain**: 过于重量级，包含大量不需要的功能（chains, agents）
- **本地 LLM (Ollama)**: 准确率不如 GPT-4，且需要用户安装额外软件
- **Fine-tuned model**: 成本高，数据准备复杂，OpenAI API 已足够准确

## Frontend Technology Decisions

### React Admin Framework: Refine

**Decision**: 使用 Refine 5 作为 React admin 框架

**Rationale**:
- **开箱即用**: 提供 CRUD 操作的完整脚手架，减少重复代码
- **Data Provider 模式**: 抽象数据层，易于切换后端或添加缓存
- **UI 框架无关**: 可以自由选择 UI 库（Ant Design, Material-UI, Chakra UI）
- **TypeScript 友好**: 完整的类型定义，提供良好的开发体验
- **路由集成**: 与 React Router 深度集成，自动生成 CRUD 路由
- **钩子系统**: 提供丰富的 hooks（useTable, useForm, useShow 等）处理常见场景

**Alternatives Considered**:
- **React Admin**: 功能类似但更固定，定制化难度更高
- **自行构建**: 需要从头实现 CRUD 逻辑、路由、状态管理等，开发时间长

### UI Library: Ant Design

**Decision**: 使用 Ant Design 5 作为 UI 组件库

**Rationale**:
- **Refine 集成**: Refine 对 Ant Design 有一流支持，提供预构建的 Refine-Ant Design 组件
- **企业级**: 组件质量高，适合数据密集型应用
- **Table 组件**: 强大的 Table 组件，支持排序、过滤、分页，完美适配查询结果展示
- **Form 组件**: 丰富的表单组件，适合数据库连接表单
- **中文友好**: 官方中文文档和社区支持

**Alternatives Considered**:
- **Material-UI**: 设计风格偏移动端，不如 Ant Design 适合数据展示
- **Chakra UI**: 组件较简单，缺少复杂的 Table 和 Form 场景支持

### Code Editor: Monaco Editor

**Decision**: 使用 Monaco Editor 作为 SQL 编辑器

**Rationale**:
- **VSCode 引擎**: 与 VSCode 使用相同的编辑器，功能强大
- **语法高亮**: 内置 SQL 语法高亮
- **智能提示**: 可以配置自定义的自动补全（表名、列名）
- **多光标**: 支持多光标编辑、查找替换等高级功能
- **主题支持**: 支持亮色/暗色主题
- **React 集成**: @monaco-editor/react 提供良好的 React 封装

**Alternatives Considered**:
- **CodeMirror**: 更轻量但功能较弱，定制化复杂度高
- **Ace Editor**: 较老旧，社区活跃度低
- **Textarea**: 无法满足语法高亮和自动补全需求

### Build Tool: Vite

**Decision**: 使用 Vite 作为构建工具

**Rationale**:
- **极速开发**: HMR (热模块替换) 速度极快，开发体验好
- **原生 ES Modules**: 利用浏览器原生 ESM，无需打包即可开发
- **TypeScript 支持**: 开箱即用的 TypeScript 支持
- **插件生态**: 丰富的插件系统，React 官方推荐
- **生产构建**: 使用 Rollup 进行优化的生产构建

**Alternatives Considered**:
- **Create React App**: 已过时，构建速度慢，配置不灵活
- **Webpack**: 配置复杂，开发体验不如 Vite

## Architecture Patterns

### Backend Architecture

**Pattern**: Layered Architecture (三层架构)

```
API Layer (FastAPI routers)
    ↓ 调用
Service Layer (Business logic)
    ↓ 调用
Data Layer (SQLModel, asyncpg)
```

**Layers**:

1. **API Layer** (`app/api/v1/`):
   - FastAPI 路由定义
   - 请求验证（Pydantic models）
   - 响应格式化
   - 错误处理

2. **Service Layer** (`app/services/`):
   - 业务逻辑
   - SQL 验证和转换
   - 元数据提取
   - LLM 调用
   - 事务管理

3. **Data Layer** (`app/models/` + `app/database.py`):
   - SQLModel 实体定义
   - 数据库连接管理
   - CRUD 操作

**Benefits**:
- 关注点分离
- 易于测试（可以 mock 任何层）
- 业务逻辑独立于框架

### SQL Validation Strategy

**Strategy**: Parse → Validate → Transform

**Flow**:
```python
1. Parse SQL using sqlglot
   ↓
2. Check statement type (must be SELECT)
   ↓
3. Extract components (FROM, WHERE, LIMIT)
   ↓
4. Transform: Add LIMIT if missing
   ↓
5. Generate modified SQL
   ↓
6. Execute against target database
```

**Security Checks**:
- ✅ Block INSERT/UPDATE/DELETE/DROP/ALTER/CREATE
- ✅ Block multi-statement (SQL injection via `;`)
- ✅ Block dangerous functions (pg_read_file, COPY)
- ✅ Enforce LIMIT clause
- ✅ Timeout mechanism (max 30s query time)

### Metadata Caching Strategy

**Strategy**: Database → Extract → Transform → Cache

**Flow**:
```python
1. Connect to PostgreSQL
   ↓
2. Query system tables:
   - pg_catalog.pg_tables
   - information_schema.columns
   - pg_constraint (for PKs/FKs)
   ↓
3. Transform to JSON structure
   ↓
4. Use LLM to generate summary (optional)
   ↓
5. Store in SQLite with timestamp
   ↓
6. Return cached data for subsequent requests
```

**Cache Invalidation**:
- Manual refresh button in UI
- Auto-refresh after 24 hours
- Invalidate on connection error (stale cache)

### Error Handling Strategy

**Pattern**: Exception Hierarchy

```python
# Custom exceptions
class DBQueryError(Exception):
    """Base exception"""
    pass

class ConnectionError(DBQueryError):
    """Database connection failed"""
    pass

class ValidationError(DBQueryError):
    """SQL validation failed"""
    pass

class QueryExecutionError(DBQueryError):
    """Query execution failed"""
    pass
```

**Error Response Format** (camelCase per constitution):
```json
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

## API Design

### RESTful Principles

**Resource-based URLs**:
- `/api/v1/dbs` - Database collection
- `/api/v1/dbs/{name}` - Single database
- `/api/v1/dbs/{name}/query` - Query execution (sub-resource)

**HTTP Methods Mapping**:
- `GET /api/v1/dbs` - List all databases
- `PUT /api/v1/dbs/{name}` - Create/Update database (idempotent)
- `GET /api/v1/dbs/{name}` - Get database metadata
- `DELETE /api/v1/dbs/{name}` - Delete database connection
- `POST /api/v1/dbs/{name}/query` - Execute SQL query
- `POST /api/v1/dbs/{name}/query/natural` - Natural language query

**Rationale for PUT vs POST**:
- 使用 `PUT /api/v1/dbs/{name}` 而不是 `POST /api/v1/dbs` 因为：
  - 客户端指定资源名称（数据库名）
  - 幂等性：多次 PUT 相同名称不会创建重复资源
  - 符合 REST 最佳实践

### CORS Configuration

**Decision**: Allow all origins

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Rationale**:
- 本地工具，前端和后端运行在不同端口
- 无认证需求，无安全风险
- 简化开发，无需配置特定 origins

## Testing Strategy

### Backend Testing Layers

1. **Unit Tests** (`tests/unit/`):
   - SQL validator logic
   - Metadata extraction
   - Pydantic model serialization
   - Coverage target: >90%

2. **Integration Tests** (`tests/integration/`):
   - API endpoints with test database
   - Database connection flow
   - Query execution flow
   - Coverage target: >80%

3. **Contract Tests** (`tests/contract/`):
   - API response format validation
   - camelCase field name verification
   - Error response structure

### Frontend Testing Strategy

1. **Component Tests**:
   - SqlEditor component
   - ResultTable component
   - MetadataTree component

2. **Integration Tests**:
   - Full query execution flow
   - Database connection form
   - Natural language input

3. **Type Safety**:
   - TypeScript compiler as first line of defense
   - Runtime validation for API responses

### Test Data

**Mock PostgreSQL Database**:
```sql
-- Test database schema
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    total DECIMAL(10, 2),
    status VARCHAR(20)
);
```

## Performance Optimizations

### Backend

1. **Connection Pooling**:
   - asyncpg connection pool (min=2, max=10)
   - SQLite connection pool (singleton)

2. **Metadata Caching**:
   - Cache in SQLite to avoid repeated system table queries
   - In-memory cache (LRU) for frequently accessed metadata

3. **Query Timeout**:
   - Set statement_timeout in PostgreSQL session
   - Prevent long-running queries from blocking

### Frontend

1. **Code Splitting**:
   - Lazy load Monaco Editor (large bundle)
   - Lazy load query result pages

2. **Virtual Scrolling**:
   - Use Ant Design Table's virtual scrolling for large result sets

3. **Debouncing**:
   - Debounce natural language input (500ms)
   - Debounce SQL editor autocomplete (300ms)

## Security Considerations

### SQL Injection Prevention

1. **sqlglot Parsing**: Reject malformed SQL
2. **Statement Type Check**: Only SELECT allowed
3. **Function Blacklist**: Block dangerous functions
4. **No Dynamic SQL**: Use parameterized queries for internal SQLite

### Data Privacy

1. **Local Storage**: All data stored in ~/.db_query/
2. **No Telemetry**: No data sent to external services except OpenAI API
3. **API Key Security**: OPENAI_API_KEY from environment variable, never logged

### Environment Configuration

**Environment Variables**:
```bash
OPENAI_API_KEY=sk-...           # OpenAI API key
DB_QUERY_DATA_DIR=~/.db_query  # Optional: custom data directory
LOG_LEVEL=INFO                  # Logging level
```

## Development Workflow

### Backend Setup

```bash
cd w2/db_query/backend

# Install uv if not installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv pip install -e ".[dev]"

# Run tests
pytest

# Run server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd w2/db_query/frontend

# Install dependencies
npm install  # or yarn install

# Run dev server
npm run dev  # defaults to port 5173

# Run tests
npm test

# Build for production
npm run build
```

## Deployment Considerations

虽然当前是开发工具，但考虑未来可能的部署需求：

### Local Tool Mode (Current)
- Backend: `uvicorn app.main:app --host 127.0.0.1 --port 8000`
- Frontend: `npm run preview` or serve `dist/` folder
- Access: http://localhost:5173

### Packaged Application (Future)
- 使用 PyInstaller 打包后端为独立可执行文件
- 使用 Electron 或 Tauri 打包前端
- 一键启动，无需安装 Python 或 Node.js

### Server Deployment (Future)
- Backend: Docker container with uvicorn
- Frontend: Static files served by Nginx
- Add authentication layer (OAuth2)
- PostgreSQL for user data instead of SQLite

## Risk Mitigation

### Risk: LLM API Failure
- **Mitigation**: Graceful degradation, show error message, fallback to manual SQL

### Risk: Large Result Sets
- **Mitigation**: Enforce LIMIT 1000, pagination, export to file option

### Risk: Database Connection Leaks
- **Mitigation**: Connection pool with timeout, connection health checks

### Risk: SQL Parser Bugs
- **Mitigation**: Comprehensive test suite, additional regex checks for critical patterns

## Documentation Requirements

### API Documentation
- ✅ Auto-generated OpenAPI docs via FastAPI (http://localhost:8000/docs)

### User Documentation
- README.md with setup instructions
- Quick start guide in quickstart.md

### Code Documentation
- ✅ Python: Docstrings for all public functions/classes
- ✅ TypeScript: JSDoc comments for complex logic
- ✅ Type annotations serve as inline documentation

## Conclusion

所有技术选型都基于以下原则：
- ✅ 符合项目宪法要求（类型安全、Pydantic、camelCase）
- ✅ 成熟稳定的技术栈
- ✅ 良好的开发体验
- ✅ 适合项目规模（中小型工具）
- ✅ 易于测试和维护

无需进一步研究，可以直接进入 Phase 1 设计阶段。
