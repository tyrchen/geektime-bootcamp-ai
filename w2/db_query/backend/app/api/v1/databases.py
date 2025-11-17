"""Database connection management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from app.database import get_session
from app.models.database import DatabaseConnection, ConnectionStatus, DatabaseType
from app.utils.db_parser import detect_database_type
from app.models.schemas import (
    DatabaseConnectionInput,
    DatabaseConnectionResponse,
    DatabaseMetadataResponse,
    TableMetadata,
)
from app.services.database_service import database_service
from app.services.metadata import fetch_metadata
from datetime import datetime, timezone

router = APIRouter(prefix="/api/v1/dbs", tags=["databases"])


def to_response(conn: DatabaseConnection) -> DatabaseConnectionResponse:
    """Convert DatabaseConnection to response schema."""
    return DatabaseConnectionResponse(
        name=conn.name,
        url=conn.url,
        db_type=conn.db_type.value,
        description=conn.description,
        created_at=conn.created_at,
        updated_at=conn.updated_at,
        last_connected_at=conn.last_connected_at,
        status=conn.status.value,
    )


@router.put("/{name}", response_model=DatabaseConnectionResponse)
async def create_or_update_database(
    name: str,
    input_data: DatabaseConnectionInput,
    session: Session = Depends(get_session),
) -> DatabaseConnectionResponse:
    """
    Create or update a database connection.

    Args:
        name: Database connection name
        input_data: Connection input data
        session: Database session

    Returns:
        Created/updated database connection
    """
    # Validate name format
    if not name.replace("-", "").replace("_", "").isalnum():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name must contain only alphanumeric characters, hyphens, and underscores",
        )

    # Detect or validate database type
    try:
        if input_data.db_type:
            # Validate provided db_type
            db_type = DatabaseType(input_data.db_type.lower())
            # Also verify it matches URL
            detected_type = detect_database_type(input_data.url)
            if db_type != detected_type:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Database type mismatch: provided '{db_type.value}' but URL indicates '{detected_type.value}'",
                )
        else:
            # Auto-detect from URL
            db_type = detect_database_type(input_data.url)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Test connection
    success, error_message = await database_service.test_connection(db_type, input_data.url)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Connection test failed: {error_message}",
        )

    # Check if connection exists
    statement = select(DatabaseConnection).where(
        DatabaseConnection.name == name
    )
    existing = session.exec(statement).first()

    if existing:
        # Update existing connection
        existing.url = input_data.url
        existing.db_type = db_type
        existing.description = input_data.description
        existing.updated_at = datetime.now(timezone.utc)
        existing.last_connected_at = datetime.now(timezone.utc)
        existing.status = ConnectionStatus.ACTIVE
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return to_response(existing)
    else:
        # Create new connection
        new_conn = DatabaseConnection(
            name=name,
            url=input_data.url,
            db_type=db_type,
            description=input_data.description,
            status=ConnectionStatus.ACTIVE,
            last_connected_at=datetime.now(timezone.utc),
        )
        session.add(new_conn)
        session.commit()
        session.refresh(new_conn)
        return to_response(new_conn)


@router.get("", response_model=List[DatabaseConnectionResponse])
async def list_databases(
    session: Session = Depends(get_session),
) -> List[DatabaseConnectionResponse]:
    """
    List all database connections.

    Args:
        session: Database session

    Returns:
        List of database connections
    """
    statement = select(DatabaseConnection)
    connections = session.exec(statement).all()
    return [to_response(conn) for conn in connections]


@router.get("/{name}", response_model=DatabaseMetadataResponse)
async def get_database_metadata(
    name: str,
    refresh: bool = False,
    session: Session = Depends(get_session),
) -> DatabaseMetadataResponse:
    """
    Get database metadata (tables, views, columns).

    Args:
        name: Database connection name
        refresh: Force refresh metadata
        session: Database session

    Returns:
        Database metadata
    """
    # Get connection
    statement = select(DatabaseConnection).where(
        DatabaseConnection.name == name
    )
    connection = session.exec(statement).first()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database connection '{name}' not found",
        )

    # Fetch metadata
    metadata_dict = await fetch_metadata(
        session, name, connection.db_type, connection.url, force_refresh=refresh
    )

    # Parse metadata
    tables = [
        TableMetadata(**table) for table in metadata_dict.get("tables", [])
    ]
    views = [
        TableMetadata(**view) for view in metadata_dict.get("views", [])
    ]

    # Get cache info
    from app.services.metadata import get_cached_metadata

    cached = await get_cached_metadata(session, name)
    fetched_at = cached.fetched_at if cached else datetime.now(timezone.utc)
    is_stale = cached.is_stale if cached else False

    return DatabaseMetadataResponse(
        databaseName=name,
        tables=tables,
        views=views,
        fetchedAt=fetched_at,
        isStale=is_stale,
    )


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_database(
    name: str,
    session: Session = Depends(get_session),
) -> None:
    """
    Delete a database connection.

    Args:
        name: Database connection name
        session: Database session
    """
    # Get connection
    statement = select(DatabaseConnection).where(
        DatabaseConnection.name == name
    )
    connection = session.exec(statement).first()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database connection '{name}' not found",
        )

    # Close connection pool
    await database_service.close_connection(connection.db_type, name)

    # Delete connection
    session.delete(connection)
    session.commit()


@router.post("/{name}/refresh", response_model=DatabaseMetadataResponse)
async def refresh_database_metadata(
    name: str,
    session: Session = Depends(get_session),
) -> DatabaseMetadataResponse:
    """
    Refresh database metadata cache.

    Args:
        name: Database connection name
        session: Database session

    Returns:
        Refreshed database metadata
    """
    # Get connection
    statement = select(DatabaseConnection).where(
        DatabaseConnection.name == name
    )
    connection = session.exec(statement).first()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database connection '{name}' not found",
        )

    # Force refresh metadata
    metadata_dict = await fetch_metadata(
        session, name, connection.db_type, connection.url, force_refresh=True
    )

    # Parse metadata
    tables = [
        TableMetadata(**table) for table in metadata_dict.get("tables", [])
    ]
    views = [
        TableMetadata(**view) for view in metadata_dict.get("views", [])
    ]

    # Get cache info
    from app.services.metadata import get_cached_metadata

    cached = await get_cached_metadata(session, name)
    fetched_at = cached.fetched_at if cached else datetime.now(timezone.utc)
    is_stale = False  # Just refreshed

    return DatabaseMetadataResponse(
        databaseName=name,
        tables=tables,
        views=views,
        fetchedAt=fetched_at,
        isStale=is_stale,
    )
