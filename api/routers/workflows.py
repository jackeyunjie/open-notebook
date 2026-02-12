"""API routes for Workflow management and execution.

Provides REST endpoints for:
- Managing workflow definitions (CRUD)
- Executing workflows
- Viewing execution history
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from open_notebook.domain.workflow import (
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowStatus,
)
from open_notebook.workflows.service import WorkflowService

router = APIRouter()
service = WorkflowService()


# =============================================================================
# Request/Response Models
# =============================================================================

class WorkflowStepCreate(BaseModel):
    """Step definition for workflow creation."""
    step_id: str
    skill_type: str
    name: Optional[str] = None
    description: Optional[str] = None
    parameters: Dict[str, Any] = {}
    depends_on: List[str] = []
    condition: Optional[str] = None
    retry_on_fail: int = 0
    retry_delay_seconds: int = 5
    continue_on_fail: bool = False


class WorkflowCreate(BaseModel):
    """Request to create a workflow."""
    name: str
    description: Optional[str] = None
    steps: List[WorkflowStepCreate] = []
    input_schema: Optional[Dict[str, Any]] = None
    output_mapping: Optional[Dict[str, Any]] = None
    target_notebook_id: Optional[str] = None
    schedule: Optional[str] = None
    enabled: bool = True


class WorkflowUpdate(BaseModel):
    """Request to update a workflow."""
    name: Optional[str] = None
    description: Optional[str] = None
    steps: Optional[List[WorkflowStepCreate]] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_mapping: Optional[Dict[str, Any]] = None
    target_notebook_id: Optional[str] = None
    schedule: Optional[str] = None
    enabled: Optional[bool] = None


class WorkflowResponse(BaseModel):
    """Workflow definition response."""
    model_config = {"arbitrary_types_allowed": True}

    id: str
    name: str
    description: Optional[str]
    enabled: bool
    steps: List[Dict[str, Any]]
    input_schema: Optional[Dict[str, Any]]
    output_mapping: Optional[Dict[str, Any]]
    schedule: Optional[str]
    target_notebook_id: Optional[str]
    created: Any = None
    updated: Any = None


class WorkflowStepExecutionResponse(BaseModel):
    """Step execution response."""
    step_id: str
    skill_type: str
    status: str
    started_at: Optional[Any] = None
    completed_at: Optional[Any] = None
    attempt: int = 1
    max_attempts: int = 1
    output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_source_ids: List[str] = []
    created_note_ids: List[str] = []
    duration_seconds: Optional[float] = None


class WorkflowExecutionResponse(BaseModel):
    """Workflow execution response."""
    model_config = {"arbitrary_types_allowed": True}

    id: str
    workflow_definition_id: str
    status: str
    trigger_type: str
    triggered_by: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    started_at: Optional[Any] = None
    completed_at: Optional[Any] = None
    output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    step_executions: List[WorkflowStepExecutionResponse] = []
    created_source_ids: List[str] = []
    created_note_ids: List[str] = []
    duration_seconds: Optional[float] = None
    success_rate: float = 0.0


class ExecuteWorkflowRequest(BaseModel):
    """Request to execute a workflow."""
    input_data: Optional[Dict[str, Any]] = None


class ExecuteWorkflowResponse(BaseModel):
    """Workflow execution result."""
    execution_id: str
    status: str
    message: str


class WorkflowStatsResponse(BaseModel):
    """Workflow execution statistics."""
    total: int
    by_status: Dict[str, int]
    avg_duration: float
    success_rate: float


# =============================================================================
# Workflow Definitions
# =============================================================================

def _workflow_to_response(workflow: WorkflowDefinition) -> WorkflowResponse:
    """Convert WorkflowDefinition to response model."""
    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        description=workflow.description,
        enabled=workflow.enabled,
        steps=[step.model_dump() for step in workflow.steps],
        input_schema=workflow.input_schema,
        output_mapping=workflow.output_mapping,
        schedule=workflow.schedule,
        target_notebook_id=workflow.target_notebook_id,
        created=workflow.created,
        updated=workflow.updated,
    )


def _execution_to_response(execution: WorkflowExecution) -> WorkflowExecutionResponse:
    """Convert WorkflowExecution to response model."""
    return WorkflowExecutionResponse(
        id=execution.id,
        workflow_definition_id=execution.workflow_definition_id,
        status=execution.status.value,
        trigger_type=execution.trigger_type,
        triggered_by=execution.triggered_by,
        input_data=execution.input_data,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        output=execution.output,
        error_message=execution.error_message,
        step_executions=[
            WorkflowStepExecutionResponse(
                step_id=step.step_id,
                skill_type=step.skill_type,
                status=step.status.value,
                started_at=step.started_at,
                completed_at=step.completed_at,
                attempt=step.attempt,
                max_attempts=step.max_attempts,
                output=step.output,
                error_message=step.error_message,
                created_source_ids=step.created_source_ids,
                created_note_ids=step.created_note_ids,
                duration_seconds=step.duration_seconds,
            )
            for step in execution.step_executions
        ],
        created_source_ids=execution.created_source_ids,
        created_note_ids=execution.created_note_ids,
        duration_seconds=execution.duration_seconds,
        success_rate=execution.success_rate,
    )


@router.get("/workflows", response_model=List[WorkflowResponse])
async def list_workflows(
    notebook_id: Optional[str] = None,
    enabled_only: bool = False,
):
    """List workflow definitions with optional filtering."""
    workflows = await service.list_workflows(
        notebook_id=notebook_id,
        enabled_only=enabled_only,
    )
    return [_workflow_to_response(w) for w in workflows]


@router.post("/workflows", response_model=WorkflowResponse)
async def create_workflow(request: WorkflowCreate):
    """Create a new workflow definition."""
    workflow = await service.create_workflow(
        name=request.name,
        description=request.description,
        steps=[step.model_dump() for step in request.steps],
        input_schema=request.input_schema,
        output_mapping=request.output_mapping,
        target_notebook_id=request.target_notebook_id,
        schedule=request.schedule,
        enabled=request.enabled,
    )
    return _workflow_to_response(workflow)


@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str):
    """Get a specific workflow definition."""
    workflow = await service.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return _workflow_to_response(workflow)


@router.patch("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(workflow_id: str, request: WorkflowUpdate):
    """Update a workflow definition."""
    updates = request.model_dump(exclude_unset=True)
    if "steps" in updates and updates["steps"] is not None:
        updates["steps"] = [step.model_dump() for step in updates["steps"]]

    workflow = await service.update_workflow(workflow_id, **updates)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return _workflow_to_response(workflow)


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a workflow definition."""
    success = await service.delete_workflow(workflow_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"message": "Workflow deleted"}


@router.post("/workflows/{workflow_id}/duplicate", response_model=WorkflowResponse)
async def duplicate_workflow(workflow_id: str):
    """Duplicate a workflow definition."""
    workflow = await service.duplicate_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return _workflow_to_response(workflow)


# =============================================================================
# Workflow Execution
# =============================================================================

@router.post("/workflows/{workflow_id}/execute", response_model=ExecuteWorkflowResponse)
async def execute_workflow(
    workflow_id: str,
    request: ExecuteWorkflowRequest,
    trigger_type: str = "manual",
    triggered_by: Optional[str] = None,
):
    """Execute a workflow."""
    execution = await service.execute_workflow(
        workflow_id=workflow_id,
        input_data=request.input_data,
        trigger_type=trigger_type,
        triggered_by=triggered_by,
    )
    if not execution:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return ExecuteWorkflowResponse(
        execution_id=execution.id,
        status=execution.status.value,
        message="Workflow executed" if execution.status != WorkflowStatus.FAILED else execution.error_message or "Execution failed",
    )


@router.get("/workflows/executions", response_model=List[WorkflowExecutionResponse])
async def list_executions(
    workflow_id: Optional[str] = None,
    limit: int = 50,
    status: Optional[str] = None,
):
    """List workflow executions with optional filtering."""
    workflow_status = WorkflowStatus(status) if status else None
    executions = await service.list_executions(
        workflow_id=workflow_id,
        limit=limit,
        status=workflow_status,
    )
    return [_execution_to_response(e) for e in executions]


@router.get("/workflows/executions/{execution_id}", response_model=WorkflowExecutionResponse)
async def get_execution(execution_id: str):
    """Get a specific workflow execution."""
    execution = await service.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return _execution_to_response(execution)


@router.post("/workflows/executions/{execution_id}/cancel")
async def cancel_execution(execution_id: str):
    """Cancel a running workflow execution."""
    success = await service.cancel_execution(execution_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Execution not found or already completed"
        )
    return {"message": "Execution cancelled"}


# =============================================================================
# Workflow Statistics
# =============================================================================

@router.get("/workflows/{workflow_id}/stats", response_model=WorkflowStatsResponse)
async def get_workflow_stats(workflow_id: str):
    """Get execution statistics for a workflow."""
    stats = await service.get_execution_stats(workflow_id)
    return WorkflowStatsResponse(**stats)


@router.get("/workflows/stats/overview", response_model=WorkflowStatsResponse)
async def get_overall_stats():
    """Get execution statistics across all workflows."""
    stats = await service.get_execution_stats()
    return WorkflowStatsResponse(**stats)


# =============================================================================
# Workflow Scheduling
# =============================================================================

class WorkflowScheduleResponse(BaseModel):
    """Workflow schedule response."""
    workflow_id: str
    schedule: Optional[str]
    next_run_time: Optional[str] = None
    enabled: bool


class UpdateWorkflowScheduleRequest(BaseModel):
    """Request to update workflow schedule."""
    schedule: Optional[str] = None  # Cron expression or None to remove


@router.get("/workflows/{workflow_id}/schedule", response_model=WorkflowScheduleResponse)
async def get_workflow_schedule(workflow_id: str):
    """Get schedule information for a workflow."""
    workflow = await service.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    from open_notebook.skills.scheduler import skill_scheduler
    next_run = await skill_scheduler.get_workflow_next_run_time(workflow_id)

    return WorkflowScheduleResponse(
        workflow_id=workflow_id,
        schedule=workflow.schedule,
        next_run_time=next_run.isoformat() if next_run else None,
        enabled=workflow.enabled,
    )


@router.patch("/workflows/{workflow_id}/schedule")
async def update_workflow_schedule(
    workflow_id: str,
    request: UpdateWorkflowScheduleRequest,
):
    """Update workflow schedule (set or remove cron expression)."""
    workflow = await service.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    from open_notebook.skills.scheduler import skill_scheduler

    old_schedule = workflow.schedule
    new_schedule = request.schedule

    # Update workflow
    workflow.schedule = new_schedule
    await workflow.save()

    # Update scheduler
    if new_schedule and workflow.enabled:
        # Schedule or reschedule
        success = await skill_scheduler.schedule_workflow(workflow_id, new_schedule)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to schedule workflow")
    else:
        # Unschedule if disabled or schedule removed
        await skill_scheduler.unschedule_workflow(workflow_id)

    # Get next run time
    next_run = await skill_scheduler.get_workflow_next_run_time(workflow_id)

    return {
        "message": "Schedule updated",
        "workflow_id": workflow_id,
        "schedule": new_schedule,
        "next_run_time": next_run.isoformat() if next_run else None,
    }


@router.post("/workflows/{workflow_id}/enable")
async def enable_workflow(workflow_id: str):
    """Enable a workflow and its schedule."""
    workflow = await service.update_workflow(workflow_id, enabled=True)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Schedule if has schedule
    if workflow.schedule:
        from open_notebook.skills.scheduler import skill_scheduler
        await skill_scheduler.schedule_workflow(workflow_id, workflow.schedule)

    return {"message": "Workflow enabled", "workflow_id": workflow_id}


@router.post("/workflows/{workflow_id}/disable")
async def disable_workflow(workflow_id: str):
    """Disable a workflow and remove its schedule."""
    workflow = await service.update_workflow(workflow_id, enabled=False)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Remove from scheduler
    from open_notebook.skills.scheduler import skill_scheduler
    await skill_scheduler.unschedule_workflow(workflow_id)

    return {"message": "Workflow disabled", "workflow_id": workflow_id}
