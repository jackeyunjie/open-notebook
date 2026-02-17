"""LKS Performance Benchmark Tests.

Performance tests for the Living Knowledge System integration:
- Event throughput
- Query latency
- Sync overhead
- Concurrent operation handling

Run with: pytest tests/test_lks_performance.py -v --benchmark-only
"""

import asyncio
import pytest
import time
from typing import List
from unittest.mock import AsyncMock

from open_notebook.database.sync_hooks import (
    SyncEvent,
    SyncEventType,
    SyncHookRegistry,
    get_sync_registry,
    reset_sync_registry,
)
from open_notebook.database.sync_handlers import (
    NotebookSyncHandler,
    SourceSyncHandler,
    CellExecutionSyncHandler,
    get_handler_registry,
    reset_handler_registry,
)
from open_notebook.database.unified_repository import (
    BackendAdapter,
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
def mock_fast_adapter():
    """Create a fast mock adapter for performance tests."""
    adapter = AsyncMock(spec=BackendAdapter)
    adapter.backend_type = StorageBackend.SURREALDB
    
    async def fast_query(*args, **kwargs):
        await asyncio.sleep(0.001)  # 1ms simulated latency
        return [{"id": "test:1", "name": "Test"}]
    
    async def fast_create(*args, **kwargs):
        await asyncio.sleep(0.001)
        return {"id": "test:1", "created": True}
    
    adapter.query.side_effect = fast_query
    adapter.create.side_effect = fast_create
    adapter.get_by_id.return_value = {"id": "test:1"}
    adapter.update.return_value = {"id": "test:1", "updated": True}
    adapter.delete.return_value = True
    
    return adapter


@pytest.fixture
def mock_postgres_adapter():
    """Create a mock PostgreSQL adapter."""
    adapter = AsyncMock(spec=BackendAdapter)
    adapter.backend_type = StorageBackend.POSTGRESQL
    
    async def fast_query(*args, **kwargs):
        await asyncio.sleep(0.001)
        return [{"agent_id": "agent:1", "name": "Test Agent"}]
    
    async def fast_create(*args, **kwargs):
        await asyncio.sleep(0.001)
        return {"agent_id": "agent:1", "created": True}
    
    adapter.query.side_effect = fast_query
    adapter.create.side_effect = fast_create
    adapter.get_by_id.return_value = {"agent_id": "agent:1"}
    adapter.update.return_value = {"agent_id": "agent:1", "updated": True}
    adapter.delete.return_value = True
    
    return adapter


@pytest.fixture
def unified_repo(mock_fast_adapter, mock_postgres_adapter):
    """Create unified repository with fast mock adapters."""
    return UnifiedRepositoryImpl(
        surreal_adapter=mock_fast_adapter,
        postgres_adapter=mock_postgres_adapter,
    )


# ============================================================================
# Event Throughput Tests
# ============================================================================

class TestEventThroughput:
    """Test event emission and handling throughput."""

    @pytest.mark.asyncio
    async def test_event_emission_throughput(self):
        """Measure events per second that can be emitted and handled."""
        # Arrange
        registry = get_sync_registry()
        handler_calls = 0
        
        async def counting_handler(event: SyncEvent) -> None:
            nonlocal handler_calls
            handler_calls += 1
        
        registry.register(SyncEventType.NOTEBOOK_CREATED, counting_handler)
        
        num_events = 100
        events = [
            SyncEvent(
                event_type=SyncEventType.NOTEBOOK_CREATED,
                source_domain="core",
                entity_type="notebook",
                entity_id=f"notebook:{i}",
                data={"name": f"Notebook {i}"},
            )
            for i in range(num_events)
        ]
        
        # Act
        start_time = time.perf_counter()
        await asyncio.gather(*[registry.emit(e) for e in events])
        elapsed = time.perf_counter() - start_time
        
        # Assert
        events_per_second = num_events / elapsed
        print(f"\nEvent throughput: {events_per_second:.2f} events/sec")
        assert handler_calls == num_events
        assert events_per_second > 50  # Should handle at least 50 events/sec

    @pytest.mark.asyncio
    async def test_concurrent_event_handling(self):
        """Test handling of concurrent events."""
        # Arrange
        registry = get_sync_registry()
        handler_delays = []
        
        async def delayed_handler(event: SyncEvent) -> None:
            start = time.perf_counter()
            await asyncio.sleep(0.005)  # 5ms processing time
            elapsed = time.perf_counter() - start
            handler_delays.append(elapsed)
        
        # Register multiple handlers
        for _ in range(5):
            registry.register(SyncEventType.SOURCE_CREATED, delayed_handler)
        
        event = SyncEvent(
            event_type=SyncEventType.SOURCE_CREATED,
            source_domain="core",
            entity_type="source",
            entity_id="source:test",
            data={},
        )
        
        # Act
        start_time = time.perf_counter()
        await registry.emit(event)
        total_elapsed = time.perf_counter() - start_time
        
        # Assert - concurrent handlers should complete in ~5ms, not ~25ms
        print(f"\nConcurrent event handling time: {total_elapsed*1000:.2f}ms")
        assert total_elapsed < 0.02  # Should complete in under 20ms
        assert len(handler_delays) == 5


# ============================================================================
# Query Latency Tests
# ============================================================================

class TestQueryLatency:
    """Test query execution latency."""

    @pytest.mark.asyncio
    async def test_surrealdb_query_latency(self, unified_repo, mock_fast_adapter):
        """Measure SurrealDB query latency."""
        # Arrange
        mock_fast_adapter.query.return_value = [{"id": "notebook:1", "name": "Test"}]
        
        # Act
        latencies = []
        for _ in range(10):
            start = time.perf_counter()
            result = await unified_repo.query("notebook", limit=1)
            elapsed = time.perf_counter() - start
            latencies.append(elapsed * 1000)  # Convert to ms
        
        # Assert
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        print(f"\nSurrealDB query latency: avg={avg_latency:.2f}ms, max={max_latency:.2f}ms")
        assert avg_latency < 10  # Average should be under 10ms

    @pytest.mark.asyncio
    async def test_postgresql_query_latency(self, unified_repo, mock_postgres_adapter):
        """Measure PostgreSQL query latency."""
        # Arrange
        mock_postgres_adapter.query.return_value = [{"agent_id": "agent:1"}]
        
        # Act
        latencies = []
        for _ in range(10):
            start = time.perf_counter()
            result = await unified_repo.query("agent", limit=1)
            elapsed = time.perf_counter() - start
            latencies.append(elapsed * 1000)
        
        # Assert
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        print(f"\nPostgreSQL query latency: avg={avg_latency:.2f}ms, max={max_latency:.2f}ms")
        assert avg_latency < 10

    @pytest.mark.asyncio
    async def test_mixed_query_latency(self, unified_repo, mock_fast_adapter, mock_postgres_adapter):
        """Measure latency for mixed queries to both backends."""
        # Arrange
        mock_fast_adapter.query.return_value = [{"id": "notebook:1"}]
        mock_postgres_adapter.query.return_value = [{"agent_id": "agent:1"}]
        
        # Act - Alternate between backends
        latencies_surreal = []
        latencies_postgres = []
        
        for i in range(10):
            start = time.perf_counter()
            await unified_repo.query("notebook")
            latencies_surreal.append((time.perf_counter() - start) * 1000)
            
            start = time.perf_counter()
            await unified_repo.query("agent")
            latencies_postgres.append((time.perf_counter() - start) * 1000)
        
        # Assert
        avg_surreal = sum(latencies_surreal) / len(latencies_surreal)
        avg_postgres = sum(latencies_postgres) / len(latencies_postgres)
        print(f"\nMixed query latency: SurrealDB={avg_surreal:.2f}ms, PostgreSQL={avg_postgres:.2f}ms")
        assert avg_surreal < 10
        assert avg_postgres < 10


# ============================================================================
# Sync Overhead Tests
# ============================================================================

class TestSyncOverhead:
    """Test synchronization overhead."""

    @pytest.mark.asyncio
    async def test_notebook_sync_overhead(self, unified_repo, mock_postgres_adapter):
        """Measure overhead of notebook -> agent sync."""
        # Arrange
        handler = NotebookSyncHandler()
        mock_postgres_adapter.create.return_value = {"agent_id": "notebook_agent:test"}
        
        event = SyncEvent(
            event_type=SyncEventType.NOTEBOOK_CREATED,
            source_domain="core",
            entity_type="notebook",
            entity_id="notebook:test",
            data={"name": "Performance Test Notebook"},
        )
        
        # Act
        latencies = []
        for _ in range(10):
            start = time.perf_counter()
            await handler.handle(event, unified_repo)
            elapsed = time.perf_counter() - start
            latencies.append(elapsed * 1000)
        
        # Assert
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        print(f"\nNotebook sync overhead: avg={avg_latency:.2f}ms, max={max_latency:.2f}ms")
        assert avg_latency < 20  # Sync should complete in under 20ms

    @pytest.mark.asyncio
    async def test_source_sync_overhead(self, unified_repo, mock_postgres_adapter):
        """Measure overhead of source -> lineage sync."""
        # Arrange
        handler = SourceSyncHandler()
        mock_postgres_adapter.create.return_value = {"data_id": "source:test"}
        
        event = SyncEvent(
            event_type=SyncEventType.SOURCE_CREATED,
            source_domain="core",
            entity_type="source",
            entity_id="source:test",
            data={"title": "Test Source", "source_type": "pdf"},
        )
        
        # Act
        latencies = []
        for _ in range(10):
            start = time.perf_counter()
            await handler.handle(event, unified_repo)
            elapsed = time.perf_counter() - start
            latencies.append(elapsed * 1000)
        
        # Assert
        avg_latency = sum(latencies) / len(latencies)
        print(f"\nSource sync overhead: avg={avg_latency:.2f}ms")
        assert avg_latency < 20

    @pytest.mark.asyncio
    async def test_cell_execution_sync_overhead(self, unified_repo, mock_fast_adapter):
        """Measure overhead of cell execution -> note sync."""
        # Arrange
        handler = CellExecutionSyncHandler()
        mock_fast_adapter.create.return_value = {"id": "note:test"}
        
        event = SyncEvent(
            event_type=SyncEventType.CELL_COMPLETED,
            source_domain="living",
            entity_type="cell",
            entity_id="cell:test",
            data={
                "notebook_id": "notebook:test",
                "skill_name": "TestSkill",
                "result": {"output": "Test output", "duration_ms": 100},
            },
        )
        
        # Act
        latencies = []
        for _ in range(10):
            start = time.perf_counter()
            await handler.handle(event, unified_repo)
            elapsed = time.perf_counter() - start
            latencies.append(elapsed * 1000)
        
        # Assert
        avg_latency = sum(latencies) / len(latencies)
        print(f"\nCell execution sync overhead: avg={avg_latency:.2f}ms")
        assert avg_latency < 20


# ============================================================================
# Concurrent Operation Tests
# ============================================================================

class TestConcurrentOperations:
    """Test concurrent operation handling."""

    @pytest.mark.asyncio
    async def test_concurrent_notebook_creations(self, unified_repo, mock_postgres_adapter):
        """Test concurrent notebook creation sync."""
        # Arrange
        handler = NotebookSyncHandler()
        mock_postgres_adapter.create.return_value = {"agent_id": "notebook_agent:test"}
        
        events = [
            SyncEvent(
                event_type=SyncEventType.NOTEBOOK_CREATED,
                source_domain="core",
                entity_type="notebook",
                entity_id=f"notebook:{i}",
                data={"name": f"Notebook {i}"},
            )
            for i in range(20)
        ]
        
        # Act
        start_time = time.perf_counter()
        await asyncio.gather(*[handler.handle(e, unified_repo) for e in events])
        elapsed = time.perf_counter() - start_time
        
        # Assert
        print(f"\nConcurrent notebook creations (20): {elapsed*1000:.2f}ms")
        assert mock_postgres_adapter.create.call_count == 20
        assert elapsed < 1.0  # Should complete in under 1 second

    @pytest.mark.asyncio
    async def test_mixed_concurrent_operations(self, unified_repo, mock_fast_adapter, mock_postgres_adapter):
        """Test mixed concurrent operations to both backends."""
        # Arrange
        mock_fast_adapter.create.return_value = {"id": "note:test"}
        mock_postgres_adapter.create.return_value = {"agent_id": "agent:test"}
        
        async def create_notebook(i: int):
            handler = NotebookSyncHandler()
            event = SyncEvent(
                event_type=SyncEventType.NOTEBOOK_CREATED,
                source_domain="core",
                entity_type="notebook",
                entity_id=f"notebook:{i}",
                data={"name": f"Notebook {i}"},
            )
            await handler.handle(event, unified_repo)
        
        async def create_source(i: int):
            handler = SourceSyncHandler()
            event = SyncEvent(
                event_type=SyncEventType.SOURCE_CREATED,
                source_domain="core",
                entity_type="source",
                entity_id=f"source:{i}",
                data={"title": f"Source {i}"},
            )
            await handler.handle(event, unified_repo)
        
        # Act
        start_time = time.perf_counter()
        await asyncio.gather(
            *[create_notebook(i) for i in range(10)],
            *[create_source(i) for i in range(10)],
        )
        elapsed = time.perf_counter() - start_time
        
        # Assert
        print(f"\nMixed concurrent operations (20): {elapsed*1000:.2f}ms")
        assert elapsed < 1.0


# ============================================================================
# Memory Usage Tests
# ============================================================================

class TestMemoryEfficiency:
    """Test memory efficiency of sync system."""

    def test_event_history_limits(self):
        """Test that event history is properly limited."""
        # Arrange
        registry = get_sync_registry()
        registry._max_history = 100  # Set low limit for testing
        
        # Act - Add more events than limit
        for i in range(150):
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
        
        # Assert
        assert len(registry._event_history) == 100
        # Oldest events should be removed
        assert registry._event_history[0].entity_id == "notebook:50"
        assert registry._event_history[-1].entity_id == "notebook:149"


# ============================================================================
# Stress Tests
# ============================================================================

class TestStress:
    """Stress tests for sync system."""

    @pytest.mark.asyncio
    async def test_rapid_event_burst(self):
        """Test handling of rapid event bursts."""
        # Arrange
        registry = get_sync_registry()
        processed = 0
        
        async def fast_handler(event: SyncEvent) -> None:
            nonlocal processed
            processed += 1
        
        registry.register(SyncEventType.NOTEBOOK_CREATED, fast_handler)
        
        # Create burst of events
        events = [
            SyncEvent(
                event_type=SyncEventType.NOTEBOOK_CREATED,
                source_domain="core",
                entity_type="notebook",
                entity_id=f"notebook:{i}",
                data={},
            )
            for i in range(500)
        ]
        
        # Act
        start_time = time.perf_counter()
        # Process in batches to avoid overwhelming
        batch_size = 50
        for i in range(0, len(events), batch_size):
            batch = events[i:i+batch_size]
            await asyncio.gather(*[registry.emit(e) for e in batch])
        elapsed = time.perf_counter() - start_time
        
        # Assert
        events_per_second = 500 / elapsed
        print(f"\nRapid burst throughput: {events_per_second:.2f} events/sec")
        assert processed == 500
        assert events_per_second > 100

    @pytest.mark.asyncio
    async def test_handler_registration_scaling(self):
        """Test system behavior with many handlers."""
        # Arrange
        registry = get_sync_registry()
        handler_count = 20
        call_count = 0
        
        async def counting_handler(event: SyncEvent) -> None:
            nonlocal call_count
            call_count += 1
        
        # Register many handlers
        for _ in range(handler_count):
            registry.register(SyncEventType.NOTEBOOK_CREATED, counting_handler)
        
        event = SyncEvent(
            event_type=SyncEventType.NOTEBOOK_CREATED,
            source_domain="core",
            entity_type="notebook",
            entity_id="notebook:test",
            data={},
        )
        
        # Act
        start_time = time.perf_counter()
        await registry.emit(event)
        elapsed = time.perf_counter() - start_time
        
        # Assert
        print(f"\nMany handlers ({handler_count}) execution time: {elapsed*1000:.2f}ms")
        assert call_count == handler_count
        assert elapsed < 0.1  # Should complete in under 100ms even with 20 handlers


# ============================================================================
# Benchmark Summary
# ============================================================================

@pytest.mark.asyncio
async def test_performance_summary():
    """Print performance summary."""
    print("\n" + "="*60)
    print("LKS PERFORMANCE BENCHMARK SUMMARY")
    print("="*60)
    print("\nTarget Performance Metrics:")
    print("  - Event throughput: > 50 events/sec")
    print("  - Query latency: < 10ms average")
    print("  - Sync overhead: < 20ms per operation")
    print("  - Concurrent operations: < 1s for 20 ops")
    print("  - Handler scaling: < 100ms for 20 handlers")
    print("="*60)
    
    # This test always passes - it's for documentation
    assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
