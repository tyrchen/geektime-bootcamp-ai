"""SQL executor for PostgreSQL queries.

This module provides safe SQL execution with session parameter configuration,
result serialization, and row limiting to prevent memory overflow.
"""

import asyncio
import datetime
import decimal
import logging
import time
import uuid
from typing import Any

import asyncpg
from asyncpg import Connection, Pool

from pg_mcp.config.settings import DatabaseConfig, SecurityConfig
from pg_mcp.models.errors import DatabaseError, ExecutionTimeoutError
from pg_mcp.observability.metrics import metrics
from pg_mcp.resilience.retry import RetryConfig, retry_with_backoff

logger = logging.getLogger(__name__)


class SQLExecutor:
    """SQL executor using asyncpg with security measures.

    This executor ensures safe query execution by:
    1. Setting session parameters (timeout, search_path, role)
    2. Running queries in read-only transactions
    3. Limiting the number of returned rows
    4. Serializing PostgreSQL-specific data types

    Example:
        >>> executor = SQLExecutor(pool, security_config, db_config)
        >>> results, count = await executor.execute("SELECT * FROM users")
        >>> print(f"Retrieved {count} rows")
    """

    def __init__(
        self,
        pool: Pool,
        security_config: SecurityConfig,
        db_config: DatabaseConfig,
        retry_config: RetryConfig | None = None,
    ) -> None:
        """Initialize SQL executor.

        Args:
            pool: asyncpg connection pool for database connections.
            security_config: Security configuration including timeouts and limits.
            db_config: Database configuration including connection parameters.
            retry_config: Optional retry configuration. Uses defaults if None.
        """
        self.pool = pool
        self.security_config = security_config
        self.db_config = db_config
        self.retry_config = retry_config or RetryConfig(
            max_attempts=3,
            initial_delay=1.0,
            backoff_factor=2.0,
            max_delay=30.0,
        )

    async def execute(
        self,
        sql: str,
        timeout: float | None = None,  # noqa: ASYNC109
        max_rows: int | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """Execute SQL query with security measures and retry logic.

        This method:
        1. Acquires a connection from the pool
        2. Starts a read-only transaction
        3. Sets session parameters (timeout, search_path, role)
        4. Executes the query with timeout and retry on transient failures
        5. Limits the number of returned rows
        6. Serializes special PostgreSQL types

        Args:
            sql: SQL query to execute (should already be validated).
            timeout: Query timeout in seconds (uses config default if None).
            max_rows: Maximum rows to return (uses config default if None).

        Returns:
            tuple: (results, total_row_count) where:
                - results: List of row dictionaries with serialized values
                - total_row_count: Total number of rows (before limiting)

        Raises:
            ExecutionTimeoutError: If query execution exceeds timeout.
            DatabaseError: If database operation fails.

        Example:
            >>> results, count = await executor.execute(
            ...     "SELECT id, name FROM users WHERE active = true",
            ...     timeout=10.0,
            ...     max_rows=1000
            ... )
            >>> print(f"Retrieved {len(results)} of {count} total rows")
        """
        # Use configured defaults if not specified
        timeout = timeout or self.security_config.max_execution_time
        max_rows = max_rows or self.security_config.max_rows

        # Wrap execution in retry logic for transient failures
        return await retry_with_backoff(
            self._execute_with_connection,
            self.retry_config,
            sql,
            timeout,
            max_rows,
        )

    async def _execute_with_connection(
        self,
        sql: str,
        timeout: float,
        max_rows: int,
    ) -> tuple[list[dict[str, Any]], int]:
        """Internal method to execute query with a connection.

        This method is wrapped by retry logic to handle transient failures.

        Args:
            sql: SQL query to execute.
            timeout: Query timeout in seconds.
            max_rows: Maximum rows to return.

        Returns:
            tuple: (results, total_row_count)

        Raises:
            ExecutionTimeoutError: If query execution exceeds timeout.
            DatabaseError: If database operation fails.
        """
        query_start_time = time.time()
        
        try:
            async with (
                self.pool.acquire() as connection,
                connection.transaction(readonly=True),
            ):
                # Set session parameters for security
                await self._set_session_params(connection, timeout)

                # Execute query with timeout
                try:
                    records = await asyncio.wait_for(
                        connection.fetch(sql),
                        timeout=timeout,
                    )
                except TimeoutError as e:
                    raise ExecutionTimeoutError(
                        message=f"Query execution exceeded timeout of {timeout} seconds",
                        details={
                            "timeout_seconds": timeout,
                            "sql": sql[:200],  # Include truncated SQL for debugging
                        },
                    ) from e

                # Track total count before limiting
                total_count = len(records)

                # Limit number of returned rows
                if len(records) > max_rows:
                    records = records[:max_rows]

                # Convert asyncpg.Record to dict
                results = [dict(record) for record in records]

                # Serialize special PostgreSQL types
                results = self._serialize_results(results)

                # Record successful query metrics
                query_duration = time.time() - query_start_time
                metrics.observe_db_query_duration(query_duration)

                return results, total_count

        except ExecutionTimeoutError:
            # Re-raise timeout errors as-is (don't retry)
            raise
        except asyncpg.PostgresError as e:
            # Wrap PostgreSQL errors
            raise DatabaseError(
                message=f"Database query failed: {e!s}",
                details={
                    "error_code": e.sqlstate if hasattr(e, "sqlstate") else None,
                    "error_message": str(e),
                    "sql": sql[:200],  # Include truncated SQL for debugging
                },
            ) from e
        except Exception as e:
            # Catch-all for unexpected errors
            raise DatabaseError(
                message=f"Unexpected error during query execution: {e!s}",
                details={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
            ) from e

    async def _set_session_params(
        self,
        conn: Connection,
        timeout: float,  # noqa: ASYNC109
    ) -> None:
        """Set session parameters to ensure safe query execution.

        This method configures the database session with:
        1. statement_timeout: Prevents long-running queries
        2. search_path: Prevents schema injection attacks
        3. SET ROLE: Switches to read-only role if configured

        Args:
            conn: Database connection to configure.
            timeout: Query timeout in seconds (converted to milliseconds).

        Raises:
            DatabaseError: If setting session parameters fails.

        Note:
            These settings apply only to the current transaction and are
            automatically reset when the connection is returned to the pool.
        """
        try:
            # Set statement timeout (PostgreSQL expects milliseconds)
            timeout_ms = int(timeout * 1000)
            await conn.execute(f"SET statement_timeout = {timeout_ms}")

            # Set safe search_path to prevent schema injection
            # Using execute with literal to avoid SQL injection
            search_path = self.security_config.safe_search_path
            # Validate search_path contains only safe characters
            if not all(c.isalnum() or c in ("_", ",", " ") for c in search_path):
                raise DatabaseError(
                    message="Invalid search_path configuration",
                    details={"search_path": search_path},
                )
            await conn.execute(f"SET search_path = '{search_path}'")

            # Switch to read-only role if configured
            if self.security_config.readonly_role:
                readonly_role = self.security_config.readonly_role
                # Validate role name contains only safe characters
                if not all(c.isalnum() or c == "_" for c in readonly_role):
                    raise DatabaseError(
                        message="Invalid readonly_role configuration",
                        details={"readonly_role": readonly_role},
                    )
                await conn.execute(f"SET ROLE {readonly_role}")

        except asyncpg.PostgresError as e:
            raise DatabaseError(
                message=f"Failed to set session parameters: {e!s}",
                details={
                    "error_code": e.sqlstate if hasattr(e, "sqlstate") else None,
                    "timeout_ms": timeout_ms,
                    "search_path": self.security_config.safe_search_path,
                    "readonly_role": self.security_config.readonly_role,
                },
            ) from e

    def _serialize_results(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Serialize PostgreSQL-specific types to JSON-compatible types.

        This method handles serialization of types that are not natively
        JSON-serializable, including:
        - datetime types: converted to ISO format strings
        - decimal.Decimal: converted to float
        - uuid.UUID: converted to string
        - bytes: converted to hexadecimal string
        - Nested lists/dicts: recursively serialized

        Args:
            results: List of row dictionaries with potentially unserializable values.

        Returns:
            list: Results with all values serialized to JSON-compatible types.

        Example:
            >>> results = [
            ...     {"id": 1, "created": datetime.datetime(2024, 1, 1, 12, 0)},
            ...     {"id": 2, "price": decimal.Decimal("99.99")}
            ... ]
            >>> serialized = executor._serialize_results(results)
            >>> serialized[0]["created"]  # "2024-01-01T12:00:00"
            >>> serialized[1]["price"]  # 99.99
        """

        def serialize_value(value: Any) -> Any:
            """Recursively serialize a single value.

            Args:
                value: Value to serialize.

            Returns:
                Serialized value that is JSON-compatible.
            """
            # Handle None
            if value is None:
                return None

            # Handle datetime types
            if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
                return value.isoformat()

            # Handle timedelta
            if isinstance(value, datetime.timedelta):
                return str(value)

            # Handle Decimal (convert to float)
            if isinstance(value, decimal.Decimal):
                return float(value)

            # Handle UUID
            if isinstance(value, uuid.UUID):
                return str(value)

            # Handle bytes (convert to hex string)
            if isinstance(value, bytes):
                return value.hex()

            # Handle lists and tuples (recursively serialize)
            if isinstance(value, (list, tuple)):
                return [serialize_value(v) for v in value]

            # Handle dicts (recursively serialize values)
            if isinstance(value, dict):
                return {k: serialize_value(v) for k, v in value.items()}

            # Return other types as-is (str, int, float, bool, etc.)
            return value

        # Serialize all values in all rows
        return [{key: serialize_value(value) for key, value in row.items()} for row in results]
