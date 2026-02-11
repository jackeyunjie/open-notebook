"""API routes for Skill management and execution.

Provides REST endpoints for:
- Listing available skills
- Managing skill instances (CRUD)
- Executing skills
- Viewing execution history
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from open_notebook.domain.skill import SkillExecution, SkillInstance
from open_notebook.skills.base import SkillConfig
from open_notebook.skills.registry import SkillRegistry
from open_notebook.skills.runner import get_skill_runner

router = APIRouter()


# =============================================================================
# Response Models
# =============================================================================

class SkillInfo(BaseModel):
    """Skill metadata."""
    skill_type: str
    name: str
    description: str


class SkillInstanceCreate(BaseModel):
    """Request to create a skill instance."""
    name: str
    skill_type: str
    description: Optional[str] = None
    enabled: bool = True
    parameters: Dict[str, Any] = {}
    schedule: Optional[str] = None
    target_notebook_id: Optional[str] = None


class SkillInstanceUpdate(BaseModel):
    """Request to update a skill instance."""
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    parameters: Optional[Dict[str, Any]] = None
    schedule: Optional[str] = None
    target_notebook_id: Optional[str] = None


class SkillInstanceResponse(BaseModel):
    """Skill instance response."""
    model_config = {"arbitrary_types_allowed": True}
    
    id: str
    name: str
    skill_type: str
    description: Optional[str]
    enabled: bool
    parameters: Dict[str, Any]
    schedule: Optional[str]
    target_notebook_id: Optional[str]
    created: Any = None
    updated: Any = None


class SkillExecutionResponse(BaseModel):
    """Skill execution response."""
    model_config = {"arbitrary_types_allowed": True}
    
    id: str
    skill_instance_id: str
    status: str
    trigger_type: str
    triggered_by: Optional[str] = None
    started_at: Any = None
    completed_at: Any = None
    output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_source_ids: List[str] = []
    created_note_ids: List[str] = []
    duration_seconds: Optional[float] = None


class ExecuteSkillRequest(BaseModel):
    """Request to execute a skill."""
    parameters: Optional[Dict[str, Any]] = {}
    trigger_type: str = "manual"


class ExecuteSkillDirectRequest(BaseModel):
    """Request to execute a skill directly without instance."""
    skill_type: str
    name: str = "Ad-hoc Execution"
    description: str = ""
    parameters: Dict[str, Any] = {}


class ExecuteSkillResponse(BaseModel):
    """Skill execution result."""
    execution_id: str
    status: str
    message: str


# =============================================================================
# Available Skills
# =============================================================================

@router.get("/skills/available", response_model=List[SkillInfo])
async def list_available_skills():
    """List all available skill types that can be instantiated."""
    skills = SkillRegistry.list_skills()
    return [
        SkillInfo(
            skill_type=s["skill_type"],
            name=s["name"],
            description=s["description"],
        )
        for s in skills
    ]


# =============================================================================
# Skill Instances
# =============================================================================

@router.get("/skills/instances", response_model=List[SkillInstanceResponse])
async def list_skill_instances(
    skill_type: Optional[str] = None,
    notebook_id: Optional[str] = None,
):
    """List skill instances with optional filtering."""
    if skill_type:
        instances = await SkillInstance.get_by_skill_type(skill_type)
    elif notebook_id:
        instances = await SkillInstance.get_by_notebook(notebook_id)
    else:
        instances = await SkillInstance.get_all()
    
    return [
        SkillInstanceResponse(
            id=inst.id,
            name=inst.name,
            skill_type=inst.skill_type,
            description=inst.description,
            enabled=inst.enabled,
            parameters=inst.parameters,
            schedule=inst.schedule,
            target_notebook_id=inst.target_notebook_id,
            created=inst.created,
            updated=inst.updated,
        )
        for inst in instances
    ]


@router.post("/skills/instances", response_model=SkillInstanceResponse)
async def create_skill_instance(request: SkillInstanceCreate):
    """Create a new skill instance."""
    # Validate skill type
    if not SkillRegistry.is_registered(request.skill_type):
        raise HTTPException(
            status_code=400,
            detail=f"Unknown skill type: {request.skill_type}. "
                   f"Available: {[s['skill_type'] for s in SkillRegistry.list_skills()]}"
        )
    
    instance = SkillInstance(
        name=request.name,
        skill_type=request.skill_type,
        description=request.description,
        enabled=request.enabled,
        parameters=request.parameters,
        schedule=request.schedule,
        target_notebook_id=request.target_notebook_id,
    )
    await instance.save()
    
    return SkillInstanceResponse(
        id=instance.id,
        name=instance.name,
        skill_type=instance.skill_type,
        description=instance.description,
        enabled=instance.enabled,
        parameters=instance.parameters,
        schedule=instance.schedule,
        target_notebook_id=instance.target_notebook_id,
        created=instance.created,
        updated=instance.updated,
    )


@router.get("/skills/instances/{instance_id}", response_model=SkillInstanceResponse)
async def get_skill_instance(instance_id: str):
    """Get a specific skill instance."""
    try:
        instance = await SkillInstance.get(instance_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Skill instance not found")
    
    return SkillInstanceResponse(
        id=instance.id,
        name=instance.name,
        skill_type=instance.skill_type,
        description=instance.description,
        enabled=instance.enabled,
        parameters=instance.parameters,
        schedule=instance.schedule,
        target_notebook_id=instance.target_notebook_id,
        created=instance.created,
        updated=instance.updated,
    )


@router.patch("/skills/instances/{instance_id}", response_model=SkillInstanceResponse)
async def update_skill_instance(instance_id: str, request: SkillInstanceUpdate):
    """Update a skill instance."""
    try:
        instance = await SkillInstance.get(instance_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Skill instance not found")
    
    # Update fields
    if request.name is not None:
        instance.name = request.name
    if request.description is not None:
        instance.description = request.description
    if request.enabled is not None:
        instance.enabled = request.enabled
    if request.parameters is not None:
        instance.parameters = request.parameters
    if request.schedule is not None:
        instance.schedule = request.schedule
    if request.target_notebook_id is not None:
        instance.target_notebook_id = request.target_notebook_id
    
    await instance.save()
    
    return SkillInstanceResponse(
        id=instance.id,
        name=instance.name,
        skill_type=instance.skill_type,
        description=instance.description,
        enabled=instance.enabled,
        parameters=instance.parameters,
        schedule=instance.schedule,
        target_notebook_id=instance.target_notebook_id,
        created=instance.created,
        updated=instance.updated,
    )


@router.delete("/skills/instances/{instance_id}")
async def delete_skill_instance(instance_id: str):
    """Delete a skill instance."""
    try:
        instance = await SkillInstance.get(instance_id)
        await instance.delete()
        return {"message": "Skill instance deleted"}
    except Exception:
        raise HTTPException(status_code=404, detail="Skill instance not found")


# =============================================================================
# Skill Execution
# =============================================================================

@router.post("/skills/instances/{instance_id}/execute", response_model=ExecuteSkillResponse)
async def execute_skill_instance(
    instance_id: str,
    request: ExecuteSkillRequest,
):
    """Execute a skill instance."""
    # Verify instance exists
    try:
        instance = await SkillInstance.get(instance_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Skill instance not found")
    
    if not instance.enabled:
        raise HTTPException(status_code=400, detail="Skill instance is disabled")
    
    # Execute
    runner = get_skill_runner()
    result = await runner.run_by_instance(
        instance_id=instance_id,
        trigger_type=request.trigger_type,
        extra_parameters=request.parameters,
    )
    
    # Get execution ID from result
    execution = await SkillExecution.get_recent(limit=1)
    execution_id = execution[0].id if execution else "unknown"
    
    return ExecuteSkillResponse(
        execution_id=execution_id,
        status=result.status.value,
        message=result.error_message or "Skill executed successfully",
    )


@router.post("/skills/execute", response_model=ExecuteSkillResponse)
async def execute_skill_direct(request: ExecuteSkillDirectRequest):
    """Execute a skill directly without creating an instance."""
    # Validate skill type
    if not SkillRegistry.is_registered(request.skill_type):
        raise HTTPException(
            status_code=400,
            detail=f"Unknown skill type: {request.skill_type}"
        )
    
    runner = get_skill_runner()
    result = await runner.run_skill(
        skill_type=request.skill_type,
        parameters=request.parameters,
        name=request.name,
        description=request.description,
    )
    
    return ExecuteSkillResponse(
        execution_id=result.skill_id,
        status=result.status.value,
        message=result.error_message or "Skill executed successfully",
    )


# =============================================================================
# Execution History
# =============================================================================

@router.get("/skills/executions", response_model=List[SkillExecutionResponse])
async def list_executions(
    instance_id: Optional[str] = None,
    limit: int = 50,
):
    """List skill executions with optional filtering."""
    if instance_id:
        executions = await SkillExecution.get_by_skill_instance(instance_id, limit)
    else:
        executions = await SkillExecution.get_recent(limit)
    
    return [
        SkillExecutionResponse(
            id=exec.id,
            skill_instance_id=exec.skill_instance_id,
            status=exec.status,
            trigger_type=exec.trigger_type,
            triggered_by=exec.triggered_by,
            started_at=exec.started_at,
            completed_at=exec.completed_at,
            output=exec.output,
            error_message=exec.error_message,
            created_source_ids=exec.created_source_ids,
            created_note_ids=exec.created_note_ids,
            duration_seconds=exec.duration_seconds,
        )
        for exec in executions
    ]


@router.get("/skills/executions/{execution_id}", response_model=SkillExecutionResponse)
async def get_execution(execution_id: str):
    """Get a specific execution."""
    try:
        execution = await SkillExecution.get(execution_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return SkillExecutionResponse(
        id=execution.id,
        skill_instance_id=execution.skill_instance_id,
        status=execution.status,
        trigger_type=execution.trigger_type,
        triggered_by=execution.triggered_by,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        output=execution.output,
        error_message=execution.error_message,
        created_source_ids=execution.created_source_ids,
        created_note_ids=execution.created_note_ids,
        duration_seconds=execution.duration_seconds,
    )


@router.post("/skills/executions/{execution_id}/cancel")
async def cancel_execution(execution_id: str):
    """Cancel a running skill execution."""
    runner = get_skill_runner()
    success = await runner.cancel_execution(execution_id)
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Execution not found or already completed"
        )
    
    return {"message": "Execution cancelled"}
