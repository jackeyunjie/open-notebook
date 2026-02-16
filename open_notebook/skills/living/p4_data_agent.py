"""P4 DataAgent - Data lifecycle management organ for Living Knowledge System.

Acts as the "immune system" of the living knowledge system:
- Data metabolism: generation, flow, and expiration
- Quality monitoring: ensuring data health and consistency
- Capacity management: preventing data bloat
- Lineage tracking: where data comes from and goes to
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set

from loguru import logger

from open_notebook.skills.living.database.abstract import (
    DataLineage,
    DataTier,
    LivingDatabase,
    MeridianMetrics,
)


@dataclass
class DataGenerationRule:
    """Rule for data generation from a source."""
    source_id: str
    source_type: str  # "sensor", "processor", "event", "manual"
    rate_limit: Optional[str] = None  # e.g., "100/min"
    retention_hot: timedelta = field(default_factory=lambda: timedelta(days=7))
    retention_warm: timedelta = field(default_factory=lambda: timedelta(days=30))
    retention_cold: timedelta = field(default_factory=lambda: timedelta(days=365))
    retention_frozen: Optional[timedelta] = None  # None = keep forever
    schema: str = "default"
    compression_warm: str = "lz4"
    compression_cold: str = "zstd"


@dataclass
class QualityRule:
    """Data quality validation rule."""
    name: str
    check_type: str  # "completeness", "consistency", "timeliness", "accuracy"
    threshold: float  # 0.0 to 1.0
    validator: Optional[Callable] = None
    auto_repair: bool = False


@dataclass
class QualityReport:
    """Data quality assessment report."""
    overall_score: float
    checks: Dict[str, float]
    issues: List[Dict[str, Any]]
    timestamp: datetime = field(default_factory=datetime.now)


class DataGenerator:
    """Manages all data generation sources."""

    def __init__(self, db: LivingDatabase):
        self.db = db
        self.rules: Dict[str, DataGenerationRule] = {}
        self.generation_counts: Dict[str, int] = {}

    def register_source(self, rule: DataGenerationRule) -> None:
        """Register a data generation source."""
        self.rules[rule.source_id] = rule
        self.generation_counts[rule.source_id] = 0
        logger.info(f"Registered data source: {rule.source_id} ({rule.source_type})")

    async def record_generation(
        self,
        source_id: str,
        data_id: str,
        metadata: Optional[Dict] = None
    ) -> DataLineage:
        """Record a data generation event."""
        if source_id not in self.rules:
            logger.warning(f"Unknown data source: {source_id}")
            # Create default rule
            self.register_source(DataGenerationRule(
                source_id=source_id,
                source_type="unknown"
            ))

        rule = self.rules[source_id]
        self.generation_counts[source_id] += 1

        # Create lineage record
        lineage = DataLineage(
            data_id=data_id,
            source=source_id,
            source_type=rule.source_type,
            created_at=datetime.now(),
            current_tier=DataTier.HOT,
            schema_version=rule.schema,
        )

        await self.db.register_data_lineage(lineage)
        logger.debug(f"Recorded data generation: {data_id} from {source_id}")

        return lineage

    def get_lifecycle_policy(self, source_id: str) -> Optional[DataGenerationRule]:
        """Get lifecycle policy for a source."""
        return self.rules.get(source_id)


class DataFlowMonitor:
    """Monitors data flow through meridians."""

    def __init__(self, db: LivingDatabase):
        self.db = db
        self.monitoring: bool = False
        self._monitor_task: Optional[asyncio.Task] = None
        self.alerts: List[Dict] = []
        self.thresholds = {
            "backpressure": 1000,  # queue depth
            "error_rate": 0.01,    # 1%
            "latency_ms": 1000,    # 1 second
        }

    async def start_monitoring(self, interval_seconds: float = 5.0) -> None:
        """Start continuous flow monitoring."""
        self.monitoring = True
        self._monitor_task = asyncio.create_task(
            self._monitor_loop(interval_seconds)
        )
        logger.info("Data flow monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop flow monitoring."""
        self.monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
        logger.info("Data flow monitoring stopped")

    async def _monitor_loop(self, interval: float) -> None:
        """Main monitoring loop."""
        while self.monitoring:
            try:
                # This would collect from actual meridians in production
                # For now, we'll just wait
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Flow monitoring error: {e}")
                await asyncio.sleep(interval)

    async def record_metrics(self, metrics: MeridianMetrics) -> None:
        """Record meridian metrics."""
        await self.db.record_meridian_metrics(metrics)

        # Check thresholds
        if metrics.queue_size > self.thresholds["backpressure"]:
            await self._alert(
                "backpressure",
                f"Meridian {metrics.meridian_id} queue depth: {metrics.queue_size}"
            )

        if metrics.error_rate > self.thresholds["error_rate"]:
            await self._alert(
                "high_error_rate",
                f"Meridian {metrics.meridian_id} error rate: {metrics.error_rate:.2%}"
            )

        if metrics.latency_ms > self.thresholds["latency_ms"]:
            await self._alert(
                "high_latency",
                f"Meridian {metrics.meridian_id} latency: {metrics.latency_ms}ms"
            )

    async def _alert(self, alert_type: str, message: str) -> None:
        """Record an alert."""
        alert = {
            "type": alert_type,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        self.alerts.append(alert)
        logger.warning(f"[ALERT] {alert_type}: {message}")

        # Keep only recent alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]

    def get_recent_alerts(self, count: int = 10) -> List[Dict]:
        """Get recent alerts."""
        return self.alerts[-count:]


class DataQualityAgent:
    """Ensures data quality across the system."""

    def __init__(self, db: LivingDatabase):
        self.db = db
        self.rules: List[QualityRule] = []
        self._setup_default_rules()

    def _setup_default_rules(self) -> None:
        """Setup default quality rules."""
        self.rules = [
            QualityRule(
                name="completeness",
                check_type="completeness",
                threshold=0.99,
                auto_repair=True
            ),
            QualityRule(
                name="consistency",
                check_type="consistency",
                threshold=0.95,
                auto_repair=True
            ),
            QualityRule(
                name="timeliness",
                check_type="timeliness",
                threshold=0.98,
                auto_repair=False
            ),
        ]

    def add_rule(self, rule: QualityRule) -> None:
        """Add a quality rule."""
        self.rules.append(rule)

    async def check_quality(self, data_id: str) -> QualityReport:
        """Run quality checks on a data item."""
        lineage = await self.db.get_data_lineage(data_id)

        if not lineage:
            return QualityReport(
                overall_score=0.0,
                checks={},
                issues=[{"error": "Data not found"}]
            )

        checks = {}
        issues = []

        for rule in self.rules:
            score = await self._run_check(lineage, rule)
            checks[rule.name] = score

            if score < rule.threshold:
                issue = {
                    "rule": rule.name,
                    "score": score,
                    "threshold": rule.threshold,
                }
                issues.append(issue)

                if rule.auto_repair:
                    await self._auto_repair(data_id, rule)

        overall = sum(checks.values()) / len(checks) if checks else 0.0

        return QualityReport(
            overall_score=overall,
            checks=checks,
            issues=issues
        )

    async def _run_check(self, lineage: DataLineage, rule: QualityRule) -> float:
        """Run a single quality check."""
        # Simplified checks - real implementation would be more sophisticated
        if rule.check_type == "completeness":
            # Check if required fields are present
            return 1.0 if lineage.source and lineage.source_type else 0.0

        elif rule.check_type == "timeliness":
            # Check data freshness
            age = datetime.now() - lineage.created_at
            if age < timedelta(hours=1):
                return 1.0
            elif age < timedelta(days=1):
                return 0.8
            else:
                return 0.5

        elif rule.check_type == "consistency":
            # Check if dependencies are valid
            return 1.0 if lineage.dependencies is not None else 0.0

        return 0.0

    async def _auto_repair(self, data_id: str, rule: QualityRule) -> None:
        """Attempt auto-repair for quality issues."""
        logger.info(f"Auto-repairing {data_id} for {rule.name}")
        # Implementation would depend on specific repair strategies

    async def full_system_check(self) -> Dict[str, QualityReport]:
        """Run quality check on all recent data."""
        # This is a simplified version
        logger.info("Running full system quality check")
        return {}


class DataArchiveManager:
    """Manages data lifecycle transitions."""

    def __init__(self, db: LivingDatabase):
        self.db = db
        self.tier_costs = {
            DataTier.HOT: 3.0,     # ¥/GB/month
            DataTier.WARM: 1.0,
            DataTier.COLD: 0.3,
            DataTier.FROZEN: 0.12,
        }

    async def run_lifecycle_transition(self) -> Dict[str, int]:
        """Run the daily lifecycle transition process."""
        transitions = {
            "hot_to_warm": 0,
            "warm_to_cold": 0,
            "cold_to_frozen": 0,
            "destroyed": 0,
        }

        logger.info("Starting lifecycle transition")

        # 1. Hot -> Warm (7 days no access)
        stale_hot = await self.db.find_stale_data(
            DataTier.HOT,
            timedelta(days=7)
        )
        for lineage in stale_hot:
            await self._transition_to_warm(lineage)
            transitions["hot_to_warm"] += 1

        # 2. Warm -> Cold (30 days no access)
        stale_warm = await self.db.find_stale_data(
            DataTier.WARM,
            timedelta(days=30)
        )
        for lineage in stale_warm:
            await self._transition_to_cold(lineage)
            transitions["warm_to_cold"] += 1

        # 3. Cold -> Frozen (1 year no access)
        stale_cold = await self.db.find_stale_data(
            DataTier.COLD,
            timedelta(days=365)
        )
        for lineage in stale_cold:
            await self._transition_to_frozen(lineage)
            transitions["cold_to_frozen"] += 1

        # 4. Destroy expired data
        destroyed = await self.db.cleanup_expired_data(retention_days=2555)  # 7 years
        transitions["destroyed"] = destroyed

        logger.info(f"Lifecycle transition complete: {transitions}")
        return transitions

    async def _transition_to_warm(self, lineage: DataLineage) -> None:
        """Transition data to warm tier."""
        logger.debug(f"Transitioning {lineage.data_id} to warm tier")
        # In real implementation: compress with lz4
        await self.db.update_data_tier(lineage.data_id, DataTier.WARM)

    async def _transition_to_cold(self, lineage: DataLineage) -> None:
        """Transition data to cold tier."""
        logger.debug(f"Transitioning {lineage.data_id} to cold tier")
        # In real implementation: migrate to HDD, compress with zstd
        await self.db.update_data_tier(lineage.data_id, DataTier.COLD)

    async def _transition_to_frozen(self, lineage: DataLineage) -> None:
        """Transition data to frozen tier."""
        logger.debug(f"Transitioning {lineage.data_id} to frozen tier")
        # In real implementation: migrate to S3/object storage
        await self.db.update_data_tier(lineage.data_id, DataTier.FROZEN)

    def estimate_storage_cost(self, distribution: Dict[DataTier, float]) -> float:
        """Estimate monthly storage cost based on tier distribution."""
        total = 0.0
        for tier, gb in distribution.items():
            total += gb * self.tier_costs[tier]
        return total


class P4DataAgent:
    """P4 Data Management Organ - the immune system of living knowledge."""

    def __init__(self, db: LivingDatabase):
        self.db = db
        self.generator = DataGenerator(db)
        self.flow_monitor = DataFlowMonitor(db)
        self.quality_agent = DataQualityAgent(db)
        self.archive_manager = DataArchiveManager(db)

        self._running = False
        self._tasks: List[asyncio.Task] = []

    async def start(self) -> None:
        """Start the data management organ."""
        self._running = True

        # Start flow monitoring
        await self.flow_monitor.start_monitoring(interval_seconds=5)

        # Start periodic tasks
        self._tasks = [
            asyncio.create_task(self._quality_check_loop()),
            asyncio.create_task(self._lifecycle_loop()),
        ]

        logger.info("P4 DataAgent organ started")

    async def stop(self) -> None:
        """Stop the data management organ."""
        self._running = False

        # Stop monitoring
        await self.flow_monitor.stop_monitoring()

        # Cancel tasks
        for task in self._tasks:
            task.cancel()

        logger.info("P4 DataAgent organ stopped")

    async def _quality_check_loop(self) -> None:
        """Periodic quality checks (every hour)."""
        while self._running:
            try:
                await asyncio.sleep(3600)  # 1 hour

                if not self._running:
                    break

                logger.info("Running hourly quality check")
                await self.quality_agent.full_system_check()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Quality check error: {e}")

    async def _lifecycle_loop(self) -> None:
        """Daily lifecycle transitions (at 2 AM)."""
        while self._running:
            try:
                # Wait until 2 AM
                now = datetime.now()
                next_2am = now.replace(hour=2, minute=0, second=0)
                if next_2am <= now:
                    next_2am += timedelta(days=1)

                wait_seconds = (next_2am - now).total_seconds()
                logger.info(f"Next lifecycle transition at {next_2am} (in {wait_seconds/3600:.1f} hours)")

                await asyncio.sleep(wait_seconds)

                if not self._running:
                    break

                # Run lifecycle transition
                await self.archive_manager.run_lifecycle_transition()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Lifecycle transition error: {e}")
                await asyncio.sleep(3600)  # Retry in 1 hour on error

    def register_data_source(self, rule: DataGenerationRule) -> None:
        """Register a data generation source."""
        self.generator.register_source(rule)

    async def record_data_generation(
        self,
        source_id: str,
        data_id: str,
        metadata: Optional[Dict] = None
    ) -> DataLineage:
        """Record data generation."""
        return await self.generator.record_generation(source_id, data_id, metadata)

    async def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health."""
        db_health = await self.db.get_system_health()

        return {
            **db_health,
            "alerts": self.flow_monitor.get_recent_alerts(5),
            "monitoring_active": self.flow_monitor.monitoring,
            "timestamp": datetime.now().isoformat(),
        }


# ============================================================================
# Factory Functions
# ============================================================================

def create_p4_data_agent(db: Optional[LivingDatabase] = None) -> P4DataAgent:
    """Factory function to create P4 Data Agent.
    
    Args:
        db: Optional database instance. If not provided, uses InMemoryDatabase.
        
    Returns:
        P4DataAgent instance
    """
    if db is None:
        from open_notebook.skills.living.database.memory import InMemoryDatabase
        db = InMemoryDatabase()
    return P4DataAgent(db)


# ============================================================================
# Demo
# ============================================================================

async def demo_p4_data_agent():
    """Demo P4 Data Agent functionality."""
    from open_notebook.skills.living.database.memory import InMemoryDatabase

    # Create in-memory database for demo
    db = InMemoryDatabase()

    # Create P4 Data Agent
    agent = P4DataAgent(db)

    print("=" * 60)
    print("P4 Data Agent Demo")
    print("=" * 60)

    # Register data sources
    agent.register_data_source(DataGenerationRule(
        source_id="user_notes",
        source_type="manual",
        retention_hot=timedelta(days=7),
        retention_warm=timedelta(days=30),
        retention_cold=timedelta(days=365)
    ))

    agent.register_data_source(DataGenerationRule(
        source_id="system_logs",
        source_type="sensor",
        retention_hot=timedelta(days=1),
        retention_warm=timedelta(days=7),
        retention_cold=timedelta(days=90)
    ))

    print("\n1. Registered Data Sources:")
    print("   - user_notes (manual)")
    print("   - system_logs (sensor)")

    # Simulate data generation
    print("\n2. Recording Data Generation:")
    for i in range(5):
        lineage = await agent.record_data_generation(
            source_id="user_notes",
            data_id=f"note_{i:03d}",
            metadata={"title": f"Note {i}", "size": 1024}
        )
        print(f"   - {lineage.data_id}: {lineage.current_tier.value}")

    # Check quality
    print("\n3. Quality Check:")
    report = await agent.quality_agent.check_quality("note_000")
    print(f"   Overall Score: {report.overall_score:.2f}")
    print(f"   Checks: {report.checks}")

    # Lifecycle transition
    print("\n4. Lifecycle Transition:")
    transitions = await agent.archive_manager.run_lifecycle_transition()
    print(f"   Hot->Warm: {transitions['hot_to_warm']}")
    print(f"   Warm->Cold: {transitions['warm_to_cold']}")
    print(f"   Destroyed: {transitions['destroyed']}")

    # Cost estimation
    print("\n5. Storage Cost Estimation:")
    distribution = {
        DataTier.HOT: 10,    # 10 GB
        DataTier.WARM: 50,   # 50 GB
        DataTier.COLD: 200,  # 200 GB
        DataTier.FROZEN: 500 # 500 GB
    }
    cost = agent.archive_manager.estimate_storage_cost(distribution)
    print(f"   Distribution: {distribution}")
    print(f"   Monthly Cost: ${cost:.2f}")

    # System health
    print("\n6. System Health:")
    health = await agent.get_system_health()
    print(f"   Status: {health.get('status', 'unknown')}")
    print(f"   Monitoring: {'Active' if health['monitoring_active'] else 'Inactive'}")

    print("\n" + "=" * 60)
    print("P4 Data Agent Demo Complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(demo_p4_data_agent())
