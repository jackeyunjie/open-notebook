"""WorkflowService for high-level workflow operations.

Provides a service layer for:
- Creating and managing workflow definitions
- Executing workflows
- Querying execution history
- Managing scheduled workflows
"""

from typing import Any, Dict, List, Optional

from loguru import logger

from open_notebook.domain.workflow import (
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowStatus,
)
from open_notebook.workflows.engine import WorkflowEngine


class WorkflowService:
    """Service for workflow operations.

    This is the main interface for working with workflows.
    It coordinates between the engine, domain models, and external systems.
    """

    def __init__(self):
        self.engine = WorkflowEngine()

    async def create_workflow(
        self,
        name: str,
        description: Optional[str] = None,
        steps: Optional[List[Dict[str, Any]]] = None,
        input_schema: Optional[Dict[str, Any]] = None,
        output_mapping: Optional[Dict[str, Any]] = None,
        target_notebook_id: Optional[str] = None,
        schedule: Optional[str] = None,
        enabled: bool = True,
    ) -> WorkflowDefinition:
        """Create a new workflow definition."""
        from open_notebook.domain.workflow import WorkflowStepDefinition

        workflow = WorkflowDefinition(
            name=name,
            description=description,
            steps=[WorkflowStepDefinition(**step) for step in (steps or [])],
            input_schema=input_schema,
            output_mapping=output_mapping,
            target_notebook_id=target_notebook_id,
            schedule=schedule,
            enabled=enabled,
        )
        await workflow.save()
        logger.info(f"Created workflow: {workflow.name} (id: {workflow.id})")
        return workflow

    async def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get a workflow definition by ID."""
        try:
            return await WorkflowDefinition.get(workflow_id)
        except Exception as e:
            logger.error(f"Failed to get workflow {workflow_id}: {e}")
            return None

    async def list_workflows(
        self,
        notebook_id: Optional[str] = None,
        enabled_only: bool = False,
    ) -> List[WorkflowDefinition]:
        """List workflow definitions."""
        if notebook_id:
            return await WorkflowDefinition.get_by_notebook(notebook_id)
        elif enabled_only:
            return await WorkflowDefinition.get_enabled()
        else:
            return await WorkflowDefinition.get_all()

    async def update_workflow(
        self,
        workflow_id: str,
        **updates: Any,
    ) -> Optional[WorkflowDefinition]:
        """Update a workflow definition."""
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return None

        if "steps" in updates:
            from open_notebook.domain.workflow import WorkflowStepDefinition
            updates["steps"] = [
                WorkflowStepDefinition(**step) if isinstance(step, dict) else step
                for step in updates["steps"]
            ]

        for key, value in updates.items():
            if hasattr(workflow, key):
                setattr(workflow, key, value)

        await workflow.save()
        logger.info(f"Updated workflow: {workflow.name} (id: {workflow.id})")
        return workflow

    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow definition."""
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return False

        await workflow.delete()
        logger.info(f"Deleted workflow: {workflow_id}")
        return True

    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Optional[Dict[str, Any]] = None,
        trigger_type: str = "manual",
        triggered_by: Optional[str] = None,
    ) -> Optional[WorkflowExecution]:
        """Execute a workflow."""
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            logger.error(f"Workflow not found: {workflow_id}")
            return None

        logger.info(f"Executing workflow: {workflow.name} (id: {workflow_id})")

        execution = await self.engine.execute(
            workflow=workflow,
            input_data=input_data,
            trigger_type=trigger_type,
            triggered_by=triggered_by,
        )

        logger.info(
            f"Workflow execution completed: {execution.id} "
            f"status={execution.status.value}"
        )
        return execution

    async def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get a workflow execution by ID."""
        try:
            return await WorkflowExecution.get(execution_id)
        except Exception as e:
            logger.error(f"Failed to get execution {execution_id}: {e}")
            return None

    async def list_executions(
        self,
        workflow_id: Optional[str] = None,
        limit: int = 50,
        status: Optional[WorkflowStatus] = None,
    ) -> List[WorkflowExecution]:
        """List workflow executions."""
        if workflow_id:
            executions = await WorkflowExecution.get_by_workflow(workflow_id, limit)
        else:
            executions = await WorkflowExecution.get_recent(limit)

        if status:
            executions = [e for e in executions if e.status == status]

        return executions

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running workflow execution."""
        return await self.engine.cancel(execution_id)

    async def duplicate_workflow(
        self,
        workflow_id: str,
        new_name: Optional[str] = None,
    ) -> Optional[WorkflowDefinition]:
        """Duplicate a workflow definition."""
        original = await self.get_workflow(workflow_id)
        if not original:
            return None

        from open_notebook.domain.workflow import WorkflowStepDefinition

        workflow = WorkflowDefinition(
            name=new_name or f"{original.name} Copy",
            description=original.description,
            steps=[
                WorkflowStepDefinition(**step.model_dump())
                for step in original.steps
            ],
            input_schema=original.input_schema,
            output_mapping=original.output_mapping,
            target_notebook_id=original.target_notebook_id,
            schedule=None,
            enabled=False,
        )
        await workflow.save()

        logger.info(f"Duplicated workflow {workflow_id} to {workflow.id}")
        return workflow

    async def get_execution_stats(
        self,
        workflow_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get execution statistics."""
        executions = await self.list_executions(workflow_id, limit=1000)

        if not executions:
            return {
                "total": 0,
                "by_status": {},
                "avg_duration": 0,
                "success_rate": 0,
            }

        by_status: Dict[str, int] = {}
        total_duration = 0
        duration_count = 0
        successful = 0

        for exec in executions:
            status = exec.status.value
            by_status[status] = by_status.get(status, 0) + 1

            if exec.duration_seconds:
                total_duration += exec.duration_seconds
                duration_count += 1

            if exec.status == WorkflowStatus.SUCCESS:
                successful += 1

        return {
            "total": len(executions),
            "by_status": by_status,
            "avg_duration": total_duration / duration_count if duration_count > 0 else 0,
            "success_rate": successful / len(executions),
        }
