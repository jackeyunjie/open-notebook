"""Cross-Domain Synchronization Hooks.

Provides event-driven synchronization between SurrealDB (Core) and PostgreSQL (LKS).
This enables:
- When a notebook is created -> Create corresponding agent in LKS
- When a source is added -> Register data lineage
- When a cell runs -> Update source/note metadata
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set

from loguru import logger


class SyncEventType(Enum):
    """Types of synchronization events."""
    # Core -> Living events
    NOTEBOOK_CREATED = auto()
    NOTEBOOK_UPDATED = auto()
    NOTEBOOK_DELETED = auto()
    SOURCE_CREATED = auto()
    SOURCE_UPDATED = auto()
    SOURCE_DELETED = auto()
    NOTE_CREATED = auto()
    NOTE_UPDATED = auto()
    NOTE_DELETED = auto()
    
    # Living -> Core events
    CELL_COMPLETED = auto()
    CELL_FAILED = auto()
    AGENT_ACTIVATED = auto()
    DATA_TIER_CHANGED = auto()


@dataclass
class SyncEvent:
    """Synchronization event."""
    event_type: SyncEventType
    source_domain: str  # "core" or "living"
    entity_type: str
    entity_id: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    processed: bool = False


# Type alias for event handlers
EventHandler = Callable[[SyncEvent], Coroutine[Any, Any, None]]


class SyncHookRegistry:
    """Registry for synchronization event handlers.
    
    Implements pub/sub pattern for cross-domain events.
    """

    def __init__(self):
        self._handlers: Dict[SyncEventType, List[EventHandler]] = {
            event_type: [] for event_type in SyncEventType
        }
        self._event_history: List[SyncEvent] = []
        self._max_history = 1000

    def register(
        self,
        event_type: SyncEventType,
        handler: EventHandler,
    ) -> None:
        """Register an event handler.
        
        Args:
            event_type: Type of event to handle
            handler: Async handler function
        """
        self._handlers[event_type].append(handler)
        logger.debug(f"Registered handler for {event_type.name}")

    def unregister(
        self,
        event_type: SyncEventType,
        handler: EventHandler,
    ) -> None:
        """Unregister an event handler."""
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            logger.debug(f"Unregistered handler for {event_type.name}")

    async def emit(self, event: SyncEvent) -> None:
        """Emit an event to all registered handlers.
        
        Args:
            event: Event to emit
        """
        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        # Call handlers
        handlers = self._handlers.get(event.event_type, [])
        if not handlers:
            return

        logger.debug(f"Emitting {event.event_type.name} to {len(handlers)} handlers")
        
        # Run handlers concurrently
        tasks = [handler(event) for handler in handlers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log any errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Handler {i} for {event.event_type.name} failed: {result}")

        event.processed = True

    def get_history(
        self,
        event_type: Optional[SyncEventType] = None,
        limit: int = 100,
    ) -> List[SyncEvent]:
        """Get event history.
        
        Args:
            event_type: Filter by event type
            limit: Maximum events to return
            
        Returns:
            List of events
        """
        events = self._event_history
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]


# Global registry instance
_sync_registry: Optional[SyncHookRegistry] = None


def get_sync_registry() -> SyncHookRegistry:
    """Get or create global sync registry."""
    global _sync_registry
    if _sync_registry is None:
        _sync_registry = SyncHookRegistry()
    return _sync_registry


def reset_sync_registry() -> None:
    """Reset global sync registry (for testing)."""
    global _sync_registry
    _sync_registry = None


# ============================================================================
# Default Sync Handlers
# ============================================================================

class DefaultSyncHandlers:
    """Default synchronization handlers.
    
    These handlers implement common cross-domain sync patterns:
    - Notebook <-> Agent sync
    - Source <-> Data Lineage sync
    - Cell execution -> Note update sync
    """

    def __init__(self, unified_repo: Optional[Any] = None):
        """Initialize with optional unified repository.
        
        Args:
            unified_repo: UnifiedRepository instance for data access
        """
        self.repo = unified_repo

    async def on_notebook_created(self, event: SyncEvent) -> None:
        """When notebook created, create corresponding agent in LKS."""
        if not self.repo:
            return

        notebook_data = event.data
        agent_data = {
            "agent_id": f"notebook_agent:{event.entity_id}",
            "name": f"Agent for {notebook_data.get('name', 'Unnamed')}",
            "status": "healthy",
            "energy_level": 1.0,
            "stress_level": 0.0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "skill_states": {},
        }

        try:
            await self.repo.create("agent", agent_data)
            logger.info(f"Created agent for notebook {event.entity_id}")
        except Exception as e:
            logger.error(f"Failed to create agent for notebook: {e}")

    async def on_source_created(self, event: SyncEvent) -> None:
        """When source created, register data lineage."""
        if not self.repo:
            return

        source_data = event.data
        lineage_data = {
            "data_id": f"source:{event.entity_id}",
            "source": event.entity_id,
            "source_type": "source",
            "created_at": datetime.now(),
            "dependencies": [],
            "consumers": [],
            "schema_version": "1.0",
            "quality_score": None,
            "current_tier": "hot",
        }

        try:
            await self.repo.create("data_lineage", lineage_data)
            logger.info(f"Registered data lineage for source {event.entity_id}")
        except Exception as e:
            logger.error(f"Failed to register data lineage: {e}")

    async def on_cell_completed(self, event: SyncEvent) -> None:
        """When cell completes, update related notebook/note."""
        # This would update metadata or trigger downstream processing
        logger.info(f"Cell completed: {event.entity_id}")

    async def on_cell_failed(self, event: SyncEvent) -> None:
        """When cell fails, log error and potentially alert."""
        logger.error(f"Cell failed: {event.entity_id} - {event.data.get('error', 'Unknown error')}")

    def register_all(self, registry: SyncHookRegistry) -> None:
        """Register all default handlers."""
        registry.register(SyncEventType.NOTEBOOK_CREATED, self.on_notebook_created)
        registry.register(SyncEventType.SOURCE_CREATED, self.on_source_created)
        registry.register(SyncEventType.CELL_COMPLETED, self.on_cell_completed)
        registry.register(SyncEventType.CELL_FAILED, self.on_cell_failed)
        logger.info("Registered default sync handlers")


# ============================================================================
# Decorator for Event Handlers
# ============================================================================

def on_event(event_type: SyncEventType):
    """Decorator to register a function as an event handler.
    
    Usage:
        @on_event(SyncEventType.NOTEBOOK_CREATED)
        async def my_handler(event: SyncEvent) -> None:
            # Handle event
            pass
    """
    def decorator(func: EventHandler) -> EventHandler:
        registry = get_sync_registry()
        registry.register(event_type, func)
        return func
    return decorator


# ============================================================================
# Convenience Functions
# ============================================================================

async def emit_sync_event(
    event_type: SyncEventType,
    source_domain: str,
    entity_type: str,
    entity_id: str,
    data: Optional[Dict[str, Any]] = None,
) -> None:
    """Convenience function to emit a sync event.
    
    Args:
        event_type: Type of event
        source_domain: Source domain ("core" or "living")
        entity_type: Type of entity
        entity_id: Entity identifier
        data: Optional event data
    """
    event = SyncEvent(
        event_type=event_type,
        source_domain=source_domain,
        entity_type=entity_type,
        entity_id=entity_id,
        data=data or {},
    )
    registry = get_sync_registry()
    await registry.emit(event)
