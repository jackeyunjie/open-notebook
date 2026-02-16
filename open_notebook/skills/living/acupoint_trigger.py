"""Acupoint Trigger - External access points for the living knowledge system.

In traditional Chinese medicine, acupoints are specific points on meridians
where external stimulation can affect internal systems. Similarly, in the
living knowledge system, acupoints are trigger points where external events
(Agently workflows, time schedules, webhooks) can stimulate internal skills.
"""

import asyncio
import functools
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Union
from uuid import uuid4

from loguru import logger

from open_notebook.skills.living.meridian_flow import (
    ControlMeridian,
    DataMeridian,
    FlowNode,
    FlowType,
    MeridianSystem,
)


class TriggerType(Enum):
    """Types of acupoint triggers."""
    TEMPORAL = "temporal"      # Time-based triggers (cron, interval)
    EVENT = "event"            # Event-based triggers (data arrival, state change)
    CONDITION = "condition"    # Condition-based triggers (thresholds, patterns)
    MANUAL = "manual"          # Manual triggers (API, UI, CLI)
    AGENTLY = "agently"        # Agently workflow triggers
    WEBHOOK = "webhook"        # External webhook triggers


class TriggerState(Enum):
    """State of a trigger."""
    INACTIVE = "inactive"      # Not yet activated
    ACTIVE = "active"          # Ready to trigger
    TRIGGERED = "triggered"    # Has been triggered, processing
    COOLDOWN = "cooldown"      # In cooldown period
    DISABLED = "disabled"      # Manually disabled


@dataclass
class TriggerCondition:
    """Condition for triggering."""
    # Threshold conditions
    threshold_type: Optional[str] = None  # "value", "count", "rate", "pattern"
    threshold_value: Optional[float] = None
    comparison: Optional[str] = None  # ">", "<", "==", "!=", ">=", "<="

    # Pattern conditions
    pattern: Optional[str] = None  # Regex or pattern string
    field_path: Optional[str] = None  # Path to field to check (e.g., "data.score")

    # Composite conditions
    required_triggers: List[str] = field(default_factory=list)  # AND condition
    alternative_triggers: List[str] = field(default_factory=list)  # OR condition

    def evaluate(self, data: Dict[str, Any]) -> bool:
        """Evaluate condition against data."""
        if self.threshold_type and self.threshold_value is not None:
            value = self._get_value(data, self.field_path)
            if value is None:
                return False
            return self._compare(value, self.threshold_value, self.comparison or ">=")

        if self.pattern and self.field_path:
            value = self._get_value(data, self.field_path)
            if value is None:
                return False
            import re
            return bool(re.search(self.pattern, str(value)))

        return True

    def _get_value(self, data: Dict, path: Optional[str]) -> Any:
        """Get value from data by path."""
        if not path:
            return data
        parts = path.split(".")
        value = data
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value

    def _compare(self, a: float, b: float, op: str) -> bool:
        """Compare two values."""
        ops = {
            ">": lambda x, y: x > y,
            "<": lambda x, y: x < y,
            "==": lambda x, y: x == y,
            "!=": lambda x, y: x != y,
            ">=": lambda x, y: x >= y,
            "<=": lambda x, y: x <= y,
        }
        return ops.get(op, lambda x, y: False)(a, b)


@dataclass
class TriggerConfig:
    """Configuration for an acupoint trigger."""
    # Timing
    cooldown: timedelta = field(default_factory=lambda: timedelta(seconds=1))
    debounce: Optional[timedelta] = None
    max_triggers: Optional[int] = None  # Max triggers per period
    trigger_period: Optional[timedelta] = None

    # Routing
    target_skills: List[str] = field(default_factory=list)
    target_agents: List[str] = field(default_factory=list)
    meridians: List[str] = field(default_factory=list)  # Meridians to notify

    # Data transformation
    input_mapping: Dict[str, str] = field(default_factory=dict)
    output_template: Optional[str] = None  # Jinja2 template

    # Metadata
    priority: int = 5  # 1-10, lower is higher priority
    tags: Set[str] = field(default_factory=set)


@dataclass
class TriggerHistory:
    """History of trigger activations."""
    trigger_count: int = 0
    last_triggered: Optional[datetime] = None
    last_data: Optional[Dict] = None
    trigger_times: List[datetime] = field(default_factory=list)
    errors: List[Dict] = field(default_factory=list)

    def record(self, data: Optional[Dict] = None):
        """Record a trigger activation."""
        now = datetime.now()
        self.trigger_count += 1
        self.last_triggered = now
        self.last_data = data
        self.trigger_times.append(now)
        # Keep only last 100 timestamps
        if len(self.trigger_times) > 100:
            self.trigger_times = self.trigger_times[-100:]

    def record_error(self, error: str):
        """Record an error."""
        self.errors.append({
            "time": datetime.now().isoformat(),
            "error": error
        })
        if len(self.errors) > 10:
            self.errors = self.errors[-10:]

    def is_in_cooldown(self, cooldown: timedelta) -> bool:
        """Check if trigger is in cooldown."""
        if not self.last_triggered:
            return False
        return datetime.now() - self.last_triggered < cooldown

    def get_trigger_rate(self, window: timedelta) -> float:
        """Get trigger rate in the given time window."""
        now = datetime.now()
        recent = [t for t in self.trigger_times if now - t < window]
        return len(recent) / window.total_seconds() if window.total_seconds() > 0 else 0


class AcupointTrigger:
    """An acupoint trigger - external access point to the living system.

    Like an acupuncture point, it:
    - Can be stimulated externally (Agently, webhook, schedule)
    - Has specific effects on internal systems (skills/agents)
    - Can be activated in different ways (press, twist, tap)
    - Has connection to meridians (data/control flows)
    """

    def __init__(
        self,
        trigger_id: str,
        name: str,
        trigger_type: TriggerType,
        condition: Optional[TriggerCondition] = None,
        config: Optional[TriggerConfig] = None,
        handler: Optional[Callable] = None,
    ):
        self.trigger_id = trigger_id
        self.name = name
        self.trigger_type = trigger_type
        self.condition = condition or TriggerCondition()
        self.config = config or TriggerConfig()
        self.handler = handler

        # State
        self.state = TriggerState.INACTIVE
        self.history = TriggerHistory()

        # Debounce tracking
        self._last_data_hash: Optional[str] = None
        self._debounce_task: Optional[asyncio.Task] = None

        # Statistics
        self.created_at = datetime.now()
        self.activation_count = 0

        logger.debug(f"AcupointTrigger '{name}' ({trigger_id}) created")

    async def activate(self, data: Optional[Dict[str, Any]] = None) -> bool:
        """Activate this trigger.

        Returns True if trigger was activated, False if blocked by cooldown/condition.
        """
        # Check state
        if self.state == TriggerState.DISABLED:
            logger.debug(f"Trigger {self.trigger_id} is disabled")
            return False

        # Check cooldown
        if self.history.is_in_cooldown(self.config.cooldown):
            logger.debug(f"Trigger {self.trigger_id} in cooldown")
            return False

        # Check condition
        if data and not self.condition.evaluate(data):
            logger.debug(f"Trigger {self.trigger_id} condition not met")
            return False

        # Check debounce
        if self.config.debounce and data:
            data_hash = self._hash_data(data)
            if data_hash == self._last_data_hash:
                logger.debug(f"Trigger {self.trigger_id} debounced")
                return False
            self._last_data_hash = data_hash

        # Check rate limiting
        if self.config.max_triggers and self.config.trigger_period:
            rate = self.history.get_trigger_rate(self.config.trigger_period)
            max_rate = self.config.max_triggers / self.config.trigger_period.total_seconds()
            if rate >= max_rate:
                logger.warning(f"Trigger {self.trigger_id} rate limit exceeded")
                return False

        # Activate
        self.state = TriggerState.TRIGGERED
        self.activation_count += 1
        self.history.record(data)

        try:
            # Call handler
            if self.handler:
                if asyncio.iscoroutinefunction(self.handler):
                    result = await self.handler(data or {})
                else:
                    result = self.handler(data or {})

            # Route to meridians
            await self._route_to_meridians(data or {})

            # Route to targets
            await self._route_to_targets(data or {})

            self.state = TriggerState.ACTIVE
            logger.info(f"Trigger {self.trigger_id} activated successfully")
            return True

        except Exception as e:
            self.state = TriggerState.ACTIVE
            self.history.record_error(str(e))
            logger.error(f"Trigger {self.trigger_id} activation failed: {e}")
            return False

    def _hash_data(self, data: Dict) -> str:
        """Hash data for debounce comparison."""
        return hashlib.md5(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()

    async def _route_to_meridians(self, data: Dict):
        """Route trigger data to connected meridians."""
        for meridian_id in self.config.meridians:
            meridian = MeridianSystem.get(meridian_id)
            if meridian:
                await meridian.broadcast(
                    source=f"trigger:{self.trigger_id}",
                    payload={
                        "trigger_id": self.trigger_id,
                        "trigger_type": self.trigger_type.value,
                        "data": data,
                        "timestamp": datetime.now().isoformat()
                    },
                    priority=self.config.priority
                )

    async def _route_to_targets(self, data: Dict):
        """Route trigger to target skills/agents."""
        # Import here to avoid circular dependency
        from open_notebook.skills.living.agent_tissue import AgentTissue
        from open_notebook.skills.living.skill_cell import LivingSkill

        # Stimulate target skills
        for skill_id in self.config.target_skills:
            skill = LivingSkill.get_instance(skill_id)
            if skill:
                mapped_data = self._map_input(data)
                asyncio.create_task(skill.invoke(mapped_data))

        # Stimulate target agents
        for agent_id in self.config.target_agents:
            agent = AgentTissue.get(agent_id)
            if agent:
                asyncio.create_task(agent.stimulate(self.trigger_id, data))

    def _map_input(self, data: Dict) -> Dict:
        """Map input data based on config."""
        if not self.config.input_mapping:
            return data

        result = {"original": data}
        for key, path in self.config.input_mapping.items():
            parts = path.split(".")
            value = data
            for part in parts:
                value = value.get(part, {}) if isinstance(value, dict) else None
            result[key] = value
        return result

    def enable(self):
        """Enable this trigger."""
        self.state = TriggerState.ACTIVE
        logger.info(f"Trigger {self.trigger_id} enabled")

    def disable(self):
        """Disable this trigger."""
        self.state = TriggerState.DISABLED
        logger.info(f"Trigger {self.trigger_id} disabled")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize trigger to dictionary."""
        return {
            "trigger_id": self.trigger_id,
            "name": self.name,
            "trigger_type": self.trigger_type.value,
            "state": self.state.value,
            "activation_count": self.activation_count,
            "created_at": self.created_at.isoformat(),
            "last_triggered": self.history.last_triggered.isoformat() if self.history.last_triggered else None,
            "target_skills": self.config.target_skills,
            "target_agents": self.config.target_agents,
            "meridians": self.config.meridians,
        }


class TriggerRegistry:
    """Registry for all acupoint triggers."""

    _triggers: Dict[str, AcupointTrigger] = {}
    _by_type: Dict[TriggerType, Set[str]] = {}
    _by_tag: Dict[str, Set[str]] = {}

    @classmethod
    def register(cls, trigger: AcupointTrigger) -> AcupointTrigger:
        """Register a trigger."""
        cls._triggers[trigger.trigger_id] = trigger

        # Index by type
        if trigger.trigger_type not in cls._by_type:
            cls._by_type[trigger.trigger_type] = set()
        cls._by_type[trigger.trigger_type].add(trigger.trigger_id)

        # Index by tags
        for tag in trigger.config.tags:
            if tag not in cls._by_tag:
                cls._by_tag[tag] = set()
            cls._by_tag[tag].add(trigger.trigger_id)

        logger.info(f"Registered trigger: {trigger.trigger_id}")
        return trigger

    @classmethod
    def get(cls, trigger_id: str) -> Optional[AcupointTrigger]:
        """Get a trigger by ID."""
        return cls._triggers.get(trigger_id)

    @classmethod
    def list_all(cls) -> List[AcupointTrigger]:
        """List all registered triggers."""
        return list(cls._triggers.values())

    @classmethod
    def list_by_type(cls, trigger_type: TriggerType) -> List[AcupointTrigger]:
        """List triggers by type."""
        trigger_ids = cls._by_type.get(trigger_type, set())
        return [cls._triggers[tid] for tid in trigger_ids if tid in cls._triggers]

    @classmethod
    def list_by_tag(cls, tag: str) -> List[AcupointTrigger]:
        """List triggers by tag."""
        trigger_ids = cls._by_tag.get(tag, set())
        return [cls._triggers[tid] for tid in trigger_ids if tid in cls._triggers]

    @classmethod
    async def activate_all(
        cls,
        trigger_type: Optional[TriggerType] = None,
        data: Optional[Dict] = None
    ) -> Dict[str, bool]:
        """Activate all triggers of a given type."""
        triggers = cls.list_by_type(trigger_type) if trigger_type else cls.list_all()
        results = {}
        for trigger in triggers:
            results[trigger.trigger_id] = await trigger.activate(data)
        return results

    @classmethod
    def unregister(cls, trigger_id: str):
        """Unregister a trigger."""
        trigger = cls._triggers.pop(trigger_id, None)
        if trigger:
            cls._by_type.get(trigger.trigger_type, set()).discard(trigger_id)
            for tag in trigger.config.tags:
                cls._by_tag.get(tag, set()).discard(trigger_id)
            logger.info(f"Unregistered trigger: {trigger_id}")


# Decorator for easy trigger creation
def acupoint(
    name: Optional[str] = None,
    trigger_type: TriggerType = TriggerType.EVENT,
    condition: Optional[TriggerCondition] = None,
    target_skills: Optional[List[str]] = None,
    target_agents: Optional[List[str]] = None,
    meridians: Optional[List[str]] = None,
    cooldown_seconds: float = 1.0,
    priority: int = 5,
    tags: Optional[List[str]] = None,
):
    """Decorator to create an acupoint trigger from a function.

    Example:
        @acupoint(
            name="content_created",
            trigger_type=TriggerType.EVENT,
            target_agents=["p0_orchestrator"],
            meridians=["data.content"]
        )
        async def on_content_created(event_data):
            print(f"Content created: {event_data}")
    """
    def decorator(func: Callable) -> AcupointTrigger:
        trigger_id = f"{func.__module__}.{func.__name__}"
        config = TriggerConfig(
            target_skills=target_skills or [],
            target_agents=target_agents or [],
            meridians=meridians or [],
            cooldown=timedelta(seconds=cooldown_seconds),
            priority=priority,
            tags=set(tags or [])
        )

        trigger = AcupointTrigger(
            trigger_id=trigger_id,
            name=name or func.__name__,
            trigger_type=trigger_type,
            condition=condition,
            config=config,
            handler=func
        )

        TriggerRegistry.register(trigger)
        return trigger

    return decorator


# Predefined trigger creators for common patterns

class AgentlyAdapter:
    """Adapter for Agently workflow integration."""

    @staticmethod
    def create_workflow_trigger(
        workflow_name: str,
        on_complete: Optional[Callable] = None,
        target_agents: Optional[List[str]] = None,
    ) -> AcupointTrigger:
        """Create a trigger for Agently workflow completion."""
        return AcupointTrigger(
            trigger_id=f"agently.workflow.{workflow_name}",
            name=f"Agently Workflow: {workflow_name}",
            trigger_type=TriggerType.AGENTLY,
            config=TriggerConfig(
                target_agents=target_agents or [],
                meridians=["data.agently", "control.workflow"],
                priority=3,
                tags={"agently", "workflow", workflow_name}
            ),
            handler=on_complete
        )

    @staticmethod
    def create_node_trigger(
        workflow_name: str,
        node_name: str,
        on_execute: Optional[Callable] = None
    ) -> AcupointTrigger:
        """Create a trigger for Agently node execution."""
        return AcupointTrigger(
            trigger_id=f"agently.node.{workflow_name}.{node_name}",
            name=f"Agently Node: {workflow_name}.{node_name}",
            trigger_type=TriggerType.AGENTLY,
            config=TriggerConfig(
                meridians=["data.agently", f"control.node.{node_name}"],
                priority=2,
                tags={"agently", "node", workflow_name, node_name}
            ),
            handler=on_execute
        )


class TemporalScheduler:
    """Scheduler for temporal triggers."""

    def __init__(self):
        self._scheduled_tasks: Dict[str, asyncio.Task] = {}
        self._running = False

    async def start(self):
        """Start the temporal scheduler."""
        self._running = True
        # Schedule all temporal triggers
        temporal_triggers = TriggerRegistry.list_by_type(TriggerType.TEMPORAL)
        for trigger in temporal_triggers:
            self._schedule_trigger(trigger)
        logger.info(f"Temporal scheduler started with {len(temporal_triggers)} triggers")

    async def stop(self):
        """Stop the temporal scheduler."""
        self._running = False
        for task in self._scheduled_tasks.values():
            task.cancel()
        self._scheduled_tasks.clear()
        logger.info("Temporal scheduler stopped")

    def _schedule_trigger(self, trigger: AcupointTrigger):
        """Schedule a temporal trigger."""
        if trigger.trigger_id in self._scheduled_tasks:
            self._scheduled_tasks[trigger.trigger_id].cancel()

        task = asyncio.create_task(self._run_trigger_loop(trigger))
        self._scheduled_tasks[trigger.trigger_id] = task

    async def _run_trigger_loop(self, trigger: AcupointTrigger):
        """Run the trigger activation loop."""
        while self._running:
            try:
                await trigger.activate()
                # Wait for next activation based on trigger config
                # This is simplified - real implementation would use proper scheduling
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Temporal trigger {trigger.trigger_id} error: {e}")
                await asyncio.sleep(60)


class WebhookServer:
    """Server for webhook-based triggers."""

    def __init__(self, port: int = 8765):
        self.port = port
        self._routes: Dict[str, str] = {}  # path -> trigger_id

    def register_webhook(self, path: str, trigger_id: str) -> str:
        """Register a webhook path for a trigger."""
        self._routes[path] = trigger_id
        return f"http://localhost:{self.port}/webhook/{path}"

    async def handle_webhook(self, path: str, data: Dict) -> bool:
        """Handle incoming webhook request."""
        trigger_id = self._routes.get(path)
        if not trigger_id:
            logger.warning(f"No trigger registered for webhook path: {path}")
            return False

        trigger = TriggerRegistry.get(trigger_id)
        if not trigger:
            logger.warning(f"Trigger not found: {trigger_id}")
            return False

        return await trigger.activate(data)
