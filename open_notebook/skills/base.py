"""Base classes for the Skill system.

Skills are reusable automation units that can be triggered manually,
by schedule, or by events. They integrate with Open Notebook's
existing LangChain infrastructure.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class SkillStatus(str, Enum):
    """Execution status of a skill."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SkillContext:
    """Context passed to skill execution.
    
    Contains runtime information and dependencies needed by skills.
    """
    skill_id: str
    trigger_type: str  # "manual", "schedule", "event"
    triggered_at: datetime = field(default_factory=datetime.utcnow)
    notebook_id: Optional[str] = None
    source_id: Optional[str] = None
    user_id: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def get_param(self, key: str, default: Any = None) -> Any:
        """Get a parameter value with default."""
        return self.parameters.get(key, default)


@dataclass
class SkillResult:
    """Result of skill execution."""
    skill_id: str
    status: SkillStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    output: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    created_source_ids: List[str] = field(default_factory=list)
    created_note_ids: List[str] = field(default_factory=list)
    
    @property
    def duration_seconds(self) -> float:
        """Calculate execution duration."""
        end = self.completed_at or datetime.utcnow()
        return (end - self.started_at).total_seconds()
    
    @property
    def success(self) -> bool:
        """Check if execution was successful."""
        return self.status == SkillStatus.SUCCESS


class SkillConfig(BaseModel):
    """Configuration for a skill instance.
    
    Stored in database and editable via UI.
    """
    skill_type: str
    name: str
    description: str
    enabled: bool = True
    schedule: Optional[str] = None  # Cron expression
    parameters: Dict[str, Any] = field(default_factory=dict)
    target_notebook_id: Optional[str] = None


class Skill(ABC):
    """Base class for all skills.
    
    Skills are automation units that perform specific tasks like:
    - Content crawling (RSS, websites)
    - Note organization (summarization, tagging)
    - Podcast generation
    
    To create a new skill:
    1. Inherit from Skill
    2. Implement skill_type, name, description properties
    3. Implement execute() method
    4. Register with SkillRegistry
    """
    
    # Override these in subclasses
    skill_type: str = "base"
    name: str = "Base Skill"
    description: str = "Base skill class - do not use directly"
    
    # Parameter schema for UI configuration
    parameters_schema: Dict[str, Any] = {}
    
    def __init__(self, config: SkillConfig):
        """Initialize skill with configuration.
        
        Args:
            config: Skill configuration from database
        """
        self.config = config
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate configuration. Override for custom validation."""
        if self.config.skill_type != self.skill_type:
            raise ValueError(
                f"Config skill_type '{self.config.skill_type}' "
                f"doesn't match class skill_type '{self.skill_type}'"
            )
    
    @abstractmethod
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute the skill.
        
        This is the main entry point for skill logic.
        Must be implemented by all concrete skills.
        
        Args:
            context: Execution context with parameters and metadata
            
        Returns:
            SkillResult with execution status and output
        """
        raise NotImplementedError("Skills must implement execute()")
    
    async def before_execute(self, context: SkillContext) -> None:
        """Hook called before execute(). Override for setup."""
        pass
    
    async def after_execute(self, context: SkillContext, result: SkillResult) -> None:
        """Hook called after execute(). Override for cleanup."""
        pass
    
    async def run(self, context: SkillContext) -> SkillResult:
        """Run the skill with lifecycle hooks.
        
        This method handles the full execution lifecycle:
        before_execute -> execute -> after_execute
        
        Args:
            context: Execution context
            
        Returns:
            SkillResult with execution details
        """
        started_at = datetime.utcnow()
        
        try:
            await self.before_execute(context)
            
            result = await self.execute(context)
            result.started_at = started_at
            result.completed_at = datetime.utcnow()
            
            await self.after_execute(context, result)
            
            return result
            
        except Exception as e:
            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.utcnow(),
                error_message=str(e)
            )
    
    def get_param(self, key: str, default: Any = None) -> Any:
        """Get a parameter from config."""
        return self.config.parameters.get(key, default)
