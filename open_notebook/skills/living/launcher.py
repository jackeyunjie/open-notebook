"""Living Knowledge System Launcher.

Entry point for running the living knowledge system as an independent service.
Port: 8888
Database: PostgreSQL + TimescaleDB

Usage:
    python -m open_notebook.skills.living.launcher

    # With custom config
    LIVING_DB_HOST=localhost LIVING_DB_PORT=5432 python -m launcher
"""

import asyncio
import os
import signal
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
logger.add(
    "logs/living_system.log",
    rotation="500 MB",
    retention="10 days",
    level="DEBUG"
)

from open_notebook.skills.living import (
    # Cells
    LivingSkill,
    # Tissues
    AgentTissue,
    CoordinationPattern,
    AgentCoordination,
    AgentRhythm,
    # Meridians
    MeridianSystem,
    DataMeridian,
    ControlMeridian,
    TemporalMeridian,
    # Acupoints
    TriggerRegistry,
    TemporalScheduler,
)
from open_notebook.skills.living.database.postgresql import (
    create_postgresql_database,
)
from open_notebook.skills.living.p4_data_agent import P4DataAgent, DataGenerationRule


@dataclass
class SystemConfig:
    """Configuration for the living knowledge system."""
    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "living_system"
    db_user: str = "living"
    db_password: str = "living"

    # Server
    host: str = "0.0.0.0"
    port: int = 8888

    # P0 Organs
    p0_enabled: bool = True
    p0_daily_sync_hour: int = 9  # 9 AM

    # Data Management
    data_management_enabled: bool = True

    @classmethod
    def from_env(cls) -> "SystemConfig":
        """Load configuration from environment variables."""
        return cls(
            db_host=os.getenv("LIVING_DB_HOST", "localhost"),
            db_port=int(os.getenv("LIVING_DB_PORT", "5432")),
            db_name=os.getenv("LIVING_DB_NAME", "living_system"),
            db_user=os.getenv("LIVING_DB_USER", "living"),
            db_password=os.getenv("LIVING_DB_PASSWORD", "living"),
            host=os.getenv("LIVING_HOST", "0.0.0.0"),
            port=int(os.getenv("LIVING_PORT", "8888")),
            p0_enabled=os.getenv("LIVING_P0_ENABLED", "true").lower() == "true",
            p0_daily_sync_hour=int(os.getenv("LIVING_P0_SYNC_HOUR", "9")),
            data_management_enabled=os.getenv("LIVING_DATA_ENABLED", "true").lower() == "true",
        )


class LivingKnowledgeSystem:
    """Main living knowledge system orchestrator."""

    def __init__(self, config: SystemConfig):
        self.config = config
        self.db = None
        self.p4_data_agent: Optional[P4DataAgent] = None
        self.temporal_scheduler: Optional[TemporalScheduler] = None
        self._shutdown_event = asyncio.Event()

        # Track loaded organs
        self.organs: Dict[str, Any] = {}
        self.meridians: List[str] = []

    async def initialize(self) -> None:
        """Initialize the entire system."""
        logger.info("=" * 60)
        logger.info("🚀 Initializing Living Knowledge System")
        logger.info("=" * 60)

        # 1. Connect to database
        logger.info("\n[1/6] Connecting to database...")
        self.db = await create_postgresql_database(
            host=self.config.db_host,
            port=self.config.db_port,
            database=self.config.db_name,
            user=self.config.db_user,
            password=self.config.db_password,
        )
        logger.info("✅ Database connected")

        # 2. Start P4 Data Management (immune system)
        if self.config.data_management_enabled:
            logger.info("\n[2/6] Starting P4 Data Agent (immune system)...")
            self.p4_data_agent = P4DataAgent(self.db)

            # Register data sources
            self.p4_data_agent.register_data_source(DataGenerationRule(
                source_id="p0.pain_scanner",
                source_type="sensor",
                retention_hot=timedelta(days=7),
                retention_warm=timedelta(days=30),
            ))
            self.p4_data_agent.register_data_source(DataGenerationRule(
                source_id="p0.emotion_watcher",
                source_type="sensor",
                retention_hot=timedelta(days=7),
            ))
            self.p4_data_agent.register_data_source(DataGenerationRule(
                source_id="p0.trend_hunter",
                source_type="sensor",
                retention_hot=timedelta(days=14),
            ))

            await self.p4_data_agent.start()
            logger.info("✅ P4 Data Agent started")

        # 3. Setup meridians
        logger.info("\n[3/6] Setting up meridians (flows)...")
        await self._setup_meridians()
        logger.info(f"✅ {len(self.meridians)} meridians ready")

        # 4. Load organs
        logger.info("\n[4/6] Loading organs...")
        if self.config.p0_enabled:
            await self._load_p0_organ()
        logger.info(f"✅ {len(self.organs)} organs loaded")

        # 5. Start temporal scheduler
        logger.info("\n[5/6] Starting temporal scheduler...")
        self.temporal_scheduler = TemporalScheduler()
        await self.temporal_scheduler.start()
        logger.info("✅ Temporal scheduler running")

        # 6. Register signal handlers
        logger.info("\n[6/6] Registering signal handlers...")
        self._setup_signal_handlers()
        logger.info("✅ Signal handlers registered")

        logger.info("\n" + "=" * 60)
        logger.info("🎉 Living Knowledge System fully operational!")
        logger.info("=" * 60)
        logger.info(f"\n📊 System Status:")
        logger.info(f"   • Database: {self.config.db_host}:{self.config.db_port}")
        logger.info(f"   • API Server: http://{self.config.host}:{self.config.port}")
        logger.info(f"   • Organs: {list(self.organs.keys())}")
        logger.info(f"   • Meridians: {self.meridians}")
        logger.info(f"\n   Press Ctrl+C to shutdown gracefully")
        logger.info("=" * 60)

    async def _setup_meridians(self) -> None:
        """Setup core meridians."""
        # P0 Perception data meridian
        p0_data = DataMeridian(
            meridian_id="p0.data.perception",
            name="P0 Perception Data",
            capacity=10000
        )
        MeridianSystem.register(p0_data)
        self.meridians.append("p0.data.perception")

        # P0 Control meridian
        p0_control = ControlMeridian(
            meridian_id="p0.control",
            name="P0 Control Signals"
        )
        MeridianSystem.register(p0_control)
        self.meridians.append("p0.control")

        # Temporal sync meridian
        temporal = TemporalMeridian(
            meridian_id="system.temporal",
            name="System Temporal Sync"
        )
        MeridianSystem.register(temporal)
        self.meridians.append("system.temporal")

        # Start all meridians
        await MeridianSystem.start_all()

    async def _load_p0_organ(self) -> None:
        """Load P0 Perception Organ."""
        logger.info("   Loading P0 Perception Organ...")

        # Create P0 skills (cells)
        from open_notebook.skills.living.examples.p0_perception_organ import (
            create_pain_scanner_skill,
            create_emotion_watcher_skill,
            create_trend_hunter_skill,
            create_scene_discover_skill,
        )

        pain_scanner = create_pain_scanner_skill()
        emotion_watcher = create_emotion_watcher_skill()
        trend_hunter = create_trend_hunter_skill()
        scene_discover = create_scene_discover_skill()

        # Register skills
        self.organs["p0.skills"] = [
            pain_scanner,
            emotion_watcher,
            trend_hunter,
            scene_discover,
        ]

        # Create P0 agent (tissue)
        from open_notebook.skills.living.examples.p0_perception_organ import (
            create_p0_perception_agent,
        )

        p0_agent = create_p0_perception_agent()

        # Connect to meridians
        from open_notebook.skills.living.meridian_flow import FlowNode, FlowType

        agent_node = FlowNode(
            node_id=p0_agent.agent_id,
            node_type="agent",
            capabilities={FlowType.DATA, FlowType.CONTROL}
        )

        # Register agent
        self.organs["p0.agent"] = p0_agent

        logger.info(f"      • Skills: {len(p0_agent.skill_ids)}")
        logger.info(f"      • Coordination: {p0_agent.coordination.pattern.value}")
        logger.info(f"      • Rhythm: {p0_agent.rhythm.active_hours}")

    def _setup_signal_handlers(self) -> None:
        """Setup graceful shutdown handlers."""
        def signal_handler(sig, frame):
            logger.info(f"\nReceived signal {sig}, initiating shutdown...")
            self._shutdown_event.set()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def run(self) -> None:
        """Run the system until shutdown signal."""
        try:
            # Wait for shutdown signal
            await self._shutdown_event.wait()
        except asyncio.CancelledError:
            logger.info("Run cancelled")

    async def shutdown(self) -> None:
        """Graceful shutdown."""
        logger.info("\n" + "=" * 60)
        logger.info("🛑 Shutting down Living Knowledge System...")
        logger.info("=" * 60)

        # 1. Stop temporal scheduler
        if self.temporal_scheduler:
            logger.info("[1/4] Stopping temporal scheduler...")
            await self.temporal_scheduler.stop()
            logger.info("✅ Temporal scheduler stopped")

        # 2. Stop meridians
        logger.info("[2/4] Stopping meridians...")
        await MeridianSystem.stop_all()
        logger.info("✅ Meridians stopped")

        # 3. Stop P4 Data Agent
        if self.p4_data_agent:
            logger.info("[3/4] Stopping P4 Data Agent...")
            await self.p4_data_agent.stop()
            logger.info("✅ P4 Data Agent stopped")

        # 4. Disconnect database
        if self.db:
            logger.info("[4/4] Disconnecting database...")
            await self.db.disconnect()
            logger.info("✅ Database disconnected")

        logger.info("\n" + "=" * 60)
        logger.info("👋 Living Knowledge System shutdown complete")
        logger.info("=" * 60)


async def main():
    """Main entry point."""
    # Load configuration
    config = SystemConfig.from_env()

    # Create system
    system = LivingKnowledgeSystem(config)

    try:
        # Initialize
        await system.initialize()

        # Run (blocks until shutdown signal)
        await system.run()

    except Exception as e:
        logger.exception(f"System error: {e}")
        raise

    finally:
        # Always shutdown gracefully
        await system.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
