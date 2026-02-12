"""API routes for Conversational Workflow Builder.

Provides endpoints for generating workflows from natural language.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from open_notebook.workflows.conversational import (
    ConversationalWorkflowBuilder,
    WorkflowSuggestionEngine,
)
from open_notebook.workflows.service import WorkflowService
from open_notebook.workflows.templates import TemplateRegistry

router = APIRouter()
service = WorkflowService()
builder = ConversationalWorkflowBuilder()


# =============================================================================
# Request/Response Models
# =============================================================================

class ConversationMessage(BaseModel):
    """A message in the conversation."""
    role: str  # "user" or "assistant"
    content: str


class GenerateWorkflowRequest(BaseModel):
    """Request to generate a workflow from natural language."""
    prompt: str
    conversation_history: Optional[List[ConversationMessage]] = None


class WorkflowStepSuggestion(BaseModel):
    """Suggested workflow step."""
    step_id: str
    skill_type: str
    name: str
    description: str
    depends_on: List[str] = []


class GeneratedWorkflowResponse(BaseModel):
    """Response from workflow generation."""
    workflow_definition: Dict[str, Any]
    explanation: str
    estimated_duration: str
    suggestions: List[str] = []
    needs_confirmation: bool = True


class RefineWorkflowRequest(BaseModel):
    """Request to refine a workflow."""
    current_definition: Dict[str, Any]
    refinement_prompt: str
    conversation_history: Optional[List[ConversationMessage]] = None


class WorkflowSuggestionResponse(BaseModel):
    """Workflow suggestion."""
    id: str
    title: str
    description: str
    template_id: Optional[str]
    icon: str


class QuickCreateFromTemplateRequest(BaseModel):
    """Quick create workflow from template with AI-populated parameters."""
    template_id: str
    user_goal: str
    target_notebook_id: Optional[str] = None


# =============================================================================
# Workflow Generation
# =============================================================================

@router.post("/workflow-builder/generate", response_model=GeneratedWorkflowResponse)
async def generate_workflow(request: GenerateWorkflowRequest):
    """Generate a workflow definition from natural language description."""
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    history = None
    if request.conversation_history:
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.conversation_history
        ]

    result = await builder.generate_from_prompt(
        user_prompt=request.prompt,
        conversation_history=history,
    )

    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])

    return GeneratedWorkflowResponse(
        workflow_definition=result.get("workflow_definition", {}),
        explanation=result.get("explanation", ""),
        estimated_duration=result.get("estimated_duration", "Unknown"),
        suggestions=result.get("suggestions", []),
        needs_confirmation=True,
    )


@router.post("/workflow-builder/refine", response_model=GeneratedWorkflowResponse)
async def refine_workflow(request: RefineWorkflowRequest):
    """Refine an existing workflow based on user feedback."""
    if not request.refinement_prompt.strip():
        raise HTTPException(status_code=400, detail="Refinement prompt cannot be empty")

    history = None
    if request.conversation_history:
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.conversation_history
        ]

    result = await builder.refine_workflow(
        current_definition=request.current_definition,
        refinement_request=request.refinement_prompt,
        conversation_history=history,
    )

    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])

    return GeneratedWorkflowResponse(
        workflow_definition=result.get("workflow_definition", {}),
        explanation=result.get("explanation", ""),
        estimated_duration=result.get("estimated_duration", "Unknown"),
        suggestions=result.get("suggestions", []),
        needs_confirmation=True,
    )


# =============================================================================
# Workflow Suggestions
# =============================================================================

@router.get("/workflow-builder/suggestions", response_model=List[WorkflowSuggestionResponse])
async def get_workflow_suggestions(
    user_goal: Optional[str] = None,
    notebook_id: Optional[str] = None,
):
    """Get suggested workflows based on user context."""
    suggestions = WorkflowSuggestionEngine.get_suggestions(user_goal=user_goal)

    return [
        WorkflowSuggestionResponse(
            id=s["id"],
            title=s["title"],
            description=s["description"],
            template_id=s.get("template_id"),
            icon=s.get("icon", "📋"),
        )
        for s in suggestions
    ]


@router.post("/workflow-builder/quick-create")
async def quick_create_from_suggestion(
    suggestion_id: str,
    target_notebook_id: Optional[str] = None,
    schedule: Optional[str] = None,
):
    """Quickly create a workflow from a suggestion."""
    suggestions = WorkflowSuggestionEngine.get_suggestions()
    suggestion = next((s for s in suggestions if s["id"] == suggestion_id), None)

    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    template_id = suggestion.get("template_id")
    if not template_id:
        raise HTTPException(status_code=400, detail="Suggestion has no associated template")

    template = TemplateRegistry.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Create workflow from template
    workflow_data = template.to_workflow_data(
        name=suggestion["title"],
        target_notebook_id=target_notebook_id,
        schedule=schedule,
        enabled=bool(schedule),
    )

    workflow = await service.create_workflow(**workflow_data)

    return {
        "workflow_id": workflow.id,
        "message": f"Created '{suggestion['title']}' workflow",
        "next_steps": [
            "Configure workflow parameters" if not schedule else "Workflow is scheduled and enabled",
            f"Run manually at /api/workflows/{workflow.id}/execute",
        ],
    }


# =============================================================================
# Natural Language to Template
# =============================================================================

@router.post("/workflow-builder/match-template")
async def match_template_to_description(description: str):
    """Find the best matching template for a user description."""
    templates = TemplateRegistry.list_all()

    # Simple keyword matching (could be enhanced with AI)
    description_lower = description.lower()
    scores = []

    for template in templates:
        score = 0
        template_text = f"{template.name} {template.description}".lower()

        # Check for keyword matches
        keywords = description_lower.split()
        for keyword in keywords:
            if len(keyword) > 3 and keyword in template_text:
                score += 1

        scores.append((template, score))

    # Sort by score
    scores.sort(key=lambda x: x[1], reverse=True)

    # Return top 3 matches
    matches = [
        {
            "template_id": t.template_id,
            "name": t.name,
            "description": t.description,
            "category": t.category,
            "relevance_score": score,
        }
        for t, score in scores[:3]
    ]

    return {
        "query": description,
        "matches": matches,
        "recommended": matches[0] if matches else None,
    }


# =============================================================================
# Interactive Builder Steps
# =============================================================================

@router.post("/workflow-builder/analyze-requirements")
async def analyze_requirements(prompt: str):
    """Analyze user requirements and suggest workflow structure."""
    analysis = {
        "detected_intent": None,
        "required_skills": [],
        "suggested_steps": [],
        "complexity": "simple",  # simple, moderate, complex
    }

    prompt_lower = prompt.lower()

    # Detect intent
    if any(word in prompt_lower for word in ["rss", "feed", "news", "monitor"]):
        analysis["detected_intent"] = "content_monitoring"
        analysis["required_skills"].append("rss_crawler")
        analysis["suggested_steps"] = ["Fetch content", "Summarize", "Create notes"]

    elif any(word in prompt_lower for word in ["transform", "repurpose", "convert", "twitter", "linkedin"]):
        analysis["detected_intent"] = "content_repurposing"
        analysis["required_skills"].append("content_transform")
        analysis["suggested_steps"] = ["Transform format A", "Transform format B", "Transform format C"]
        analysis["complexity"] = "moderate"

    elif any(word in prompt_lower for word in ["competitor", "monitor", "website", "track"]):
        analysis["detected_intent"] = "competitor_monitoring"
        analysis["required_skills"].extend(["browser_crawler", "content_transform"])
        analysis["suggested_steps"] = ["Crawl website", "Extract changes", "Generate insights"]

    elif any(word in prompt_lower for word in ["organize", "tag", "clean", "structure"]):
        analysis["detected_intent"] = "content_organization"
        analysis["required_skills"].extend(["note_tagger", "note_summarizer"])
        analysis["suggested_steps"] = ["Tag content", "Summarize", "Create index"]

    elif any(word in prompt_lower for word in ["podcast", "audio", "episode"]):
        analysis["detected_intent"] = "podcast_creation"
        analysis["required_skills"].append("podcast_generator")
        analysis["suggested_steps"] = ["Prepare content", "Generate podcast"]

    else:
        analysis["detected_intent"] = "custom"
        analysis["complexity"] = "complex"

    return analysis
