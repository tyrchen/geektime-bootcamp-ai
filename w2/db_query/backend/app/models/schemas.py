"""API request/response schemas with camelCase aliases."""

from pydantic import BaseModel, Field
from typing import Literal, Any
from datetime import datetime
from app.models.query import QuerySource


# Database Connection Schemas
class DatabaseConnectionInput(BaseModel):
    """Input schema for creating/updating database connection."""

    url: str = Field(..., description="PostgreSQL connection URL")
    description: str | None = Field(default=None, max_length=200)


class DatabaseConnectionResponse(BaseModel):
    """Response schema for database connection."""

    name: str
    url: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    last_connected_at: datetime | None
    status: str


# Metadata Schemas
class ColumnMetadata(BaseModel):
    """Column metadata schema."""

    name: str = Field(..., max_length=63)
    data_type: str = Field(..., alias="dataType")
    nullable: bool
    primary_key: bool = Field(..., alias="primaryKey")
    unique: bool = False
    default_value: str | None = Field(default=None, alias="defaultValue")
    comment: str | None = None


class TableMetadata(BaseModel):
    """Table/View metadata schema."""

    name: str = Field(..., max_length=63)
    type: Literal["table", "view"]
    columns: list[ColumnMetadata]
    row_count: int | None = Field(default=None, alias="rowCount")
    schema_name: str = Field(default="public", alias="schemaName")


class DatabaseMetadataResponse(BaseModel):
    """Response schema for database metadata."""

    database_name: str = Field(..., alias="databaseName")
    tables: list[TableMetadata]
    views: list[TableMetadata]
    fetched_at: datetime = Field(..., alias="fetchedAt")
    is_stale: bool = Field(..., alias="isStale")


# Query Schemas
class QueryInput(BaseModel):
    """Input schema for SQL query execution."""

    sql: str = Field(..., min_length=1, description="SQL SELECT query to execute")


class QueryColumn(BaseModel):
    """Query result column schema."""

    name: str
    data_type: str = Field(..., alias="dataType")


class QueryResult(BaseModel):
    """Query result response schema."""

    columns: list[QueryColumn]
    rows: list[dict[str, Any]]
    row_count: int = Field(..., alias="rowCount")
    execution_time_ms: int = Field(..., alias="executionTimeMs")
    sql: str


class QueryHistoryEntry(BaseModel):
    """Query history entry schema."""

    id: int
    database_name: str = Field(..., alias="databaseName")
    sql_text: str = Field(..., alias="sqlText")
    executed_at: datetime = Field(..., alias="executedAt")
    execution_time_ms: int | None = Field(None, alias="executionTimeMs")
    row_count: int | None = Field(None, alias="rowCount")
    success: bool
    error_message: str | None = Field(None, alias="errorMessage")
    query_source: str = Field(..., alias="querySource")


# Natural Language Schemas
class NaturalLanguageInput(BaseModel):
    """Input schema for natural language to SQL conversion."""

    prompt: str = Field(..., min_length=5, max_length=500)


class GeneratedSqlResponse(BaseModel):
    """Response schema for generated SQL."""

    sql: str
    explanation: str


# Error Schema
class ErrorResponse(BaseModel):
    """Error response schema."""

    error: dict[str, Any]
