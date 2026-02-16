"""Skill Cell - The basic functional unit of the living knowledge system.

A Skill Cell is analogous to a biological cell - it has:
- Lifecycle (birth, growth, function, death)
- Temporal properties (rhythm, schedule, frequency)
- Resources (code, data, templates)
- Dependencies (inputs required, outputs produced)
"""

import asyncio
import hashlib
import importlib.util
import inspect
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union

from croniter import croniter
from jinja2 import Environment, FileSystemLoader, Template
from loguru import logger
from pydantic import BaseModel, Field


class SkillState(Enum):
    """Lifecycle states of a skill cell."""
    IDLE = "idle"              # Waiting to be invoked
    PENDING = "pending"        # Queued for execution
    RUNNING = "running"        # Currently executing
    PAUSED = "paused"          # Temporarily paused
    COMPLETED = "completed"    # Successfully finished
    FAILED = "failed"          # Execution failed
    EXPIRED = "expired"        # Past expiration time
    DISABLED = "disabled"      # Manually disabled


@dataclass
class SkillTemporal:
    """Temporal properties - when and how often the skill executes."""
    # Scheduling
    cron: Optional[str] = None           # Cron expression (e.g., "0 9 * * *")
    interval: Optional[timedelta] = None  # Interval between executions
    delay: Optional[timedelta] = None    # Delay before first execution

    # Timing
    timezone: str = "UTC"                # Timezone for scheduling
    timeout: timedelta = field(default_factory=lambda: timedelta(minutes=5))
    duration_estimate: timedelta = field(default_factory=lambda: timedelta(minutes=1))

    # Lifecycle
    start_at: Optional[datetime] = None  # When skill becomes active
    expires_at: Optional[datetime] = None  # When skill expires
    max_retries: int = 3
    retry_delay: timedelta = field(default_factory=lambda: timedelta(minutes=1))

    def is_due(self, last_run: Optional[datetime] = None) -> bool:
        """Check if skill is due for execution."""
        now = datetime.now()

        # Check start time
        if self.start_at and now < self.start_at:
            return False

        # Check expiration
        if self.expires_at and now > self.expires_at:
            return False

        # Check cron schedule
        if self.cron:
            if last_run is None:
                # First run - always ready
                return True
            else:
                # Check if we passed a scheduled time since last run
                itr = croniter(self.cron, last_run)
                next_scheduled = itr.get_next(datetime)
                return now >= next_scheduled

        # Check interval
        if self.interval and last_run:
            return now >= last_run + self.interval

        return True

    def get_next_run(self, last_run: Optional[datetime] = None) -> Optional[datetime]:
        """Get next scheduled execution time."""
        now = datetime.now()

        if self.cron:
            base = last_run or now
            itr = croniter(self.cron, base)
            return itr.get_next(datetime)

        if self.interval:
            base = last_run or now
            return base + self.interval

        return None


@dataclass
class SkillLifecycle:
    """Lifecycle tracking for a skill cell."""
    state: SkillState = SkillState.IDLE
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    fail_count: int = 0
    success_count: int = 0

    # Health metrics
    avg_duration: Optional[timedelta] = None
    last_error: Optional[str] = None
    last_error_at: Optional[datetime] = None

    def transition_to(self, new_state: SkillState, error: Optional[str] = None):
        """Transition to a new state."""
        old_state = self.state
        self.state = new_state
        self.updated_at = datetime.now()

        if error:
            self.last_error = error
            self.last_error_at = datetime.now()

        logger.debug(f"Skill lifecycle: {old_state.value} -> {new_state.value}")

        # Update counters
        if new_state == SkillState.COMPLETED:
            self.success_count += 1
        elif new_state == SkillState.FAILED:
            self.fail_count += 1

    def record_run_start(self):
        """Record the start of a run."""
        self.last_run = datetime.now()
        self.run_count += 1
        self.transition_to(SkillState.RUNNING)

    def record_run_end(self, duration: timedelta, success: bool, error: Optional[str] = None):
        """Record the end of a run."""
        # Update average duration
        if self.avg_duration is None:
            self.avg_duration = duration
        else:
            # Rolling average
            self.avg_duration = (self.avg_duration * (self.run_count - 1) + duration) / self.run_count

        if success:
            self.transition_to(SkillState.COMPLETED)
        else:
            self.transition_to(SkillState.FAILED, error)


@dataclass
class SkillResource:
    """Resource definition (scripts, templates, data)."""
    name: str
    type: str  # "python", "jinja2", "json", "yaml", "prompt", "data"
    path: Optional[str] = None
    content: Optional[str] = None
    hash: Optional[str] = None

    # For Python scripts
    entry_point: Optional[str] = "execute"  # Function name to call

    # For templates
    template_vars: Optional[List[str]] = None

    def load(self, base_path: Optional[str] = None) -> Any:
        """Load the resource content."""
        if self.content is not None:
            return self._parse_content()

        if self.path and base_path:
            full_path = os.path.join(base_path, self.path)
            with open(full_path, 'r', encoding='utf-8') as f:
                self.content = f.read()
                self.hash = hashlib.md5(self.content.encode()).hexdigest()
            return self._parse_content()

        return None

    def _parse_content(self) -> Any:
        """Parse content based on resource type."""
        if self.type == "json":
            return json.loads(self.content)
        elif self.type == "python":
            # Return as-is, will be executed later
            return self.content
        elif self.type == "jinja2":
            return Template(self.content)
        return self.content


@dataclass
class SkillDependency:
    """Dependency definition for a skill."""
    skill_id: str                          # ID of required skill
    required: bool = True                  # Whether this is a hard dependency
    input_mapping: Dict[str, str] = field(default_factory=dict)  # Map outputs to inputs
    condition: Optional[str] = None        # Conditional dependency


class LivingSkill:
    """A living skill cell with lifecycle, temporal properties, and resources.

    This is the basic functional unit of the living knowledge system.
    Analogous to a biological cell, it can:
    - Grow and evolve (update resources)
    - Execute functions (when triggered)
    - Reproduce (create variations)
    - Die (expire and cleanup)
    """

    # Class-level registry
    _registry: Dict[str, Type["LivingSkill"]] = {}
    _instances: Dict[str, "LivingSkill"] = {}

    def __init__(
        self,
        skill_id: str,
        name: str,
        description: str,
        version: str = "1.0.0",
        temporal: Optional[SkillTemporal] = None,
        resources: Optional[List[SkillResource]] = None,
        dependencies: Optional[List[SkillDependency]] = None,
        provides: Optional[List[str]] = None,  # Data/events this skill provides
        triggers: Optional[List[str]] = None,  # Skills/events this skill triggers
        config: Optional[Dict[str, Any]] = None,
    ):
        # Identity
        self.skill_id = skill_id
        self.name = name
        self.description = description
        self.version = version

        # Temporal properties (when to run)
        self.temporal = temporal or SkillTemporal()

        # Resources (how to run)
        self.resources = resources or []
        self._loaded_resources: Dict[str, Any] = {}

        # Dependencies (what's needed)
        self.dependencies = dependencies or []
        self.provides = provides or []
        self.triggers = triggers or []

        # Configuration
        self.config = config or {}
        self._config_schema: Optional[Dict] = None

        # Lifecycle tracking
        self.lifecycle = SkillLifecycle()

        # Runtime state
        self._execution_context: Optional[Dict] = None
        self._current_task: Optional[asyncio.Task] = None

        # Register instance
        LivingSkill._instances[skill_id] = self

        logger.info(f"LivingSkill '{name}' ({skill_id}) created")

    @classmethod
    def register(cls, skill_class: Type["LivingSkill"]):
        """Register a skill class."""
        cls._registry[skill_class.__name__] = skill_class
        logger.info(f"Registered skill class: {skill_class.__name__}")

    @classmethod
    def get_instance(cls, skill_id: str) -> Optional["LivingSkill"]:
        """Get a skill instance by ID."""
        return cls._instances.get(skill_id)

    @classmethod
    def list_instances(cls, state: Optional[SkillState] = None) -> List["LivingSkill"]:
        """List all skill instances, optionally filtered by state."""
        skills = list(cls._instances.values())
        if state:
            skills = [s for s in skills if s.lifecycle.state == state]
        return skills

    def load_resources(self, base_path: Optional[str] = None):
        """Load all resources for this skill."""
        for resource in self.resources:
            try:
                self._loaded_resources[resource.name] = resource.load(base_path)
                logger.debug(f"Loaded resource: {resource.name}")
            except Exception as e:
                logger.error(f"Failed to load resource {resource.name}: {e}")
                raise

    def get_resource(self, name: str) -> Any:
        """Get a loaded resource by name."""
        if name not in self._loaded_resources:
            # Try to find and load it
            for resource in self.resources:
                if resource.name == name:
                    self._loaded_resources[name] = resource.load()
                    break
        return self._loaded_resources.get(name)

    def check_dependencies(self, available_skills: Set[str]) -> Tuple[bool, List[str]]:
        """Check if all dependencies are satisfied."""
        missing = []
        for dep in self.dependencies:
            if dep.required and dep.skill_id not in available_skills:
                missing.append(dep.skill_id)
        return len(missing) == 0, missing

    def is_ready(self) -> bool:
        """Check if skill is ready to execute."""
        # Check lifecycle state
        if self.lifecycle.state in [SkillState.DISABLED, SkillState.EXPIRED]:
            return False

        # Check temporal constraints
        if not self.temporal.is_due(self.lifecycle.last_run):
            return False

        return True

    async def invoke(self, context: Optional[Dict[str, Any]] = None) -> Any:
        """Invoke the skill execution."""
        if not self.is_ready():
            raise RuntimeError(f"Skill {self.skill_id} is not ready to execute")

        # Record start
        start_time = datetime.now()
        self.lifecycle.record_run_start()
        self._execution_context = context or {}

        try:
            # Execute main function
            result = await self._execute(context)

            # Record success
            duration = datetime.now() - start_time
            self.lifecycle.record_run_end(duration, success=True)

            # Schedule next run
            self.lifecycle.next_run = self.temporal.get_next_run(self.lifecycle.last_run)

            # Trigger follow-up skills
            await self._trigger_follow_ups(result)

            return result

        except Exception as e:
            # Record failure
            duration = datetime.now() - start_time
            self.lifecycle.record_run_end(duration, success=False, error=str(e))

            # Retry logic
            if self.lifecycle.fail_count < self.temporal.max_retries:
                logger.warning(f"Skill {self.skill_id} failed, will retry: {e}")
                await asyncio.sleep(self.temporal.retry_delay.total_seconds())
                return await self.invoke(context)

            raise

    async def _execute(self, context: Optional[Dict[str, Any]]) -> Any:
        """Execute the skill's main function. Override in subclasses."""
        # Load and execute Python resource if available
        for resource in self.resources:
            if resource.type == "python":
                return await self._execute_python_resource(resource, context)

        raise NotImplementedError(f"Skill {self.skill_id} has no execution method defined")

    async def _execute_python_resource(
        self,
        resource: SkillResource,
        context: Optional[Dict[str, Any]]
    ) -> Any:
        """Execute a Python script resource."""
        # Create temporary module
        module_name = f"skill_{self.skill_id}_{resource.name}"
        spec = importlib.util.spec_from_loader(module_name, loader=None)
        module = importlib.util.module_from_spec(spec)

        # Add skill context to module
        module.__dict__['skill'] = self
        module.__dict__['context'] = context or {}
        module.__dict__['config'] = self.config
        module.__dict__['resources'] = self._loaded_resources

        # Execute code
        exec(resource.content, module.__dict__)

        # Call entry point
        entry_func = module.__dict__.get(resource.entry_point)
        if entry_func is None:
            raise RuntimeError(f"Entry point '{resource.entry_point}' not found in {resource.name}")

        # Check if async
        if inspect.iscoroutinefunction(entry_func):
            return await entry_func()
        else:
            return entry_func()

    async def _trigger_follow_ups(self, result: Any):
        """Trigger skills that depend on this one."""
        for trigger_id in self.triggers:
            triggered_skill = LivingSkill.get_instance(trigger_id)
            if triggered_skill and triggered_skill.is_ready():
                logger.info(f"Triggering follow-up skill: {trigger_id}")
                # Fire and forget
                asyncio.create_task(triggered_skill.invoke({"triggered_by": self.skill_id, "result": result}))

    def pause(self):
        """Pause the skill execution."""
        if self.lifecycle.state == SkillState.RUNNING:
            self.lifecycle.transition_to(SkillState.PAUSED)
            if self._current_task:
                self._current_task.cancel()

    def resume(self):
        """Resume the skill execution."""
        if self.lifecycle.state == SkillState.PAUSED:
            self.lifecycle.transition_to(SkillState.IDLE)

    def disable(self):
        """Disable the skill."""
        self.lifecycle.transition_to(SkillState.DISABLED)

    def enable(self):
        """Enable the skill."""
        self.lifecycle.transition_to(SkillState.IDLE)

    def update_config(self, new_config: Dict[str, Any]):
        """Update skill configuration."""
        self.config.update(new_config)
        self.lifecycle.updated_at = datetime.now()
        logger.info(f"Updated config for skill {self.skill_id}")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize skill to dictionary."""
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "state": self.lifecycle.state.value,
            "temporal": {
                "cron": self.temporal.cron,
                "interval": self.temporal.interval.total_seconds() if self.temporal.interval else None,
                "timezone": self.temporal.timezone,
                "next_run": self.lifecycle.next_run.isoformat() if self.lifecycle.next_run else None,
            },
            "lifecycle": {
                "created_at": self.lifecycle.created_at.isoformat(),
                "last_run": self.lifecycle.last_run.isoformat() if self.lifecycle.last_run else None,
                "run_count": self.lifecycle.run_count,
                "success_count": self.lifecycle.success_count,
                "fail_count": self.lifecycle.fail_count,
            },
            "dependencies": [d.skill_id for d in self.dependencies],
            "provides": self.provides,
            "triggers": self.triggers,
        }

    def __repr__(self) -> str:
        return f"<LivingSkill {self.skill_id} ({self.lifecycle.state.value})>"
