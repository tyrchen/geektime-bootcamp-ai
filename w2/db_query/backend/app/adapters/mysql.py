"""MySQL database adapter."""

import aiomysql
from typing import Dict, List, Any, Tuple, Optional
from urllib.parse import urlparse
from datetime import datetime

from app.adapters.base import (
    DatabaseAdapter,
    ConnectionConfig,
    QueryResult,
    MetadataResult,
)


class MySQLAdapter(DatabaseAdapter):
    """MySQL database adapter using aiomysql."""

    def _parse_url(self, url: str) -> Dict[str, Any]:
        """Parse MySQL connection URL."""
        parsed = urlparse(url)
        return {
            'host': parsed.hostname or 'localhost',
            'port': parsed.port or 3306,
            'user': parsed.username or 'root',
            'password': parsed.password or '',
            'db': parsed.path.lstrip('/') if parsed.path else None,
        }

    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test MySQL connection."""
        try:
            params = self._parse_url(self.config.url)
            conn = await aiomysql.connect(**params)
            await conn.ensure_closed()
            return True, None
        except Exception as e:
            return False, str(e)

    async def get_connection_pool(self) -> aiomysql.Pool:
        """Get or create aiomysql connection pool."""
        if self._pool is None:
            params = self._parse_url(self.config.url)
            self._pool = await aiomysql.create_pool(
                host=params['host'],
                port=params['port'],
                user=params['user'],
                password=params['password'],
                db=params['db'],
                minsize=self.config.min_pool_size,
                maxsize=self.config.max_pool_size,
                autocommit=True,
            )
        return self._pool

    async def close_connection_pool(self) -> None:
        """Close MySQL connection pool."""
        if self._pool is not None:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None

    async def extract_metadata(self) -> MetadataResult:
        """Extract MySQL metadata from INFORMATION_SCHEMA."""
        pool = await self.get_connection_pool()

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                # Get the actual database name from the connection
                await cursor.execute("SELECT DATABASE()")
                result = await cursor.fetchone()
                db_name = result["DATABASE()"]

                if not db_name:
                    return MetadataResult(tables=[], views=[])

                # Get all tables and views
                tables_query = """
                    SELECT
                        TABLE_SCHEMA as schemaname,
                        TABLE_NAME as tablename,
                        TABLE_TYPE as type
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_SCHEMA = %s
                    ORDER BY TABLE_SCHEMA, TABLE_NAME
                """
                await cursor.execute(tables_query, (db_name,))
                tables_rows = await cursor.fetchall()

                tables: List[Dict[str, Any]] = []
                views: List[Dict[str, Any]] = []

                for row in tables_rows:
                    schema_name = row["schemaname"]
                    table_name = row["tablename"]
                    table_type = "table" if row["type"] == "BASE TABLE" else "view"

                    # Get columns for this table/view
                    columns = await self._get_columns(cursor, schema_name, table_name)

                    # Get row count for tables (not views)
                    row_count = None
                    if table_type == "table":
                        row_count = await self._get_row_count(cursor, schema_name, table_name)

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

        return MetadataResult(tables=tables, views=views)

    async def _get_columns(
        self, cursor, schema_name: str, table_name: str
    ) -> List[Dict[str, Any]]:
        """Get column metadata for a table/view."""
        columns_query = """
            SELECT
                c.COLUMN_NAME as column_name,
                c.DATA_TYPE as data_type,
                c.CHARACTER_MAXIMUM_LENGTH as character_maximum_length,
                c.IS_NULLABLE as is_nullable,
                c.COLUMN_DEFAULT as column_default,
                c.ORDINAL_POSITION as ordinal_position,
                c.COLUMN_KEY as column_key,
                c.EXTRA as extra
            FROM INFORMATION_SCHEMA.COLUMNS c
            WHERE c.TABLE_SCHEMA = %s
                AND c.TABLE_NAME = %s
            ORDER BY c.ORDINAL_POSITION
        """
        await cursor.execute(columns_query, (schema_name, table_name))
        columns_rows = await cursor.fetchall()

        # Get primary key and unique constraints
        constraints_query = """
            SELECT
                kcu.COLUMN_NAME,
                tc.CONSTRAINT_TYPE
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
                ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
                AND tc.TABLE_SCHEMA = kcu.TABLE_SCHEMA
                AND tc.TABLE_NAME = kcu.TABLE_NAME
            WHERE tc.TABLE_SCHEMA = %s
                AND tc.TABLE_NAME = %s
                AND tc.CONSTRAINT_TYPE IN ('PRIMARY KEY', 'UNIQUE')
        """
        await cursor.execute(constraints_query, (schema_name, table_name))
        constraints_rows = await cursor.fetchall()

        # Build constraint maps
        primary_keys = set()
        unique_cols = set()
        for constraint in constraints_rows:
            if constraint["CONSTRAINT_TYPE"] == "PRIMARY KEY":
                primary_keys.add(constraint["COLUMN_NAME"])
            elif constraint["CONSTRAINT_TYPE"] == "UNIQUE":
                unique_cols.add(constraint["COLUMN_NAME"])

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
                "primaryKey": col_row["column_name"] in primary_keys,
                "unique": col_row["column_name"] in unique_cols,
                "defaultValue": col_row["column_default"],
            }
            columns.append(column_meta)

        return columns

    async def _get_row_count(
        self, cursor, schema_name: str, table_name: str
    ) -> Optional[int]:
        """Get row count for a table."""
        try:
            count_query = f"SELECT COUNT(*) as count FROM `{schema_name}`.`{table_name}`"
            await cursor.execute(count_query)
            count_result = await cursor.fetchone()
            if count_result:
                return count_result["count"]
        except Exception:
            # If count fails, return None
            pass
        return None

    async def execute_query(self, sql: str) -> QueryResult:
        """Execute query against MySQL."""
        pool = await self.get_connection_pool()

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                # Execute query
                await cursor.execute(sql)

                # Fetch all rows
                rows = await cursor.fetchall()

                # Get column metadata from cursor description
                columns: List[Dict[str, str]] = []
                if cursor.description:
                    for desc in cursor.description:
                        column_name = desc[0]
                        type_code = desc[1]
                        data_type = self._map_mysql_type(type_code)
                        columns.append({"name": column_name, "dataType": data_type})

                # Convert rows to list of dictionaries
                result_rows: List[Dict[str, Any]] = []
                for row in rows:
                    # Convert datetime objects to strings for JSON serialization
                    processed_row = {}
                    for key, value in row.items():
                        if isinstance(value, datetime):
                            processed_row[key] = value.isoformat()
                        else:
                            processed_row[key] = value
                    result_rows.append(processed_row)

                return QueryResult(
                    columns=columns,
                    rows=result_rows,
                    row_count=len(result_rows)
                )

    def get_dialect_name(self) -> str:
        """Get MySQL dialect name."""
        return "mysql"

    def get_identifier_quote_char(self) -> str:
        """MySQL uses backticks."""
        return "`"

    @staticmethod
    def _map_mysql_type(type_code: int) -> str:
        """Map MySQL type codes to human-readable type names."""
        type_map = {
            0: "DECIMAL",
            1: "TINY",
            2: "SHORT",
            3: "LONG",
            4: "FLOAT",
            5: "DOUBLE",
            6: "NULL",
            7: "TIMESTAMP",
            8: "LONGLONG",
            9: "INT24",
            10: "DATE",
            11: "TIME",
            12: "DATETIME",
            13: "YEAR",
            14: "NEWDATE",
            15: "VARCHAR",
            16: "BIT",
            245: "JSON",
            246: "NEWDECIMAL",
            247: "ENUM",
            248: "SET",
            249: "TINY_BLOB",
            250: "MEDIUM_BLOB",
            251: "LONG_BLOB",
            252: "BLOB",
            253: "VAR_STRING",
            254: "STRING",
            255: "GEOMETRY",
        }
        return type_map.get(type_code, f"UNKNOWN({type_code})")
