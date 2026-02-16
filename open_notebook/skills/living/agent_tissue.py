"""Agent Tissue - Groups of collaborating skill cells.

An Agent is like a tissue in biology - it's composed of multiple cells (skills)
that work together to perform a specific function. The agent coordinates
the execution of its skills in a specific pattern.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Callable

from loguru import logger

from open_notebook.skills.living.skill_cell import LivingSkill, SkillState


class CoordinationPattern(Enum):
    """Patterns for coordinating multiple skills."""
    SEQUENCE = "sequence"           # Execute one after another
    PARALLEL = "parallel"           # Execute all at once
    PIPELINE = "pipeline"           # Output of one is input to next
    CONDITIONAL = "conditional"     # Execute based on conditions
    LOOP = "loop"                   # Repeat until condition met
    VOTING = "voting"               # Multiple skills vote on result
    RACE = "race"                   # First to complete wins


@dataclass
class AgentCoordination:
    """Coordination configuration for skills within an agent."""
    pattern: CoordinationPattern = CoordinationPattern.SEQUENCE
    skill_order: List[str] = field(default_factory=list)  # For SEQUENCE/PIPELINE
    condition: Optional[str] = None  # For CONDITIONAL/LOOP
    max_parallel: int = 5  # For PARALLEL
    timeout: timedelta = field(default_factory=lambda: timedelta(minutes=10))

    # Data flow mapping
    input_mapping: Dict[str, Dict[str, str]] = field(default_factory=dict)
    output_mapping: Dict[str, Dict[str, str]] = field(default_factory=dict)


@dataclass
class AgentRhythm:
    """Rhythm properties - the 'heartbeat' and temporal pattern of the agent."""
    # Pulse - regular health check
    pulse_interval: timedelta = field(default_factory=lambda: timedelta(minutes=5))

    # Breathing - active/passive cycles
    active_hours: Optional[tuple] = None  # (start_hour, end_hour) e.g., (9, 18)
    rest_days: List[int] = field(default_factory=list)  # 0=Monday, 6=Sunday

    # Metabolism - update/rebuild frequency
    update_interval: Optional[timedelta] = None

    # Circadian alignment - peak performance times
    peak_hours: List[int] = field(default_factory=lambda: [9, 10, 14, 15, 20, 21])

    last_pulse: Optional[datetime] = None
    next_update: Optional[datetime] = None

    def is_active_time(self, dt: Optional[datetime] = None) -> bool:
        """Check if current time is within active hours."""
        if dt is None:
            dt = datetime.now()

        # Check day
        if dt.weekday() in self.rest_days:
            return False

        # Check hours
        if self.active_hours:
            start, end = self.active_hours
            if not (start <= dt.hour <= end):
                return False

        return True

    def is_peak_time(self, dt: Optional[datetime] = None) -> bool:
        """Check if current time is a peak performance hour."""
        if dt is None:
            dt = datetime.now()
        return dt.hour in self.peak_hours

    def should_pulse(self) -> bool:
        """Check if it's time for a health check pulse."""
        if self.last_pulse is None:
            return True
        return datetime.now() >= self.last_pulse + self.pulse_interval

    def record_pulse(self):
        """Record that a pulse was performed."""
        self.last_pulse = datetime.now()


@dataclass
class AgentState:
    """Current state of an agent tissue."""
    status: str = "healthy"  # healthy, stressed, recovering, dormant
    energy_level: float = 1.0  # 0.0 to 1.0
    stress_level: float = 0.0  # 0.0 to 1.0

    # Skill states
    skill_states: Dict[str, str] = field(default_factory=dict)

    # Performance metrics
    tasks_completed: int = 0
    tasks_failed: int = 0
    avg_response_time: Optional[timedelta] = None

    def update_health(self):
        """Update agent health based on metrics."""
        if self.stress_level > 0.8:
            self.status = "critical"
        elif self.stress_level > 0.5:
            self.status = "stressed"
        elif self.stress_level > 0.2:
            self.status = "healthy"
        else:
            self.status = "optimal"

        # Energy decreases with stress
        self.energy_level = max(0.0, 1.0 - self.stress_level)


class AgentTissue:
    """An agent tissue composed of collaborating skill cells.

    Like biological tissue, an agent:
    - Has multiple cells (skills) working together
    - Has a specific function (its purpose)
    - Has a lifecycle (growth, maintenance, renewal)
    - Responds to stimuli (events/triggers)
    - Can adapt and evolve
    """

    # Class-level registry
    _registry: Dict[str, "AgentTissue"] = {}

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        purpose: str,  # What this agent is meant to do
        skills: Optional[List[str]] = None,  # Skill IDs
        coordination: Optional[AgentCoordination] = None,
        rhythm: Optional[AgentRhythm] = None,
        stimuli: Optional[List[str]] = None,  # What triggers this agent
        receptors: Optional[Dict[str, Callable]] = None,  # How it responds
    ):
        # Identity
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.purpose = purpose

        # Components
        self.skill_ids = skills or []
        self._skills: Dict[str, LivingSkill] = {}
        self.coordination = coordination or AgentCoordination()
        self.rhythm = rhythm or AgentRhythm()
        self.stimuli = stimuli or []
        self.receptors = receptors or {}

        # State
        self.state = AgentState()
        self.created_at = datetime.now()
        self.last_executed: Optional[datetime] = None

        # Runtime
        self._running = False
        self._pulse_task: Optional[asyncio.Task] = None
        self._event_queue: asyncio.Queue = asyncio.Queue()

        # Register
        AgentTissue._registry[agent_id] = self

        logger.info(f"AgentTissue '{name}' ({agent_id}) created with {len(self.skill_ids)} skills")

    @classmethod
    def get(cls, agent_id: str) -> Optional["AgentTissue"]:
        """Get an agent by ID."""
        return cls._registry.get(agent_id)

    @classmethod
    def list_all(cls) -> List["AgentTissue"]:
        """List all registered agents."""
        return list(cls._registry.values())

    def add_skill(self, skill_id: str):
        """Add a skill to this agent."""
        if skill_id not in self.skill_ids:
            self.skill_ids.append(skill_id)
            logger.debug(f"Added skill {skill_id} to agent {self.agent_id}")

    def remove_skill(self, skill_id: str):
        """Remove a skill from this agent."""
        if skill_id in self.skill_ids:
            self.skill_ids.remove(skill_id)
            self._skills.pop(skill_id, None)

    def resolve_skills(self):
        """Resolve skill references to actual instances."""
        self._skills = {}
        for skill_id in self.skill_ids:
            skill = LivingSkill.get_instance(skill_id)
            if skill:
                self._skills[skill_id] = skill
            else:
                logger.warning(f"Skill {skill_id} not found for agent {self.agent_id}")

    async def stimulate(self, stimulus: str, data: Optional[Dict] = None):
        """Stimulate the agent with an external trigger.

        Like a nerve stimulus triggering a tissue response.
        """
        if stimulus not in self.stimuli:
            logger.debug(f"Agent {self.agent_id} ignoring stimulus {stimulus}")
            return

        logger.info(f"Agent {self.agent_id} stimulated by {stimulus}")

        # Check if agent can respond
        if not self.can_respond():
            logger.warning(f"Agent {self.agent_id} cannot respond (status: {self.state.status})")
            return

        # Queue the event
        await self._event_queue.put({
            "stimulus": stimulus,
            "data": data,
            "timestamp": datetime.now()
        })

    def can_respond(self) -> bool:
        """Check if agent is able to respond to stimuli."""
        if self.state.status in ["critical", "dormant"]:
            return False
        if not self.rhythm.is_active_time():
            return False
        return self.state.energy_level > 0.2

    async def execute(self, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute the agent's coordinated skills.

        This is the main function that orchestrates all skills.
        """
        if not self._skills:
            self.resolve_skills()

        self.last_executed = datetime.now()
        start_time = datetime.now()

        # Increase stress during execution
        self.state.stress_level = min(1.0, self.state.stress_level + 0.1)

        try:
            logger.info(f"Agent {self.agent_id} executing with pattern {self.coordination.pattern.value}")

            if self.coordination.pattern == CoordinationPattern.SEQUENCE:
                result = await self._execute_sequence(context)
            elif self.coordination.pattern == CoordinationPattern.PARALLEL:
                result = await self._execute_parallel(context)
            elif self.coordination.pattern == CoordinationPattern.PIPELINE:
                result = await self._execute_pipeline(context)
            elif self.coordination.pattern == CoordinationPattern.CONDITIONAL:
                result = await self._execute_conditional(context)
            elif self.coordination.pattern == CoordinationPattern.RACE:
                result = await self._execute_race(context)
            else:
                result = await self._execute_sequence(context)

            # Update metrics
            duration = datetime.now() - start_time
            self._update_metrics(duration, success=True)
            self.state.tasks_completed += 1

            return {"success": True, "result": result, "duration": duration}

        except Exception as e:
            duration = datetime.now() - start_time
            self._update_metrics(duration, success=False)
            self.state.tasks_failed += 1
            logger.exception(f"Agent {self.agent_id} execution failed: {e}")
            return {"success": False, "error": str(e)}

        finally:
            # Decrease stress after execution
            self.state.stress_level = max(0.0, self.state.stress_level - 0.05)
            self.state.update_health()

    async def _execute_sequence(self, context: Optional[Dict]) -> Any:
        """Execute skills in sequence."""
        results = []
        skill_order = self.coordination.skill_order or list(self._skills.keys())

        for skill_id in skill_order:
            skill = self._skills.get(skill_id)
            if skill and skill.is_ready():
                result = await skill.invoke(context)
                results.append({"skill_id": skill_id, "result": result})
                # Update context for next skill
                context = context or {}
                context[f"{skill_id}_output"] = result

        return results

    async def _execute_parallel(self, context: Optional[Dict]) -> Any:
        """Execute skills in parallel."""
        tasks = []
        skills = list(self._skills.values())[:self.coordination.max_parallel]

        for skill in skills:
            if skill.is_ready():
                task = asyncio.create_task(skill.invoke(context.copy() if context else {}))
                tasks.append((skill.skill_id, task))

        results = []
        for skill_id, task in tasks:
            try:
                result = await task
                results.append({"skill_id": skill_id, "result": result, "success": True})
            except Exception as e:
                results.append({"skill_id": skill_id, "error": str(e), "success": False})

        return results

    async def _execute_pipeline(self, context: Optional[Dict]) -> Any:
        """Execute skills in pipeline (output -> input)."""
        data = context.copy() if context else {}
        skill_order = self.coordination.skill_order or list(self._skills.keys())

        for skill_id in skill_order:
            skill = self._skills.get(skill_id)
            if skill and skill.is_ready():
                # Map input
                skill_input = self._map_input(skill_id, data)
                result = await skill.invoke(skill_input)
                # Map output
                data = self._map_output(skill_id, result, data)

        return data

    async def _execute_conditional(self, context: Optional[Dict]) -> Any:
        """Execute skills based on conditions."""
        results = []

        for skill_id, skill in self._skills.items():
            if self._check_condition(skill_id, context):
                if skill.is_ready():
                    result = await skill.invoke(context)
                    results.append({"skill_id": skill_id, "result": result})

        return results

    async def _execute_race(self, context: Optional[Dict]) -> Any:
        """Execute skills in race (first to complete wins)."""
        tasks = []

        for skill in self._skills.values():
            if skill.is_ready():
                task = asyncio.create_task(skill.invoke(context.copy() if context else {}))
                tasks.append((skill.skill_id, task))

        # Wait for first to complete
        pending = [task for _, task in tasks]
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)

        # Cancel remaining
        for task in pending:
            task.cancel()

        # Get result
        winner_task = done.pop()
        winner_id = next(sid for sid, t in tasks if t == winner_task)

        try:
            result = await winner_task
            return {"winner": winner_id, "result": result}
        except Exception as e:
            return {"winner": winner_id, "error": str(e)}

    def _map_input(self, skill_id: str, data: Dict) -> Dict:
        """Map data to skill input based on coordination config."""
        mapping = self.coordination.input_mapping.get(skill_id, {})
        result = {"original": data}
        for key, path in mapping.items():
            # Simple path traversal
            parts = path.split(".")
            value = data
            for part in parts:
                value = value.get(part, {}) if isinstance(value, dict) else None
            result[key] = value
        return result

    def _map_output(self, skill_id: str, result: Any, data: Dict) -> Dict:
        """Map skill output to data based on coordination config."""
        mapping = self.coordination.output_mapping.get(skill_id, {})
        new_data = data.copy()
        new_data[f"{skill_id}_output"] = result
        return new_data

    def _check_condition(self, skill_id: str, context: Optional[Dict]) -> bool:
        """Check if condition is met for skill execution."""
        # Simple condition checking - can be extended
        condition = self.coordination.condition
        if not condition:
            return True
        # TODO: Implement proper condition evaluation
        return True

    def _update_metrics(self, duration: timedelta, success: bool):
        """Update agent performance metrics."""
        if self.state.avg_response_time is None:
            self.state.avg_response_time = duration
        else:
            # Rolling average
            n = self.state.tasks_completed + self.state.tasks_failed
            self.state.avg_response_time = (
                (self.state.avg_response_time * (n - 1) + duration) / n
            )

    async def start(self):
        """Start the agent's background processes."""
        self._running = True
        self._pulse_task = asyncio.create_task(self._pulse_loop())
        logger.info(f"Agent {self.agent_id} started")

    async def stop(self):
        """Stop the agent."""
        self._running = False
        if self._pulse_task:
            self._pulse_task.cancel()
        logger.info(f"Agent {self.agent_id} stopped")

    async def _pulse_loop(self):
        """Background pulse loop for health checks."""
        while self._running:
            try:
                if self.rhythm.should_pulse():
                    await self._pulse()
                    self.rhythm.record_pulse()

                # Process any queued events
                while not self._event_queue.empty():
                    event = await self._event_queue.get()
                    await self.execute(event.get("data"))

                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Agent {self.agent_id} pulse error: {e}")
                await asyncio.sleep(5)

    async def _pulse(self):
        """Perform a health check pulse."""
        # Resolve any missing skills
        self.resolve_skills()

        # Check skill health
        for skill_id, skill in list(self._skills.items()):
            self.state.skill_states[skill_id] = skill.lifecycle.state.value

        # Update agent health
        self.state.update_health()

        logger.debug(f"Agent {self.agent_id} pulse: status={self.state.status}, energy={self.state.energy_level:.2f}")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize agent to dictionary."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "purpose": self.purpose,
            "status": self.state.status,
            "energy_level": self.state.energy_level,
            "skill_count": len(self.skill_ids),
            "skills": list(self.skill_ids),
            "coordination_pattern": self.coordination.pattern.value,
            "stimuli": self.stimuli,
            "created_at": self.created_at.isoformat(),
            "last_executed": self.last_executed.isoformat() if self.last_executed else None,
        }

    def __repr__(self) -> str:
        return f"<AgentTissue {self.agent_id} ({self.state.status}, {len(self.skill_ids)} skills)>"
