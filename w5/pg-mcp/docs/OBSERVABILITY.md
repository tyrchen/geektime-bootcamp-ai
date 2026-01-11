# Observability Guide

This guide covers metrics, logging, and health monitoring for the PostgreSQL MCP Server.

## Metrics

The server exposes Prometheus-compatible metrics for monitoring.

### Configuration

```env
# Enable/disable metrics collection
OBSERVABILITY__METRICS_ENABLED=true

# Metrics HTTP server port
OBSERVABILITY__METRICS_PORT=9090
```

### Available Metrics

#### Query Metrics

- **`pg_mcp_query_requests_total`** (Counter)
  - Total number of query requests processed
  - Labels: `status` (success/error), `database`
  
- **`pg_mcp_query_duration_seconds`** (Histogram)
  - Query request processing duration
  - Buckets: 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0 seconds

#### LLM Metrics

- **`pg_mcp_llm_calls_total`** (Counter)
  - Total number of LLM API calls
  - Labels: `operation` (generate_sql, validate_result)

- **`pg_mcp_llm_latency_seconds`** (Histogram)
  - LLM API call latency
  - Labels: `operation`
  - Buckets: 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0 seconds

- **`pg_mcp_llm_tokens_used`** (Counter)
  - Total number of LLM tokens consumed
  - Labels: `operation`

#### Security Metrics

- **`pg_mcp_sql_rejected_total`** (Counter)
  - Total number of SQL queries rejected by security checks
  - Labels: `reason` (multiple_statements, dangerous_function, blocked_table, etc.)

#### Database Metrics

- **`pg_mcp_db_connections_active`** (Gauge)
  - Number of active database connections
  - Labels: `database`
  - Updated every 10 seconds

- **`pg_mcp_db_query_duration_seconds`** (Histogram)
  - Database query execution duration
  - Buckets: 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0 seconds

#### Cache Metrics

- **`pg_mcp_schema_cache_age_seconds`** (Gauge)
  - Age of the schema cache in seconds
  - Labels: `database`

### Accessing Metrics

Metrics are exposed at `http://localhost:9090/metrics` by default.

```bash
# View all metrics
curl http://localhost:9090/metrics

# Use with Prometheus
# Add to prometheus.yml:
scrape_configs:
  - job_name: 'pg-mcp'
    static_configs:
      - targets: ['localhost:9090']
```

### Example Queries

```promql
# Query success rate
rate(pg_mcp_query_requests_total{status="success"}[5m])
/ rate(pg_mcp_query_requests_total[5m])

# Average LLM latency
rate(pg_mcp_llm_latency_seconds_sum[5m])
/ rate(pg_mcp_llm_latency_seconds_count[5m])

# Active database connections
pg_mcp_db_connections_active

# SQL rejection rate by reason
sum by (reason) (rate(pg_mcp_sql_rejected_total[5m]))
```

## Health Checks

The server provides a health check tool for monitoring.

### Health Endpoint

```python
from mcp.client import use_mcp_server

async with use_mcp_server("pg-mcp") as client:
    health = await client.call_tool("health", {})
    print(health)
```

### Health Response

```json
{
  "status": "healthy",  // or "degraded" or "unhealthy"
  "timestamp": "2026-01-11T10:30:00Z",
  "components": {
    "databases": {
      "blog_small": {
        "status": "healthy",
        "pool_size": 20,
        "free_connections": 15,
        "active_connections": 5
      }
    },
    "schema_cache": "healthy",
    "orchestrator": "healthy"
  },
  "metrics": {
    "database_count": 3
  }
}
```

### Status Values

- **healthy**: All components operational
- **degraded**: Some components have issues but server is functional
- **unhealthy**: Critical components failed, server not operational

## Logging

### Configuration

```env
# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
OBSERVABILITY__LOG_LEVEL=INFO

# Log format: json or text
OBSERVABILITY__LOG_FORMAT=json
```

### Structured Logging

All logs include structured fields for easy parsing:

```json
{
  "timestamp": "2026-01-11T10:30:00Z",
  "level": "INFO",
  "logger": "pg_mcp.services.orchestrator",
  "message": "Starting query execution",
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "question": "How many users?",
  "database": "blog_small"
}
```

### Key Log Fields

- **request_id**: Unique identifier for request tracing
- **database**: Target database name
- **attempt**: Retry attempt number
- **error_type**: Exception class name
- **execution_time_ms**: Query execution time

### Log Aggregation

For production, use log aggregation tools:

```bash
# JSON logs work well with structured logging tools
OBSERVABILITY__LOG_FORMAT=json uv run python main.py | tee server.log

# Parse with jq
cat server.log | jq 'select(.level == "ERROR")'

# Search by request_id
cat server.log | jq 'select(.request_id == "123e4567-e89b-12d3-a456-426614174000")'
```

## Monitoring Dashboard

### Grafana Example

Create a dashboard with the following panels:

1. **Query Rate**: `rate(pg_mcp_query_requests_total[5m])`
2. **Query Success Rate**: Success vs total queries
3. **Query Duration P95**: `histogram_quantile(0.95, pg_mcp_query_duration_seconds_bucket)`
4. **LLM Token Usage**: `rate(pg_mcp_llm_tokens_used[1h])`
5. **Database Connections**: `pg_mcp_db_connections_active`
6. **Security Rejections**: SQL queries rejected by reason

### Alerting Rules

```yaml
groups:
  - name: pg_mcp
    rules:
      # High error rate
      - alert: HighQueryErrorRate
        expr: rate(pg_mcp_query_requests_total{status="error"}[5m]) > 0.1
        for: 5m
        annotations:
          summary: "High query error rate detected"

      # Slow queries
      - alert: SlowQueries
        expr: histogram_quantile(0.95, pg_mcp_query_duration_seconds_bucket) > 10
        for: 5m
        annotations:
          summary: "95th percentile query duration exceeds 10s"

      # Connection pool exhaustion
      - alert: ConnectionPoolExhausted
        expr: pg_mcp_db_connections_active == 20
        for: 1m
        annotations:
          summary: "Database connection pool is exhausted"
```

## Performance Tuning

### Connection Pools

Monitor `pg_mcp_db_connections_active` to tune pool sizes:

```env
# Increase if frequently exhausted
DATABASES__0__MAX_POOL_SIZE=50

# Reduce if connections are mostly idle
DATABASES__0__MIN_POOL_SIZE=5
```

### Rate Limiting

Adjust rate limits based on metrics:

```python
# In server.py lifespan
_rate_limiter = MultiRateLimiter(
    query_limit=20,  # Increase if queue_depth grows
    llm_limit=10,    # Increase if LLM timeouts occur
)
```

### Cache Tuning

Monitor `pg_mcp_schema_cache_age_seconds`:

```env
# Increase TTL if schema rarely changes
CACHE__SCHEMA_TTL=7200  # 2 hours

# Enable cache if disabled
CACHE__ENABLED=true
```

## Troubleshooting

### High Query Error Rate

1. Check logs for error patterns:
   ```bash
   cat server.log | jq 'select(.level == "ERROR")' | jq .error_type | sort | uniq -c
   ```

2. Review rejected SQL queries:
   ```promql
   sum by (reason) (pg_mcp_sql_rejected_total)
   ```

3. Check LLM availability:
   ```promql
   rate(pg_mcp_llm_calls_total[5m])
   ```

### Slow Queries

1. Check database query duration:
   ```promql
   histogram_quantile(0.95, pg_mcp_db_query_duration_seconds_bucket)
   ```

2. Review LLM latency:
   ```promql
   histogram_quantile(0.95, pg_mcp_llm_latency_seconds_bucket)
   ```

3. Check for retries in logs:
   ```bash
   cat server.log | jq 'select(.attempt > 1)'
   ```

### Connection Issues

1. Monitor connection pool:
   ```promql
   pg_mcp_db_connections_active
   ```

2. Check pool configuration in logs
3. Review database server connection limits

## Best Practices

1. **Always enable metrics in production**
   ```env
   OBSERVABILITY__METRICS_ENABLED=true
   ```

2. **Use JSON logging for production**
   ```env
   OBSERVABILITY__LOG_FORMAT=json
   ```

3. **Set appropriate log levels**
   - Development: DEBUG
   - Staging: INFO
   - Production: WARNING

4. **Monitor key metrics**
   - Query success rate
   - Query duration P95
   - LLM token usage
   - Connection pool utilization

5. **Set up alerts for**
   - High error rate (>5%)
   - Slow queries (P95 >10s)
   - Connection pool exhaustion
   - High LLM latency (>30s)

6. **Regular review**
   - Weekly: Review error logs
   - Monthly: Analyze performance trends
   - Quarterly: Tune configuration based on metrics
