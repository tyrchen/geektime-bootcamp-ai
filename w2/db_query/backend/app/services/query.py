"""Query execution service."""

import time
from typing import Dict, List, Any
from datetime import datetime, timezone
from sqlmodel import Session, select, desc
from app.models.query import QueryHistory, QuerySource
from app.models.schemas import QueryResult, QueryColumn
from app.services.sql_validator import validate_and_transform_sql, SqlValidationError
from app.services.db_connection import get_connection_pool


async def execute_query(
    session: Session,
    database_name: str,
    url: str,
    sql: str,
    query_source: QuerySource = QuerySource.MANUAL,
) -> QueryResult:
    """
    Execute SQL query against PostgreSQL database.

    Args:
        session: SQLite database session
        database_name: Database connection name
        url: PostgreSQL connection URL
        sql: SQL query string
        query_source: Source of the query (manual or natural language)

    Returns:
        QueryResult with columns, rows, and metadata

    Raises:
        SqlValidationError: If SQL validation fails
        Exception: If query execution fails
    """
    # Validate and transform SQL
    try:
        validated_sql = validate_and_transform_sql(sql, limit=1000)
    except SqlValidationError as e:
        # Save failed query to history
        await save_query_history(
            session,
            database_name,
            sql,
            None,
            None,
            False,
            str(e),
            query_source,
        )
        raise

    # Get connection pool
    pool = await get_connection_pool(database_name, url)

    # Execute query
    start_time = time.time()
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(validated_sql)

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Convert rows to dictionaries
            result_rows: List[Dict[str, Any]] = []
            columns: List[QueryColumn] = []

            if rows:
                # Get column names and types from first row
                first_row = rows[0]
                for key, value in first_row.items():
                    # Determine data type
                    if value is None:
                        data_type = "unknown"
                    elif isinstance(value, int):
                        data_type = "integer"
                    elif isinstance(value, float):
                        data_type = "double precision"
                    elif isinstance(value, bool):
                        data_type = "boolean"
                    elif isinstance(value, str):
                        data_type = "character varying"
                    elif isinstance(value, datetime):
                        data_type = "timestamp"
                    else:
                        data_type = str(type(value).__name__)

                    columns.append(QueryColumn(name=key, dataType=data_type))

                # Convert all rows
                for row in rows:
                    result_rows.append(dict(row))

            # Save successful query to history
            await save_query_history(
                session,
                database_name,
                validated_sql,
                len(result_rows),
                execution_time_ms,
                True,
                None,
                query_source,
            )

            return QueryResult(
                columns=columns,
                rows=result_rows,
                rowCount=len(result_rows),
                executionTimeMs=execution_time_ms,
                sql=validated_sql,
            )

    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)

        # Save failed query to history
        await save_query_history(
            session,
            database_name,
            validated_sql,
            None,
            execution_time_ms,
            False,
            str(e),
            query_source,
        )

        raise


async def save_query_history(
    session: Session,
    database_name: str,
    sql: str,
    row_count: int | None,
    execution_time_ms: int | None,
    success: bool,
    error_message: str | None,
    query_source: QuerySource,
) -> QueryHistory:
    """
    Save query to history.

    Args:
        session: SQLite database session
        database_name: Database connection name
        sql: SQL query string
        row_count: Number of rows returned
        execution_time_ms: Execution time in milliseconds
        success: Whether query succeeded
        error_message: Error message if failed
        query_source: Source of the query

    Returns:
        Saved QueryHistory instance
    """
    history = QueryHistory(
        database_name=database_name,
        sql_text=sql,
        executed_at=datetime.now(timezone.utc),
        execution_time_ms=execution_time_ms,
        row_count=row_count,
        success=success,
        error_message=error_message,
        query_source=query_source,
    )

    session.add(history)
    session.commit()
    session.refresh(history)

    # Keep only last 50 queries per database
    await cleanup_old_queries(session, database_name)

    return history


async def cleanup_old_queries(session: Session, database_name: str) -> None:
    """
    Keep only the last 50 queries for a database.

    Args:
        session: SQLite database session
        database_name: Database connection name
    """
    # Get all queries for this database, ordered by executed_at DESC
    statement = (
        select(QueryHistory)
        .where(QueryHistory.database_name == database_name)
        .order_by(desc(QueryHistory.executed_at))
    )
    all_queries = session.exec(statement).all()

    # Delete queries beyond the 50th
    if len(all_queries) > 50:
        queries_to_delete = all_queries[50:]
        for query in queries_to_delete:
            session.delete(query)
        session.commit()


async def get_query_history(
    session: Session, database_name: str, limit: int = 50
) -> List[QueryHistory]:
    """
    Get query history for a database.

    Args:
        session: SQLite database session
        database_name: Database connection name
        limit: Maximum number of queries to return

    Returns:
        List of QueryHistory entries
    """
    statement = (
        select(QueryHistory)
        .where(QueryHistory.database_name == database_name)
        .order_by(desc(QueryHistory.executed_at))
        .limit(limit)
    )
    return list(session.exec(statement).all())
