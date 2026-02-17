# LKS Integration - Phase 1: Unified Data Access Layer

## Overview

This document describes the Phase 1 implementation of the Living Knowledge System (LKS) integration with Open Notebook. The goal is to create a unified data access layer that bridges SurrealDB (core business data) and PostgreSQL (living system data).

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Application Layer                            │
│  (API Routers, Services, Domain Models)                         │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Unified Repository Layer                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ UnifiedRepository│  │  DomainRouter   │  │  SyncHookRegistry│ │
│  │   (Interface)   │  │   (Routing)     │  │   (Events)      │ │
│  └────────┬────────┘  └─────────────────┘  └─────────────────┘ │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Backend Adapter Interface                  │   │
│  │         (BackendAdapter abstract class)                 │   │
│  └──────────────────────┬─────────────────┬────────────────┘   │
│                         │                 │                     │
└─────────────────────────┼─────────────────┼─────────────────────┘
                          │                 │
                          ▼                 ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│    SurrealDB Adapter        │   │    PostgreSQL Adapter       │
│  ┌─────────────────────┐    │   │  ┌─────────────────────┐    │
│  │  SurrealDBAdapter   │    │   │  │  PostgreSQLAdapter  │    │
│  │                     │    │   │  │                     │    │
│  │ - query()           │    │   │  │ - query()           │    │
│  │ - get_by_id()       │    │   │  │ - get_by_id()       │    │
│  │ - create()          │    │   │  │ - create()          │    │
│  │ - update()          │    │   │  │ - update()          │    │
│  │ - delete()          │    │   │  │ - delete()          │    │
│  │ - get_related()     │    │   │  │ - get_related()     │    │
│  └─────────────────────┘    │   │  └─────────────────────┘    │
└──────────────┬──────────────┘   └──────────────┬──────────────┘
               │                                 │
               ▼                                 ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│      SurrealDB (Core)       │   │   PostgreSQL + TimescaleDB  │
│  - notebook                 │   │   (Living System)           │
│  - source                   │   │                             │
│  - note                     │   │  - cell_states              │
│  - chat_session             │   │  - agent_states             │
│  - insight                  │   │  - meridian_metrics         │
│  - transformation           │   │  - trigger_records          │
│  - workflow                 │   │  - data_lineage             │
└─────────────────────────────┘   └─────────────────────────────┘
```

## Key Components

### 1. Unified Repository (`unified_repository.py`)

The central abstraction that provides a single interface to both databases.

**Key Classes:**
- `UnifiedRepository` (ABC): Abstract interface
- `UnifiedRepositoryImpl`: Production implementation with routing
- `DomainRouter`: Routes entity types to correct backend
- `QueryResult[T]`: Standardized result wrapper with metadata

**Usage:**
```python
from open_notebook.database import get_unified_repository

repo = await get_unified_repository()

# Query core data (routes to SurrealDB)
notebooks = await repo.query("notebook", limit=10)

# Query living data (routes to PostgreSQL)
cells = await repo.query("cell", state_filter="running")

# Create entity (auto-routed)
new_notebook = await repo.create("notebook", {"name": "My Notebook"})
```

### 2. Backend Adapters

#### SurrealDB Adapter (`surrealdb_adapter.py`)

Wraps the existing `repository.py` functions.

**Entity Types:**
- notebook, source, note, chat_session
- insight, transformation, workflow

**Features:**
- Uses SurrealQL for queries
- Supports graph relationships via `get_related()`
- Handles RecordID parsing

#### PostgreSQL Adapter (`postgresql_adapter.py`)

Wraps the existing `PostgreSQLDatabase` class from LKS.

**Entity Types:**
- cell, agent, meridian_metrics
- trigger_record, data_lineage

**Features:**
- Maps to LKS dataclasses (CellState, AgentState, etc.)
- Uses SQL with asyncpg
- Leverages existing LKS implementation

### 3. Sync Hooks (`sync_hooks.py`)

Event-driven synchronization between domains.

**Key Classes:**
- `SyncEvent`: Event with type, source, entity info
- `SyncHookRegistry`: Pub/sub event registry
- `DefaultSyncHandlers`: Built-in sync handlers

**Event Types:**
- Core → Living: NOTEBOOK_CREATED, SOURCE_CREATED, etc.
- Living → Core: CELL_COMPLETED, CELL_FAILED, etc.

**Usage:**
```python
from open_notebook.database import (
    get_sync_registry,
    SyncEventType,
    on_event,
)

# Register handler
@on_event(SyncEventType.NOTEBOOK_CREATED)
async def on_notebook(event):
    print(f"Notebook created: {event.entity_id}")

# Emit event
await emit_sync_event(
    SyncEventType.NOTEBOOK_CREATED,
    source_domain="core",
    entity_type="notebook",
    entity_id="notebook:123",
    data={"name": "My Notebook"},
)
```

## Data Domain Mapping

| Entity Type | Domain | Backend | Table/Collection |
|-------------|--------|---------|------------------|
| notebook | CORE | SurrealDB | notebook |
| source | CORE | SurrealDB | source |
| note | CORE | SurrealDB | note |
| chat_session | CORE | SurrealDB | chat_session |
| insight | CORE | SurrealDB | insight |
| transformation | CORE | SurrealDB | transformation |
| workflow | CORE | SurrealDB | workflow |
| cell | LIVING | PostgreSQL | cell_states |
| agent | LIVING | PostgreSQL | agent_states |
| meridian_metrics | LIVING | PostgreSQL | meridian_metrics |
| trigger_record | LIVING | PostgreSQL | trigger_records |
| data_lineage | LIVING | PostgreSQL | data_lineage |

## Integration Roadmap

### Phase 1: Unified Data Access ✅ (COMPLETE)

**Deliverables:**
- [x] `unified_repository.py` - Core abstraction
- [x] `surrealdb_adapter.py` - SurrealDB adapter
- [x] `postgresql_adapter.py` - PostgreSQL adapter
- [x] `sync_hooks.py` - Event synchronization
- [x] `__init__.py` - Module exports

**Status:** Scaffold complete, ready for testing

### Phase 2: Sync Hook Implementation (NEXT)

**Tasks:**
1. Implement actual sync handlers
   - Notebook → Agent creation
   - Source → Data lineage registration
   - Cell execution → Note updates

2. Add event emission points
   - Hook into existing repo_create/repo_update calls
   - Add to domain model save() methods

3. Testing
   - Unit tests for sync handlers
   - Integration tests for cross-domain consistency

**Estimated Time:** 2-3 days

### Phase 3: API Unification

**Tasks:**
1. Create unified API router
   - Merge ports 5055 (main) and 8888 (LKS)
   - Single entry point for all operations

2. Update service layer
   - Migrate services to use UnifiedRepository
   - Maintain backward compatibility

3. Frontend updates
   - Update API client
   - Unified data fetching

**Estimated Time:** 3-4 days

### Phase 4: Migration & Validation

**Tasks:**
1. Data migration (if needed)
2. Performance testing
3. Consistency validation
4. Documentation updates

**Estimated Time:** 2-3 days

## Usage Examples

### Basic CRUD

```python
from open_notebook.database import get_unified_repository

async def example():
    repo = await get_unified_repository()
    
    # Create
    notebook = await repo.create("notebook", {
        "name": "Research Notes",
        "description": "My research"
    })
    
    # Read
    found = await repo.get_by_id("notebook", notebook["id"])
    
    # Update
    updated = await repo.update("notebook", notebook["id"], {
        "name": "Updated Name"
    })
    
    # Delete
    success = await repo.delete("notebook", notebook["id"])
```

### Cross-Domain Query

```python
async def get_notebook_with_agent(notebook_id: str):
    """Get notebook and its corresponding agent."""
    repo = await get_unified_repository()
    
    # Query both domains
    notebook = await repo.get_by_id("notebook", notebook_id)
    agent = await repo.get_by_id(
        "agent", 
        f"notebook_agent:{notebook_id}"
    )
    
    return {
        "notebook": notebook.data,
        "agent": agent.data,
    }
```

### Event Handling

```python
from open_notebook.database import (
    get_sync_registry,
    DefaultSyncHandlers,
    emit_sync_event,
    SyncEventType,
)

async def setup_sync():
    # Initialize default handlers
    registry = get_sync_registry()
    handlers = DefaultSyncHandlers()
    handlers.register_all(registry)
    
    # Emit events in your code
    await emit_sync_event(
        SyncEventType.SOURCE_CREATED,
        source_domain="core",
        entity_type="source",
        entity_id="source:456",
        data={"title": "Important Document"},
    )
```

## Testing

### Unit Tests

```python
import pytest
from open_notebook.database import (
    UnifiedRepositoryImpl,
    SurrealDBAdapter,
    PostgreSQLAdapter,
)

@pytest.fixture
async def mock_repo():
    # Create with mock adapters
    return UnifiedRepositoryImpl(
        surreal_adapter=MockSurrealAdapter(),
        postgres_adapter=MockPostgresAdapter(),
    )

async def test_query_routing(mock_repo):
    # Should route to SurrealDB
    result = await mock_repo.query("notebook")
    assert result.source == StorageBackend.SURREALDB
    
    # Should route to PostgreSQL
    result = await mock_repo.query("cell")
    assert result.source == StorageBackend.POSTGRESQL
```

### Integration Tests

```python
async def test_cross_domain_sync():
    """Test that notebook creation triggers agent creation."""
    repo = await get_unified_repository()
    registry = get_sync_registry()
    
    # Setup handler
    events = []
    registry.register(
        SyncEventType.NOTEBOOK_CREATED,
        lambda e: events.append(e)
    )
    
    # Create notebook
    notebook = await repo.create("notebook", {"name": "Test"})
    
    # Verify event was emitted
    assert len(events) == 1
    assert events[0].entity_id == notebook["id"]
```

## Migration Guide

### For Existing Code

**Before:**
```python
from open_notebook.database.repository import repo_query, repo_create

# Direct SurrealDB access
results = await repo_query("SELECT * FROM notebook")
```

**After:**
```python
from open_notebook.database import get_unified_repository

repo = await get_unified_repository()

# Routed automatically
results = await repo.query("notebook")
```

### Gradual Migration

1. **Phase A:** New code uses UnifiedRepository
2. **Phase B:** Existing code updated incrementally
3. **Phase C:** Legacy repo_* functions become wrappers

## Performance Considerations

1. **Query Routing Overhead:** Minimal (dictionary lookup)
2. **Connection Pooling:** PostgreSQL uses pool, SurrealDB per-operation
3. **Cross-Domain Queries:** Require multiple round-trips
4. **Event Processing:** Async handlers run concurrently

## Future Enhancements

1. **Caching Layer:** Redis for hot data
2. **Read Replicas:** For PostgreSQL scaling
3. **Connection Pool:** For SurrealDB
4. **Batch Operations:** Multi-entity queries
5. **GraphQL Interface:** Unified query language

## References

- `unified_repository.py` - Core abstraction
- `surrealdb_adapter.py` - SurrealDB implementation
- `postgresql_adapter.py` - PostgreSQL implementation
- `sync_hooks.py` - Event synchronization
- `repository.py` - Legacy SurrealDB access
- `../skills/living/database/postgresql.py` - LKS PostgreSQL
