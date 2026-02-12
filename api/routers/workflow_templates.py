"""API routes for Workflow Templates.

Provides endpoints for browsing and instantiating pre-built workflow templates.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from open_notebook.workflows.service import WorkflowService
from open_notebook.workflows.templates import TemplateRegistry, WorkflowTemplate

router = APIRouter()
service = WorkflowService()


# =============================================================================
# Response Models
# =============================================================================

class WorkflowTemplateStep(BaseModel):
    """Template step response."""
    step_id: str
    skill_type: str
    name: Optional[str] = None
    description: Optional[str] = None
    depends_on: List[str] = []


class WorkflowTemplateResponse(BaseModel):
    """Workflow template response."""
    template_id: str
    name: str
    description: str
    category: str
    steps: List[WorkflowTemplateStep]
    input_schema: Dict[str, Any]


class WorkflowTemplateListResponse(BaseModel):
    """List of templates with categories."""
    categories: List[str]
    templates: List[WorkflowTemplateResponse]


class InstantiateTemplateRequest(BaseModel):
    """Request to instantiate a template."""
    name: Optional[str] = None
    target_notebook_id: Optional[str] = None
    schedule: Optional[str] = None
    enabled: bool = False
    parameters: Dict[str, Any] = {}


class InstantiateTemplateResponse(BaseModel):
    """Response from template instantiation."""
    workflow_id: str
    message: str


# =============================================================================
# Template Browsing
# =============================================================================

def _template_to_response(template: WorkflowTemplate) -> WorkflowTemplateResponse:
    """Convert template to response model."""
    return WorkflowTemplateResponse(
        template_id=template.template_id,
        name=template.name,
        description=template.description,
        category=template.category,
        steps=[
            WorkflowTemplateStep(
                step_id=step["step_id"],
                skill_type=step["skill_type"],
                name=step.get("name"),
                description=step.get("description"),
                depends_on=step.get("depends_on", []),
            )
            for step in template.steps
        ],
        input_schema=template.input_schema,
    )


@router.get("/workflow-templates", response_model=WorkflowTemplateListResponse)
async def list_templates(category: Optional[str] = None):
    """List available workflow templates."""
    if category:
        templates = TemplateRegistry.list_by_category(category)
    else:
        templates = TemplateRegistry.list_all()

    return WorkflowTemplateListResponse(
        categories=TemplateRegistry.get_categories(),
        templates=[_template_to_response(t) for t in templates],
    )


@router.get("/workflow-templates/{template_id}", response_model=WorkflowTemplateResponse)
async def get_template(template_id: str):
    """Get a specific workflow template."""
    template = TemplateRegistry.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return _template_to_response(template)


@router.get("/workflow-templates/categories", response_model=List[str])
async def get_template_categories():
    """Get all template categories."""
    return TemplateRegistry.get_categories()


# =============================================================================
# Template Instantiation
# =============================================================================

@router.post("/workflow-templates/{template_id}/instantiate", response_model=InstantiateTemplateResponse)
async def instantiate_template(template_id: str, request: InstantiateTemplateRequest):
    """Create a workflow from a template."""
    template = TemplateRegistry.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Generate workflow data from template
    workflow_data = template.to_workflow_data(
        name=request.name or template.name,
        target_notebook_id=request.target_notebook_id,
        schedule=request.schedule,
        enabled=request.enabled,
    )

    # Merge parameters into input_schema defaults
    if request.parameters:
        for key, value in request.parameters.items():
            # Update any step parameters that reference this input
            for step in workflow_data["steps"]:
                if isinstance(step["parameters"], dict):
                    for param_key, param_value in step["parameters"].items():
                        if isinstance(param_value, str) and f"{{{{input.{key}" in param_value:
                            # Replace template variable with actual value
                            step["parameters"][param_key] = value

    # Create workflow
    workflow = await service.create_workflow(**workflow_data)

    return InstantiateTemplateResponse(
        workflow_id=workflow.id,
        message=f"Created workflow '{workflow.name}' from template '{template.name}'",
    )


# =============================================================================
# Common Template Helpers
# =============================================================================

@router.post("/workflow-templates/quick/rss-to-notes", response_model=InstantiateTemplateResponse)
async def quick_rss_to_notes(
    feed_urls: List[str],
    notebook_id: Optional[str] = None,
    schedule: Optional[str] = None,
):
    """Quick create RSS to Notes workflow."""
    template = TemplateRegistry.get("rss_to_notes")
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    workflow_data = template.to_workflow_data(
        name=f"RSS Monitor: {len(feed_urls)} feeds",
        target_notebook_id=notebook_id,
        schedule=schedule,
        enabled=bool(schedule),
    )

    # Inject feed URLs into first step
    for step in workflow_data["steps"]:
        if step["step_id"] == "fetch_rss":
            step["parameters"]["feed_urls"] = feed_urls

    workflow = await service.create_workflow(**workflow_data)

    return InstantiateTemplateResponse(
        workflow_id=workflow.id,
        message=f"Created RSS monitor for {len(feed_urls)} feeds",
    )


@router.post("/workflow-templates/quick/repurpose-content", response_model=InstantiateTemplateResponse)
async def quick_repurpose_content(
    source_ids: List[str],
    notebook_id: Optional[str] = None,
):
    """Quick create content repurposing workflow."""
    template = TemplateRegistry.get("content_repurpose")
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    workflow_data = template.to_workflow_data(
        name=f"Repurpose {len(source_ids)} sources",
        target_notebook_id=notebook_id,
    )

    # Inject source IDs into all transformation steps
    for step in workflow_data["steps"]:
        step["parameters"]["source_ids"] = source_ids

    workflow = await service.create_workflow(**workflow_data)

    return InstantiateTemplateResponse(
        workflow_id=workflow.id,
        message=f"Created repurposing workflow for {len(source_ids)} sources",
    )
