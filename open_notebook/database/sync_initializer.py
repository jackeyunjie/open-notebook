"""Sync System Initializer.

Handles initialization of the cross-domain synchronization system:
1. Creates unified repository with both backends
2. Registers all sync handlers
3. Connects handlers to event registry
4. Provides lifecycle management (startup/shutdown)

Usage:
    from open_notebook.database.sync_initializer import SyncSystem
    
    # Initialize
    sync_system = SyncSystem()
    await sync_system.startup()
    
    # Use the repository
    repo = sync_system.repository
    
    # Shutdown
    await sync_system.shutdown()
"""

from typing import Optional

from loguru import logger

from open_notebook.database.sync_handlers import (
    NotebookSyncHandler,
    SourceSyncHandler,
    CellExecutionSyncHandler,
    SyncHandler,
    SyncHandlerRegistry,
    get_handler_registry,
)
from open_notebook.database.sync_hooks import (
    SyncEvent,
    SyncHookRegistry,
    get_sync_registry,
)
from open_notebook.database.unified_repository import (
    BackendAdapter,
    UnifiedRepository,
    UnifiedRepositoryImpl,
    get_unified_repository,
    reset_repository,
)


class SyncSystem:
    """Manages the cross-domain synchronization system lifecycle.
    
    This is the main entry point for enabling sync functionality.
    It handles:
    - Repository initialization
    - Handler registration
    - Event routing
    - Lifecycle management
    """

    def __init__(
        self,
        surreal_adapter: Optional[BackendAdapter] = None,
        postgres_adapter: Optional[BackendAdapter] = None,
        auto_create_adapters: bool = True,
    ):
        """Initialize sync system.
        
        Args:
            surreal_adapter: Optional SurrealDB adapter
            postgres_adapter: Optional PostgreSQL adapter
            auto_create_adapters: Whether to auto-create adapters if not provided
        """
        self.surreal_adapter = surreal_adapter
        self.postgres_adapter = postgres_adapter
        self.auto_create_adapters = auto_create_adapters
        
        self._repository: Optional[UnifiedRepository] = None
        self._handler_registry = get_handler_registry()
        self._event_registry = get_sync_registry()
        self._handlers: list[SyncHandler] = []
        self._initialized = False

    @property
    def repository(self) -> Optional[UnifiedRepository]:
        """Get the unified repository instance."""
        return self._repository

    async def startup(self) -> None:
        """Initialize and start the sync system.
        
        This method:
        1. Creates/connects backend adapters
        2. Initializes unified repository
        3. Registers sync handlers
        4. Starts listening for events
        """
        if self._initialized:
            logger.warning("SyncSystem already initialized")
            return

        logger.info("Starting SyncSystem...")

        # Step 1: Create adapters if needed
        if self.auto_create_adapters:
            await self._create_adapters()

        # Step 2: Initialize repository
        self._repository = await get_unified_repository(
            surreal_adapter=self.surreal_adapter,
            postgres_adapter=self.postgres_adapter,
        )
        logger.info("Unified repository initialized")

        # Step 3: Register handlers
        self._register_handlers()
        logger.info("Sync handlers registered")

        # Step 4: Subscribe to events
        self._subscribe_to_events()
        logger.info("Subscribed to sync events")

        self._initialized = True
        logger.info("SyncSystem startup complete")

    async def shutdown(self) -> None:
        """Shutdown the sync system.
        
        This method:
        1. Unsubscribes from events
        2. Clears handlers
        3. Disconnects adapters
        """
        if not self._initialized:
            return

        logger.info("Shutting down SyncSystem...")

        # Unsubscribe from events
        self._unsubscribe_from_events()

        # Clear handlers
        self._handlers.clear()

        # Disconnect adapters
        if self.surreal_adapter:
            await self.surreal_adapter.disconnect()
        if self.postgres_adapter:
            await self.postgres_adapter.disconnect()

        # Reset global instances
        reset_repository()

        self._initialized = False
        logger.info("SyncSystem shutdown complete")

    async def _create_adapters(self) -> None:
        """Create and connect backend adapters."""
        # Create SurrealDB adapter
        if self.surreal_adapter is None:
            from open_notebook.database.surrealdb_adapter import create_surrealdb_adapter
            try:
                self.surreal_adapter = await create_surrealdb_adapter()
                logger.info("SurrealDB adapter created")
            except Exception as e:
                logger.error(f"Failed to create SurrealDB adapter: {e}")
                raise

        # Create PostgreSQL adapter
        if self.postgres_adapter is None:
            from open_notebook.database.postgresql_adapter import create_postgresql_adapter
            try:
                self.postgres_adapter = await create_postgresql_adapter()
                logger.info("PostgreSQL adapter created")
            except Exception as e:
                logger.warning(f"Failed to create PostgreSQL adapter: {e}")
                logger.warning("SyncSystem will operate without PostgreSQL backend")
                # Don't raise - system can work without LKS

    def _register_handlers(self) -> None:
        """Register all sync handlers."""
        # Create default handlers
        default_handlers = self._handler_registry.create_default_handlers()
        
        for handler in default_handlers:
            self._handler_registry.register(handler)
            self._handlers.append(handler)
            logger.debug(f"Registered handler: {handler.__class__.__name__}")

    def _subscribe_to_events(self) -> None:
        """Subscribe to sync events."""
        # Create a wrapper that routes events to handlers
        async def event_router(event: SyncEvent) -> None:
            await self._route_event(event)

        # Subscribe to all event types
        for event_type in self._handler_registry._handlers.keys():
            if self._handler_registry._handlers[event_type]:  # Only if handlers exist
                self._event_registry.register(event_type, event_router)
                logger.debug(f"Subscribed to {event_type.name}")

    def _unsubscribe_from_events(self) -> None:
        """Unsubscribe from sync events."""
        # The registry doesn't support individual unsubscription
        # So we reset it (handlers will be re-registered on next startup)
        from open_notebook.database.sync_hooks import reset_sync_registry
        reset_sync_registry()

    async def _route_event(self, event: SyncEvent) -> None:
        """Route an event to appropriate handlers.
        
        Args:
            event: The sync event to route
        """
        if not self._repository:
            logger.error("Cannot route event: repository not initialized")
            return

        # Get handlers for this event type
        handlers = self._handler_registry.get_handlers(event.event_type)
        
        if not handlers:
            return

        logger.debug(
            f"Routing {event.event_type.name} to {len(handlers)} handlers"
        )

        # Execute handlers
        for handler in handlers:
            try:
                await handler.handle(event, self._repository)
            except Exception as e:
                logger.error(
                    f"Handler {handler.__class__.__name__} failed: {e}"
                )
                # Continue with other handlers


# ============================================================================
# Convenience Functions
# ============================================================================

_global_sync_system: Optional[SyncSystem] = None


async def initialize_sync_system(
    surreal_adapter: Optional[BackendAdapter] = None,
    postgres_adapter: Optional[BackendAdapter] = None,
) -> SyncSystem:
    """Initialize and return the global sync system.
    
    Args:
        surreal_adapter: Optional SurrealDB adapter
        postgres_adapter: Optional PostgreSQL adapter
        
    Returns:
        Initialized SyncSystem instance
    """
    global _global_sync_system
    
    if _global_sync_system is None:
        _global_sync_system = SyncSystem(
            surreal_adapter=surreal_adapter,
            postgres_adapter=postgres_adapter,
        )
        await _global_sync_system.startup()
    
    return _global_sync_system


def get_sync_system() -> Optional[SyncSystem]:
    """Get the global sync system instance."""
    return _global_sync_system


async def shutdown_sync_system() -> None:
    """Shutdown the global sync system."""
    global _global_sync_system
    
    if _global_sync_system:
        await _global_sync_system.shutdown()
        _global_sync_system = None


def reset_sync_system() -> None:
    """Reset the global sync system (for testing)."""
    global _global_sync_system
    _global_sync_system = None
