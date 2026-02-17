"""Repository functions with event emission.

This module wraps the existing repository functions to emit sync events
automatically when data changes. This enables cross-domain synchronization
without modifying existing code.

Usage:
    # Instead of:
    from open_notebook.database.repository import repo_create
    
    # Use:
    from open_notebook.database.repository_with_events import repo_create
    
    # Events are emitted automatically
"""

from typing import Any, Dict, List, Optional

from loguru import logger

# Import original repository functions
from open_notebook.database.repository import (
    db_connection,
    ensure_record_id,
    parse_record_ids,
    repo_create as _original_repo_create,
    repo_delete as _original_repo_delete,
    repo_insert as _original_repo_insert,
    repo_query,
    repo_relate,
    repo_update as _original_repo_update,
    repo_upsert as _original_repo_upsert,
)
from open_notebook.database.sync_hooks import (
    SyncEventType,
    emit_sync_event,
    get_sync_registry,
)


# ============================================================================
# Event-Emitting Wrappers
# ============================================================================

async def repo_create(table: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Create record with event emission.
    
    Emits appropriate sync event based on table name:
    - notebook -> NOTEBOOK_CREATED
    - source -> SOURCE_CREATED
    - note -> NOTE_CREATED
    """
    # Call original function
    result = await _original_repo_create(table, data)
    
    # Emit event if table is tracked
    event_type = _get_create_event_type(table)
    if event_type and result:
        entity_id = result.get("id", "")
        try:
            await emit_sync_event(
                event_type=event_type,
                source_domain="core",
                entity_type=table,
                entity_id=entity_id,
                data={**data, "id": entity_id},
            )
            logger.debug(f"Emitted {event_type.name} for {entity_id}")
        except Exception as e:
            # Log but don't fail the operation
            logger.error(f"Failed to emit sync event: {e}")
    
    return result


async def repo_update(
    table: str,
    id: str,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """Update record with event emission.
    
    Emits appropriate sync event based on table name:
    - notebook -> NOTEBOOK_UPDATED
    - source -> SOURCE_UPDATED
    - note -> NOTE_UPDATED
    """
    # Call original function
    result = await _original_repo_update(table, id, data)
    
    # Emit event if table is tracked
    event_type = _get_update_event_type(table)
    if event_type and result:
        entity_id = result.get("id", id)
        try:
            await emit_sync_event(
                event_type=event_type,
                source_domain="core",
                entity_type=table,
                entity_id=entity_id,
                data=data,
            )
            logger.debug(f"Emitted {event_type.name} for {entity_id}")
        except Exception as e:
            logger.error(f"Failed to emit sync event: {e}")
    
    return result


async def repo_delete(record_id: Any) -> None:
    """Delete record with event emission.
    
    Emits appropriate sync event based on record type.
    """
    # Extract table and id from record_id
    table, entity_id = _parse_record_id(record_id)
    
    # Call original function
    await _original_repo_delete(record_id)
    
    # Emit event if table is tracked
    event_type = _get_delete_event_type(table)
    if event_type:
        try:
            await emit_sync_event(
                event_type=event_type,
                source_domain="core",
                entity_type=table,
                entity_id=entity_id,
                data={},
            )
            logger.debug(f"Emitted {event_type.name} for {entity_id}")
        except Exception as e:
            logger.error(f"Failed to emit sync event: {e}")


async def repo_upsert(
    table: str,
    id: str,
    data: Dict[str, Any],
    add_timestamp: bool = True,
) -> Dict[str, Any]:
    """Upsert record with event emission.
    
    Emits CREATE or UPDATE event based on whether record existed.
    """
    # Check if record exists to determine event type
    from open_notebook.database.repository import repo_query
    
    existing = await repo_query(
        f"SELECT * FROM {table}:{id}",
    )
    
    is_create = not existing
    
    # Call original function
    result = await _original_repo_upsert(table, id, data, add_timestamp)
    
    # Emit appropriate event
    if is_create:
        event_type = _get_create_event_type(table)
    else:
        event_type = _get_update_event_type(table)
    
    if event_type and result:
        entity_id = result.get("id", f"{table}:{id}")
        try:
            await emit_sync_event(
                event_type=event_type,
                source_domain="core",
                entity_type=table,
                entity_id=entity_id,
                data=data,
            )
            logger.debug(f"Emitted {event_type.name} for {entity_id}")
        except Exception as e:
            logger.error(f"Failed to emit sync event: {e}")
    
    return result


async def repo_insert(
    table: str,
    data_list: List[Dict[str, Any]],
    ignore_duplicates: bool = False,
) -> List[Dict[str, Any]]:
    """Bulk insert with event emission.
    
    Emits CREATE event for each inserted record.
    """
    # Call original function
    results = await _original_repo_insert(table, data_list, ignore_duplicates)
    
    # Emit events for each record
    event_type = _get_create_event_type(table)
    if event_type:
        for result in results:
            entity_id = result.get("id", "")
            try:
                await emit_sync_event(
                    event_type=event_type,
                    source_domain="core",
                    entity_type=table,
                    entity_id=entity_id,
                    data=result,
                )
            except Exception as e:
                logger.error(f"Failed to emit sync event: {e}")
    
    return results


# ============================================================================
# Helper Functions
# ============================================================================

def _get_create_event_type(table: str) -> Optional[SyncEventType]:
    """Get CREATE event type for table."""
    mapping = {
        "notebook": SyncEventType.NOTEBOOK_CREATED,
        "source": SyncEventType.SOURCE_CREATED,
        "note": SyncEventType.NOTE_CREATED,
    }
    return mapping.get(table)


def _get_update_event_type(table: str) -> Optional[SyncEventType]:
    """Get UPDATE event type for table."""
    mapping = {
        "notebook": SyncEventType.NOTEBOOK_UPDATED,
        "source": SyncEventType.SOURCE_UPDATED,
        "note": SyncEventType.NOTE_UPDATED,
    }
    return mapping.get(table)


def _get_delete_event_type(table: str) -> Optional[SyncEventType]:
    """Get DELETE event type for table."""
    mapping = {
        "notebook": SyncEventType.NOTEBOOK_DELETED,
        "source": SyncEventType.SOURCE_DELETED,
        "note": SyncEventType.NOTE_DELETED,
    }
    return mapping.get(table)


def _parse_record_id(record_id: Any) -> tuple[str, str]:
    """Parse record_id into (table, id) tuple."""
    from surrealdb import RecordID
    
    if isinstance(record_id, RecordID):
        return record_id.tb, str(record_id.id)
    elif isinstance(record_id, str):
        if ":" in record_id:
            parts = record_id.split(":", 1)
            return parts[0], parts[1]
    return "unknown", str(record_id)


# ============================================================================
# Re-exports (functions that don't need event emission)
# ============================================================================

__all__ = [
    # Event-emitting wrappers
    "repo_create",
    "repo_update",
    "repo_delete",
    "repo_upsert",
    "repo_insert",
    
    # Direct re-exports (no events needed)
    "repo_query",
    "repo_relate",
    "db_connection",
    "ensure_record_id",
    "parse_record_ids",
]
