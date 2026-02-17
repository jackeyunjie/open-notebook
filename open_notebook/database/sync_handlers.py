"""Cross-Domain Synchronization Handlers.

Implements concrete synchronization logic between Core (SurrealDB) and
Living (PostgreSQL) domains.

Handlers:
- NotebookSyncHandler: Notebook <-> Agent sync
- SourceSyncHandler: Source <-> DataLineage sync
- CellExecutionSyncHandler: Cell execution -> Note update
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional

from loguru import logger

from open_notebook.database.sync_hooks import SyncEvent, SyncEventType


class SyncHandler(ABC):
    """Abstract base class for sync handlers."""

    @property
    @abstractmethod
    def event_types(self) -> list[SyncEventType]:
        """Return list of event types this handler handles."""
        pass

    @abstractmethod
    async def handle(self, event: SyncEvent, repo: Any) -> None:
        """Handle the sync event.
        
        Args:
            event: The sync event
            repo: UnifiedRepository instance
        """
        pass


# ============================================================================
# Notebook Sync Handler
# ============================================================================

class NotebookSyncHandler(SyncHandler):
    """Synchronizes Notebook (Core) with Agent (Living).
    
    Patterns:
    - Notebook created -> Create Agent to manage it
    - Notebook updated -> Update Agent configuration
    - Notebook deleted -> Mark Agent as dormant
    """

    @property
    def event_types(self) -> list[SyncEventType]:
        return [
            SyncEventType.NOTEBOOK_CREATED,
            SyncEventType.NOTEBOOK_UPDATED,
            SyncEventType.NOTEBOOK_DELETED,
        ]

    def _get_agent_id(self, notebook_id: str) -> str:
        """Generate agent ID from notebook ID."""
        # Remove table prefix if present
        if ":" in notebook_id:
            notebook_id = notebook_id.split(":")[1]
        return f"notebook_agent:{notebook_id}"

    async def handle(self, event: SyncEvent, repo: Any) -> None:
        """Handle notebook events."""
        handler_map = {
            SyncEventType.NOTEBOOK_CREATED: self._on_created,
            SyncEventType.NOTEBOOK_UPDATED: self._on_updated,
            SyncEventType.NOTEBOOK_DELETED: self._on_deleted,
        }
        
        handler = handler_map.get(event.event_type)
        if handler:
            await handler(event, repo)

    async def _on_created(self, event: SyncEvent, repo: Any) -> None:
        """Create agent when notebook is created."""
        notebook_data = event.data
        agent_id = self._get_agent_id(event.entity_id)
        
        agent_data = {
            "agent_id": agent_id,
            "name": f"Agent: {notebook_data.get('name', 'Unnamed Notebook')}",
            "status": "healthy",
            "energy_level": 1.0,
            "stress_level": 0.0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "avg_response_time_ms": None,
            "last_executed": None,
            "skill_states": {
                "notebook_id": event.entity_id,
                "notebook_name": notebook_data.get('name', ''),
                "auto_process": True,
            },
        }
        
        try:
            result = await repo.create("agent", agent_data)
            logger.info(
                f"Created agent {agent_id} for notebook {event.entity_id}"
            )
        except Exception as e:
            logger.error(f"Failed to create agent for notebook: {e}")
            raise

    async def _on_updated(self, event: SyncEvent, repo: Any) -> None:
        """Update agent when notebook is updated."""
        notebook_data = event.data
        agent_id = self._get_agent_id(event.entity_id)
        
        # Check if agent exists
        existing = await repo.get_by_id("agent", agent_id)
        if not existing.data:
            logger.warning(f"Agent {agent_id} not found, creating new one")
            await self._on_created(event, repo)
            return
        
        # Update agent configuration
        update_data = {}
        if "name" in notebook_data:
            update_data["name"] = f"Agent: {notebook_data['name']}"
        
        # Merge skill_states
        current_states = existing.data.get("skill_states", {})
        new_states = {
            **current_states,
            "notebook_name": notebook_data.get("name", current_states.get("notebook_name", "")),
            "updated_at": datetime.now().isoformat(),
        }
        update_data["skill_states"] = new_states
        
        try:
            await repo.update("agent", agent_id, update_data)
            logger.info(f"Updated agent {agent_id} for notebook {event.entity_id}")
        except Exception as e:
            logger.error(f"Failed to update agent for notebook: {e}")
            raise

    async def _on_deleted(self, event: SyncEvent, repo: Any) -> None:
        """Mark agent as dormant when notebook is deleted."""
        agent_id = self._get_agent_id(event.entity_id)
        
        # Check if agent exists
        existing = await repo.get_by_id("agent", agent_id)
        if not existing.data:
            logger.warning(f"Agent {agent_id} not found for deletion")
            return
        
        # Mark as dormant instead of deleting (for audit trail)
        update_data = {
            "status": "dormant",
            "skill_states": {
                **existing.data.get("skill_states", {}),
                "notebook_deleted_at": datetime.now().isoformat(),
                "notebook_deleted": True,
            },
        }
        
        try:
            await repo.update("agent", agent_id, update_data)
            logger.info(f"Marked agent {agent_id} as dormant (notebook deleted)")
        except Exception as e:
            logger.error(f"Failed to update agent status: {e}")
            raise


# ============================================================================
# Source Sync Handler
# ============================================================================

class SourceSyncHandler(SyncHandler):
    """Synchronizes Source (Core) with DataLineage (Living).
    
    Patterns:
    - Source created -> Register data lineage
    - Source updated -> Update lineage metadata
    - Source deleted -> Mark lineage as archived
    """

    @property
    def event_types(self) -> list[SyncEventType]:
        return [
            SyncEventType.SOURCE_CREATED,
            SyncEventType.SOURCE_UPDATED,
            SyncEventType.SOURCE_DELETED,
        ]

    def _get_data_id(self, source_id: str) -> str:
        """Generate data lineage ID from source ID."""
        if ":" in source_id:
            source_id = source_id.split(":")[1]
        return f"source:{source_id}"

    async def handle(self, event: SyncEvent, repo: Any) -> None:
        """Handle source events."""
        handler_map = {
            SyncEventType.SOURCE_CREATED: self._on_created,
            SyncEventType.SOURCE_UPDATED: self._on_updated,
            SyncEventType.SOURCE_DELETED: self._on_deleted,
        }
        
        handler = handler_map.get(event.event_type)
        if handler:
            await handler(event, repo)

    async def _on_created(self, event: SyncEvent, repo: Any) -> None:
        """Register data lineage when source is created."""
        source_data = event.data
        data_id = self._get_data_id(event.entity_id)
        
        # Determine source type
        source_type = source_data.get("source_type", "unknown")
        
        lineage_data = {
            "data_id": data_id,
            "source": event.entity_id,
            "source_type": source_type,
            "created_at": datetime.now(),
            "dependencies": [],
            "consumers": [],
            "schema_version": "1.0",
            "quality_score": None,
            "current_tier": "hot",
            "metadata": {
                "title": source_data.get("title", ""),
                "url": source_data.get("url", ""),
                "notebook_id": source_data.get("notebook_id", ""),
            },
        }
        
        try:
            await repo.create("data_lineage", lineage_data)
            logger.info(f"Registered data lineage for source {event.entity_id}")
        except Exception as e:
            logger.error(f"Failed to register data lineage: {e}")
            raise

    async def _on_updated(self, event: SyncEvent, repo: Any) -> None:
        """Update data lineage when source is updated."""
        source_data = event.data
        data_id = self._get_data_id(event.entity_id)
        
        # Check if lineage exists
        existing = await repo.get_by_id("data_lineage", data_id)
        if not existing.data:
            logger.warning(f"Data lineage {data_id} not found, creating new one")
            await self._on_created(event, repo)
            return
        
        # Update metadata
        current_metadata = existing.data.get("metadata", {})
        new_metadata = {
            **current_metadata,
            "title": source_data.get("title", current_metadata.get("title", "")),
            "updated_at": datetime.now().isoformat(),
        }
        
        update_data = {
            "metadata": new_metadata,
        }
        
        try:
            await repo.update("data_lineage", data_id, update_data)
            logger.info(f"Updated data lineage for source {event.entity_id}")
        except Exception as e:
            logger.error(f"Failed to update data lineage: {e}")
            raise

    async def _on_deleted(self, event: SyncEvent, repo: Any) -> None:
        """Archive data lineage when source is deleted."""
        data_id = self._get_data_id(event.entity_id)
        
        # Check if lineage exists
        existing = await repo.get_by_id("data_lineage", data_id)
        if not existing.data:
            logger.warning(f"Data lineage {data_id} not found for deletion")
            return
        
        # Move to frozen tier (archived)
        update_data = {
            "current_tier": "frozen",
            "metadata": {
                **existing.data.get("metadata", {}),
                "source_deleted_at": datetime.now().isoformat(),
                "source_deleted": True,
            },
        }
        
        try:
            await repo.update("data_lineage", data_id, update_data)
            logger.info(f"Archived data lineage for deleted source {event.entity_id}")
        except Exception as e:
            logger.error(f"Failed to archive data lineage: {e}")
            raise


# ============================================================================
# Cell Execution Sync Handler
# ============================================================================

class CellExecutionSyncHandler(SyncHandler):
    """Synchronizes Cell execution results with Notes.
    
    Patterns:
    - Cell completed -> Create/update note with results
    - Cell failed -> Create error note
    """

    @property
    def event_types(self) -> list[SyncEventType]:
        return [
            SyncEventType.CELL_COMPLETED,
            SyncEventType.CELL_FAILED,
        ]

    async def handle(self, event: SyncEvent, repo: Any) -> None:
        """Handle cell execution events."""
        if event.event_type == SyncEventType.CELL_COMPLETED:
            await self._on_completed(event, repo)
        elif event.event_type == SyncEventType.CELL_FAILED:
            await self._on_failed(event, repo)

    async def _on_completed(self, event: SyncEvent, repo: Any) -> None:
        """Create or update note when cell completes successfully."""
        cell_data = event.data
        
        # Extract relevant info
        notebook_id = cell_data.get("notebook_id")
        cell_id = event.entity_id
        result = cell_data.get("result", {})
        output = result.get("output", "")
        
        if not notebook_id:
            logger.warning(f"No notebook_id in cell completion event: {cell_id}")
            return
        
        # Generate note title and content
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        note_title = f"Cell Output: {cell_data.get('skill_name', 'Unknown')} ({timestamp})"
        
        note_content = f"""# {note_title}

**Cell ID:** {cell_id}
**Skill:** {cell_data.get('skill_name', 'Unknown')}
**Completed:** {timestamp}
**Duration:** {result.get('duration_ms', 'N/A')}ms

## Output

{output}

## Metadata

- Run Count: {cell_data.get('run_count', 0)}
- Success Count: {cell_data.get('success_count', 0)}
"""
        
        note_data = {
            "title": note_title,
            "content": note_content,
            "notebook_id": notebook_id,
            "source_id": None,
            "type": "cell_output",
            "metadata": {
                "cell_id": cell_id,
                "skill_id": cell_data.get("skill_id"),
                "execution_time": timestamp,
                "duration_ms": result.get("duration_ms"),
            },
        }
        
        try:
            result = await repo.create("note", note_data)
            logger.info(
                f"Created note from cell {cell_id} in notebook {notebook_id}"
            )
        except Exception as e:
            logger.error(f"Failed to create note from cell output: {e}")
            raise

    async def _on_failed(self, event: SyncEvent, repo: Any) -> None:
        """Create error note when cell fails."""
        cell_data = event.data
        
        notebook_id = cell_data.get("notebook_id")
        cell_id = event.entity_id
        error = cell_data.get("error", "Unknown error")
        
        if not notebook_id:
            logger.warning(f"No notebook_id in cell failure event: {cell_id}")
            return
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        note_title = f"Cell Error: {cell_data.get('skill_name', 'Unknown')} ({timestamp})"
        
        note_content = f"""# {note_title}

**Cell ID:** {cell_id}
**Skill:** {cell_data.get('skill_name', 'Unknown')}
**Failed:** {timestamp}

## Error

```
{error}
```

## Context

- Run Count: {cell_data.get('run_count', 0)}
- Fail Count: {cell_data.get('fail_count', 0)}
- Last Error At: {cell_data.get('last_error_at', 'N/A')}
"""
        
        note_data = {
            "title": note_title,
            "content": note_content,
            "notebook_id": notebook_id,
            "source_id": None,
            "type": "cell_error",
            "metadata": {
                "cell_id": cell_id,
                "skill_id": cell_data.get("skill_id"),
                "error_time": timestamp,
                "error": error,
            },
        }
        
        try:
            result = await repo.create("note", note_data)
            logger.info(
                f"Created error note from cell {cell_id} in notebook {notebook_id}"
            )
        except Exception as e:
            logger.error(f"Failed to create error note: {e}")
            raise


# ============================================================================
# Handler Registry
# ============================================================================

class SyncHandlerRegistry:
    """Registry for all sync handlers."""

    def __init__(self):
        self._handlers: Dict[SyncEventType, list[SyncHandler]] = {
            event_type: [] for event_type in SyncEventType
        }

    def register(self, handler: SyncHandler) -> None:
        """Register a sync handler."""
        for event_type in handler.event_types:
            self._handlers[event_type].append(handler)
            logger.debug(f"Registered {handler.__class__.__name__} for {event_type.name}")

    def get_handlers(self, event_type: SyncEventType) -> list[SyncHandler]:
        """Get all handlers for an event type."""
        return self._handlers.get(event_type, [])

    def create_default_handlers(self) -> list[SyncHandler]:
        """Create default set of sync handlers."""
        return [
            NotebookSyncHandler(),
            SourceSyncHandler(),
            CellExecutionSyncHandler(),
        ]


# Global registry instance
_handler_registry: Optional[SyncHandlerRegistry] = None


def get_handler_registry() -> SyncHandlerRegistry:
    """Get or create global handler registry."""
    global _handler_registry
    if _handler_registry is None:
        _handler_registry = SyncHandlerRegistry()
    return _handler_registry


def reset_handler_registry() -> None:
    """Reset global handler registry (for testing)."""
    global _handler_registry
    _handler_registry = None
