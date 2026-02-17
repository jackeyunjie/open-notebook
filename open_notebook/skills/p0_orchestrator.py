"""P0 Orchestrator - Daily Sync Coordinator for Organic Growth System.

This module provides the orchestration layer that coordinates the four P0 agents
(Q1P0-Q4P0) through the Daily Sync protocol, enabling cross-quadrant intelligence
and emergent insights.

Daily Sync Protocol:
    1. Trigger: Orchestrator triggers all P0 agents to perform their scans
    2. Collect: Each agent generates a DailySyncReport with their signals
    3. Synthesize: Orchestrator analyzes reports for cross-quadrant patterns
    4. Route: Signals are routed to appropriate upper-layer agents (P1)
    5. Store: All data is persisted to SharedMemory for system-wide access

Architecture:
    ┌─────────────────────────────────────────┐
    │         P0 Orchestrator                 │
    │  (Daily Sync Coordinator)               │
    └──────┬──────┬──────┬──────┬────────────┘
           │      │      │      │
           ▼      ▼      ▼      ▼
        Q1P0   Q2P0   Q3P0   Q4P0
       (Pain) (Emotion) (Trend) (Scene)
           │      │      │      │
           └──────┴──────┴──────┘
                      │
                      ▼
              SharedMemory
              (System State)
"""

import asyncio
import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from loguru import logger

from open_notebook.domain.notebook import Note
from open_notebook.skills.base import Skill, SkillConfig, SkillContext, SkillResult, SkillStatus
from open_notebook.skills.registry import register_skill


class SignalPriority(Enum):
    """Priority levels for cross-agent signals."""
    CRITICAL = "critical"    # Immediate action required
    HIGH = "high"           # Should be processed today
    MEDIUM = "medium"       # Process within 24h
    LOW = "low"             # Background processing


@dataclass
class CrossQuadrantSignal:
    """A signal that has been synthesized from multiple quadrants."""
    signal_id: str
    source_quadrants: List[str]  # ["Q1", "Q2"] if combined from multiple
    signal_type: str  # "pain+emotion", "trend+scene", etc.
    title: str
    description: str
    priority: SignalPriority
    confidence_score: float  # 0-1, how confident is the synthesis
    raw_signals: List[Dict[str, Any]]  # Original signals from P0 agents
    recommended_action: str
    target_quadrants: List[str]  # Which upper-layer agents should receive this
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "source_quadrants": self.source_quadrants,
            "signal_type": self.signal_type,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "confidence_score": self.confidence_score,
            "raw_signals": self.raw_signals,
            "recommended_action": self.recommended_action,
            "target_quadrants": self.target_quadrants,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }


@dataclass
class SyncSession:
    """A single Daily Sync session record."""
    session_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    agent_reports: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    cross_quadrant_signals: List[CrossQuadrantSignal] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)
    status: str = "running"  # running, completed, failed
    error_message: Optional[str] = None
    p1_trigger_results: List[Dict[str, Any]] = field(default_factory=list)  # Results from P1 agents
    p2_trigger_results: List[Dict[str, Any]] = field(default_factory=list)  # Results from P2 agents

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "agent_count": len(self.agent_reports),
            "cross_quadrant_signals": [s.to_dict() for s in self.cross_quadrant_signals],
            "insights": self.insights,
            "status": self.status,
            "error_message": self.error_message,
            "p1_trigger_results": self.p1_trigger_results,
            "p2_trigger_results": self.p2_trigger_results
        }


class SharedMemory:
    """In-memory storage for P0 layer shared state.

    In production, this would be backed by Redis or a database.
    """
    _instance = None
    _data: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def store(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Store a value with optional TTL."""
        expires_at = None
        if ttl_seconds:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)

        self._data[key] = {
            "value": value,
            "stored_at": datetime.utcnow(),
            "expires_at": expires_at
        }
        logger.debug(f"SharedMemory: Stored {key}")

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value, respecting TTL."""
        if key not in self._data:
            return default

        entry = self._data[key]
        if entry.get("expires_at") and datetime.utcnow() > entry["expires_at"]:
            del self._data[key]
            return default

        return entry["value"]

    def get_recent_signals(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get all signals stored in the last N hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        signals = []

        for key, entry in list(self._data.items()):
            if key.startswith("signal:"):
                if entry["stored_at"] > cutoff:
                    signals.append(entry["value"])

        return signals

    def clear_expired(self) -> int:
        """Clear expired entries, return count cleared."""
        now = datetime.utcnow()
        expired_keys = [
            key for key, entry in self._data.items()
            if entry.get("expires_at") and now > entry["expires_at"]
        ]
        for key in expired_keys:
            del self._data[key]
        return len(expired_keys)


@register_skill
class P0OrchestratorAgent(Skill):
    """P0 Layer Orchestrator - Coordinates the four P0 agents through Daily Sync.

    The Orchestrator is the "central nervous system" of the P0 perception layer.
    It manages the Daily Sync protocol that enables the four quadrant agents to
    share intelligence and generate emergent insights.

    Responsibilities:
        1. Trigger P0 agents (Q1P0-Q4P0) to perform their scans
        2. Collect and synthesize DailySyncReports from all agents
        3. Detect cross-quadrant patterns (e.g., pain + trend alignment)
        4. Generate CrossQuadrantSignals for upper-layer processing
        5. Manage SharedMemory for system-wide state
        6. Route signals to appropriate P1 agents (Value Judgment layer)

    Daily Sync Cycle:
        Hour 0:   Trigger Q1P0 (PainScanner) - highest priority
        Hour 0:   Trigger Q2P0 (EmotionWatcher)
        Hour 0:   Trigger Q3P0 (TrendHunter)
        Hour 0:   Trigger Q4P0 (SceneDiscover)
        Hour 0-1: Synthesis phase - analyze all reports
        Hour 1:   Store results to SharedMemory
        Hour 1:   Route signals to P1 layer

    Cross-Quadrant Pattern Detection:
        - Pain + Trend: Urgent painpoints that are also trending (high priority)
        - Emotion + Scene: Emotional needs in specific scenarios
        - Pain + Emotion: Painpoints with strong emotional resonance
        - Trend + Scene: Trends that open new usage scenarios

    Configuration:
        sync_schedule: When to run daily sync (default: "00:00")
        enable_cross_synthesis: Whether to synthesize cross-quadrant signals (default: true)
        signal_ttl_hours: How long to keep signals in SharedMemory (default: 48)
        min_confidence_threshold: Minimum confidence for cross-quadrant signals (default: 0.7)
        target_notebook_id: Where to store sync reports

    Example:
        config = SkillConfig(
            skill_type="p0_orchestrator",
            name="P0 Orchestrator",
            parameters={
                "sync_schedule": "00:00",
                "enable_cross_synthesis": True,
                "min_confidence_threshold": 0.75,
                "target_notebook_id": "notebook:system"
            }
        )
    """

    skill_type = "p0_orchestrator"
    name = "P0 Orchestrator Agent"
    description = "Coordinates P0 layer agents through Daily Sync protocol"

    parameters_schema = {
        "sync_schedule": {
            "type": "string",
            "default": "00:00",
            "description": "When to run daily sync (HH:MM format)"
        },
        "enable_cross_synthesis": {
            "type": "boolean",
            "default": True,
            "description": "Enable cross-quadrant signal synthesis"
        },
        "signal_ttl_hours": {
            "type": "integer",
            "default": 48,
            "minimum": 1,
            "maximum": 168,
            "description": "Signal retention time in hours"
        },
        "min_confidence_threshold": {
            "type": "number",
            "default": 0.7,
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "Minimum confidence for synthesized signals"
        },
        "agents_to_run": {
            "type": "array",
            "items": {"type": "string", "enum": ["Q1P0", "Q2P0", "Q3P0", "Q4P0"]},
            "default": ["Q1P0", "Q2P0", "Q3P0", "Q4P0"],
            "description": "Which P0 agents to coordinate"
        },
        "target_notebook_id": {
            "type": "string",
            "default": "",
            "description": "Notebook to store sync reports"
        },
        "enable_p1_trigger": {
            "type": "boolean",
            "default": True,
            "description": "Automatically trigger P1 value judgment after sync"
        },
        "p1_agents_to_trigger": {
            "type": "array",
            "items": {"type": "string", "enum": ["Q1P1", "Q2P1", "Q3P1", "Q4P1"]},
            "default": ["Q1P1", "Q2P1", "Q3P1", "Q4P1"],
            "description": "Which P1 agents to trigger after sync"
        },
        "enable_p2_trigger": {
            "type": "boolean",
            "default": True,
            "description": "Automatically trigger P2 relationship building after P1"
        },
        "p2_agents_to_trigger": {
            "type": "array",
            "items": {"type": "string", "enum": ["Q1P2", "Q2P2", "Q3P2", "Q4P2"]},
            "default": ["Q1P2", "Q2P2", "Q3P2", "Q4P2"],
            "description": "Which P2 agents to trigger after P1"
        }
    }

    def __init__(self, config: SkillConfig):
        self.sync_schedule: str = config.parameters.get("sync_schedule", "00:00")
        self.enable_cross_synthesis: bool = config.parameters.get("enable_cross_synthesis", True)
        self.signal_ttl_hours: int = config.parameters.get("signal_ttl_hours", 48)
        self.min_confidence_threshold: float = config.parameters.get("min_confidence_threshold", 0.7)
        self.agents_to_run: List[str] = config.parameters.get("agents_to_run", ["Q1P0", "Q2P0", "Q3P0", "Q4P0"])
        self.target_notebook_id: str = config.parameters.get("target_notebook_id", "")
        self.enable_p1_trigger: bool = config.parameters.get("enable_p1_trigger", True)
        self.p1_agents_to_trigger: List[str] = config.parameters.get("p1_agents_to_trigger", ["Q1P1", "Q2P1", "Q3P1", "Q4P1"])
        self.enable_p2_trigger: bool = config.parameters.get("enable_p2_trigger", True)
        self.p2_agents_to_trigger: List[str] = config.parameters.get("p2_agents_to_trigger", ["Q1P2", "Q2P2", "Q3P2", "Q4P2"])

        # Shared memory for P0 layer
        self.shared_memory = SharedMemory()

        # Session tracking
        self.current_session: Optional[SyncSession] = None
        self.session_history: List[SyncSession] = []

        # Learning engine for feedback-driven improvement
        from open_notebook.skills.feedback_loop import LearningEngine
        self.learning_engine = LearningEngine()
        self._apply_learned_config()

        super().__init__(config)

    def _apply_learned_config(self):
        """Apply learned thresholds from feedback loop."""
        improved_config = self.learning_engine.get_improved_p0_config()
        # Update thresholds based on learning
        if "min_confidence_threshold" in improved_config:
            self.min_confidence_threshold = improved_config["min_confidence_threshold"]
            logger.info(f"Applied learned confidence threshold: {self.min_confidence_threshold}")

    async def _trigger_agent(self, agent_type: str, context: SkillContext) -> Optional[Dict[str, Any]]:
        """Trigger a specific P0 agent and return its report."""
        from open_notebook.skills.runner import get_skill_runner

        logger.info(f"Triggering {agent_type}...")

        try:
            runner = get_skill_runner()

            # Map agent types to skill types
            skill_type_map = {
                "Q1P0": "pain_scanner_agent",
                "Q2P0": "emotion_watcher_agent",
                "Q3P0": "trend_hunter_agent",
                "Q4P0": "scene_discover_agent"
            }

            skill_type = skill_type_map.get(agent_type)
            if not skill_type:
                logger.error(f"Unknown agent type: {agent_type}")
                return None

            # Execute the agent
            result = await runner.execute_skill(
                skill_type=skill_type,
                parameters={
                    "target_notebook_id": self.target_notebook_id,
                    "daily_sync_enabled": True
                },
                notebook_id=self.target_notebook_id
            )

            if result.status == SkillStatus.SUCCESS:
                logger.info(f"{agent_type} completed successfully")
                return result.output
            else:
                logger.warning(f"{agent_type} failed: {result.error_message}")
                return None

        except Exception as e:
            logger.error(f"Error triggering {agent_type}: {e}")
            return None

    def _detect_pain_trend_alignment(
        self,
        pain_signals: List[Dict],
        trend_signals: List[Dict]
    ) -> List[CrossQuadrantSignal]:
        """Detect when urgent painpoints align with trending topics.

        This is a high-value pattern: urgent pain + trending = immediate opportunity
        """
        synthesized = []

        for pain in pain_signals:
            pain_keywords = set(pain.get("keywords", []))

            for trend in trend_signals:
                trend_keywords = set(trend.get("keywords", []))

                # Calculate overlap
                overlap = pain_keywords & trend_keywords
                if len(overlap) >= 1:  # At least one shared keyword
                    confidence = min(0.5 + len(overlap) * 0.2, 1.0)

                    if confidence >= self.min_confidence_threshold:
                        synthesized.append(CrossQuadrantSignal(
                            signal_id=f"PT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{len(synthesized)}",
                            source_quadrants=["Q1", "Q3"],
                            signal_type="pain+trend",
                            title=f"Trending Painpoint: {pain.get('text', '')[:50]}...",
                            description=(
                                f"An urgent painpoint is currently trending. "
                                f"Pain: {pain.get('text', '')[:100]}. "
                                f"Trend: {trend.get('topic', '')}. "
                                f"This represents an immediate content opportunity."
                            ),
                            priority=SignalPriority.CRITICAL if pain.get("urgency_score", 0) > 80 else SignalPriority.HIGH,
                            confidence_score=confidence,
                            raw_signals=[pain, trend],
                            recommended_action="Create immediate response content capturing this trend",
                            target_quadrants=["Q1P1", "Q3P1"]  # Route to value judgment layers
                        ))

        return synthesized

    def _detect_emotion_scene_alignment(
        self,
        emotion_signals: List[Dict],
        scene_signals: List[Dict]
    ) -> List[CrossQuadrantSignal]:
        """Detect emotional needs in specific scenarios.

        Pattern: Strong emotion + concrete scenario = resonance opportunity
        """
        synthesized = []

        for emotion in emotion_signals:
            emotion_type = emotion.get("emotion", "")

            for scene in scene_signals:
                scene_context = scene.get("scene", "")

                # Check if emotion is likely in this scenario
                # Simple heuristic: emotion intensity + scenario specificity
                emotion_intensity = emotion.get("intensity", 50)

                if emotion_intensity > 70:
                    confidence = min(emotion_intensity / 100 + 0.2, 1.0)

                    if confidence >= self.min_confidence_threshold:
                        synthesized.append(CrossQuadrantSignal(
                            signal_id=f"ES-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{len(synthesized)}",
                            source_quadrants=["Q2", "Q4"],
                            signal_type="emotion+scene",
                            title=f"Emotional Scenario: {emotion_type} in {scene_context[:30]}...",
                            description=(
                                f"Strong {emotion_type} emotion detected in scenario: {scene_context}. "
                                f"This is an opportunity for deep resonance content."
                            ),
                            priority=SignalPriority.HIGH,
                            confidence_score=confidence,
                            raw_signals=[emotion, scene],
                            recommended_action="Create emotionally resonant scenario-based content",
                            target_quadrants=["Q2P1", "Q4P1"]
                        ))

        return synthesized

    def _detect_pain_emotion_resonance(
        self,
        pain_signals: List[Dict],
        emotion_signals: List[Dict]
    ) -> List[CrossQuadrantSignal]:
        """Detect painpoints with strong emotional components.

        Pattern: Pain + High Emotion = High Conversion Potential
        """
        synthesized = []

        for pain in pain_signals:
            pain_text = pain.get("text", "").lower()
            pain_urgency = pain.get("urgency_score", 0)

            for emotion in emotion_signals:
                emotion_triggers = emotion.get("triggers", [])
                emotion_intensity = emotion.get("intensity", 0)

                # Check alignment
                trigger_overlap = any(t.lower() in pain_text for t in emotion_triggers)

                if trigger_overlap or emotion_intensity > 75:
                    confidence = min(0.6 + (emotion_intensity / 100) * 0.3, 1.0)

                    if confidence >= self.min_confidence_threshold:
                        synthesized.append(CrossQuadrantSignal(
                            signal_id=f"PE-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{len(synthesized)}",
                            source_quadrants=["Q1", "Q2"],
                            signal_type="pain+emotion",
                            title=f"Emotional Painpoint: {pain.get('text', '')[:50]}...",
                            description=(
                                f"Painpoint with strong emotional resonance detected. "
                                f"Urgency: {pain_urgency}/100, Emotion: {emotion_intensity}/100. "
                                f"High conversion potential."
                            ),
                            priority=SignalPriority.HIGH,
                            confidence_score=confidence,
                            raw_signals=[pain, emotion],
                            recommended_action="Create content that both solves problem and validates emotion",
                            target_quadrants=["Q1P1", "Q2P1"]
                        ))

        return synthesized

    def _synthesize_cross_quadrant_signals(
        self,
        agent_reports: Dict[str, Dict[str, Any]]
    ) -> List[CrossQuadrantSignal]:
        """Analyze all agent reports and generate cross-quadrant signals."""
        if not self.enable_cross_synthesis:
            return []

        logger.info("Synthesizing cross-quadrant signals...")

        synthesized = []

        # Extract signals from reports
        q1_signals = agent_reports.get("Q1P0", {}).get("top_signals", [])
        q2_signals = agent_reports.get("Q2P0", {}).get("emotion_signals", [])
        q3_signals = agent_reports.get("Q3P0", {}).get("trend_signals", [])
        q4_signals = agent_reports.get("Q4P0", {}).get("scene_signals", [])

        # Pattern 1: Pain + Trend alignment (immediate opportunity)
        if q1_signals and q3_signals:
            synthesized.extend(self._detect_pain_trend_alignment(q1_signals, q3_signals))

        # Pattern 2: Emotion + Scene alignment (resonance opportunity)
        if q2_signals and q4_signals:
            synthesized.extend(self._detect_emotion_scene_alignment(q2_signals, q4_signals))

        # Pattern 3: Pain + Emotion alignment (high conversion)
        if q1_signals and q2_signals:
            synthesized.extend(self._detect_pain_emotion_resonance(q1_signals, q2_signals))

        # Sort by confidence
        synthesized.sort(key=lambda x: x.confidence_score, reverse=True)

        logger.info(f"Generated {len(synthesized)} cross-quadrant signals")
        return synthesized

    def _generate_insights(
        self,
        agent_reports: Dict[str, Dict[str, Any]],
        cross_signals: List[CrossQuadrantSignal]
    ) -> List[str]:
        """Generate high-level insights from the sync session."""
        insights = []

        # Count signals by quadrant
        signal_counts = {
            q: len(r.get("top_signals", []) or r.get("signals_detected", 0) or [])
            for q, r in agent_reports.items()
        }

        # Insight 1: Which quadrant is most active?
        if signal_counts:
            max_quadrant = max(signal_counts.items(), key=lambda x: x[1])
            if max_quadrant[1] > 5:
                insights.append(
                    f"{max_quadrant[0]} is highly active with {max_quadrant[1]} signals. "
                    f"Consider allocating more resources to this quadrant today."
                )

        # Insight 2: Cross-quadrant opportunities
        if cross_signals:
            critical_count = sum(1 for s in cross_signals if s.priority == SignalPriority.CRITICAL)
            if critical_count > 0:
                insights.append(
                    f"Detected {critical_count} CRITICAL cross-quadrant opportunities. "
                    f"These should be acted on immediately."
                )

        # Insight 3: Patterns
        pain_count = signal_counts.get("Q1P0", 0)
        trend_count = signal_counts.get("Q3P0", 0)
        if pain_count > 10 and trend_count > 5:
            insights.append(
                "High painpoint volume + active trends suggests a volatile market day. "
                "Opportunity for timely intervention content."
            )

        return insights

    async def _store_to_shared_memory(
        self,
        session: SyncSession,
        cross_signals: List[CrossQuadrantSignal]
    ) -> None:
        """Store session results to SharedMemory for upper-layer access."""
        ttl = self.signal_ttl_hours * 3600  # Convert to seconds

        # Store each cross-quadrant signal
        for signal in cross_signals:
            key = f"signal:{signal.signal_id}"
            self.shared_memory.store(key, signal.to_dict(), ttl_seconds=ttl)

        # Store session summary
        session_key = f"session:{session.session_id}"
        self.shared_memory.store(session_key, session.to_dict(), ttl_seconds=ttl)

        # Store latest snapshot
        self.shared_memory.store("p0:latest_session", session.to_dict())
        self.shared_memory.store("p0:latest_signals", [s.to_dict() for s in cross_signals])

        logger.info(f"Stored {len(cross_signals)} signals to SharedMemory")

    async def _trigger_p1_assessment(self, context: SkillContext) -> List[Dict[str, Any]]:
        """Trigger P1 Value Judgment agents after P0 sync completes.

        This enables the organic flow from perception (P0) to judgment (P1).
        """
        from open_notebook.skills.runner import get_skill_runner

        results = []
        runner = get_skill_runner()

        # Map P1 agent types to skill types
        p1_skill_map = {
            "Q1P1": "painpoint_value_agent",
            "Q2P1": "emotion_alignment_agent",
            "Q3P1": "trend_value_agent",
            "Q4P1": "demand_assessment_agent"
        }

        for agent_type in self.p1_agents_to_trigger:
            skill_type = p1_skill_map.get(agent_type)
            if not skill_type:
                logger.warning(f"Unknown P1 agent type: {agent_type}")
                continue

            try:
                logger.info(f"Triggering P1 agent: {agent_type}...")

                result = await runner.execute_skill(
                    skill_type=skill_type,
                    parameters={
                        "target_notebook_id": self.target_notebook_id,
                        "hours_lookback": self.signal_ttl_hours
                    }
                )

                if result.status.value == "success":
                    results.append({
                        "agent": agent_type,
                        "status": "success",
                        "output": result.output
                    })
                    logger.info(f"{agent_type} completed successfully")
                else:
                    results.append({
                        "agent": agent_type,
                        "status": "failed",
                        "error": result.error_message
                    })
                    logger.warning(f"{agent_type} failed: {result.error_message}")

            except Exception as e:
                logger.error(f"Error triggering {agent_type}: {e}")
                results.append({
                    "agent": agent_type,
                    "status": "error",
                    "error": str(e)
                })

        return results

    async def _trigger_p2_building(self, context: SkillContext) -> List[Dict[str, Any]]:
        """Trigger P2 Relationship Building agents after P1 completes.

        This enables the organic flow from value judgment (P1) to relationship building (P2).
        """
        from open_notebook.skills.runner import get_skill_runner

        results = []
        runner = get_skill_runner()

        # Map P2 agent types to skill types
        p2_skill_map = {
            "Q1P2": "trust_builder_agent",
            "Q2P2": "community_binder_agent",
            "Q3P2": "viral_engine_agent",
            "Q4P2": "influence_network_agent"
        }

        for agent_type in self.p2_agents_to_trigger:
            skill_type = p2_skill_map.get(agent_type)
            if not skill_type:
                logger.warning(f"Unknown P2 agent type: {agent_type}")
                continue

            try:
                logger.info(f"Triggering P2 agent: {agent_type}...")

                result = await runner.execute_skill(
                    skill_type=skill_type,
                    parameters={
                        "target_notebook_id": self.target_notebook_id,
                        "hours_lookback": self.signal_ttl_hours
                    }
                )

                if result.status.value == "success":
                    results.append({
                        "agent": agent_type,
                        "status": "success",
                        "output": result.output
                    })
                    logger.info(f"{agent_type} completed successfully")
                else:
                    results.append({
                        "agent": agent_type,
                        "status": "failed",
                        "error": result.error_message
                    })
                    logger.warning(f"{agent_type} failed: {result.error_message}")

            except Exception as e:
                logger.error(f"Error triggering {agent_type}: {e}")
                results.append({
                    "agent": agent_type,
                    "status": "error",
                    "error": str(e)
                })

        return results

    async def run_daily_sync(self, context: SkillContext) -> SyncSession:
        """Execute a complete Daily Sync cycle."""
        session_id = f"sync-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        session = SyncSession(session_id=session_id, started_at=datetime.utcnow())
        self.current_session = session

        logger.info(f"=== Starting Daily Sync Session: {session_id} ===")

        try:
            # Phase 1: Trigger all agents
            logger.info("Phase 1: Triggering P0 agents...")

            agent_tasks = []
            for agent_type in self.agents_to_run:
                task = self._trigger_agent(agent_type, context)
                agent_tasks.append((agent_type, task))

            # Wait for all agents to complete
            for agent_type, task in agent_tasks:
                result = await task
                if result:
                    session.agent_reports[agent_type] = result
                    logger.info(f"Collected report from {agent_type}")
                else:
                    logger.warning(f"No report from {agent_type}")

            # Phase 2: Synthesize cross-quadrant signals
            logger.info("Phase 2: Synthesizing cross-quadrant patterns...")
            cross_signals = self._synthesize_cross_quadrant_signals(session.agent_reports)
            session.cross_quadrant_signals = cross_signals

            # Phase 3: Generate insights
            logger.info("Phase 3: Generating insights...")
            session.insights = self._generate_insights(session.agent_reports, cross_signals)

            # Phase 4: Store to SharedMemory
            logger.info("Phase 4: Storing to SharedMemory...")
            await self._store_to_shared_memory(session, cross_signals)

            # Phase 5: Trigger P1 Value Judgment Layer (optional)
            if self.enable_p1_trigger:
                logger.info("Phase 5: Triggering P1 Value Judgment Layer...")
                p1_results = await self._trigger_p1_assessment(context)
                session.p1_trigger_results = p1_results
                logger.info(f"P1 assessment triggered for {len(p1_results)} agents")

            # Phase 6: Trigger P2 Relationship Layer (optional)
            if self.enable_p2_trigger:
                logger.info("Phase 6: Triggering P2 Relationship Layer...")
                p2_results = await self._trigger_p2_building(context)
                session.p2_trigger_results = p2_results
                logger.info(f"P2 building triggered for {len(p2_results)} agents")

            # Mark complete
            session.status = "completed"
            session.completed_at = datetime.utcnow()
            self.session_history.append(session)

            logger.info(f"=== Daily Sync Completed: {len(cross_signals)} cross-quadrant signals ===")

            return session

        except Exception as e:
            logger.exception(f"Daily Sync failed: {e}")
            session.status = "failed"
            session.error_message = str(e)
            session.completed_at = datetime.utcnow()
            return session

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute the P0 Orchestrator - run Daily Sync."""
        started_at = datetime.utcnow()

        try:
            # Run the daily sync
            session = await self.run_daily_sync(context)

            # Prepare output
            output = {
                "session_id": session.session_id,
                "status": session.status,
                "started_at": session.started_at.isoformat(),
                "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                "agents_triggered": len(session.agent_reports),
                "cross_quadrant_signals": len(session.cross_quadrant_signals),
                "insights": session.insights,
                "error_message": session.error_message
            }

            # Create summary note if target notebook specified
            created_note_ids = []
            if self.target_notebook_id and session.status == "completed":
                note_content = self._format_session_report(session)
                result_note = Note(
                    title=f"[P0 Sync] Daily Sync Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    content=note_content,
                    note_type="ai"
                )
                await result_note.save()
                await result_note.add_to_notebook(self.target_notebook_id)
                created_note_ids.append(str(result_note.id))

            status = SkillStatus.SUCCESS if session.status == "completed" else SkillStatus.FAILED

            return SkillResult(
                skill_id=context.skill_id,
                status=status,
                started_at=started_at,
                completed_at=datetime.utcnow(),
                output=output,
                created_note_ids=created_note_ids,
                error_message=session.error_message
            )

        except Exception as e:
            logger.exception(f"P0 Orchestrator execution failed: {e}")
            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.FAILED,
                started_at=started_at,
                error_message=str(e)
            )

    def _format_session_report(self, session: SyncSession) -> str:
        """Format the sync session as a readable report."""
        lines = [
            "# 🎯 P0 Daily Sync Report\n",
            f"**Session ID:** {session.session_id}",
            f"**Status:** {session.status}",
            f"**Started:** {session.started_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Duration:** {(session.completed_at - session.started_at).total_seconds() // 60} minutes\n",
            "## Agent Participation\n"
        ]

        for agent, report in session.agent_reports.items():
            signal_count = report.get("signals_detected", len(report.get("top_signals", [])))
            lines.append(f"- **{agent}**: {signal_count} signals")

        lines.extend(["\n## Cross-Quadrant Signals\n"])

        if session.cross_quadrant_signals:
            for i, signal in enumerate(session.cross_quadrant_signals[:10], 1):
                emoji = "🔴" if signal.priority == SignalPriority.CRITICAL else "🟡" if signal.priority == SignalPriority.HIGH else "🟢"
                lines.extend([
                    f"### {emoji} Signal #{i}: {signal.signal_type}",
                    f"**Title:** {signal.title}",
                    f"**Confidence:** {signal.confidence_score:.0%}",
                    f"**Priority:** {signal.priority.value}",
                    f"**Source Quadrants:** {', '.join(signal.source_quadrants)}",
                    f"**Recommended Action:** {signal.recommended_action}",
                    ""
                ])
        else:
            lines.append("No cross-quadrant signals detected in this sync.\n")

        lines.extend(["## System Insights\n"])

        if session.insights:
            for insight in session.insights:
                lines.append(f"- 💡 {insight}")
        else:
            lines.append("No high-level insights generated.\n")

        lines.extend([
            "\n---\n",
            "*This report was generated by the P0 Orchestrator Agent.*",
            "*Next: Route signals to P1 (Value Judgment) layer for prioritization.*"
        ])

        return "\n".join(lines)

    def get_recent_sessions(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get recent sync sessions for analysis."""
        return [s.to_dict() for s in self.session_history[-count:]]

    def get_active_signals(self) -> List[Dict[str, Any]]:
        """Get all currently active signals from SharedMemory."""
        return self.shared_memory.get_recent_signals(hours=self.signal_ttl_hours)
