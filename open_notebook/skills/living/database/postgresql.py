"""PostgreSQL implementation of LivingDatabase.

Uses:
- PostgreSQL 15+ for core data
- TimescaleDB 2.11+ for time-series metrics
- pgvector 0.5+ for vector embeddings (optional)
"""

import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import asyncpg
from loguru import logger

from open_notebook.skills.living.database.abstract import (
    CellState,
    AgentState,
    DataLineage,
    DataTier,
    LivingDatabase,
    MeridianMetrics,
    TriggerRecord,
)


class PostgreSQLDatabase(LivingDatabase):
    """PostgreSQL implementation of Living Knowledge System database."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "living_system",
        user: str = "living",
        password: str = "living",
    ):
        self.connection_params = {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password,
        }
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        """Establish database connection pool."""
        self.pool = await asyncpg.create_pool(
            **self.connection_params,
            min_size=5,
            max_size=20,
            command_timeout=60,
        )
        logger.info("PostgreSQL connection pool established")

        # Ensure tables exist
        await self._ensure_tables()

    async def disconnect(self) -> None:
        """Close database connection."""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection pool closed")

    async def _ensure_tables(self) -> None:
        """Create tables if they don't exist."""
        async with self.pool.acquire() as conn:
            # Cell states table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS cell_states (
                    skill_id TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    last_run TIMESTAMP WITH TIME ZONE,
                    next_run TIMESTAMP WITH TIME ZONE,
                    run_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    fail_count INTEGER DEFAULT 0,
                    avg_duration_ms FLOAT,
                    last_error TEXT,
                    last_error_at TIMESTAMP WITH TIME ZONE,
                    config JSONB DEFAULT '{}',
                    metadata JSONB DEFAULT '{}'
                )
            """)

            # Agent states table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_states (
                    agent_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    energy_level FLOAT NOT NULL DEFAULT 1.0,
                    stress_level FLOAT NOT NULL DEFAULT 0.0,
                    tasks_completed INTEGER DEFAULT 0,
                    tasks_failed INTEGER DEFAULT 0,
                    avg_response_time_ms FLOAT,
                    last_executed TIMESTAMP WITH TIME ZONE,
                    skill_states JSONB DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)

            # Try to create TimescaleDB extension
            try:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
                logger.info("TimescaleDB extension available")
            except asyncpg.Error:
                logger.warning("TimescaleDB extension not available, using regular tables")

            # Meridian metrics - time-series data
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS meridian_metrics (
                    meridian_id TEXT NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    packets_sent INTEGER DEFAULT 0,
                    packets_received INTEGER DEFAULT 0,
                    packets_dropped INTEGER DEFAULT 0,
                    queue_size INTEGER DEFAULT 0,
                    blockages INTEGER DEFAULT 0,
                    throughput_per_sec FLOAT DEFAULT 0.0,
                    latency_ms FLOAT DEFAULT 0.0,
                    error_rate FLOAT DEFAULT 0.0
                )
            """)

            # Convert to hypertable if TimescaleDB is available
            try:
                await conn.execute("""
                    SELECT create_hypertable('meridian_metrics', 'timestamp',
                        if_not_exists => TRUE,
                        migrate_data => TRUE
                    )
                """)
                logger.info("meridian_metrics converted to hypertable")
            except asyncpg.Error:
                # Create index instead for non-TimescaleDB
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_metrics_time
                    ON meridian_metrics (timestamp DESC)
                """)

            # Trigger records
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS trigger_records (
                    id SERIAL PRIMARY KEY,
                    trigger_id TEXT NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    success BOOLEAN NOT NULL,
                    data JSONB,
                    error TEXT,
                    processing_time_ms FLOAT
                )
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_trigger_time
                ON trigger_records (trigger_id, timestamp DESC)
            """)

            # Data lineage
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS data_lineage (
                    data_id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    dependencies JSONB DEFAULT '[]',
                    consumers JSONB DEFAULT '[]',
                    schema_version TEXT DEFAULT '1.0',
                    quality_score FLOAT,
                    current_tier TEXT DEFAULT 'hot',
                    last_accessed TIMESTAMP WITH TIME ZONE
                )
            """)

            logger.info("Database tables ensured")

    # =========================================================================
    # Cell (Skill) Operations
    # =========================================================================

    async def save_cell_state(self, state: CellState) -> None:
        """Save or update cell state."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO cell_states (
                    skill_id, state, created_at, updated_at, last_run, next_run,
                    run_count, success_count, fail_count, avg_duration_ms,
                    last_error, last_error_at, config, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                ON CONFLICT (skill_id) DO UPDATE SET
                    state = EXCLUDED.state,
                    updated_at = EXCLUDED.updated_at,
                    last_run = EXCLUDED.last_run,
                    next_run = EXCLUDED.next_run,
                    run_count = EXCLUDED.run_count,
                    success_count = EXCLUDED.success_count,
                    fail_count = EXCLUDED.fail_count,
                    avg_duration_ms = EXCLUDED.avg_duration_ms,
                    last_error = EXCLUDED.last_error,
                    last_error_at = EXCLUDED.last_error_at,
                    config = EXCLUDED.config,
                    metadata = EXCLUDED.metadata
            """,
                state.skill_id, state.state, state.created_at, state.updated_at,
                state.last_run, state.next_run, state.run_count,
                state.success_count, state.fail_count, state.avg_duration_ms,
                state.last_error, state.last_error_at,
                json.dumps(state.config), json.dumps(state.metadata)
            )

    async def get_cell_state(self, skill_id: str) -> Optional[CellState]:
        """Get cell state by ID."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM cell_states WHERE skill_id = $1",
                skill_id
            )
            if row:
                return self._row_to_cell_state(row)
            return None

    async def list_cell_states(
        self,
        state_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[CellState]:
        """List cell states with optional filtering."""
        async with self.pool.acquire() as conn:
            if state_filter:
                rows = await conn.fetch(
                    """SELECT * FROM cell_states
                       WHERE state = $1
                       ORDER BY updated_at DESC
                       LIMIT $2 OFFSET $3""",
                    state_filter, limit, offset
                )
            else:
                rows = await conn.fetch(
                    """SELECT * FROM cell_states
                       ORDER BY updated_at DESC
                       LIMIT $1 OFFSET $2""",
                    limit, offset
                )
            return [self._row_to_cell_state(r) for r in rows]

    async def delete_cell_state(self, skill_id: str) -> bool:
        """Delete a cell state."""
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM cell_states WHERE skill_id = $1",
                skill_id
            )
            return "DELETE 1" in result

    def _row_to_cell_state(self, row: asyncpg.Record) -> CellState:
        """Convert database row to CellState."""
        return CellState(
            skill_id=row["skill_id"],
            state=row["state"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            last_run=row["last_run"],
            next_run=row["next_run"],
            run_count=row["run_count"],
            success_count=row["success_count"],
            fail_count=row["fail_count"],
            avg_duration_ms=row["avg_duration_ms"],
            last_error=row["last_error"],
            last_error_at=row["last_error_at"],
            config=json.loads(row["config"]) if row["config"] else {},
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )

    # =========================================================================
    # Agent (Tissue) Operations
    # =========================================================================

    async def save_agent_state(self, state: AgentState) -> None:
        """Save or update agent state."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO agent_states (
                    agent_id, name, status, energy_level, stress_level,
                    tasks_completed, tasks_failed, avg_response_time_ms,
                    last_executed, skill_states, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT (agent_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    status = EXCLUDED.status,
                    energy_level = EXCLUDED.energy_level,
                    stress_level = EXCLUDED.stress_level,
                    tasks_completed = EXCLUDED.tasks_completed,
                    tasks_failed = EXCLUDED.tasks_failed,
                    avg_response_time_ms = EXCLUDED.avg_response_time_ms,
                    last_executed = EXCLUDED.last_executed,
                    skill_states = EXCLUDED.skill_states,
                    updated_at = EXCLUDED.updated_at
            """,
                state.agent_id, state.name, state.status,
                state.energy_level, state.stress_level,
                state.tasks_completed, state.tasks_failed,
                state.avg_response_time_ms, state.last_executed,
                json.dumps(state.skill_states),
                state.created_at or datetime.now(),
                state.updated_at or datetime.now()
            )

    async def get_agent_state(self, agent_id: str) -> Optional[AgentState]:
        """Get agent state by ID."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM agent_states WHERE agent_id = $1",
                agent_id
            )
            if row:
                return self._row_to_agent_state(row)
            return None

    async def list_agent_states(
        self,
        status_filter: Optional[str] = None,
        limit: int = 100
    ) -> List[AgentState]:
        """List agent states with optional filtering."""
        async with self.pool.acquire() as conn:
            if status_filter:
                rows = await conn.fetch(
                    """SELECT * FROM agent_states
                       WHERE status = $1
                       ORDER BY updated_at DESC
                       LIMIT $2""",
                    status_filter, limit
                )
            else:
                rows = await conn.fetch(
                    """SELECT * FROM agent_states
                       ORDER BY updated_at DESC
                       LIMIT $1""",
                    limit
                )
            return [self._row_to_agent_state(r) for r in rows]

    def _row_to_agent_state(self, row: asyncpg.Record) -> AgentState:
        """Convert database row to AgentState."""
        return AgentState(
            agent_id=row["agent_id"],
            name=row["name"],
            status=row["status"],
            energy_level=row["energy_level"],
            stress_level=row["stress_level"],
            tasks_completed=row["tasks_completed"],
            tasks_failed=row["tasks_failed"],
            avg_response_time_ms=row["avg_response_time_ms"],
            last_executed=row["last_executed"],
            skill_states=json.loads(row["skill_states"]) if row["skill_states"] else {},
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    # =========================================================================
    # Meridian (Flow) Operations
    # =========================================================================

    async def record_meridian_metrics(self, metrics: MeridianMetrics) -> None:
        """Record meridian metrics (time-series data)."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO meridian_metrics (
                    meridian_id, timestamp, packets_sent, packets_received,
                    packets_dropped, queue_size, blockages, throughput_per_sec,
                    latency_ms, error_rate
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
                metrics.meridian_id, metrics.timestamp,
                metrics.packets_sent, metrics.packets_received,
                metrics.packets_dropped, metrics.queue_size,
                metrics.blockages, metrics.throughput_per_sec,
                metrics.latency_ms, metrics.error_rate
            )

    async def get_meridian_metrics(
        self,
        meridian_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[MeridianMetrics]:
        """Get meridian metrics for a time range."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM meridian_metrics
                WHERE meridian_id = $1
                  AND timestamp >= $2
                  AND timestamp <= $3
                ORDER BY timestamp DESC
            """, meridian_id, start_time, end_time)
            return [self._row_to_meridian_metrics(r) for r in rows]

    async def get_latest_meridian_metrics(
        self,
        meridian_id: str
    ) -> Optional[MeridianMetrics]:
        """Get the most recent metrics for a meridian."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM meridian_metrics
                WHERE meridian_id = $1
                ORDER BY timestamp DESC
                LIMIT 1
            """, meridian_id)
            if row:
                return self._row_to_meridian_metrics(row)
            return None

    def _row_to_meridian_metrics(self, row: asyncpg.Record) -> MeridianMetrics:
        """Convert database row to MeridianMetrics."""
        return MeridianMetrics(
            meridian_id=row["meridian_id"],
            timestamp=row["timestamp"],
            packets_sent=row["packets_sent"],
            packets_received=row["packets_received"],
            packets_dropped=row["packets_dropped"],
            queue_size=row["queue_size"],
            blockages=row["blockages"],
            throughput_per_sec=row["throughput_per_sec"],
            latency_ms=row["latency_ms"],
            error_rate=row["error_rate"],
        )

    # =========================================================================
    # Acupoint (Trigger) Operations
    # =========================================================================

    async def record_trigger_activation(self, record: TriggerRecord) -> None:
        """Record a trigger activation."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO trigger_records (
                    trigger_id, timestamp, success, data, error, processing_time_ms
                ) VALUES ($1, $2, $3, $4, $5, $6)
            """,
                record.trigger_id, record.timestamp, record.success,
                json.dumps(record.data) if record.data else None,
                record.error, record.processing_time_ms
            )

    async def get_trigger_history(
        self,
        trigger_id: str,
        start_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[TriggerRecord]:
        """Get activation history for a trigger."""
        async with self.pool.acquire() as conn:
            if start_time:
                rows = await conn.fetch("""
                    SELECT * FROM trigger_records
                    WHERE trigger_id = $1 AND timestamp >= $2
                    ORDER BY timestamp DESC
                    LIMIT $3
                """, trigger_id, start_time, limit)
            else:
                rows = await conn.fetch("""
                    SELECT * FROM trigger_records
                    WHERE trigger_id = $1
                    ORDER BY timestamp DESC
                    LIMIT $2
                """, trigger_id, limit)
            return [self._row_to_trigger_record(r) for r in rows]

    def _row_to_trigger_record(self, row: asyncpg.Record) -> TriggerRecord:
        """Convert database row to TriggerRecord."""
        return TriggerRecord(
            trigger_id=row["trigger_id"],
            timestamp=row["timestamp"],
            success=row["success"],
            data=json.loads(row["data"]) if row["data"] else None,
            error=row["error"],
            processing_time_ms=row["processing_time_ms"],
        )

    # =========================================================================
    # Data Lifecycle (DataAgent) Operations
    # =========================================================================

    async def register_data_lineage(self, lineage: DataLineage) -> None:
        """Register data lineage information."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO data_lineage (
                    data_id, source, source_type, created_at,
                    dependencies, consumers, schema_version, quality_score, current_tier
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (data_id) DO UPDATE SET
                    consumers = EXCLUDED.consumers,
                    quality_score = EXCLUDED.quality_score,
                    current_tier = EXCLUDED.current_tier,
                    last_accessed = NOW()
            """,
                lineage.data_id, lineage.source, lineage.source_type,
                lineage.created_at,
                json.dumps(lineage.dependencies),
                json.dumps(lineage.consumers),
                lineage.schema_version,
                lineage.quality_score,
                lineage.current_tier.value
            )

    async def get_data_lineage(self, data_id: str) -> Optional[DataLineage]:
        """Get lineage for a data item."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM data_lineage WHERE data_id = $1",
                data_id
            )
            if row:
                return self._row_to_data_lineage(row)
            return None

    async def find_stale_data(
        self,
        tier: DataTier,
        older_than: timedelta
    ) -> List[DataLineage]:
        """Find data that should be transitioned to next tier."""
        cutoff = datetime.now() - older_than
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM data_lineage
                WHERE current_tier = $1
                  AND last_accessed < $2
                ORDER BY last_accessed ASC
            """, tier.value, cutoff)
            return [self._row_to_data_lineage(r) for r in rows]

    async def update_data_tier(self, data_id: str, new_tier: DataTier) -> None:
        """Update the storage tier of data."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE data_lineage
                SET current_tier = $1, last_accessed = NOW()
                WHERE data_id = $2
            """, new_tier.value, data_id)

    def _row_to_data_lineage(self, row: asyncpg.Record) -> DataLineage:
        """Convert database row to DataLineage."""
        return DataLineage(
            data_id=row["data_id"],
            source=row["source"],
            source_type=row["source_type"],
            created_at=row["created_at"],
            dependencies=json.loads(row["dependencies"]) if row["dependencies"] else [],
            consumers=json.loads(row["consumers"]) if row["consumers"] else [],
            schema_version=row["schema_version"],
            quality_score=row["quality_score"],
            current_tier=DataTier(row["current_tier"]),
        )

    # =========================================================================
    # Health & Statistics
    # =========================================================================

    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics."""
        async with self.pool.acquire() as conn:
            # Cell statistics
            cell_stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE state = 'running') as running,
                    COUNT(*) FILTER (WHERE state = 'failed') as failed,
                    COUNT(*) FILTER (WHERE state = 'completed') as completed
                FROM cell_states
            """)

            # Agent statistics
            agent_stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'healthy') as healthy,
                    COUNT(*) FILTER (WHERE status = 'stressed') as stressed,
                    COUNT(*) FILTER (WHERE status = 'critical') as critical
                FROM agent_states
            """)

            # Recent trigger activity
            trigger_stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total_24h,
                    COUNT(*) FILTER (WHERE success) as success_24h,
                    COUNT(*) FILTER (WHERE NOT success) as failed_24h
                FROM trigger_records
                WHERE timestamp > NOW() - INTERVAL '24 hours'
            """)

            return {
                "cells": {
                    "total": cell_stats["total"],
                    "running": cell_stats["running"],
                    "failed": cell_stats["failed"],
                    "completed": cell_stats["completed"],
                },
                "agents": {
                    "total": agent_stats["total"],
                    "healthy": agent_stats["healthy"],
                    "stressed": agent_stats["stressed"],
                    "critical": agent_stats["critical"],
                },
                "triggers_24h": {
                    "total": trigger_stats["total_24h"],
                    "success": trigger_stats["success_24h"],
                    "failed": trigger_stats["failed_24h"],
                },
                "timestamp": datetime.now().isoformat(),
            }

    async def get_cell_statistics(self, skill_id: str) -> Dict[str, Any]:
        """Get detailed statistics for a cell."""
        async with self.pool.acquire() as conn:
            # Get cell state
            cell = await conn.fetchrow(
                "SELECT * FROM cell_states WHERE skill_id = $1",
                skill_id
            )

            if not cell:
                return {}

            # Get success rate over time
            history = await conn.fetch("""
                SELECT
                    DATE_TRUNC('hour', timestamp) as hour,
                    COUNT(*) FILTER (WHERE success) as successes,
                    COUNT(*) as total
                FROM trigger_records
                WHERE trigger_id LIKE $1
                  AND timestamp > NOW() - INTERVAL '7 days'
                GROUP BY hour
                ORDER BY hour DESC
            """, f"%{skill_id}%")

            return {
                "skill_id": skill_id,
                "current_state": cell["state"],
                "run_count": cell["run_count"],
                "success_rate": cell["success_count"] / max(cell["run_count"], 1),
                "avg_duration_ms": cell["avg_duration_ms"],
                "history": [
                    {
                        "hour": h["hour"].isoformat(),
                        "successes": h["successes"],
                        "total": h["total"]
                    }
                    for h in history
                ]
            }

    async def cleanup_expired_data(self, retention_days: int) -> int:
        """Clean up data older than retention period. Returns count deleted."""
        cutoff = datetime.now() - timedelta(days=retention_days)
        async with self.pool.acquire() as conn:
            # Delete old meridian metrics
            result = await conn.execute("""
                DELETE FROM meridian_metrics
                WHERE timestamp < $1
            """, cutoff)
            metrics_deleted = int(result.split()[1]) if "DELETE" in result else 0

            # Delete old trigger records
            result = await conn.execute("""
                DELETE FROM trigger_records
                WHERE timestamp < $1
            """, cutoff)
            triggers_deleted = int(result.split()[1]) if "DELETE" in result else 0

            return metrics_deleted + triggers_deleted


async def create_postgresql_database(
    host: str = "localhost",
    port: int = 5432,
    database: str = "living_system",
    user: str = "living",
    password: str = "living",
) -> PostgreSQLDatabase:
    """Factory function to create and connect PostgreSQL database."""
    db = PostgreSQLDatabase(
        host=host, port=port, database=database,
        user=user, password=password
    )
    await db.connect()
    return db
