"""Abstract database interface for Living Knowledge System.

Defines the contract that all database implementations must follow.
This allows seamless switching between PostgreSQL, SurrealDB, etc.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class DataTier(Enum):
    """Data lifecycle tiers."""
    HOT = "hot"        # Active, SSD, uncompressed
    WARM = "warm"      # Less active, SSD, lz4
    COLD = "cold"      # Rarely accessed, HDD, zstd
    FROZEN = "frozen"  # Archived, S3/object storage


@dataclass
class CellState:
    """Persisted state of a skill cell."""
    skill_id: str
    state: str  # idle, running, completed, failed, etc.
    created_at: datetime
    updated_at: datetime
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    success_count: int = 0
    fail_count: int = 0
    avg_duration_ms: Optional[float] = None
    last_error: Optional[str] = None
    last_error_at: Optional[datetime] = None
    config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentState:
    """Persisted state of an agent tissue."""
    agent_id: str
    name: str
    status: str  # healthy, stressed, recovering, dormant, critical
    energy_level: float  # 0.0 to 1.0
    stress_level: float  # 0.0 to 1.0
    tasks_completed: int = 0
    tasks_failed: int = 0
    avg_response_time_ms: Optional[float] = None
    last_executed: Optional[datetime] = None
    skill_states: Dict[str, str] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class MeridianMetrics:
    """Metrics for a meridian flow."""
    meridian_id: str
    timestamp: datetime
    packets_sent: int = 0
    packets_received: int = 0
    packets_dropped: int = 0
    queue_size: int = 0
    blockages: int = 0
    throughput_per_sec: float = 0.0
    latency_ms: float = 0.0
    error_rate: float = 0.0


@dataclass
class TriggerRecord:
    """Record of a trigger activation."""
    trigger_id: str
    timestamp: datetime
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None
    processing_time_ms: Optional[float] = None


@dataclass
class DataLineage:
    """Data lineage tracking."""
    data_id: str
    source: str  # skill_id, agent_id, external
    source_type: str  # sensor, processor, event
    created_at: datetime
    dependencies: List[str] = field(default_factory=list)
    consumers: List[str] = field(default_factory=list)
    schema_version: str = "1.0"
    quality_score: Optional[float] = None
    current_tier: DataTier = DataTier.HOT


class LivingDatabase(ABC):
    """Abstract interface for Living Knowledge System database.

    All implementations must support async operations.
    """

    @abstractmethod
    async def connect(self) -> None:
        """Establish database connection."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close database connection."""
        pass

    # =========================================================================
    # Cell (Skill) Operations
    # =========================================================================

    @abstractmethod
    async def save_cell_state(self, state: CellState) -> None:
        """Save or update cell state."""
        pass

    @abstractmethod
    async def get_cell_state(self, skill_id: str) -> Optional[CellState]:
        """Get cell state by ID."""
        pass

    @abstractmethod
    async def list_cell_states(
        self,
        state_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[CellState]:
        """List cell states with optional filtering."""
        pass

    @abstractmethod
    async def delete_cell_state(self, skill_id: str) -> bool:
        """Delete a cell state. Returns True if deleted."""
        pass

    # =========================================================================
    # Agent (Tissue) Operations
    # =========================================================================

    @abstractmethod
    async def save_agent_state(self, state: AgentState) -> None:
        """Save or update agent state."""
        pass

    @abstractmethod
    async def get_agent_state(self, agent_id: str) -> Optional[AgentState]:
        """Get agent state by ID."""
        pass

    @abstractmethod
    async def list_agent_states(
        self,
        status_filter: Optional[str] = None,
        limit: int = 100
    ) -> List[AgentState]:
        """List agent states with optional filtering."""
        pass

    # =========================================================================
    # Meridian (Flow) Operations
    # =========================================================================

    @abstractmethod
    async def record_meridian_metrics(self, metrics: MeridianMetrics) -> None:
        """Record meridian metrics (time-series data)."""
        pass

    @abstractmethod
    async def get_meridian_metrics(
        self,
        meridian_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[MeridianMetrics]:
        """Get meridian metrics for a time range."""
        pass

    @abstractmethod
    async def get_latest_meridian_metrics(
        self,
        meridian_id: str
    ) -> Optional[MeridianMetrics]:
        """Get the most recent metrics for a meridian."""
        pass

    # =========================================================================
    # Acupoint (Trigger) Operations
    # =========================================================================

    @abstractmethod
    async def record_trigger_activation(self, record: TriggerRecord) -> None:
        """Record a trigger activation."""
        pass

    @abstractmethod
    async def get_trigger_history(
        self,
        trigger_id: str,
        start_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[TriggerRecord]:
        """Get activation history for a trigger."""
        pass

    # =========================================================================
    # Data Lifecycle (DataAgent) Operations
    # =========================================================================

    @abstractmethod
    async def register_data_lineage(self, lineage: DataLineage) -> None:
        """Register data lineage information."""
        pass

    @abstractmethod
    async def get_data_lineage(self, data_id: str) -> Optional[DataLineage]:
        """Get lineage for a data item."""
        pass

    @abstractmethod
    async def find_stale_data(
        self,
        tier: DataTier,
        older_than: timedelta
    ) -> List[DataLineage]:
        """Find data that should be transitioned to next tier."""
        pass

    @abstractmethod
    async def update_data_tier(self, data_id: str, new_tier: DataTier) -> None:
        """Update the storage tier of data."""
        pass

    # =========================================================================
    # Health & Statistics
    # =========================================================================

    @abstractmethod
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics."""
        pass

    @abstractmethod
    async def get_cell_statistics(self, skill_id: str) -> Dict[str, Any]:
        """Get detailed statistics for a cell."""
        pass

    @abstractmethod
    async def cleanup_expired_data(self, retention_days: int) -> int:
        """Clean up data older than retention period. Returns count deleted."""
        pass
