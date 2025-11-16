"""Metadata extraction service for PostgreSQL databases."""

import asyncpg
import json
from typing import Dict, List, Any
from datetime import datetime, timezone
from sqlmodel import Session, select
from app.models.metadata import DatabaseMetadata
from app.models.schemas import TableMetadata, ColumnMetadata
from app.services.db_connection import get_connection_pool


async def extract_metadata(
    database_name: str, pool: asyncpg.Pool
) -> Dict[str, Any]:
    """
    Extract database metadata from PostgreSQL.

    Args:
        database_name: Database connection name
        pool: asyncpg connection pool

    Returns:
        Dictionary containing tables and views metadata
    """
    async with pool.acquire() as conn:
        # Get all tables and views
        tables_query = """
            SELECT
                schemaname,
                tablename,
                'table' AS type
            FROM pg_tables
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            UNION ALL
            SELECT
                schemaname,
                viewname AS tablename,
                'view' AS type
            FROM pg_views
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY schemaname, tablename
        """
        tables_rows = await conn.fetch(tables_query)

        tables: List[Dict[str, Any]] = []
        views: List[Dict[str, Any]] = []

        for row in tables_rows:
            schema_name = row["schemaname"]
            table_name = row["tablename"]
            table_type = row["type"]

            # Get columns for this table/view
            columns_query = """
                SELECT
                    c.column_name,
                    c.data_type,
                    c.character_maximum_length,
                    c.is_nullable,
                    c.column_default,
                    c.ordinal_position,
                    CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END AS is_primary_key,
                    CASE WHEN uq.column_name IS NOT NULL THEN true ELSE false END AS is_unique
                FROM information_schema.columns c
                LEFT JOIN (
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                        AND tc.table_name = kcu.table_name
                    WHERE tc.table_schema = $1
                        AND tc.table_name = $2
                        AND tc.constraint_type = 'PRIMARY KEY'
                ) pk ON c.column_name = pk.column_name
                LEFT JOIN (
                    SELECT DISTINCT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                        AND tc.table_name = kcu.table_name
                    WHERE tc.table_schema = $1
                        AND tc.table_name = $2
                        AND tc.constraint_type = 'UNIQUE'
                ) uq ON c.column_name = uq.column_name
                WHERE c.table_schema = $1
                    AND c.table_name = $2
                ORDER BY c.ordinal_position
            """
            columns_rows = await conn.fetch(columns_query, schema_name, table_name)

            # Build column metadata
            columns: List[Dict[str, Any]] = []
            for col_row in columns_rows:
                data_type = col_row["data_type"]
                if col_row["character_maximum_length"]:
                    data_type = f"{data_type}({col_row['character_maximum_length']})"

                column_meta = {
                    "name": col_row["column_name"],
                    "dataType": data_type,
                    "nullable": col_row["is_nullable"] == "YES",
                    "primaryKey": col_row["is_primary_key"],
                    "unique": col_row["is_unique"],
                    "defaultValue": col_row["column_default"],
                }
                columns.append(column_meta)

            # Get row count for tables (not views)
            row_count = None
            if table_type == "table":
                try:
                    count_query = f'SELECT COUNT(*) FROM "{schema_name}"."{table_name}"'
                    count_result = await conn.fetchrow(count_query)
                    if count_result:
                        row_count = count_result[0]
                except Exception:
                    # If count fails, leave as None
                    pass

            table_meta = {
                "name": table_name,
                "type": table_type,
                "schemaName": schema_name,
                "columns": columns,
            }
            if row_count is not None:
                table_meta["rowCount"] = row_count

            if table_type == "table":
                tables.append(table_meta)
            else:
                views.append(table_meta)

        return {
            "tables": tables,
            "views": views,
        }


async def get_cached_metadata(
    session: Session, database_name: str
) -> DatabaseMetadata | None:
    """
    Get cached metadata from SQLite if not stale.

    Args:
        session: SQLite database session
        database_name: Database connection name

    Returns:
        DatabaseMetadata if found and not stale, None otherwise
    """
    statement = select(DatabaseMetadata).where(
        DatabaseMetadata.database_name == database_name
    )
    metadata = session.exec(statement).first()

    if metadata and not metadata.is_stale:
        return metadata

    return None


async def cache_metadata(
    session: Session,
    database_name: str,
    metadata_dict: Dict[str, Any],
) -> DatabaseMetadata:
    """
    Cache metadata in SQLite.

    Args:
        session: SQLite database session
        database_name: Database connection name
        metadata_dict: Metadata dictionary to cache

    Returns:
        Cached DatabaseMetadata instance
    """
    # Check if metadata already exists
    statement = select(DatabaseMetadata).where(
        DatabaseMetadata.database_name == database_name
    )
    existing = session.exec(statement).first()

    metadata_json = json.dumps(metadata_dict)
    table_count = len(metadata_dict.get("tables", [])) + len(
        metadata_dict.get("views", [])
    )

    if existing:
        existing.metadata_json = metadata_json
        existing.fetched_at = datetime.now(timezone.utc)
        existing.table_count = table_count
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    else:
        new_metadata = DatabaseMetadata(
            database_name=database_name,
            metadata_json=metadata_json,
            fetched_at=datetime.now(timezone.utc),
            table_count=table_count,
        )
        session.add(new_metadata)
        session.commit()
        session.refresh(new_metadata)
        return new_metadata


async def fetch_metadata(
    session: Session, database_name: str, url: str, force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Fetch database metadata with caching.

    Args:
        session: SQLite database session
        database_name: Database connection name
        url: PostgreSQL connection URL
        force_refresh: Force refresh even if cache exists

    Returns:
        Metadata dictionary
    """
    # Check cache first
    if not force_refresh:
        cached = await get_cached_metadata(session, database_name)
        if cached:
            return json.loads(cached.metadata_json)

    # Fetch fresh metadata
    pool = await get_connection_pool(database_name, url)
    metadata_dict = await extract_metadata(database_name, pool)

    # Cache it
    await cache_metadata(session, database_name, metadata_dict)

    return metadata_dict
