"""Workflow domain models for orchestrating skills into pipelines.

This module provides database models for:
- WorkflowDefinition: Configuration for a multi-step workflow
- WorkflowExecution: Execution history for workflow runs
- WorkflowStepExecution: Execution history for individual steps
"""

from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from open_notebook.database.repository import repo_query
from open_notebook.domain.base import ObjectModel


class WorkflowStatus(str, Enum):
    """Execution status of a workflow."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"  # Some steps succeeded, some failed


class StepStatus(str, Enum):
    """Execution status of a workflow step."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"  # Skipped due to condition
    RETRYING = "retrying"


class WorkflowStepDefinition(BaseModel):
    """Definition of a single step in a workflow.

    Steps are stored as JSON within WorkflowDefinition.
    """
    step_id: str  # Unique identifier for this step
    skill_type: str  # Skill to execute (from SkillRegistry)
    name: Optional[str] = None  # Display name
    description: Optional[str] = None

    # Parameters for the skill (can reference outputs from previous steps)
    # Use template syntax: "{{steps.prev_step.output.source_id}}"
    parameters: Dict[str, Any] = Field(default_factory=dict)

    # Dependencies - which steps must complete before this one
    depends_on: List[str] = Field(default_factory=list)

    # Execution condition (Python expression evaluated at runtime)
    # Example: "steps.step1.status == 'success'"
    condition: Optional[str] = None

    # Retry configuration
    retry_on_fail: int = 0  # Number of retries
    retry_delay_seconds: int = 5  # Delay between retries

    # Continue on failure (don't fail the entire workflow)
    continue_on_fail: bool = False


class WorkflowDefinition(ObjectModel):
    """A configured workflow stored in the database.

    Workflows orchestrate multiple skills into a pipeline with
    dependencies, conditions, and retry logic.
    """

    table_name: ClassVar[str] = "workflow_definition"
    nullable_fields: ClassVar[set[str]] = {
        "description",
        "target_notebook_id",
        "schedule",
        "input_schema",
        "output_mapping",
        "created",
        "updated",
    }

    name: str
    description: Optional[str] = None
    enabled: bool = True

    # Steps in this workflow (ordered but dependencies determine execution order)
    steps: List[WorkflowStepDefinition] = Field(default_factory=list)

    # Input/output schema for validation and UI
    input_schema: Optional[Dict[str, Any]] = None  # Expected input parameters
    output_mapping: Optional[Dict[str, str]] = None  # Map outputs to result keys

    # Optional scheduling (cron expression)
    schedule: Optional[str] = None

    # Target notebook for this workflow
    target_notebook_id: Optional[str] = None

    # Metadata
    created: Optional[Union[str, datetime]] = None
    updated: Optional[Union[str, datetime]] = None

    @classmethod
    async def get_enabled(cls) -> List["WorkflowDefinition"]:
        """Get all enabled workflow definitions."""
        results = await repo_query(
            "SELECT * FROM workflow_definition WHERE enabled = true",
        )
        return [cls(**row) for row in results]

    @classmethod
    async def get_by_notebook(cls, notebook_id: str) -> List["WorkflowDefinition"]:
        """Get all workflows targeting a specific notebook."""
        results = await repo_query(
            "SELECT * FROM workflow_definition WHERE target_notebook_id = $notebook_id",
            {"notebook_id": notebook_id},
        )
        return [cls(**row) for row in results]

    def get_step(self, step_id: str) -> Optional[WorkflowStepDefinition]:
        """Get a step by its ID."""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None

    def get_root_steps(self) -> List[WorkflowStepDefinition]:
        """Get steps with no dependencies (can start immediately)."""
        return [step for step in self.steps if not step.depends_on]

    def get_dependent_steps(self, step_id: str) -> List[WorkflowStepDefinition]:
        """Get steps that depend on the given step."""
        return [step for step in self.steps if step_id in step.depends_on]


class WorkflowStepExecution(BaseModel):
    """Execution record for a single step within a workflow run.

    Stored as part of WorkflowExecution.output.steps
    """
    step_id: str
    skill_type: str
    status: StepStatus = StepStatus.PENDING

    # Timing
    started_at: Optional[Union[str, datetime]] = None
    completed_at: Optional[Union[str, datetime]] = None

    # Execution details
    attempt: int = 1  # Which retry attempt this is
    max_attempts: int = 1

    # Results
    output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    # Created resources
    created_source_ids: List[str] = Field(default_factory=list)
    created_note_ids: List[str] = Field(default_factory=list)

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate execution duration."""
        if not self.completed_at or not self.started_at:
            return None
        try:
            if isinstance(self.started_at, str):
                start = datetime.fromisoformat(self.started_at.replace("Z", "+00:00"))
            else:
                start = self.started_at
            if isinstance(self.completed_at, str):
                end = datetime.fromisoformat(self.completed_at.replace("Z", "+00:00"))
            else:
                end = self.completed_at
            return (end - start).total_seconds()
        except (ValueError, TypeError):
            return None


class WorkflowExecution(ObjectModel):
    """Execution history for a workflow run.

    Tracks the status, timing, and results of a workflow execution,
    including individual step results.
    """

    table_name: ClassVar[str] = "workflow_execution"
    nullable_fields: ClassVar[set[str]] = {
        "error_message",
        "output",
        "completed_at",
        "started_at",
        "input_data",
        "triggered_by",
    }

    # Link to workflow definition
    workflow_definition_id: str

    # Execution status
    status: WorkflowStatus = WorkflowStatus.PENDING

    # Trigger information
    trigger_type: str = "manual"  # manual, schedule, event, api
    triggered_by: Optional[str] = None  # user_id or system

    # Input data passed to the workflow
    input_data: Optional[Dict[str, Any]] = None

    # Timing
    started_at: Optional[Union[str, datetime]] = None
    completed_at: Optional[Union[str, datetime]] = None

    # Overall results
    output: Optional[Dict[str, Any]] = None  # Final aggregated output
    error_message: Optional[str] = None

    # Step executions (stored as list of dicts in DB)
    step_executions: List[WorkflowStepExecution] = Field(default_factory=list)

    # Created resources across all steps
    created_source_ids: List[str] = Field(default_factory=list)
    created_note_ids: List[str] = Field(default_factory=list)

    @classmethod
    async def get_by_workflow(cls, workflow_definition_id: str, limit: int = 50) -> List["WorkflowExecution"]:
        """Get execution history for a workflow."""
        results = await repo_query(
            """SELECT * FROM workflow_execution
            WHERE workflow_definition_id = $workflow_id
            ORDER BY started_at DESC LIMIT $limit""",
            {"workflow_id": workflow_definition_id, "limit": limit},
        )
        return [cls(**row) for row in results]

    @classmethod
    async def get_recent(cls, limit: int = 50) -> List["WorkflowExecution"]:
        """Get recent executions across all workflows."""
        results = await repo_query(
            "SELECT * FROM workflow_execution ORDER BY started_at DESC LIMIT $limit",
            {"limit": limit},
        )
        return [cls(**row) for row in results]

    @classmethod
    async def get_running(cls) -> List["WorkflowExecution"]:
        """Get currently running executions."""
        results = await repo_query(
            "SELECT * FROM workflow_execution WHERE status = 'running'",
        )
        return [cls(**row) for row in results]

    def get_step_execution(self, step_id: str) -> Optional[WorkflowStepExecution]:
        """Get execution record for a specific step."""
        for step_exec in self.step_executions:
            if step_exec.step_id == step_id:
                return step_exec
        return None

    def update_step_execution(self, step_execution: WorkflowStepExecution) -> None:
        """Update or add a step execution record."""
        for i, existing in enumerate(self.step_executions):
            if existing.step_id == step_execution.step_id:
                self.step_executions[i] = step_execution
                return
        self.step_executions.append(step_execution)

    def mark_completed(self, status: WorkflowStatus, output: Optional[Dict] = None, error: Optional[str] = None):
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
            if isinstance(self.started_at, str):
                start = datetime.fromisoformat(self.started_at.replace("Z", "+00:00"))
            else:
                start = self.started_at
            if isinstance(self.completed_at, str):
                end = datetime.fromisoformat(self.completed_at.replace("Z", "+00:00"))
            else:
                end = self.completed_at
            return (end - start).total_seconds()
        except (ValueError, TypeError):
            return None

    @property
    def success_rate(self) -> float:
        """Calculate success rate of steps."""
        if not self.step_executions:
            return 0.0
        successful = sum(
            1 for step in self.step_executions
            if step.status == StepStatus.SUCCESS
        )
        return successful / len(self.step_executions)
