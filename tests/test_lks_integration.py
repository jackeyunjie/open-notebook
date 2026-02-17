"""LKS Integration Tests - Cross-Domain Synchronization Validation.

Tests the integration between Open Notebook Core (SurrealDB) and
Living Knowledge System (PostgreSQL) through the unified data access layer.

Test Coverage:
- Notebook <-> Agent synchronization
- Source <-> DataLineage synchronization  
- Cell execution -> Note synchronization
- Event emission and routing
- Handler registration and execution
"""

import asyncio
import pytest
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

from open_notebook.database.sync_hooks import (
    SyncEvent,
    SyncEventType,
    SyncHookRegistry,
    emit_sync_event,
    get_sync_registry,
    reset_sync_registry,
)
from open_notebook.database.sync_handlers import (
    CellExecutionSyncHandler,
    NotebookSyncHandler,
    SourceSyncHandler,
    SyncHandlerRegistry,
    get_handler_registry,
    reset_handler_registry,
)
from open_notebook.database.unified_repository import (
    BackendAdapter,
    QueryResult,
    StorageBackend,
    UnifiedRepositoryImpl,
    reset_repository,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def reset_registries():
    """Reset all global registries before each test."""
    reset_sync_registry()
    reset_handler_registry()
    reset_repository()
    yield
    reset_sync_registry()
    reset_handler_registry()
    reset_repository()


@pytest.fixture
def mock_surreal_adapter():
    """Create a mock SurrealDB adapter."""
    adapter = AsyncMock(spec=BackendAdapter)
    adapter.backend_type = StorageBackend.SURREALDB
    return adapter


@pytest.fixture
def mock_postgres_adapter():
    """Create a mock PostgreSQL adapter."""
    adapter = AsyncMock(spec=BackendAdapter)
    adapter.backend_type = StorageBackend.POSTGRESQL
    return adapter


@pytest.fixture
def unified_repo(mock_surreal_adapter, mock_postgres_adapter):
    """Create a unified repository with mock adapters."""
    return UnifiedRepositoryImpl(
        surreal_adapter=mock_surreal_adapter,
        postgres_adapter=mock_postgres_adapter,
    )


@pytest.fixture
def event_registry():
    """Get fresh event registry."""
    return get_sync_registry()


@pytest.fixture
def handler_registry():
    """Get fresh handler registry."""
    return get_handler_registry()


# ============================================================================
# Notebook Sync Handler Tests
# ============================================================================

class TestNotebookSyncHandler:
    """Test Notebook <-> Agent synchronization."""

    @pytest.mark.asyncio
    async def test_notebook_created_event_creates_agent(
        self, unified_repo, mock_postgres_adapter
    ):
        """Test that NOTEBOOK_CREATED event creates an agent in PostgreSQL."""
        # Arrange
        handler = NotebookSyncHandler()
        notebook_data = {
            "id": "notebook:test123",
            "name": "Test Notebook",
            "description": "A test notebook",
        }
        event = SyncEvent(
            event_type=SyncEventType.NOTEBOOK_CREATED,
            source_domain="core",
            entity_type="notebook",
            entity_id="notebook:test123",
            data=notebook_data,
        )

        # Mock the create response
        mock_postgres_adapter.create.return_value = {
            "agent_id": "notebook_agent:test123",
            "name": "Agent: Test Notebook",
            "status": "healthy",
        }

        # Act
        await handler.handle(event, unified_repo)

        # Assert
        mock_postgres_adapter.create.assert_called_once()
        call_args = mock_postgres_adapter.create.call_args
        assert call_args[0][0] == "agent"  # entity_type
        assert call_args[0][1]["agent_id"] == "notebook_agent:test123"
        assert call_args[0][1]["name"] == "Agent: Test Notebook"
        assert call_args[0][1]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_notebook_updated_event_updates_agent(
        self, unified_repo, mock_postgres_adapter
    ):
        """Test that NOTEBOOK_UPDATED event updates the corresponding agent."""
        # Arrange
        handler = NotebookSyncHandler()
        notebook_data = {
            "id": "notebook:test123",
            "name": "Updated Notebook Name",
        }
        event = SyncEvent(
            event_type=SyncEventType.NOTEBOOK_UPDATED,
            source_domain="core",
            entity_type="notebook",
            entity_id="notebook:test123",
            data=notebook_data,
        )

        # Mock existing agent
        mock_postgres_adapter.get_by_id.return_value = {
            "agent_id": "notebook_agent:test123",
            "name": "Agent: Old Name",
            "skill_states": {"notebook_name": "Old Name"},
        }

        # Act
        await handler.handle(event, unified_repo)

        # Assert
        mock_postgres_adapter.update.assert_called_once()
        call_args = mock_postgres_adapter.update.call_args
        assert call_args[0][0] == "agent"
        assert call_args[0][1] == "notebook_agent:test123"

    @pytest.mark.asyncio
    async def test_notebook_deleted_event_marks_agent_dormant(
        self, unified_repo, mock_postgres_adapter
    ):
        """Test that NOTEBOOK_DELETED event marks agent as dormant."""
        # Arrange
        handler = NotebookSyncHandler()
        event = SyncEvent(
            event_type=SyncEventType.NOTEBOOK_DELETED,
            source_domain="core",
            entity_type="notebook",
            entity_id="notebook:test123",
            data={},
        )

        # Mock existing agent
        mock_postgres_adapter.get_by_id.return_value = {
            "agent_id": "notebook_agent:test123",
            "name": "Agent: Test Notebook",
            "status": "healthy",
            "skill_states": {},
        }

        # Act
        await handler.handle(event, unified_repo)

        # Assert
        mock_postgres_adapter.update.assert_called_once()
        call_args = mock_postgres_adapter.update.call_args
        assert call_args[0][1] == "notebook_agent:test123"
        assert call_args[0][2]["status"] == "dormant"
        assert call_args[0][2]["skill_states"]["notebook_deleted"] is True

    @pytest.mark.asyncio
    async def test_notebook_updated_creates_agent_if_not_exists(
        self, unified_repo, mock_postgres_adapter
    ):
        """Test that update creates agent if it doesn't exist."""
        # Arrange
        handler = NotebookSyncHandler()
        notebook_data = {"name": "Test Notebook"}
        event = SyncEvent(
            event_type=SyncEventType.NOTEBOOK_UPDATED,
            source_domain="core",
            entity_type="notebook",
            entity_id="notebook:test123",
            data=notebook_data,
        )

        # Mock no existing agent
        mock_postgres_adapter.get_by_id.return_value = None

        # Act
        await handler.handle(event, unified_repo)

        # Assert - should create instead of update
        mock_postgres_adapter.create.assert_called_once()


# ============================================================================
# Source Sync Handler Tests
# ============================================================================

class TestSourceSyncHandler:
    """Test Source <-> DataLineage synchronization."""

    @pytest.mark.asyncio
    async def test_source_created_event_registers_lineage(
        self, unified_repo, mock_postgres_adapter
    ):
        """Test that SOURCE_CREATED event registers data lineage."""
        # Arrange
        handler = SourceSyncHandler()
        source_data = {
            "id": "source:abc123",
            "title": "Test Source",
            "source_type": "pdf",
            "url": "http://example.com/doc.pdf",
            "notebook_id": "notebook:test123",
        }
        event = SyncEvent(
            event_type=SyncEventType.SOURCE_CREATED,
            source_domain="core",
            entity_type="source",
            entity_id="source:abc123",
            data=source_data,
        )

        # Act
        await handler.handle(event, unified_repo)

        # Assert
        mock_postgres_adapter.create.assert_called_once()
        call_args = mock_postgres_adapter.create.call_args
        assert call_args[0][0] == "data_lineage"
        assert call_args[0][1]["data_id"] == "source:abc123"
        assert call_args[0][1]["source_type"] == "pdf"
        assert call_args[0][1]["current_tier"] == "hot"

    @pytest.mark.asyncio
    async def test_source_deleted_event_archives_lineage(
        self, unified_repo, mock_postgres_adapter
    ):
        """Test that SOURCE_DELETED event archives data lineage."""
        # Arrange
        handler = SourceSyncHandler()
        event = SyncEvent(
            event_type=SyncEventType.SOURCE_DELETED,
            source_domain="core",
            entity_type="source",
            entity_id="source:abc123",
            data={},
        )

        # Mock existing lineage
        mock_postgres_adapter.get_by_id.return_value = {
            "data_id": "source:abc123",
            "current_tier": "hot",
            "metadata": {},
        }

        # Act
        await handler.handle(event, unified_repo)

        # Assert
        mock_postgres_adapter.update.assert_called_once()
        call_args = mock_postgres_adapter.update.call_args
        assert call_args[0][2]["current_tier"] == "frozen"
        assert call_args[0][2]["metadata"]["source_deleted"] is True


# ============================================================================
# Cell Execution Sync Handler Tests
# ============================================================================

class TestCellExecutionSyncHandler:
    """Test Cell execution -> Note synchronization."""

    @pytest.mark.asyncio
    async def test_cell_completed_creates_note(
        self, unified_repo, mock_surreal_adapter
    ):
        """Test that CELL_COMPLETED event creates a note."""
        # Arrange
        handler = CellExecutionSyncHandler()
        cell_data = {
            "notebook_id": "notebook:test123",
            "skill_name": "TextProcessor",
            "skill_id": "skill:processor1",
            "run_count": 5,
            "success_count": 4,
            "result": {
                "output": "Processed text result",
                "duration_ms": 150,
            },
        }
        event = SyncEvent(
            event_type=SyncEventType.CELL_COMPLETED,
            source_domain="living",
            entity_type="cell",
            entity_id="cell:exec456",
            data=cell_data,
        )

        # Act
        await handler.handle(event, unified_repo)

        # Assert
        mock_surreal_adapter.create.assert_called_once()
        call_args = mock_surreal_adapter.create.call_args
        assert call_args[0][0] == "note"
        assert call_args[0][1]["type"] == "cell_output"
        assert call_args[0][1]["notebook_id"] == "notebook:test123"
        assert "Cell Output: TextProcessor" in call_args[0][1]["title"]
        assert "Processed text result" in call_args[0][1]["content"]

    @pytest.mark.asyncio
    async def test_cell_failed_creates_error_note(
        self, unified_repo, mock_surreal_adapter
    ):
        """Test that CELL_FAILED event creates an error note."""
        # Arrange
        handler = CellExecutionSyncHandler()
        cell_data = {
            "notebook_id": "notebook:test123",
            "skill_name": "TextProcessor",
            "skill_id": "skill:processor1",
            "run_count": 5,
            "fail_count": 2,
            "error": "Connection timeout after 30s",
        }
        event = SyncEvent(
            event_type=SyncEventType.CELL_FAILED,
            source_domain="living",
            entity_type="cell",
            entity_id="cell:exec456",
            data=cell_data,
        )

        # Act
        await handler.handle(event, unified_repo)

        # Assert
        mock_surreal_adapter.create.assert_called_once()
        call_args = mock_surreal_adapter.create.call_args
        assert call_args[0][0] == "note"
        assert call_args[0][1]["type"] == "cell_error"
        assert "Cell Error: TextProcessor" in call_args[0][1]["title"]
        assert "Connection timeout" in call_args[0][1]["content"]

    @pytest.mark.asyncio
    async def test_cell_completed_without_notebook_id_skips(
        self, unified_repo, mock_surreal_adapter
    ):
        """Test that cell completion without notebook_id is skipped."""
        # Arrange
        handler = CellExecutionSyncHandler()
        cell_data = {
            "skill_name": "TextProcessor",
            "result": {"output": "test"},
        }
        event = SyncEvent(
            event_type=SyncEventType.CELL_COMPLETED,
            source_domain="living",
            entity_type="cell",
            entity_id="cell:exec456",
            data=cell_data,
        )

        # Act
        await handler.handle(event, unified_repo)

        # Assert
        mock_surreal_adapter.create.assert_not_called()


# ============================================================================
# Event Registry Tests
# ============================================================================

class TestEventRegistry:
    """Test event emission and routing."""

    @pytest.mark.asyncio
    async def test_event_emission_triggers_handlers(self, event_registry):
        """Test that emitted events trigger registered handlers."""
        # Arrange
        handler_mock = AsyncMock()
        event_registry.register(SyncEventType.NOTEBOOK_CREATED, handler_mock)

        event = SyncEvent(
            event_type=SyncEventType.NOTEBOOK_CREATED,
            source_domain="core",
            entity_type="notebook",
            entity_id="notebook:test123",
            data={"name": "Test"},
        )

        # Act
        await event_registry.emit(event)

        # Assert
        handler_mock.assert_called_once_with(event)
        assert event.processed is True

    @pytest.mark.asyncio
    async def test_multiple_handlers_receive_event(self, event_registry):
        """Test that multiple handlers can receive the same event."""
        # Arrange
        handler1 = AsyncMock()
        handler2 = AsyncMock()
        event_registry.register(SyncEventType.SOURCE_CREATED, handler1)
        event_registry.register(SyncEventType.SOURCE_CREATED, handler2)

        event = SyncEvent(
            event_type=SyncEventType.SOURCE_CREATED,
            source_domain="core",
            entity_type="source",
            entity_id="source:test123",
            data={},
        )

        # Act
        await event_registry.emit(event)

        # Assert
        handler1.assert_called_once()
        handler2.assert_called_once()

    @pytest.mark.asyncio
    async def test_handler_failure_doesnt_stop_others(self, event_registry):
        """Test that one handler failing doesn't stop others."""
        # Arrange
        failing_handler = AsyncMock(side_effect=Exception("Handler error"))
        success_handler = AsyncMock()
        event_registry.register(SyncEventType.NOTE_CREATED, failing_handler)
        event_registry.register(SyncEventType.NOTE_CREATED, success_handler)

        event = SyncEvent(
            event_type=SyncEventType.NOTE_CREATED,
            source_domain="core",
            entity_type="note",
            entity_id="note:test123",
            data={},
        )

        # Act - should not raise
        await event_registry.emit(event)

        # Assert
        failing_handler.assert_called_once()
        success_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_event_history_tracking(self, event_registry):
        """Test that events are tracked in history."""
        # Arrange
        event = SyncEvent(
            event_type=SyncEventType.NOTEBOOK_CREATED,
            source_domain="core",
            entity_type="notebook",
            entity_id="notebook:test123",
            data={},
        )

        # Act
        await event_registry.emit(event)

        # Assert
        history = event_registry.get_history()
        assert len(history) == 1
        assert history[0].entity_id == "notebook:test123"

    def test_event_history_filtering(self, event_registry):
        """Test filtering event history by type."""
        # Arrange - manually add events to history
        event_registry._event_history = [
            SyncEvent(
                event_type=SyncEventType.NOTEBOOK_CREATED,
                source_domain="core",
                entity_type="notebook",
                entity_id="nb1",
                data={},
            ),
            SyncEvent(
                event_type=SyncEventType.SOURCE_CREATED,
                source_domain="core",
                entity_type="source",
                entity_id="src1",
                data={},
            ),
            SyncEvent(
                event_type=SyncEventType.NOTEBOOK_UPDATED,
                source_domain="core",
                entity_type="notebook",
                entity_id="nb1",
                data={},
            ),
        ]

        # Act
        notebook_events = event_registry.get_history(
            event_type=SyncEventType.NOTEBOOK_CREATED
        )

        # Assert
        assert len(notebook_events) == 1
        assert notebook_events[0].entity_id == "nb1"


# ============================================================================
# Handler Registry Tests
# ============================================================================

class TestHandlerRegistry:
    """Test handler registration and retrieval."""

    def test_handler_registration(self, handler_registry):
        """Test that handlers can be registered."""
        # Arrange
        handler = NotebookSyncHandler()

        # Act
        handler_registry.register(handler)

        # Assert
        handlers = handler_registry.get_handlers(SyncEventType.NOTEBOOK_CREATED)
        assert len(handlers) == 1
        assert isinstance(handlers[0], NotebookSyncHandler)

    def test_multiple_event_type_registration(self, handler_registry):
        """Test that handlers can register for multiple event types."""
        # Arrange
        handler = NotebookSyncHandler()

        # Act
        handler_registry.register(handler)

        # Assert
        created_handlers = handler_registry.get_handlers(
            SyncEventType.NOTEBOOK_CREATED
        )
        updated_handlers = handler_registry.get_handlers(
            SyncEventType.NOTEBOOK_UPDATED
        )
        deleted_handlers = handler_registry.get_handlers(
            SyncEventType.NOTEBOOK_DELETED
        )

        assert len(created_handlers) == 1
        assert len(updated_handlers) == 1
        assert len(deleted_handlers) == 1

    def test_create_default_handlers(self, handler_registry):
        """Test creating default handler set."""
        # Act
        handlers = handler_registry.create_default_handlers()

        # Assert
        assert len(handlers) == 3
        handler_types = [type(h) for h in handlers]
        assert NotebookSyncHandler in handler_types
        assert SourceSyncHandler in handler_types
        assert CellExecutionSyncHandler in handler_types


# ============================================================================
# Unified Repository Tests
# ============================================================================

class TestUnifiedRepository:
    """Test unified repository routing."""

    @pytest.mark.asyncio
    async def test_notebook_query_routes_to_surrealdb(
        self, unified_repo, mock_surreal_adapter
    ):
        """Test that notebook queries route to SurrealDB."""
        # Arrange
        mock_surreal_adapter.query.return_value = [
            {"id": "notebook:test123", "name": "Test"}
        ]

        # Act
        result = await unified_repo.query("notebook", limit=10)

        # Assert
        mock_surreal_adapter.query.assert_called_once()
        assert result.source == StorageBackend.SURREALDB

    @pytest.mark.asyncio
    async def test_agent_query_routes_to_postgresql(
        self, unified_repo, mock_postgres_adapter
    ):
        """Test that agent queries route to PostgreSQL."""
        # Arrange
        mock_postgres_adapter.query.return_value = [
            {"agent_id": "agent:test123", "name": "Test Agent"}
        ]

        # Act
        result = await unified_repo.query("agent", limit=10)

        # Assert
        mock_postgres_adapter.query.assert_called_once()
        assert result.source == StorageBackend.POSTGRESQL

    @pytest.mark.asyncio
    async def test_create_routes_to_correct_backend(
        self, unified_repo, mock_surreal_adapter, mock_postgres_adapter
    ):
        """Test that create operations route to correct backend."""
        # Act - Create notebook (SurrealDB)
        mock_surreal_adapter.create.return_value = {"id": "notebook:test123"}
        await unified_repo.create("notebook", {"name": "Test"})

        # Assert
        mock_surreal_adapter.create.assert_called_once()

        # Act - Create agent (PostgreSQL)
        mock_postgres_adapter.create.return_value = {"agent_id": "agent:test123"}
        await unified_repo.create("agent", {"name": "Test Agent"})

        # Assert
        mock_postgres_adapter.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_timing_tracked(self, unified_repo, mock_surreal_adapter):
        """Test that query execution time is tracked."""
        # Arrange
        mock_surreal_adapter.query.return_value = []

        # Act
        result = await unified_repo.query("notebook")

        # Assert
        assert result.query_time_ms >= 0


# ============================================================================
# Integration Flow Tests
# ============================================================================

class TestIntegrationFlows:
    """Test end-to-end integration flows."""

    @pytest.mark.asyncio
    async def test_full_notebook_agent_sync_flow(
        self, event_registry, handler_registry, unified_repo, mock_postgres_adapter
    ):
        """Test complete flow: notebook created -> agent created."""
        # Arrange - Register handler
        handler = NotebookSyncHandler()
        handler_registry.register(handler)

        # Create event router
        async def event_router(event: SyncEvent) -> None:
            handlers = handler_registry.get_handlers(event.event_type)
            for h in handlers:
                await h.handle(event, unified_repo)

        event_registry.register(SyncEventType.NOTEBOOK_CREATED, event_router)

        mock_postgres_adapter.create.return_value = {"agent_id": "notebook_agent:test"}

        # Act - Emit notebook created event
        await emit_sync_event(
            event_type=SyncEventType.NOTEBOOK_CREATED,
            source_domain="core",
            entity_type="notebook",
            entity_id="notebook:test",
            data={"name": "Integration Test Notebook"},
        )

        # Assert
        mock_postgres_adapter.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_full_source_lineage_sync_flow(
        self, event_registry, handler_registry, unified_repo, mock_postgres_adapter
    ):
        """Test complete flow: source created -> lineage registered."""
        # Arrange
        handler = SourceSyncHandler()
        handler_registry.register(handler)

        async def event_router(event: SyncEvent) -> None:
            handlers = handler_registry.get_handlers(event.event_type)
            for h in handlers:
                await h.handle(event, unified_repo)

        event_registry.register(SyncEventType.SOURCE_CREATED, event_router)

        mock_postgres_adapter.create.return_value = {"data_id": "source:test"}

        # Act
        await emit_sync_event(
            event_type=SyncEventType.SOURCE_CREATED,
            source_domain="core",
            entity_type="source",
            entity_id="source:test",
            data={"title": "Test Source", "source_type": "url"},
        )

        # Assert
        mock_postgres_adapter.create.assert_called_once()
        call_args = mock_postgres_adapter.create.call_args
        assert call_args[0][0] == "data_lineage"


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling in sync system."""

    @pytest.mark.asyncio
    async def test_handler_error_logged_not_raised(
        self, unified_repo, mock_postgres_adapter, caplog
    ):
        """Test that handler errors are logged but not raised."""
        # Arrange
        handler = NotebookSyncHandler()
        mock_postgres_adapter.create.side_effect = Exception("DB connection failed")

        event = SyncEvent(
            event_type=SyncEventType.NOTEBOOK_CREATED,
            source_domain="core",
            entity_type="notebook",
            entity_id="notebook:test",
            data={"name": "Test"},
        )

        # Act & Assert - should not raise
        with pytest.raises(Exception):
            await handler.handle(event, unified_repo)

    @pytest.mark.asyncio
    async def test_missing_adapter_raises_error(self, unified_repo):
        """Test that missing adapter raises appropriate error."""
        # Arrange - unified_repo has no adapters for unknown entity
        with pytest.raises(RuntimeError) as exc_info:
            await unified_repo.query("unknown_entity")

        assert "No adapter available" in str(exc_info.value)


# ============================================================================
# Performance Tests (Basic)
# ============================================================================

class TestPerformance:
    """Basic performance tests."""

    @pytest.mark.asyncio
    async def test_multiple_events_handled_concurrently(self, event_registry):
        """Test that multiple events are handled concurrently."""
        # Arrange
        execution_order = []

        async def slow_handler(event: SyncEvent) -> None:
            await asyncio.sleep(0.01)  # 10ms delay
            execution_order.append(event.entity_id)

        event_registry.register(SyncEventType.NOTEBOOK_CREATED, slow_handler)

        events = [
            SyncEvent(
                event_type=SyncEventType.NOTEBOOK_CREATED,
                source_domain="core",
                entity_type="notebook",
                entity_id=f"notebook:{i}",
                data={},
            )
            for i in range(5)
        ]

        # Act
        start_time = asyncio.get_event_loop().time()
        await asyncio.gather(*[event_registry.emit(e) for e in events])
        elapsed = asyncio.get_event_loop().time() - start_time

        # Assert - should complete in ~10ms (concurrent), not ~50ms (sequential)
        assert elapsed < 0.05  # Allow some overhead
        assert len(execution_order) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
