"""Database module for Open Notebook.

Provides data access layer with support for:
- SurrealDB: Core business data (notebooks, sources, notes)
- PostgreSQL: Living Knowledge System data (cells, agents, metrics)
- Unified Repository: Single interface to both backends
"""

# Legacy repository functions (SurrealDB only)
from .repository import (
    db_connection,
    ensure_record_id,
    parse_record_ids,
    repo_create,
    repo_delete,
    repo_insert,
    repo_query,
    repo_relate,
    repo_update,
    repo_upsert,
)

# Unified repository (multi-backend)
from .unified_repository import (
    BackendAdapter,
    DataDomain,
    DomainRouter,
    EntityReference,
    QueryResult,
    StorageBackend,
    UnifiedRepository,
    UnifiedRepositoryImpl,
    get_unified_repository,
    reset_repository,
)

# Backend adapters
from .surrealdb_adapter import SurrealDBAdapter, create_surrealdb_adapter
from .postgresql_adapter import PostgreSQLAdapter, create_postgresql_adapter

# Sync hooks
from .sync_hooks import (
    DefaultSyncHandlers,
    SyncEvent,
    SyncEventType,
    SyncHookRegistry,
    emit_sync_event,
    get_sync_registry,
    on_event,
    reset_sync_registry,
)

# Sync handlers (Phase 2)
from .sync_handlers import (
    CellExecutionSyncHandler,
    NotebookSyncHandler,
    SourceSyncHandler,
    SyncHandler,
    SyncHandlerRegistry,
    get_handler_registry,
    reset_handler_registry,
)

# Sync initializer (Phase 2)
from .sync_initializer import (
    SyncSystem,
    get_sync_system,
    initialize_sync_system,
    reset_sync_system,
    shutdown_sync_system,
)

# Repository with events (Phase 2)
from .repository_with_events import (
    repo_create,
    repo_delete,
    repo_insert,
    repo_update,
    repo_upsert,
)

__all__ = [
    # Legacy SurrealDB repository
    "db_connection",
    "ensure_record_id",
    "parse_record_ids",
    "repo_query",
    "repo_relate",
    
    # Repository with events (Phase 2 - recommended)
    "repo_create",
    "repo_delete",
    "repo_insert",
    "repo_update",
    "repo_upsert",
    
    # Unified repository
    "BackendAdapter",
    "DataDomain",
    "DomainRouter",
    "EntityReference",
    "QueryResult",
    "StorageBackend",
    "UnifiedRepository",
    "UnifiedRepositoryImpl",
    "get_unified_repository",
    "reset_repository",
    
    # Adapters
    "SurrealDBAdapter",
    "PostgreSQLAdapter",
    "create_surrealdb_adapter",
    "create_postgresql_adapter",
    
    # Sync hooks
    "DefaultSyncHandlers",
    "SyncEvent",
    "SyncEventType",
    "SyncHookRegistry",
    "emit_sync_event",
    "get_sync_registry",
    "on_event",
    "reset_sync_registry",
    
    # Sync handlers (Phase 2)
    "CellExecutionSyncHandler",
    "NotebookSyncHandler",
    "SourceSyncHandler",
    "SyncHandler",
    "SyncHandlerRegistry",
    "get_handler_registry",
    "reset_handler_registry",
    
    # Sync initializer (Phase 2)
    "SyncSystem",
    "get_sync_system",
    "initialize_sync_system",
    "reset_sync_system",
    "shutdown_sync_system",
]
