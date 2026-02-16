"""In-memory database implementation for demos and testing."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from open_notebook.skills.living.database.abstract import (
    CellState,
    AgentState,
    DataLineage,
    DataTier,
    LivingDatabase,
    MeridianMetrics,
    TriggerRecord,
)


class InMemoryDatabase(LivingDatabase):
    """In-memory implementation for testing and demos."""

    def __init__(self):
        self._cells: Dict[str, CellState] = {}
        self._agents: Dict[str, AgentState] = {}
        self._lineage: Dict[str, DataLineage] = {}
        self._metrics: List[MeridianMetrics] = []
        self._triggers: List[TriggerRecord] = []

    async def connect(self) -> None:
        """No-op for in-memory."""
        pass

    async def disconnect(self) -> None:
        """No-op for in-memory."""
        pass

    # Cell operations
    async def save_cell_state(self, state: CellState) -> None:
        self._cells[state.skill_id] = state

    async def get_cell_state(self, skill_id: str) -> Optional[CellState]:
        return self._cells.get(skill_id)

    async def list_cell_states(
        self,
        state_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[CellState]:
        cells = list(self._cells.values())
        if state_filter:
            cells = [c for c in cells if c.state == state_filter]
        return cells[offset:offset + limit]

    async def delete_cell_state(self, skill_id: str) -> bool:
        if skill_id in self._cells:
            del self._cells[skill_id]
            return True
        return False

    async def get_cell_statistics(self, skill_id: str) -> Optional[Dict[str, Any]]:
        cell = self._cells.get(skill_id)
        if not cell:
            return None
        return {
            "run_count": cell.run_count,
            "success_rate": cell.success_count / cell.run_count if cell.run_count > 0 else 0,
            "avg_duration_ms": cell.avg_duration_ms,
        }

    # Agent operations
    async def save_agent_state(self, state: AgentState) -> None:
        self._agents[state.agent_id] = state

    async def get_agent_state(self, agent_id: str) -> Optional[AgentState]:
        return self._agents.get(agent_id)

    async def list_agent_states(
        self,
        status_filter: Optional[str] = None,
        limit: int = 100
    ) -> List[AgentState]:
        agents = list(self._agents.values())
        if status_filter:
            agents = [a for a in agents if a.status == status_filter]
        return agents[:limit]

    # Data lineage operations
    async def register_data_lineage(self, lineage: DataLineage) -> None:
        self._lineage[lineage.data_id] = lineage

    async def get_data_lineage(self, data_id: str) -> Optional[DataLineage]:
        return self._lineage.get(data_id)

    async def update_data_tier(self, data_id: str, tier: DataTier) -> None:
        if data_id in self._lineage:
            self._lineage[data_id].current_tier = tier

    async def find_stale_data(self, tier: DataTier, age: timedelta) -> List[DataLineage]:
        now = datetime.now()
        stale = []
        for lineage in self._lineage.values():
            if lineage.current_tier == tier:
                if (now - lineage.created_at) > age:
                    stale.append(lineage)
        return stale

    async def cleanup_expired_data(self, retention_days: int) -> int:
        cutoff = datetime.now() - timedelta(days=retention_days)
        expired = [
            data_id for data_id, lineage in self._lineage.items()
            if lineage.created_at < cutoff
        ]
        for data_id in expired:
            del self._lineage[data_id]
        return len(expired)

    # Metrics operations
    async def record_meridian_metrics(self, metrics: MeridianMetrics) -> None:
        self._metrics.append(metrics)

    async def get_meridian_metrics(
        self,
        meridian_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[MeridianMetrics]:
        return [
            m for m in self._metrics
            if m.meridian_id == meridian_id and start_time <= m.timestamp <= end_time
        ]

    async def get_latest_meridian_metrics(self, meridian_id: str) -> Optional[MeridianMetrics]:
        metrics = [m for m in self._metrics if m.meridian_id == meridian_id]
        return max(metrics, key=lambda m: m.timestamp) if metrics else None

    # Trigger operations
    async def record_trigger_activation(self, record: TriggerRecord) -> None:
        self._triggers.append(record)

    async def get_trigger_history(
        self,
        trigger_id: str,
        since: Optional[datetime] = None
    ) -> List[TriggerRecord]:
        records = [r for r in self._triggers if r.trigger_id == trigger_id]
        if since:
            records = [r for r in records if r.timestamp >= since]
        return records

    # System health
    async def get_system_health(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "cells": len(self._cells),
            "agents": len(self._agents),
            "data_items": len(self._lineage),
            "metrics_count": len(self._metrics),
        }
