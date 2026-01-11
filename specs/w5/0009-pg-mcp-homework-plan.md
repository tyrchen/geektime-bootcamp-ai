# PostgreSQL MCP Server - Homework Plan (Gap Resolution)

## Document Information

| Item | Content |
|------|---------|
| Document Version | v1.0 |
| Creation Date | 2026-01-11 |
| Status | Draft |
| Related Documents | 0002-pg-mcp-design.md, 0004-pg-mcp-impl-plan.md, 0006-pg-mcp-code-review.md |
| Project Code | pg-mcp-homework |

---

## 1. Executive Summary

This plan addresses the four major gaps identified in the code review:

1. **Multi-database support** - Not implemented despite design specs
2. **Security controls** - Configuration exists but not wired up
3. **Resilience & Observability** - Modules exist but not integrated
4. **Testing** - Heavy reliance on external services; needs mocks

Each section provides a detailed action plan with concrete implementation steps, acceptance criteria, and testing requirements.

---

## 2. Gap 1: Multi-Database Support

### 2.1 Current State

**Problems**:
- `Settings` only supports single `DatabaseConfig` object instead of a list
- Always uses a single executor bound to default pool
- `_resolve_database` returns different DB name but execution ignores it
- `create_pools` function exists but is unused
- Cross-database data leakage risk

**Impact**: Cannot support multiple databases as designed; security vulnerability where requests specifying DB "B" still run on DB "A"

### 2.2 Solution Design

**Core Changes**:

```python
# config/settings.py - BEFORE
class Settings(BaseSettings):
    database: DatabaseConfig = Field(...)
    # ...

# config/settings.py - AFTER
class Settings(BaseSettings):
    databases: list[DatabaseConfig] = Field(default_factory=list)
    
    @field_validator("databases")
    @classmethod
    def validate_databases(cls, v: list[DatabaseConfig]) -> list[DatabaseConfig]:
        if not v:
            raise ValueError("At least one database must be configured")
        names = [db.name for db in v]
        if len(names) != len(set(names)):
            raise ValueError("Database names must be unique")
        return v
```

```python
# server.py - BEFORE
pools = {db_config.name: pool}
executor = SQLExecutor(pool, ...)

# server.py - AFTER
pools = await create_pools(settings.databases)  # Use the function
executors = {
    db_name: SQLExecutor(pool, settings.security, db_config, metrics)
    for db_name, pool in pools.items()
    for db_config in settings.databases if db_config.name == db_name
}
```

```python
# services/orchestrator.py - BEFORE
executor = self.executors.get(db_name)  # Always returns same executor

# services/orchestrator.py - AFTER
executor = self.executors.get(db_name)
if not executor:
    raise PgMcpError(
        code=ErrorCode.DB_CONNECTION_ERROR,
        message=f"Database '{db_name}' connection not available",
    )
```

### 2.3 Implementation Tasks

| ID | Task | Files | Priority |
|----|------|-------|----------|
| M1.1 | Change `Settings.database` to `Settings.databases` list | `config/settings.py` | P0 |
| M1.2 | Add database name uniqueness validator | `config/settings.py` | P0 |
| M1.3 | Update `.env.example` with multi-DB configuration examples | `.env.example` | P1 |
| M1.4 | Use `create_pools` in server initialization | `server.py` | P0 |
| M1.5 | Build per-database executor dict | `server.py` | P0 |
| M1.6 | Fix `_resolve_database` to raise error when DB not found | `services/orchestrator.py` | P0 |
| M1.7 | Ensure orchestrator selects correct executor | `services/orchestrator.py` | P0 |
| M1.8 | Update `schema_cache.load()` calls for each database | `server.py` | P1 |
| M1.9 | Add multi-database integration tests | `tests/integration/test_multi_db.py` | P1 |
| M1.10 | Update README with multi-DB configuration guide | `README.md` | P2 |

### 2.4 Acceptance Criteria

- [ ] `Settings` accepts list of databases via environment variables
- [ ] Server initializes one connection pool per database
- [ ] Schema cache loaded independently for each database
- [ ] Query orchestrator routes to correct executor based on `database` parameter
- [ ] Error returned if non-existent database requested
- [ ] Auto-selection works when only one database configured
- [ ] Multi-database integration test passes

### 2.5 Testing Requirements

```python
# tests/integration/test_multi_db.py

async def test_multi_database_routing():
    """Verify queries route to correct database"""
    # Setup: Configure 3 databases (blog_small, ecommerce_medium, saas_crm_large)
    # Action 1: Query blog_small for posts
    # Verify: Results only from blog_small
    # Action 2: Query ecommerce_medium for orders
    # Verify: Results only from ecommerce_medium
    # Action 3: Query without specifying DB (should fail with BAD_REQUEST)
    # Verify: Error code matches

async def test_database_not_found():
    """Verify error when requesting non-existent database"""
    # Action: Request query for database "nonexistent"
    # Verify: ErrorCode.SCHEMA_NOT_FOUND returned

async def test_single_database_auto_selection():
    """Verify auto-selection when only one database configured"""
    # Setup: Configure only blog_small
    # Action: Query without specifying database
    # Verify: Query succeeds against blog_small
```

---

## 3. Gap 2: Security Controls Not Wired Up

### 3.1 Current State

**Problems**:
- `SecurityConfig` missing `blocked_tables`, `blocked_columns`, `allow_explain` fields
- `SQLValidator` instantiated with `None` for these fields
- `ValidationConfig.max_question_length` never enforced
- No input size protection against cost amplification
- Sensitive resource protection cannot be configured

**Impact**: Cannot prevent access to sensitive tables/columns beyond built-in blacklist; no protection against excessive prompt costs

### 3.2 Solution Design

**Configuration Updates**:

```python
# config/settings.py
class SecurityConfig(BaseSettings):
    query_timeout_seconds: int = Field(default=30, ge=1, le=300)
    max_result_rows: int = Field(default=10000, ge=1, le=100000)
    
    # ADD THESE FIELDS:
    blocked_tables: list[str] = Field(
        default_factory=list,
        description="List of table names (or schema.table) that cannot be accessed"
    )
    blocked_columns: list[str] = Field(
        default_factory=list,
        description="List of column names (or table.column) that cannot be accessed"
    )
    blocked_functions: list[str] = Field(
        default_factory=lambda: [
            "pg_sleep", "pg_terminate_backend", "pg_cancel_backend",
            "pg_reload_conf", "pg_rotate_logfile", "lo_import", "lo_export"
        ],
        description="List of SQL functions that cannot be called"
    )
    allow_explain: bool = Field(
        default=False,
        description="Whether to allow EXPLAIN queries"
    )
    readonly_role: str | None = Field(
        default=None,
        description="PostgreSQL role to switch to for read-only access"
    )
    safe_search_path: str = Field(
        default="public",
        description="Safe search_path to set in query session"
    )

class ValidationConfig(BaseSettings):
    enabled: bool = Field(default=True)
    confidence_threshold: int = Field(default=70, ge=0, le=100)
    max_retries: int = Field(default=2, ge=0, le=5)
    timeout_seconds: float = Field(default=10.0, ge=1.0)
    sample_rows: int = Field(default=10, ge=1, le=100)
    
    # ADD THIS FIELD:
    max_question_length: int = Field(
        default=5000,
        ge=100,
        le=50000,
        description="Maximum allowed question length in characters"
    )
```

**Validator Integration**:

```python
# server.py - BEFORE
sql_validator = SQLValidator(settings.security)

# server.py - AFTER
sql_validator = SQLValidator(
    config=settings.security
)  # Now security config has all required fields
```

**Input Validation**:

```python
# services/orchestrator.py
async def execute_query(self, request: QueryRequest) -> QueryResponse:
    request_id = f"req_{uuid.uuid4().hex[:12]}"
    
    # ADD THIS CHECK:
    if len(request.question) > self.settings.validation.max_question_length:
        return QueryResponse(
            success=False,
            error=ErrorDetail(
                code=ErrorCode.BAD_REQUEST,
                message=f"Question exceeds maximum length of {self.settings.validation.max_question_length} characters",
                details=f"Question length: {len(request.question)}",
            ),
            request_id=request_id,
        )
    
    # ... rest of implementation
```

### 3.3 Implementation Tasks

| ID | Task | Files | Priority |
|----|------|-------|----------|
| S2.1 | Add security fields to `SecurityConfig` | `config/settings.py` | P0 |
| S2.2 | Add `max_question_length` to `ValidationConfig` | `config/settings.py` | P0 |
| S2.3 | Ensure `SQLValidator` receives complete config | `server.py`, `services/sql_validator.py` | P0 |
| S2.4 | Add question length validation in orchestrator | `services/orchestrator.py` | P0 |
| S2.5 | Add confidence threshold enforcement | `services/orchestrator.py` | P1 |
| S2.6 | Update `.env.example` with security configuration | `.env.example` | P1 |
| S2.7 | Add security config unit tests | `tests/unit/test_config.py` | P1 |
| S2.8 | Add security validation integration tests | `tests/integration/test_security.py` | P1 |
| S2.9 | Document security configuration in README | `README.md` | P2 |

### 3.4 Acceptance Criteria

- [ ] `SecurityConfig` has all fields from design spec (blocked_tables, blocked_columns, allow_explain, etc.)
- [ ] `SQLValidator` receives and enforces blocked tables/columns configuration
- [ ] Queries accessing blocked tables/columns are rejected with security violation error
- [ ] Questions exceeding `max_question_length` are rejected before LLM call
- [ ] EXPLAIN queries rejected when `allow_explain=false`
- [ ] EXPLAIN queries allowed when `allow_explain=true`
- [ ] Confidence threshold properly enforced based on configuration
- [ ] All security tests pass

### 3.5 Testing Requirements

```python
# tests/unit/test_config.py

def test_security_config_blocked_resources():
    """Verify blocked_tables and blocked_columns configuration"""
    config = SecurityConfig(
        blocked_tables=["users", "public.secrets"],
        blocked_columns=["password", "users.ssn"]
    )
    assert "users" in config.blocked_tables
    assert "password" in config.blocked_columns

def test_validation_config_max_question_length():
    """Verify max_question_length configuration and bounds"""
    config = ValidationConfig(max_question_length=1000)
    assert config.max_question_length == 1000
    
    # Test bounds
    with pytest.raises(ValidationError):
        ValidationConfig(max_question_length=50)  # Too small

# tests/integration/test_security.py

async def test_blocked_table_rejected():
    """Verify query accessing blocked table is rejected"""
    # Setup: Configure blocked_tables=["secrets"]
    # Action: Ask "Show me all secrets"
    # Verify: SecurityViolationError raised

async def test_blocked_column_rejected():
    """Verify query accessing blocked column is rejected"""
    # Setup: Configure blocked_columns=["password"]
    # Action: Ask "Show me user passwords"
    # Verify: SecurityViolationError raised

async def test_explain_policy():
    """Verify EXPLAIN query handling based on allow_explain"""
    # Test 1: allow_explain=false, EXPLAIN rejected
    # Test 2: allow_explain=true, EXPLAIN allowed

async def test_question_length_limit():
    """Verify overly long questions are rejected"""
    # Setup: max_question_length=100
    # Action: Submit 200-char question
    # Verify: BAD_REQUEST error before LLM call
```

---

## 4. Gap 3: Resilience & Observability Not Integrated

### 4.1 Current State

**Problems**:
- `MultiRateLimiter` created but never used around LLM/DB calls
- No retry/backoff implementation despite `ResilienceConfig` support
- `resilience/retry.py` module missing
- Metrics/tracing modules exist but not instrumented in request path
- No health check endpoint
- Circuit breaker instantiated twice (server and orchestrator)
- No request_id propagation through logs

**Impact**: No production monitoring, no traffic control, no resilience against transient failures

### 4.2 Solution Design

#### 4.2.1 Rate Limiting Integration

```python
# services/orchestrator.py
class QueryOrchestrator:
    def __init__(
        self,
        settings: Settings,
        # ... existing params
        rate_limiter: MultiRateLimiter,
        # ...
    ):
        self.rate_limiter = rate_limiter
        # ...
    
    async def _generate_sql_with_retry(self, ...):
        # BEFORE LLM call
        async with self.rate_limiter.acquire("llm"):
            sql = await self.sql_generator.generate(...)
        # ...
    
    async def execute_query(self, request: QueryRequest):
        # ...
        # BEFORE DB execution
        async with self.rate_limiter.acquire("db"):
            results, total_count = await executor.execute(sql)
        # ...
```

#### 4.2.2 Retry/Backoff Implementation

```python
# resilience/retry.py
from typing import Callable, TypeVar, Any
import asyncio
from functools import wraps

T = TypeVar('T')

class RetryConfig:
    """Retry configuration"""
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 60.0,
        retriable_exceptions: tuple[type[Exception], ...] = (Exception,),
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
        self.retriable_exceptions = retriable_exceptions

async def retry_with_backoff(
    func: Callable[..., T],
    config: RetryConfig,
    *args: Any,
    **kwargs: Any,
) -> T:
    """Execute function with exponential backoff retry"""
    last_exception = None
    delay = config.initial_delay
    
    for attempt in range(config.max_attempts):
        try:
            return await func(*args, **kwargs)
        except config.retriable_exceptions as e:
            last_exception = e
            if attempt < config.max_attempts - 1:
                await asyncio.sleep(min(delay, config.max_delay))
                delay *= config.backoff_factor
            else:
                raise last_exception
    
    raise last_exception

def with_retry(config: RetryConfig):
    """Decorator for automatic retry with backoff"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_with_backoff(func, config, *args, **kwargs)
        return wrapper
    return decorator
```

**Usage in SQL Executor**:

```python
# services/sql_executor.py
from pg_mcp.resilience.retry import retry_with_backoff, RetryConfig
import asyncpg

class SQLExecutor:
    def __init__(self, ..., retry_config: RetryConfig):
        self.retry_config = retry_config
        # ...
    
    async def execute(self, sql: str, ...):
        # Wrap DB query with retry
        return await retry_with_backoff(
            self._execute_internal,
            self.retry_config,
            sql, timeout, max_rows
        )
    
    async def _execute_internal(self, sql, timeout, max_rows):
        # Existing implementation
        async with self.pool.acquire() as conn:
            # ...
```

#### 4.2.3 Metrics Instrumentation

```python
# services/orchestrator.py
from pg_mcp.observability.metrics import MetricsCollector

class QueryOrchestrator:
    async def execute_query(self, request: QueryRequest) -> QueryResponse:
        start_time = time.time()
        
        try:
            # ... existing logic
            
            # Record success
            if self.metrics:
                self.metrics.query_requests_total.labels(
                    status="success",
                    database=db_name
                ).inc()
            
            return response
            
        except PgMcpError as e:
            # Record failure
            if self.metrics:
                self.metrics.query_requests_total.labels(
                    status="error",
                    database=db_name or "unknown"
                ).inc()
                self.metrics.sql_rejected_total.labels(
                    reason=e.code.value
                ).inc()
            raise
            
        finally:
            # Record duration
            if self.metrics:
                duration = time.time() - start_time
                self.metrics.query_duration_seconds.observe(duration)
```

#### 4.2.4 Request ID Propagation

```python
# observability/logging.py
import contextvars

request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    'request_id', default='unknown'
)

class RequestIDFilter(logging.Filter):
    """Add request_id to log records"""
    def filter(self, record):
        record.request_id = request_id_ctx.get()
        return True

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.addFilter(RequestIDFilter())
    return logger
```

```python
# services/orchestrator.py
from pg_mcp.observability.logging import request_id_ctx

async def execute_query(self, request: QueryRequest) -> QueryResponse:
    request_id = f"req_{uuid.uuid4().hex[:12]}"
    request_id_ctx.set(request_id)  # Propagate through context
    
    logger.info("Processing query", extra={"question": request.question[:100]})
    # ... rest of implementation
```

#### 4.2.5 Health Check Endpoint

```python
# server.py
from mcp.server.fastmcp import FastMCP

@mcp.resource("health://status")
async def health_check() -> dict:
    """Health check endpoint"""
    try:
        # Check DB connections
        db_status = {}
        for db_name, pool in _pools.items():
            try:
                async with pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                db_status[db_name] = "healthy"
            except Exception as e:
                db_status[db_name] = f"unhealthy: {str(e)}"
        
        # Check LLM circuit breaker
        llm_status = "healthy" if _llm_circuit_breaker.allow_request() else "circuit_open"
        
        return {
            "status": "healthy" if all(s == "healthy" for s in db_status.values()) else "degraded",
            "databases": db_status,
            "llm": llm_status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
```

### 4.3 Implementation Tasks

| ID | Task | Files | Priority |
|----|------|-------|----------|
| R3.1 | Implement `resilience/retry.py` module | `resilience/retry.py` | P0 |
| R3.2 | Integrate rate limiter in orchestrator | `services/orchestrator.py` | P0 |
| R3.3 | Apply retry logic to SQL executor | `services/sql_executor.py` | P0 |
| R3.4 | Add metrics instrumentation to orchestrator | `services/orchestrator.py` | P1 |
| R3.5 | Add metrics instrumentation to SQL generator | `services/sql_generator.py` | P1 |
| R3.6 | Implement request_id context propagation | `observability/logging.py` | P1 |
| R3.7 | Add request_id to all log statements | All service files | P1 |
| R3.8 | Consolidate circuit breaker instances | `server.py`, `services/orchestrator.py` | P1 |
| R3.9 | Implement health check endpoint | `server.py` | P1 |
| R3.10 | Add resilience component unit tests | `tests/unit/test_resilience.py` | P1 |
| R3.11 | Add observability integration tests | `tests/integration/test_observability.py` | P2 |
| R3.12 | Document monitoring/metrics in README | `README.md` | P2 |

### 4.4 Acceptance Criteria

- [ ] Rate limiter enforces concurrent request limits for LLM and DB
- [ ] Retry logic handles transient DB connection failures
- [ ] Exponential backoff applied with configurable parameters
- [ ] Metrics collected for all query requests (success/failure)
- [ ] Metrics collected for LLM calls (count, latency, tokens)
- [ ] Metrics collected for DB queries (latency, rejections)
- [ ] Request ID propagated through all log statements
- [ ] Health check endpoint returns DB and LLM status
- [ ] Only one circuit breaker instance per component type
- [ ] Resilience components tested with failure scenarios

### 4.5 Testing Requirements

```python
# tests/unit/test_resilience.py

async def test_retry_with_backoff_success_after_failure():
    """Verify retry succeeds after transient failure"""
    # Mock function that fails twice then succeeds
    # Verify: 3 attempts made, correct delays applied

async def test_retry_max_attempts_exceeded():
    """Verify retry gives up after max attempts"""
    # Mock function that always fails
    # Verify: Exception raised after max_attempts

async def test_rate_limiter_concurrent_limit():
    """Verify rate limiter enforces concurrent request limit"""
    # Setup: max_concurrent=2
    # Action: Start 5 concurrent tasks
    # Verify: Only 2 run concurrently, others queued

# tests/integration/test_observability.py

async def test_metrics_collection():
    """Verify metrics collected for query execution"""
    # Action: Execute successful query
    # Verify: query_requests_total incremented
    # Verify: query_duration_seconds recorded

async def test_request_id_propagation():
    """Verify request_id appears in all logs for a query"""
    # Action: Execute query
    # Verify: All log entries contain same request_id

async def test_health_check_endpoint():
    """Verify health check returns correct status"""
    # Action: Call health check
    # Verify: Returns database status, LLM status, timestamp
```

---

## 5. Gap 4: Testing with Mocks

### 5.1 Current State

**Problems**:
- Integration/E2E tests assume live PostgreSQL and OpenAI
- No mocks or fixtures for deterministic testing
- CI will fail without external services
- Tests are non-deterministic and expensive
- Missing test coverage for:
  - Schema introspection
  - Pool lifecycle management
  - Metrics instrumentation
  - Rate limiting behavior
  - Session parameter setup
  - Multi-DB routing

**Impact**: Cannot run tests in CI/CD without external dependencies; unpredictable test failures

### 5.2 Solution Design

#### 5.2.1 Mock LLM Client

```python
# tests/conftest.py
import pytest
from unittest.mock import AsyncMock, Mock
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessage, Choice

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing"""
    client = AsyncMock(spec=AsyncOpenAI)
    
    async def mock_create(**kwargs):
        # Extract user question from messages
        messages = kwargs.get("messages", [])
        user_message = next((m for m in messages if m["role"] == "user"), None)
        
        # Generate realistic SQL based on question
        sql = "SELECT * FROM posts LIMIT 10;"  # Simple default
        
        # Return mock completion
        return ChatCompletion(
            id="chatcmpl-test",
            object="chat.completion",
            created=1234567890,
            model="gpt-4",
            choices=[
                Choice(
                    index=0,
                    message=ChatCompletionMessage(
                        role="assistant",
                        content=f"```sql\n{sql}\n```"
                    ),
                    finish_reason="stop"
                )
            ],
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
        )
    
    client.chat.completions.create = mock_create
    return client

@pytest.fixture
def mock_sql_generator(mock_openai_client):
    """Mock SQL generator using mock OpenAI client"""
    from pg_mcp.services.sql_generator import SQLGenerator
    from pg_mcp.config.settings import OpenAIConfig
    
    config = OpenAIConfig(
        api_key="sk-test-key",
        model="gpt-4",
        max_tokens=1000,
        temperature=0.0,
        timeout=30.0
    )
    
    generator = SQLGenerator(config)
    generator.client = mock_openai_client
    return generator
```

#### 5.2.2 Mock Database with pytest-asyncpg

```python
# tests/conftest.py
import pytest
import asyncpg
from typing import AsyncGenerator

@pytest.fixture
async def test_db_pool() -> AsyncGenerator[asyncpg.Pool, None]:
    """Create test database connection pool"""
    pool = await asyncpg.create_pool(
        host="localhost",
        port=5432,
        user="postgres",
        password="postgres",
        database="test_db",
        min_size=1,
        max_size=5
    )
    
    # Setup: Create test schema
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255),
                content TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        await conn.execute("""
            INSERT INTO posts (title, content) VALUES
            ('Test Post 1', 'Content 1'),
            ('Test Post 2', 'Content 2')
        """)
    
    yield pool
    
    # Teardown: Clean up
    async with pool.acquire() as conn:
        await conn.execute("DROP TABLE IF EXISTS posts")
    
    await pool.close()

@pytest.fixture
def mock_db_pool():
    """Mock database pool for unit tests (no real DB)"""
    pool = AsyncMock(spec=asyncpg.Pool)
    
    async def mock_acquire():
        conn = AsyncMock(spec=asyncpg.Connection)
        
        # Mock fetch to return test data
        async def mock_fetch(sql):
            if "SELECT" in sql.upper():
                return [
                    {"id": 1, "title": "Test Post", "content": "Test Content"}
                ]
            return []
        
        conn.fetch = mock_fetch
        conn.execute = AsyncMock()
        conn.transaction = AsyncMock()
        
        return conn
    
    pool.acquire = mock_acquire
    return pool
```

#### 5.2.3 Deterministic Test Data

```python
# tests/fixtures/test_data.py

TEST_SCHEMAS = {
    "blog_small": {
        "tables": [
            {
                "name": "posts",
                "columns": [
                    {"name": "id", "type": "integer", "pk": True},
                    {"name": "title", "type": "varchar(255)"},
                    {"name": "content", "type": "text"},
                ]
            },
            {
                "name": "comments",
                "columns": [
                    {"name": "id", "type": "integer", "pk": True},
                    {"name": "post_id", "type": "integer", "fk": "posts.id"},
                    {"name": "content", "type": "text"},
                ]
            }
        ]
    }
}

TEST_QUERIES = {
    "simple_select": {
        "question": "Show me all posts",
        "expected_sql": "SELECT * FROM posts",
        "expected_result": [
            {"id": 1, "title": "Post 1", "content": "Content 1"}
        ]
    },
    "with_filter": {
        "question": "Show me posts from last week",
        "expected_sql": "SELECT * FROM posts WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'",
        "expected_result": []
    }
}
```

### 5.3 Implementation Tasks

| ID | Task | Files | Priority |
|----|------|-------|----------|
| T4.1 | Create mock OpenAI client fixture | `tests/conftest.py` | P0 |
| T4.2 | Create mock database pool fixture | `tests/conftest.py` | P0 |
| T4.3 | Create test data fixtures | `tests/fixtures/test_data.py` | P0 |
| T4.4 | Update unit tests to use mocks | `tests/unit/*.py` | P0 |
| T4.5 | Create Docker Compose for integration tests | `docker-compose.test.yml` | P1 |
| T4.6 | Update integration tests to use test DB | `tests/integration/*.py` | P1 |
| T4.7 | Add schema introspection tests | `tests/integration/test_schema.py` | P1 |
| T4.8 | Add pool lifecycle tests | `tests/integration/test_pool.py` | P1 |
| T4.9 | Add metrics collection tests | `tests/integration/test_metrics.py` | P2 |
| T4.10 | Add rate limiting tests | `tests/unit/test_rate_limiter.py` | P2 |
| T4.11 | Create CI/CD workflow with test DB | `.github/workflows/test.yml` | P2 |

### 5.4 Acceptance Criteria

- [ ] Unit tests run without external dependencies (all mocked)
- [ ] Integration tests use Docker Compose test database
- [ ] E2E tests use mock OpenAI client
- [ ] Test coverage ≥ 80% overall
- [ ] SQL validator tests ≥ 95% coverage
- [ ] All tests pass in CI/CD pipeline
- [ ] Tests are deterministic and repeatable
- [ ] Test execution time < 60 seconds for unit tests
- [ ] Test execution time < 5 minutes for all tests

### 5.5 Testing Requirements

```python
# tests/unit/test_sql_generator_mock.py

async def test_sql_generation_with_mock_llm(mock_sql_generator):
    """Verify SQL generation using mock LLM"""
    # Setup: Mock schema
    schema = DatabaseSchema(database_name="test_db", ...)
    
    # Action: Generate SQL
    sql = await mock_sql_generator.generate(
        question="Show me all posts",
        schema=schema
    )
    
    # Verify: SQL contains SELECT statement
    assert "SELECT" in sql.upper()
    assert "posts" in sql.lower()

# tests/integration/test_schema.py

async def test_schema_introspection(test_db_pool):
    """Verify schema introspection from real database"""
    from pg_mcp.cache.schema_cache import SchemaCache
    
    cache = SchemaCache()
    schema = await cache.load("test_db", test_db_pool, ...)
    
    # Verify: Schema contains expected tables
    assert len(schema.tables) > 0
    assert any(t.table_name == "posts" for t in schema.tables)

# tests/integration/test_pool.py

async def test_pool_lifecycle():
    """Verify connection pool creation and cleanup"""
    from pg_mcp.db.pool import create_pools
    
    configs = [DatabaseConfig(name="test", ...)]
    pools = await create_pools(configs)
    
    # Verify: Pool created
    assert "test" in pools
    assert pools["test"].get_size() > 0
    
    # Cleanup
    for pool in pools.values():
        await pool.close()
    
    # Verify: Pool closed
    assert pools["test"].get_size() == 0
```

---

## 6. Implementation Roadmap

### 6.1 Phase Breakdown

```
Phase 1: Multi-Database Support (Week 1)
├── Update Settings to support database list
├── Implement per-DB executor creation
├── Fix database routing in orchestrator
├── Add multi-DB integration tests
└── Update documentation

Phase 2: Security Controls (Week 1)
├── Add security fields to configurations
├── Wire security config to validator
├── Implement input validation (question length)
├── Add security unit and integration tests
└── Update security documentation

Phase 3: Resilience Integration (Week 2)
├── Implement retry/backoff module
├── Integrate rate limiter in orchestrator
├── Apply retry logic to SQL executor
├── Consolidate circuit breaker instances
└── Add resilience tests

Phase 4: Observability Integration (Week 2)
├── Instrument metrics in all services
├── Implement request_id propagation
├── Add health check endpoint
├── Add observability tests
└── Update monitoring documentation

Phase 5: Testing with Mocks (Week 3)
├── Create mock fixtures (OpenAI, DB)
├── Update unit tests to use mocks
├── Setup Docker Compose for integration tests
├── Add missing test coverage
└── Setup CI/CD pipeline

Phase 6: Validation & Documentation (Week 3)
├── Run full test suite
├── Fix any failing tests
├── Update README with all features
├── Create deployment guide
└── Final review and cleanup
```

### 6.2 Priority Matrix

| Gap | Severity | Effort | Priority | Phase |
|-----|----------|--------|----------|-------|
| Multi-Database Support | High | Medium | P0 | Phase 1 |
| Security Controls | High | Low | P0 | Phase 2 |
| Rate Limiting | Medium | Low | P1 | Phase 3 |
| Retry/Backoff | Medium | Medium | P1 | Phase 3 |
| Metrics Instrumentation | Medium | Medium | P1 | Phase 4 |
| Request ID Propagation | Low | Low | P2 | Phase 4 |
| Health Check | Low | Low | P2 | Phase 4 |
| Mock Testing | Medium | High | P1 | Phase 5 |
| CI/CD Setup | Medium | Medium | P2 | Phase 5 |

### 6.3 Dependencies

```
Phase 1 (Multi-DB) → Independent (can start immediately)
Phase 2 (Security) → Independent (can start immediately)
Phase 3 (Resilience) → Depends on Phase 1 (needs multi-executor support)
Phase 4 (Observability) → Depends on Phase 3 (needs instrumented paths)
Phase 5 (Testing) → Depends on Phase 1-4 (tests updated features)
Phase 6 (Validation) → Depends on Phase 1-5 (validates everything)
```

---

## 7. Success Metrics

### 7.1 Code Quality Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Test Coverage (Overall) | ~60% | ≥ 80% |
| Test Coverage (SQLValidator) | ~85% | ≥ 95% |
| Lines of Code (Tests) | ~2,000 | ≥ 4,000 |
| Pylint Score | ~8.5/10 | ≥ 9.0/10 |
| MyPy Strict Pass | Partial | 100% |

### 7.2 Functionality Metrics

| Feature | Status | Target |
|---------|--------|--------|
| Multi-Database Support | ❌ | ✅ |
| Blocked Tables/Columns | ❌ | ✅ |
| Question Length Limits | ❌ | ✅ |
| Rate Limiting | ❌ | ✅ |
| Retry/Backoff | ❌ | ✅ |
| Metrics Collection | ❌ | ✅ |
| Health Check | ❌ | ✅ |
| Mock-Based Tests | ❌ | ✅ |
| CI/CD Pipeline | ❌ | ✅ |

### 7.3 Performance Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Query Latency (p50) | ~3s | < 3s |
| Query Latency (p95) | ~8s | < 5s |
| Test Execution Time | ~2min | < 5min |
| Unit Test Time | N/A | < 60s |

---

## 8. Risk Assessment

### 8.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Breaking existing functionality | High | Medium | Comprehensive regression testing |
| Mock behavior diverges from real | Medium | Medium | Validate mocks against real behavior |
| Performance degradation from instrumentation | Low | Low | Benchmark before/after |
| Configuration migration issues | Medium | Low | Provide migration guide |

### 8.2 Schedule Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Underestimated effort | Medium | Medium | Build in 20% buffer |
| Dependency delays | Low | Low | Phases 1-2 can run in parallel |
| Testing reveals major issues | High | Medium | Early integration testing |

---

## 9. Deliverables Checklist

### 9.1 Code Deliverables

- [ ] Updated `config/settings.py` with multi-DB and security fields
- [ ] Updated `server.py` with multi-DB initialization
- [ ] Updated `services/orchestrator.py` with routing and validation
- [ ] New `resilience/retry.py` module
- [ ] Updated all services with metrics instrumentation
- [ ] Updated all services with request_id logging
- [ ] New health check endpoint in `server.py`
- [ ] Mock fixtures in `tests/conftest.py`
- [ ] Complete test suite with ≥80% coverage
- [ ] Docker Compose configuration for testing
- [ ] CI/CD workflow configuration

### 9.2 Documentation Deliverables

- [ ] Updated README.md with:
  - [ ] Multi-database configuration guide
  - [ ] Security configuration guide
  - [ ] Monitoring/metrics documentation
  - [ ] Testing guide
  - [ ] Deployment guide
- [ ] Updated `.env.example` with all configuration options
- [ ] Configuration migration guide
- [ ] Architecture diagram updates
- [ ] API documentation updates

### 9.3 Testing Deliverables

- [ ] Unit tests for all new modules
- [ ] Integration tests for multi-DB support
- [ ] Integration tests for security controls
- [ ] Integration tests for resilience components
- [ ] Integration tests for observability
- [ ] E2E tests with mocks
- [ ] Performance benchmarks
- [ ] Test coverage report

---

## 10. Appendix

### 10.1 Configuration Migration Example

**Old Configuration (.env)**:
```bash
# OLD - Single database
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=postgres
DATABASE_PASSWORD=secret
DATABASE_NAME=mydb
```

**New Configuration (.env)**:
```bash
# NEW - Multiple databases
DATABASES__0__NAME=blog_small
DATABASES__0__HOST=localhost
DATABASES__0__PORT=5432
DATABASES__0__USER=postgres
DATABASES__0__PASSWORD=secret
DATABASES__0__DATABASE=blog_small

DATABASES__1__NAME=ecommerce_medium
DATABASES__1__HOST=localhost
DATABASES__1__PORT=5432
DATABASES__1__USER=postgres
DATABASES__1__PASSWORD=secret
DATABASES__1__DATABASE=ecommerce

# Security Configuration
SECURITY__BLOCKED_TABLES=["users", "secrets"]
SECURITY__BLOCKED_COLUMNS=["password", "ssn"]
SECURITY__ALLOW_EXPLAIN=false

# Validation Configuration
VALIDATION__MAX_QUESTION_LENGTH=5000
```

### 10.2 Testing Command Reference

```bash
# Run all tests
pytest

# Run only unit tests
pytest tests/unit/

# Run with coverage
pytest --cov=pg_mcp --cov-report=html

# Run specific test
pytest tests/unit/test_sql_validator.py::test_blocked_table_rejected

# Run with Docker Compose test DB
docker-compose -f docker-compose.test.yml up -d
pytest tests/integration/
docker-compose -f docker-compose.test.yml down
```

### 10.3 Reference Links

- [Original Design Document](./0002-pg-mcp-design.md)
- [Implementation Plan](./0004-pg-mcp-impl-plan.md)
- [Code Review Report](./0006-pg-mcp-code-review.md)
- [Test Plan](./0007-pg-mcp-test-plan.md)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| v1.0 | 2026-01-11 | GitHub Copilot | Initial version |
