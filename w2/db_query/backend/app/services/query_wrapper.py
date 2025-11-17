"""Query execution wrapper using new database service."""

from typing import List
from sqlmodel import Session, select, desc
from app.models.query import QueryHistory, QuerySource
from app.models.database import DatabaseType
from app.models.schemas import QueryResult, QueryColumn
from app.services.database_service import database_service
from app.services.sql_validator import SqlValidationError
from app.services.query import save_query_history, get_query_history, cleanup_old_queries


async def execute_query_with_service(
    session: Session,
    database_name: str,
    db_type: DatabaseType,
    url: str,
    sql: str,
    query_source: QuerySource = QuerySource.MANUAL,
) -> QueryResult:
    """
    Execute SQL query using new database service.

    Args:
        session: SQLite database session
        database_name: Database connection name
        db_type: Database type
        url: Database connection URL
        sql: SQL query string
        query_source: Source of the query (manual or natural language)

    Returns:
        QueryResult with columns, rows, and metadata

    Raises:
        SqlValidationError: If SQL validation fails
        Exception: If query execution fails
    """
    # Execute query using new service
    try:
        result, execution_time_ms = await database_service.execute_query(
            db_type=db_type,
            name=database_name,
            url=url,
            sql=sql,
            limit=1000,
        )

        # Convert adapter result to API schema
        columns = [QueryColumn(**col) for col in result.columns]

        # Save successful query to history
        await save_query_history(
            session,
            database_name,
            sql,
            result.row_count,
            execution_time_ms,
            True,
            None,
            query_source,
        )

        return QueryResult(
            columns=columns,
            rows=result.rows,
            rowCount=result.row_count,
            executionTimeMs=execution_time_ms,
            sql=sql,
        )

    except SqlValidationError as e:
        # Save failed query to history (validation error)
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

    except Exception as e:
        # Save failed query to history (execution error)
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
