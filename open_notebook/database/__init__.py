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

__all__ = [
    # Legacy SurrealDB repository
    "db_connection",
    "ensure_record_id",
    "parse_record_ids",
    "repo_create",
    "repo_delete",
    "repo_insert",
    "repo_query",
    "repo_relate",
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
]
