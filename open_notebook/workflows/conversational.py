"""Conversational Workflow Builder - Generate workflows from natural language.

Uses AI to understand user intent and generate appropriate workflow definitions
with proper steps, dependencies, and parameter mappings.
"""

import json
from typing import Any, Dict, List, Optional

from loguru import logger

from open_notebook.ai.provision import provision_langchain_model
from open_notebook.skills.registry import SkillRegistry


CONVERSATIONAL_SYSTEM_PROMPT = """You are a workflow design assistant for Open Notebook, an AI-powered research and content creation platform.

Your task is to convert user requests into structured workflow definitions that orchestrate multiple "Skills" (automation units).

## Available Skills

1. **rss_crawler** - Fetches articles from RSS feeds
   - Parameters: feed_urls (list), max_entries (int), deduplicate (bool)

2. **note_summarizer** - Generates summaries using AI
   - Parameters: source_ids (list), summary_length (str), summary_style (str)

3. **note_tagger** - Auto-generates tags for content
   - Parameters: target_ids (list), target_type (str), max_tags (int)

4. **browser_task** - Performs browser automation
   - Parameters: task (str), url (str), max_steps (int)

5. **browser_crawler** - Crawls websites for content
   - Parameters: urls (list), extraction_task (str), max_pages (int)

6. **content_transform** - Transforms content format/style
   - Parameters: source_ids (list), transformation_type (str), options (dict)

7. **podcast_generator** - Generates podcast from sources
   - Parameters: source_ids (list), episode_profile_id (str), speaker_profile_ids (list)

## Workflow Definition Format

```json
{
  "name": "Human-readable workflow name",
  "description": "What this workflow does",
  "steps": [
    {
      "step_id": "unique_id_for_step",
      "skill_type": "one_of_available_skills",
      "name": "Human-readable step name",
      "description": "What this step does",
      "parameters": {
        "param_key": "value or {{input.field}} or {{steps.prev_step.output.field}}"
      },
      "depends_on": ["step_ids_that_must_complete_first"],
      "condition": "optional_python_condition",
      "retry_on_fail": 0,
      "continue_on_fail": false
    }
  ],
  "input_schema": {
    "field_name": {
      "type": "string|integer|array|boolean",
      "description": "What this field is for",
      "default": "optional_default_value"
    }
  },
  "output_mapping": {
    "result_key": "{{steps.step_id.output.field}}"
  }
}
```

## Template Variable Syntax

- `{{input.field_name}}` - Reference to workflow input parameter
- `{{steps.step_id.output.field}}` - Reference to previous step output
- `{{input.field|default(value)}}` - With default value

## Common Patterns

1. **Sequential**: Step A → Step B → Step C
2. **Parallel**: Step A → [Step B, Step C] → Step D
3. **Conditional**: Step A → Step B (if condition) → Step C
4. **Retry**: Set retry_on_fail > 0 for flaky operations

## Response Format

Respond with a JSON object:
```json
{
  "workflow_definition": { ... },
  "explanation": "Human-readable explanation of the workflow design",
  "estimated_duration": "Rough estimate (e.g., '2-5 minutes')",
  "suggestions": ["Optional improvement suggestions"]
}
```
"""


class ConversationalWorkflowBuilder:
    """Build workflows from natural language descriptions using AI."""

    def __init__(self):
        self.available_skills = self._get_available_skills()

    def _get_available_skills(self) -> List[Dict[str, Any]]:
        """Get list of available skills with their metadata."""
        skills = SkillRegistry.list_skills()
        return [
            {
                "skill_type": s["skill_type"],
                "name": s["name"],
                "description": s["description"],
            }
            for s in skills
        ]

    async def generate_from_prompt(
        self,
        user_prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Generate a workflow definition from natural language.

        Args:
            user_prompt: User's natural language description of desired workflow
            conversation_history: Optional previous conversation for context

        Returns:
            Dict with workflow_definition, explanation, and suggestions
        """
        # Build the prompt
        system_prompt = self._build_system_prompt()

        messages = [
            {"role": "system", "content": system_prompt},
        ]

        # Add conversation history if provided
        if conversation_history:
            for msg in conversation_history:
                messages.append({"role": msg["role"], "content": msg["content"]})

        # Add user request
        messages.append({"role": "user", "content": f"Create a workflow for: {user_prompt}"})

        try:
            # Get AI model
            chain = await provision_langchain_model(
                prompt_text="",
                model_id=None,  # Use default model
                feature_type="workflow_generation"
            )

            # Generate workflow
            response = await chain.ainvoke(messages)
            content = response.content if hasattr(response, 'content') else str(response)

            # Parse JSON response
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code block
                result = self._extract_json_from_markdown(content)

            # Validate the workflow definition
            validated = self._validate_workflow_definition(result.get("workflow_definition", {}))
            result["workflow_definition"] = validated

            return result

        except Exception as e:
            logger.exception(f"Failed to generate workflow: {e}")
            return {
                "error": str(e),
                "workflow_definition": None,
                "explanation": "Failed to generate workflow. Please try again with a clearer description.",
            }

    async def refine_workflow(
        self,
        current_definition: Dict[str, Any],
        refinement_request: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Refine an existing workflow based on user feedback.

        Args:
            current_definition: Current workflow definition
            refinement_request: User's request for changes
            conversation_history: Optional conversation history

        Returns:
            Updated workflow definition
        """
        system_prompt = self._build_system_prompt() + """

## Additional Instructions

You are refining an EXISTING workflow based on user feedback.
Current workflow definition will be provided.
Make minimal changes to address the user's request while preserving the overall structure.
"""

        messages = [
            {"role": "system", "content": system_prompt},
        ]

        if conversation_history:
            for msg in conversation_history:
                messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({
            "role": "user",
            "content": f"""Current workflow:
{json.dumps(current_definition, indent=2)}

Refinement request: {refinement_request}

Please provide the updated workflow definition."""
        })

        try:
            chain = await provision_langchain_model(
                prompt_text="",
                model_id=None,
                feature_type="workflow_generation"
            )

            response = await chain.ainvoke(messages)
            content = response.content if hasattr(response, 'content') else str(response)

            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                result = self._extract_json_from_markdown(content)

            validated = self._validate_workflow_definition(result.get("workflow_definition", {}))
            result["workflow_definition"] = validated

            return result

        except Exception as e:
            logger.exception(f"Failed to refine workflow: {e}")
            return {
                "error": str(e),
                "workflow_definition": current_definition,
                "explanation": "Failed to refine workflow. Keeping original definition.",
            }

    def _build_system_prompt(self) -> str:
        """Build system prompt with current available skills."""
        skills_text = "\n".join([
            f"- **{s['skill_type']}**: {s['name']} - {s['description']}"
            for s in self.available_skills
        ])

        return f"""{CONVERSATIONAL_SYSTEM_PROMPT}

## Currently Available Skills

{skills_text}
"""

    def _extract_json_from_markdown(self, content: str) -> Dict[str, Any]:
        """Extract JSON from markdown code block."""
        import re

        # Try to find JSON in code blocks
        patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
            r'\{.*\}',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue

        # If all else fails, return empty dict
        return {}

    def _validate_workflow_definition(self, definition: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize workflow definition."""
        if not definition:
            return {}

        # Ensure required fields
        validated = {
            "name": definition.get("name", "Untitled Workflow"),
            "description": definition.get("description", ""),
            "steps": [],
            "input_schema": definition.get("input_schema", {}),
            "output_mapping": definition.get("output_mapping", {}),
        }

        # Validate steps
        steps = definition.get("steps", [])
        step_ids = set()

        for step in steps:
            step_id = step.get("step_id")
            if not step_id:
                continue

            # Check for duplicate step IDs
            if step_id in step_ids:
                step_id = f"{step_id}_2"
            step_ids.add(step_id)

            # Validate skill type exists
            skill_type = step.get("skill_type", "")
            if not SkillRegistry.is_registered(skill_type):
                logger.warning(f"Skill type '{skill_type}' not registered, may fail at runtime")

            validated["steps"].append({
                "step_id": step_id,
                "skill_type": skill_type,
                "name": step.get("name") or step_id,
                "description": step.get("description", ""),
                "parameters": step.get("parameters", {}),
                "depends_on": step.get("depends_on", []),
                "condition": step.get("condition"),
                "retry_on_fail": step.get("retry_on_fail", 0),
                "retry_delay_seconds": step.get("retry_delay_seconds", 5),
                "continue_on_fail": step.get("continue_on_fail", False),
            })

        # Validate dependencies (ensure all referenced steps exist)
        for step in validated["steps"]:
            for dep in step["depends_on"]:
                if dep not in step_ids:
                    logger.warning(f"Step '{step['step_id']}' depends on unknown step '{dep}'")
                    step["depends_on"] = [d for d in step["depends_on"] if d != dep]

        return validated


class WorkflowSuggestionEngine:
    """Suggest workflows based on user's content and goals."""

    COMMON_SUGGESTIONS = [
        {
            "id": "daily_news_digest",
            "title": "Daily News Digest",
            "description": "Automatically collect and summarize news from your favorite sources every morning",
            "template_id": "rss_to_notes",
            "icon": "📰",
        },
        {
            "id": "weekly_research_report",
            "title": "Weekly Research Report",
            "description": "Compile all your research from the week into a structured report",
            "template_id": "research_digest",
            "icon": "📊",
        },
        {
            "id": "content_multiply",
            "title": "Content Multiplier",
            "description": "Turn one article into a Twitter thread, LinkedIn post, and newsletter",
            "template_id": "content_repurpose",
            "icon": "🔄",
        },
        {
            "id": "competitor_watch",
            "title": "Competitor Watch",
            "description": "Monitor competitor websites for updates and changes",
            "template_id": "competitor_monitor",
            "icon": "👁️",
        },
        {
            "id": "auto_organize",
            "title": "Auto-Organizer",
            "description": "Automatically tag and organize all unprocessed content",
            "template_id": "auto_organize",
            "icon": "🗂️",
        },
    ]

    @classmethod
    def get_suggestions(
        cls,
        user_goal: Optional[str] = None,
        content_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Get workflow suggestions based on user context."""
        suggestions = cls.COMMON_SUGGESTIONS.copy()

        if user_goal:
            # Could use AI to rank suggestions based on goal
            pass

        if content_types:
            # Filter suggestions based on content types
            pass

        return suggestions

    @classmethod
    def suggest_for_notebook(
        cls,
        notebook_name: str,
        source_count: int = 0,
    ) -> List[Dict[str, Any]]:
        """Suggest workflows based on notebook characteristics."""
        suggestions = []

        if "news" in notebook_name.lower() or "rss" in notebook_name.lower():
            suggestions.append(cls.COMMON_SUGGESTIONS[0])  # Daily News Digest

        if "research" in notebook_name.lower() or "study" in notebook_name.lower():
            suggestions.append(cls.COMMON_SUGGESTIONS[1])  # Weekly Research Report

        if source_count > 10:
            suggestions.append(cls.COMMON_SUGGESTIONS[4])  # Auto-Organizer

        return suggestions or cls.COMMON_SUGGESTIONS[:3]
