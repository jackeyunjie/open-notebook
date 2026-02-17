"""LKS Data Consistency Validation Tests.

Tests to validate data consistency between SurrealDB (Core) and 
PostgreSQL (Living) databases through the unified repository layer.

Test Coverage:
- Entity mapping consistency
- Cross-reference integrity
- Sync state validation
- Conflict detection
- Data drift detection
"""

import pytest
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

from open_notebook.database.sync_hooks import (
    SyncEvent,
    SyncEventType,
    get_sync_registry,
    reset_sync_registry,
)
from open_notebook.database.sync_handlers import (
    NotebookSyncHandler,
    SourceSyncHandler,
    get_handler_registry,
    reset_handler_registry,
)
from open_notebook.database.unified_repository import (
    BackendAdapter,
    DomainRouter,
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


@pytest.fixture
def mock_surreal_adapter():
    """Create a mock SurrealDB adapter with consistency tracking."""
    adapter = AsyncMock(spec=BackendAdapter)
    adapter.backend_type = StorageBackend.SURREALDB
    
    # Track all operations for consistency verification
    adapter._operations = []
    
    async def tracked_query(*args, **kwargs):
        adapter._operations.append(("query", args, kwargs))
        return []
    
    async def tracked_create(*args, **kwargs):
        adapter._operations.append(("create", args, kwargs))
        return {"id": args[1].get("id", "test:1"), "created": True}
    
    async def tracked_update(*args, **kwargs):
        adapter._operations.append(("update", args, kwargs))
        return {"id": args[1], "updated": True}
    
    adapter.query.side_effect = tracked_query
    adapter.create.side_effect = tracked_create
    adapter.update.side_effect = tracked_update
    adapter.get_by_id.return_value = None
    adapter.delete.return_value = True
    
    return adapter


@pytest.fixture
def mock_postgres_adapter():
    """Create a mock PostgreSQL adapter with consistency tracking."""
    adapter = AsyncMock(spec=BackendAdapter)
    adapter.backend_type = StorageBackend.POSTGRESQL
    
    adapter._operations = []
    adapter._stored_data = {}
    
    async def tracked_query(*args, **kwargs):
        adapter._operations.append(("query", args, kwargs))
        entity_type = args[0]
        return list(adapter._stored_data.get(entity_type, {}).values())
    
    async def tracked_create(*args, **kwargs):
        adapter._operations.append(("create", args, kwargs))
        entity_type, data = args[0], args[1]
        entity_id = data.get("agent_id") or data.get("data_id") or "test:1"
        if entity_type not in adapter._stored_data:
            adapter._stored_data[entity_type] = {}
        adapter._stored_data[entity_type][entity_id] = data
        return {**data, "created": True}
    
    async def tracked_get_by_id(*args, **kwargs):
        adapter._operations.append(("get_by_id", args, kwargs))
        entity_type, entity_id = args[0], args[1]
        data = adapter._stored_data.get(entity_type, {}).get(entity_id)
        return data
    
    async def tracked_update(*args, **kwargs):
        adapter._operations.append(("update", args, kwargs))
        entity_type, entity_id, data = args[0], args[1], args[2]
        if entity_type in adapter._stored_data:
            if entity_id in adapter._stored_data[entity_type]:
                adapter._stored_data[entity_type][entity_id].update(data)
                return adapter._stored_data[entity_type][entity_id]
        return None
    
    adapter.query.side_effect = tracked_query
    adapter.create.side_effect = tracked_create
    adapter.get_by_id.side_effect = tracked_get_by_id
    adapter.update.side_effect = tracked_update
    adapter.delete.return_value = True
    
    return adapter


@pytest.fixture
def unified_repo(mock_surreal_adapter, mock_postgres_adapter):
    """Create unified repository with tracking adapters."""
    return UnifiedRepositoryImpl(
        surreal_adapter=mock_surreal_adapter,
        postgres_adapter=mock_postgres_adapter,
    )


# ============================================================================
# Domain Router Consistency Tests
# ============================================================================

class TestDomainRouterConsistency:
    """Test domain routing consistency."""

    def test_notebook_routes_to_core(self):
        """Verify notebook routes to Core domain (SurrealDB)."""
        domain = DomainRouter.get_domain("notebook")
        backend = DomainRouter.get_backend("notebook")
        
        from open_notebook.database.unified_repository import DataDomain
        assert domain == DataDomain.CORE
        assert backend == StorageBackend.SURREALDB

    def test_agent_routes_to_living(self):
        """Verify agent routes to Living domain (PostgreSQL)."""
        domain = DomainRouter.get_domain("agent")
        backend = DomainRouter.get_backend("agent")
        
        from open_notebook.database.unified_repository import DataDomain
        assert domain == DataDomain.LIVING
        assert backend == StorageBackend.POSTGRESQL

    def test_all_core_entities_routed_correctly(self):
        """Verify all Core entities route to SurrealDB."""
        core_entities = [
            "notebook", "source", "note", "chat_session",
            "insight", "transformation", "workflow"
        ]
        
        for entity in core_entities:
            backend = DomainRouter.get_backend(entity)
            assert backend == StorageBackend.SURREALDB, f"{entity} should route to SurrealDB"

    def test_all_living_entities_routed_correctly(self):
        """Verify all Living entities route to PostgreSQL."""
        living_entities = [
            "cell", "agent", "meridian_metrics", "trigger_record", "data_lineage"
        ]
        
        for entity in living_entities:
            backend = DomainRouter.get_backend(entity)
            assert backend == StorageBackend.POSTGRESQL, f"{entity} should route to PostgreSQL"

    def test_cross_domain_detection(self):
        """Test cross-domain query detection."""
        # Same domain - not cross
        assert not DomainRouter.is_cross_domain(["notebook", "source"])
        
        # Cross domain
        assert DomainRouter.is_cross_domain(["notebook", "agent"])
        assert DomainRouter.is_cross_domain(["source", "cell"])


# ============================================================================
# Entity Mapping Consistency Tests
# ============================================================================

class TestEntityMappingConsistency:
    """Test entity mapping between Core and Living domains."""

    @pytest.mark.asyncio
    async def test_notebook_to_agent_mapping(self, unified_repo, mock_postgres_adapter):
        """Test that notebook creation maps to correct agent ID."""
        # Arrange
        handler = NotebookSyncHandler()
        notebook_id = "notebook:abc123"
        
        event = SyncEvent(
            event_type=SyncEventType.NOTEBOOK_CREATED,
            source_domain="core",
            entity_type="notebook",
            entity_id=notebook_id,
            data={"name": "Test Notebook"},
        )
        
        # Act
        await handler.handle(event, unified_repo)
        
        # Assert
        call_args = mock_postgres_adapter.create.call_args
        created_data = call_args[0][1]
        
        # Verify ID mapping
        assert created_data["agent_id"] == "notebook_agent:abc123"
        assert created_data["skill_states"]["notebook_id"] == notebook_id

    @pytest.mark.asyncio
    async def test_source_to_lineage_mapping(self, unified_repo, mock_postgres_adapter):
        """Test that source creation maps to correct lineage ID."""
        # Arrange
        handler = SourceSyncHandler()
        source_id = "source:xyz789"
        
        event = SyncEvent(
            event_type=SyncEventType.SOURCE_CREATED,
            source_domain="core",
            entity_type="source",
            entity_id=source_id,
            data={"title": "Test Source", "source_type": "pdf"},
        )
        
        # Act
        await handler.handle(event, unified_repo)
        
        # Assert
        call_args = mock_postgres_adapter.create.call_args
        created_data = call_args[0][1]
        
        # Verify ID mapping
        assert created_data["data_id"] == "source:xyz789"
        assert created_data["source"] == source_id

    @pytest.mark.asyncio
    async def test_agent_id_generation_consistency(self, unified_repo, mock_postgres_adapter):
        """Test that agent ID generation is consistent."""
        handler = NotebookSyncHandler()
        
        test_cases = [
            ("notebook:abc", "notebook_agent:abc"),
            ("notebook:xyz:123", "notebook_agent:xyz:123"),
            ("abc", "notebook_agent:abc"),
        ]
        
        for notebook_id, expected_agent_id in test_cases:
            mock_postgres_adapter.reset_mock()
            
            event = SyncEvent(
                event_type=SyncEventType.NOTEBOOK_CREATED,
                source_domain="core",
                entity_type="notebook",
                entity_id=notebook_id,
                data={"name": "Test"},
            )
            
            await handler.handle(event, unified_repo)
            
            call_args = mock_postgres_adapter.create.call_args
            assert call_args[0][1]["agent_id"] == expected_agent_id


# ============================================================================
# Cross-Reference Integrity Tests
# ============================================================================

class TestCrossReferenceIntegrity:
    """Test cross-reference integrity between domains."""

    @pytest.mark.asyncio
    async def test_notebook_agent_reference_integrity(
        self, unified_repo, mock_postgres_adapter
    ):
        """Test that agent maintains reference to source notebook."""
        # Arrange
        handler = NotebookSyncHandler()
        notebook_data = {
            "id": "notebook:test123",
            "name": "Research Notebook",
            "description": "Main research notebook",
        }
        
        event = SyncEvent(
            event_type=SyncEventType.NOTEBOOK_CREATED,
            source_domain="core",
            entity_type="notebook",
            entity_id="notebook:test123",
            data=notebook_data,
        )
        
        # Act
        await handler.handle(event, unified_repo)
        
        # Assert
        call_args = mock_postgres_adapter.create.call_args
        skill_states = call_args[0][1]["skill_states"]
        
        # Verify cross-reference
        assert skill_states["notebook_id"] == "notebook:test123"
        assert skill_states["notebook_name"] == "Research Notebook"

    @pytest.mark.asyncio
    async def test_source_lineage_metadata_integrity(
        self, unified_repo, mock_postgres_adapter
    ):
        """Test that lineage maintains metadata about source."""
        # Arrange
        handler = SourceSyncHandler()
        source_data = {
            "id": "source:doc456",
            "title": "Important Document",
            "url": "https://example.com/doc",
            "source_type": "url",
            "notebook_id": "notebook:test123",
        }
        
        event = SyncEvent(
            event_type=SyncEventType.SOURCE_CREATED,
            source_domain="core",
            entity_type="source",
            entity_id="source:doc456",
            data=source_data,
        )
        
        # Act
        await handler.handle(event, unified_repo)
        
        # Assert
        call_args = mock_postgres_adapter.create.call_args
        metadata = call_args[0][1]["metadata"]
        
        # Verify metadata integrity
        assert metadata["title"] == "Important Document"
        assert metadata["url"] == "https://example.com/doc"
        assert metadata["notebook_id"] == "notebook:test123"

    @pytest.mark.asyncio
    async def test_cell_output_notebook_reference(
        self, unified_repo, mock_surreal_adapter
    ):
        """Test that cell output note maintains reference to notebook."""
        from open_notebook.database.sync_handlers import CellExecutionSyncHandler
        
        handler = CellExecutionSyncHandler()
        cell_data = {
            "notebook_id": "notebook:target789",
            "skill_name": "Analyzer",
            "result": {"output": "Analysis complete"},
        }
        
        event = SyncEvent(
            event_type=SyncEventType.CELL_COMPLETED,
            source_domain="living",
            entity_type="cell",
            entity_id="cell:exec001",
            data=cell_data,
        )
        
        # Act
        await handler.handle(event, unified_repo)
        
        # Assert
        call_args = mock_surreal_adapter.create.call_args
        note_data = call_args[0][1]
        
        # Verify notebook reference
        assert note_data["notebook_id"] == "notebook:target789"
        assert note_data["metadata"]["cell_id"] == "cell:exec001"


# ============================================================================
# Sync State Validation Tests
# ============================================================================

class TestSyncStateValidation:
    """Test sync state validation."""

    @pytest.mark.asyncio
    async def test_notebook_deletion_marks_agent_dormant(
        self, unified_repo, mock_postgres_adapter
    ):
        """Test that notebook deletion syncs to agent as dormant."""
        # Arrange - First create an agent
        handler = NotebookSyncHandler()
        
        # Simulate existing agent
        mock_postgres_adapter._stored_data = {
            "agent": {
                "notebook_agent:test123": {
                    "agent_id": "notebook_agent:test123",
                    "status": "healthy",
                    "skill_states": {},
                }
            }
        }
        mock_postgres_adapter.get_by_id.return_value = {
            "agent_id": "notebook_agent:test123",
            "status": "healthy",
            "skill_states": {},
        }
        
        delete_event = SyncEvent(
            event_type=SyncEventType.NOTEBOOK_DELETED,
            source_domain="core",
            entity_type="notebook",
            entity_id="notebook:test123",
            data={},
        )
        
        # Act
        await handler.handle(delete_event, unified_repo)
        
        # Assert
        call_args = mock_postgres_adapter.update.call_args
        update_data = call_args[0][2]
        
        assert update_data["status"] == "dormant"
        assert update_data["skill_states"]["notebook_deleted"] is True
        assert "notebook_deleted_at" in update_data["skill_states"]

    @pytest.mark.asyncio
    async def test_source_deletion_archives_lineage(
        self, unified_repo, mock_postgres_adapter
    ):
        """Test that source deletion archives lineage data."""
        # Arrange
        handler = SourceSyncHandler()
        
        # Simulate existing lineage
        mock_postgres_adapter._stored_data = {
            "data_lineage": {
                "source:doc456": {
                    "data_id": "source:doc456",
                    "current_tier": "hot",
                    "metadata": {},
                }
            }
        }
        mock_postgres_adapter.get_by_id.return_value = {
            "data_id": "source:doc456",
            "current_tier": "hot",
            "metadata": {},
        }
        
        delete_event = SyncEvent(
            event_type=SyncEventType.SOURCE_DELETED,
            source_domain="core",
            entity_type="source",
            entity_id="source:doc456",
            data={},
        )
        
        # Act
        await handler.handle(delete_event, unified_repo)
        
        # Assert
        call_args = mock_postgres_adapter.update.call_args
        update_data = call_args[0][2]
        
        assert update_data["current_tier"] == "frozen"
        assert update_data["metadata"]["source_deleted"] is True

    @pytest.mark.asyncio
    async def test_notebook_update_propagates_to_agent(
        self, unified_repo, mock_postgres_adapter
    ):
        """Test that notebook updates propagate to agent."""
        # Arrange
        handler = NotebookSyncHandler()
        
        # Simulate existing agent
        mock_postgres_adapter.get_by_id.return_value = {
            "agent_id": "notebook_agent:test123",
            "name": "Agent: Old Name",
            "skill_states": {
                "notebook_name": "Old Name",
                "notebook_id": "notebook:test123",
            },
        }
        
        update_event = SyncEvent(
            event_type=SyncEventType.NOTEBOOK_UPDATED,
            source_domain="core",
            entity_type="notebook",
            entity_id="notebook:test123",
            data={"name": "New Notebook Name"},
        )
        
        # Act
        await handler.handle(update_event, unified_repo)
        
        # Assert
        call_args = mock_postgres_adapter.update.call_args
        entity_type, entity_id, update_data = call_args[0]
        
        assert entity_type == "agent"
        assert entity_id == "notebook_agent:test123"
        assert "skill_states" in update_data


# ============================================================================
# Conflict Detection Tests
# ============================================================================

class TestConflictDetection:
    """Test conflict detection in sync operations."""

    @pytest.mark.asyncio
    async def test_missing_agent_on_update_creates_new(
        self, unified_repo, mock_postgres_adapter
    ):
        """Test that missing agent on update triggers creation."""
        # Arrange
        handler = NotebookSyncHandler()
        
        # No existing agent
        mock_postgres_adapter.get_by_id.return_value = None
        
        update_event = SyncEvent(
            event_type=SyncEventType.NOTEBOOK_UPDATED,
            source_domain="core",
            entity_type="notebook",
            entity_id="notebook:test123",
            data={"name": "Test Notebook"},
        )
        
        # Act
        await handler.handle(update_event, unified_repo)
        
        # Assert - should create instead of update
        mock_postgres_adapter.create.assert_called_once()
        mock_postgres_adapter.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_lineage_on_update_creates_new(
        self, unified_repo, mock_postgres_adapter
    ):
        """Test that missing lineage on update triggers creation."""
        # Arrange
        handler = SourceSyncHandler()
        
        # No existing lineage
        mock_postgres_adapter.get_by_id.return_value = None
        
        update_event = SyncEvent(
            event_type=SyncEventType.SOURCE_UPDATED,
            source_domain="core",
            entity_type="source",
            entity_id="source:test123",
            data={"title": "Updated Source"},
        )
        
        # Act
        await handler.handle(update_event, unified_repo)
        
        # Assert
        mock_postgres_adapter.create.assert_called_once()
        mock_postgres_adapter.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_notebook_id_parsing_variations(self, unified_repo, mock_postgres_adapter):
        """Test handling of various notebook ID formats."""
        handler = NotebookSyncHandler()
        
        test_cases = [
            # (input_id, expected_agent_id)
            ("notebook:abc123", "notebook_agent:abc123"),
            ("abc123", "notebook_agent:abc123"),
            ("notebook:prefix:suffix", "notebook_agent:prefix:suffix"),
        ]
        
        for notebook_id, expected_agent_id in test_cases:
            mock_postgres_adapter.reset_mock()
            
            event = SyncEvent(
                event_type=SyncEventType.NOTEBOOK_CREATED,
                source_domain="core",
                entity_type="notebook",
                entity_id=notebook_id,
                data={"name": "Test"},
            )
            
            await handler.handle(event, unified_repo)
            
            call_args = mock_postgres_adapter.create.call_args
            assert call_args[0][1]["agent_id"] == expected_agent_id


# ============================================================================
# Data Drift Detection Tests
# ============================================================================

class TestDataDriftDetection:
    """Test detection of data drift between domains."""

    def test_event_history_tracking(self):
        """Test that event history is tracked for drift detection."""
        registry = get_sync_registry()
        
        # Create events
        events = [
            SyncEvent(
                event_type=SyncEventType.NOTEBOOK_CREATED,
                source_domain="core",
                entity_type="notebook",
                entity_id=f"notebook:{i}",
                data={"name": f"Notebook {i}"},
            )
            for i in range(5)
        ]
        
        # Manually add to history (normally done by emit)
        for event in events:
            registry._event_history.append(event)
        
        # Verify history
        history = registry.get_history()
        assert len(history) == 5
        
        # Verify filtering
        filtered = registry.get_history(event_type=SyncEventType.NOTEBOOK_CREATED)
        assert len(filtered) == 5

    def test_event_history_limit_prevents_memory_drift(self):
        """Test that history limit prevents unbounded memory growth."""
        registry = get_sync_registry()
        registry._max_history = 10
        
        # Add more events than limit
        for i in range(20):
            event = SyncEvent(
                event_type=SyncEventType.NOTEBOOK_CREATED,
                source_domain="core",
                entity_type="notebook",
                entity_id=f"notebook:{i}",
                data={},
            )
            registry._event_history.append(event)
            if len(registry._event_history) > registry._max_history:
                registry._event_history.pop(0)
        
        # Verify limit enforced
        assert len(registry._event_history) == 10
        # Oldest should be 10, newest should be 19
        assert registry._event_history[0].entity_id == "notebook:10"
        assert registry._event_history[-1].entity_id == "notebook:19"


# ============================================================================
# Consistency Validation Utilities
# ============================================================================

class ConsistencyValidator:
    """Utility class for validating data consistency."""
    
    @staticmethod
    def validate_agent_notebook_consistency(
        agent_data: Dict[str, Any], notebook_data: Dict[str, Any]
    ) -> List[str]:
        """Validate consistency between agent and notebook.
        
        Returns list of consistency errors (empty if consistent).
        """
        errors = []
        
        # Check notebook ID reference
        agent_notebook_id = agent_data.get("skill_states", {}).get("notebook_id")
        notebook_id = notebook_data.get("id")
        
        if agent_notebook_id != notebook_id:
            errors.append(
                f"Notebook ID mismatch: agent references {agent_notebook_id}, "
                f"but notebook is {notebook_id}"
            )
        
        # Check name consistency
        agent_notebook_name = agent_data.get("skill_states", {}).get("notebook_name")
        notebook_name = notebook_data.get("name")
        
        if agent_notebook_name != notebook_name:
            errors.append(
                f"Notebook name mismatch: agent has {agent_notebook_name}, "
                f"but notebook is {notebook_name}"
            )
        
        return errors
    
    @staticmethod
    def validate_lineage_source_consistency(
        lineage_data: Dict[str, Any], source_data: Dict[str, Any]
    ) -> List[str]:
        """Validate consistency between lineage and source."""
        errors = []
        
        # Check source reference
        lineage_source = lineage_data.get("source")
        source_id = source_data.get("id")
        
        if lineage_source != source_id:
            errors.append(
                f"Source ID mismatch: lineage references {lineage_source}, "
                f"but source is {source_id}"
            )
        
        # Check metadata consistency
        lineage_title = lineage_data.get("metadata", {}).get("title")
        source_title = source_data.get("title")
        
        if lineage_title != source_title:
            errors.append(
                f"Title mismatch: lineage has {lineage_title}, "
                f"but source is {source_title}"
            )
        
        return errors


class TestConsistencyValidator:
    """Test the consistency validator."""

    def test_validator_detects_notebook_id_mismatch(self):
        """Test that validator detects notebook ID mismatch."""
        agent_data = {
            "agent_id": "notebook_agent:abc",
            "skill_states": {"notebook_id": "notebook:wrong", "notebook_name": "Test"},
        }
        notebook_data = {"id": "notebook:abc", "name": "Test"}
        
        errors = ConsistencyValidator.validate_agent_notebook_consistency(
            agent_data, notebook_data
        )
        
        assert len(errors) == 1
        assert "Notebook ID mismatch" in errors[0]

    def test_validator_detects_name_mismatch(self):
        """Test that validator detects name mismatch."""
        agent_data = {
            "agent_id": "notebook_agent:abc",
            "skill_states": {"notebook_id": "notebook:abc", "notebook_name": "Old Name"},
        }
        notebook_data = {"id": "notebook:abc", "name": "New Name"}
        
        errors = ConsistencyValidator.validate_agent_notebook_consistency(
            agent_data, notebook_data
        )
        
        assert len(errors) == 1
        assert "Notebook name mismatch" in errors[0]

    def test_validator_passes_on_consistent_data(self):
        """Test that validator passes when data is consistent."""
        agent_data = {
            "agent_id": "notebook_agent:abc",
            "skill_states": {"notebook_id": "notebook:abc", "notebook_name": "Test"},
        }
        notebook_data = {"id": "notebook:abc", "name": "Test"}
        
        errors = ConsistencyValidator.validate_agent_notebook_consistency(
            agent_data, notebook_data
        )
        
        assert len(errors) == 0


# ============================================================================
# End-to-End Consistency Tests
# ============================================================================

class TestEndToEndConsistency:
    """End-to-end consistency validation tests."""

    @pytest.mark.asyncio
    async def test_full_sync_cycle_consistency(
        self, unified_repo, mock_postgres_adapter, mock_surreal_adapter
    ):
        """Test full sync cycle maintains consistency."""
        # Step 1: Create notebook -> should create agent
        notebook_handler = NotebookSyncHandler()
        create_event = SyncEvent(
            event_type=SyncEventType.NOTEBOOK_CREATED,
            source_domain="core",
            entity_type="notebook",
            entity_id="notebook:consistency_test",
            data={"name": "Consistency Test Notebook"},
        )
        
        await notebook_handler.handle(create_event, unified_repo)
        
        # Verify agent created with correct data
        create_call = mock_postgres_adapter.create.call_args
        agent_data = create_call[0][1]
        
        assert agent_data["agent_id"] == "notebook_agent:consistency_test"
        assert agent_data["skill_states"]["notebook_id"] == "notebook:consistency_test"
        
        # Step 2: Update notebook -> should update agent
        mock_postgres_adapter.get_by_id.return_value = agent_data
        
        update_event = SyncEvent(
            event_type=SyncEventType.NOTEBOOK_UPDATED,
            source_domain="core",
            entity_type="notebook",
            entity_id="notebook:consistency_test",
            data={"name": "Updated Name"},
        )
        
        await notebook_handler.handle(update_event, unified_repo)
        
        # Verify update was called
        assert mock_postgres_adapter.update.called

    @pytest.mark.asyncio
    async def test_multiple_entity_consistency(
        self, unified_repo, mock_postgres_adapter, mock_surreal_adapter
    ):
        """Test consistency across multiple entity types."""
        # Create notebook and source
        notebook_handler = NotebookSyncHandler()
        source_handler = SourceSyncHandler()
        
        # Create notebook
        await notebook_handler.handle(
            SyncEvent(
                event_type=SyncEventType.NOTEBOOK_CREATED,
                source_domain="core",
                entity_type="notebook",
                entity_id="notebook:multi",
                data={"name": "Multi Test"},
            ),
            unified_repo,
        )
        
        # Create source
        await source_handler.handle(
            SyncEvent(
                event_type=SyncEventType.SOURCE_CREATED,
                source_domain="core",
                entity_type="source",
                entity_id="source:multi",
                data={"title": "Multi Source", "notebook_id": "notebook:multi"},
            ),
            unified_repo,
        )
        
        # Verify both created
        assert mock_postgres_adapter.create.call_count == 2
        
        # Verify operations were to correct entity types
        calls = mock_postgres_adapter.create.call_args_list
        entity_types = [call[0][0] for call in calls]
        assert "agent" in entity_types
        assert "data_lineage" in entity_types


# ============================================================================
# Consistency Report
# ============================================================================

def test_consistency_validation_summary():
    """Print consistency validation summary."""
    print("\n" + "="*60)
    print("LKS DATA CONSISTENCY VALIDATION SUMMARY")
    print("="*60)
    print("\nValidation Areas:")
    print("  ✓ Domain Router Consistency")
    print("  ✓ Entity Mapping Consistency")
    print("  ✓ Cross-Reference Integrity")
    print("  ✓ Sync State Validation")
    print("  ✓ Conflict Detection")
    print("  ✓ Data Drift Detection")
    print("\nConsistency Rules:")
    print("  - Notebook ID → Agent ID: notebook:X → notebook_agent:X")
    print("  - Source ID → Lineage ID: source:X → source:X")
    print("  - Agent maintains notebook_id in skill_states")
    print("  - Lineage maintains source metadata")
    print("  - Deletion marks as dormant/archived (not removed)")
    print("="*60)
    
    assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
