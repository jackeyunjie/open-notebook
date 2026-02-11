"""Skill domain models for storing skill configurations and execution history.

This module provides database models for:
- SkillInstance: Configuration for a skill instance (schedule, parameters)
- SkillExecution: Execution history and logs
"""

from datetime import datetime
from typing import Any, ClassVar, Dict, List, Optional, Union

from pydantic import Field

from open_notebook.database.repository import repo_query, repo_upsert
from open_notebook.domain.base import ObjectModel


class SkillInstance(ObjectModel):
    """A configured skill instance stored in the database.
    
    Each instance represents a skill with specific configuration,
    scheduling, and target notebook.
    """
    
    table_name: ClassVar[str] = "skill_instance"
    nullable_fields: ClassVar[set[str]] = {
        "schedule",
        "target_notebook_id",
        "description",
        "created",
        "updated",
    }
    
    name: str
    skill_type: str  # e.g., "rss_crawler", "note_summarizer"
    description: Optional[str] = None
    enabled: bool = True
    
    # Configuration
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    # Scheduling (optional cron expression)
    schedule: Optional[str] = None  # e.g., "0 9 * * *" for daily at 9am
    
    # Target notebook for this skill
    target_notebook_id: Optional[str] = None
    
    # Metadata - can be string or datetime from DB
    created: Optional[Union[str, datetime]] = None
    updated: Optional[Union[str, datetime]] = None
    
    @classmethod
    async def get_by_skill_type(cls, skill_type: str) -> List["SkillInstance"]:
        """Get all skill instances of a specific type."""
        results = await repo_query(
            "SELECT * FROM skill_instance WHERE skill_type = $skill_type",
            {"skill_type": skill_type},
        )
        return [cls(**row) for row in results]
    
    @classmethod
    async def get_enabled(cls) -> List["SkillInstance"]:
        """Get all enabled skill instances."""
        results = await repo_query(
            "SELECT * FROM skill_instance WHERE enabled = true",
        )
        return [cls(**row) for row in results]
    
    @classmethod
    async def get_by_notebook(cls, notebook_id: str) -> List["SkillInstance"]:
        """Get all skill instances targeting a specific notebook."""
        results = await repo_query(
            "SELECT * FROM skill_instance WHERE target_notebook_id = $notebook_id",
            {"notebook_id": notebook_id},
        )
        return [cls(**row) for row in results]
    



class SkillExecution(ObjectModel):
    """Execution history for a skill instance.
    
    Each execution is logged with status, output, and timing information.
    """
    
    table_name: ClassVar[str] = "skill_execution"
    nullable_fields: ClassVar[set[str]] = {
        "error_message",
        "output",
        "completed_at",
        "started_at",
    }
    
    # Link to skill instance
    skill_instance_id: str
    
    # Execution status
    status: str = "pending"  # pending, running, success, failed, cancelled
    
    # Trigger information
    trigger_type: str = "manual"  # manual, schedule, event
    triggered_by: Optional[str] = None  # user_id or system
    
    # Timing - can be string or datetime from DB
    started_at: Optional[Union[str, datetime]] = None
    completed_at: Optional[Union[str, datetime]] = None
    
    # Results
    output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    # Created source/note IDs
    created_source_ids: List[str] = Field(default_factory=list)
    created_note_ids: List[str] = Field(default_factory=list)
    
    @classmethod
    async def get_by_skill_instance(cls, skill_instance_id: str, limit: int = 50) -> List["SkillExecution"]:
        """Get execution history for a skill instance."""
        results = await repo_query(
            "SELECT * FROM skill_execution WHERE skill_instance_id = $skill_instance_id ORDER BY started_at DESC LIMIT $limit",
            {"skill_instance_id": skill_instance_id, "limit": limit},
        )
        return [cls(**row) for row in results]
    
    @classmethod
    async def get_recent(cls, limit: int = 50) -> List["SkillExecution"]:
        """Get recent executions across all skills."""
        results = await repo_query(
            "SELECT * FROM skill_execution ORDER BY started_at DESC LIMIT $limit",
            {"limit": limit},
        )
        return [cls(**row) for row in results]
    
    @classmethod
    async def get_running(cls) -> List["SkillExecution"]:
        """Get currently running executions."""
        results = await repo_query(
            "SELECT * FROM skill_execution WHERE status = 'running'",
        )
        return [cls(**row) for row in results]
    
    def mark_completed(self, status: str, output: Optional[Dict] = None, error: Optional[str] = None):
        """Mark execution as completed."""
        self.status = status
        self.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if output:
            self.output = output
        if error:
            self.error_message = error
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate execution duration."""
        if not self.completed_at:
            return None
        try:
            start = datetime.strptime(self.started_at, "%Y-%m-%d %H:%M:%S")
            end = datetime.strptime(self.completed_at, "%Y-%m-%d %H:%M:%S")
            return (end - start).total_seconds()
        except (ValueError, TypeError):
            return None
