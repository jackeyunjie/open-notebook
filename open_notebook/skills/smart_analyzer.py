"""Smart Source Analyzer - Automatic content analysis for uploaded sources.

This skill automatically analyzes source content and generates:
- Concise summary
- Topic tags
- Content outline (table of contents)

It can be triggered automatically when a source is processed or run manually.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from open_notebook.domain.notebook import Note, Source
from open_notebook.skills.base import Skill, SkillConfig, SkillContext, SkillResult, SkillStatus
from open_notebook.skills.registry import register_skill


class SmartSourceAnalyzer(Skill):
    """Automatically analyze source content and generate insights.

    This skill performs comprehensive analysis of source content:
    1. Generates concise summary (100-300 words)
    2. Extracts 3-5 relevant topic tags
    3. Creates hierarchical content outline

    Results are saved as:
    - Source topics (updated on source)
    - Source insights (for outline)
    - Note (for summary, optional)

    Parameters:
        - source_ids: List of source IDs to analyze
        - generate_summary_note: Create a summary note (default: true)
        - summary_length: Target length in words (default: 200)
        - max_topics: Maximum tags to generate (default: 5)
        - generate_outline: Generate content outline (default: true)

    Example:
        config = SkillConfig(
            skill_type="smart_analyzer",
            name="Smart Source Analyzer",
            parameters={
                "source_ids": ["source:abc123"],
                "generate_summary_note": True,
                "summary_length": 200,
                "max_topics": 5,
                "generate_outline": True
            }
        )
    """

    skill_type = "smart_analyzer"
    name = "Smart Source Analyzer"
    description = "Automatically analyze source content and generate summary, tags, and outline"

    parameters_schema = {
        "source_ids": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of source IDs to analyze"
        },
        "generate_summary_note": {
            "type": "boolean",
            "default": True,
            "description": "Create a summary note for each source"
        },
        "summary_length": {
            "type": "integer",
            "default": 200,
            "minimum": 50,
            "maximum": 1000,
            "description": "Target summary length in words"
        },
        "max_topics": {
            "type": "integer",
            "default": 5,
            "minimum": 1,
            "maximum": 10,
            "description": "Maximum number of topic tags to generate"
        },
        "generate_outline": {
            "type": "boolean",
            "default": True,
            "description": "Generate hierarchical content outline"
        }
    }

    def __init__(self, config: SkillConfig):
        self.source_ids: List[str] = config.parameters.get("source_ids", [])
        self.generate_summary_note: bool = config.parameters.get("generate_summary_note", True)
        self.summary_length: int = config.parameters.get("summary_length", 200)
        self.max_topics: int = config.parameters.get("max_topics", 5)
        self.generate_outline: bool = config.parameters.get("generate_outline", True)
        super().__init__(config)

    def _validate_config(self) -> None:
        """Validate analyzer configuration."""
        super()._validate_config()

        if not self.source_ids:
            raise ValueError("At least one source ID is required")

    def _build_analysis_prompt(self, content: str, title: Optional[str] = None) -> str:
        """Build the prompt for comprehensive source analysis."""
        return f"""Analyze the following content comprehensively. Provide your analysis in this exact format:

===SUMMARY===
Provide a concise summary of approximately {self.summary_length} words that captures the main points and key takeaways.

===TOPICS===
List {self.max_topics} relevant topic tags as comma-separated values (e.g., "AI, Machine Learning, Ethics")

===OUTLINE===
Create a hierarchical outline of the content structure using markdown format:
- Use ## for main sections
- Use ### for subsections
- Brief description for each section

Content Title: {title or "Untitled"}

Content to analyze:
---
{content[:15000]}
---

Analysis:"""

    async def _analyze_content(self, content: str, title: Optional[str] = None) -> Dict[str, Any]:
        """Analyze content using AI to generate summary, topics, and outline."""
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            from open_notebook.ai.provision import provision_langchain_model

            prompt = self._build_analysis_prompt(content, title)

            messages = [
                SystemMessage(content="""You are an expert content analyst. Your task is to:
1. Create accurate, concise summaries
2. Extract relevant topic tags
3. Generate well-structured content outlines

Always follow the exact output format requested."""),
                HumanMessage(content=prompt)
            ]

            # Use transformation type for analysis (typically cheaper/faster model)
            chain = await provision_langchain_model(
                prompt_text=prompt,
                model_id=None,
                default_type="transformation"
            )

            response = await chain.ainvoke(messages)
            response_text = response.content if hasattr(response, 'content') else str(response)

            # Parse the response
            return self._parse_analysis_response(response_text)

        except Exception as e:
            logger.error(f"Failed to analyze content: {e}")
            raise

    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the AI response to extract summary, topics, and outline."""
        result = {
            "summary": "",
            "topics": [],
            "outline": ""
        }

        try:
            # Extract summary
            if "===SUMMARY===" in response_text:
                summary_start = response_text.find("===SUMMARY===") + len("===SUMMARY===")
                summary_end = response_text.find("===TOPICS===", summary_start)
                if summary_end == -1:
                    summary_end = len(response_text)
                result["summary"] = response_text[summary_start:summary_end].strip()

            # Extract topics
            if "===TOPICS===" in response_text:
                topics_start = response_text.find("===TOPICS===") + len("===TOPICS===")
                topics_end = response_text.find("===OUTLINE===", topics_start)
                if topics_end == -1:
                    topics_end = len(response_text)
                topics_text = response_text[topics_start:topics_end].strip()

                # Parse comma-separated topics
                topics = [t.strip() for t in topics_text.split(",") if t.strip()]
                result["topics"] = topics[:self.max_topics]

            # Extract outline
            if "===OUTLINE===" in response_text:
                outline_start = response_text.find("===OUTLINE===") + len("===OUTLINE===")
                result["outline"] = response_text[outline_start:].strip()

        except Exception as e:
            logger.warning(f"Error parsing analysis response: {e}")
            # Fallback: use entire response as summary
            result["summary"] = response_text[:500]

        return result

    async def _update_source_topics(self, source: Source, topics: List[str]) -> None:
        """Update source with generated topics."""
        if not topics:
            return

        try:
            # Merge with existing topics
            existing_topics = set(source.topics or [])
            new_topics = existing_topics.union(set(topics))
            source.topics = list(new_topics)
            await source.save()
            logger.info(f"Updated source {source.id} with {len(topics)} topics")
        except Exception as e:
            logger.error(f"Failed to update source topics: {e}")

    async def _create_summary_note(
        self,
        source: Source,
        summary: str,
        topics: List[str],
        notebook_id: Optional[str] = None
    ) -> Optional[str]:
        """Create a summary note for the source."""
        try:
            note_title = f"Summary: {source.title or 'Untitled Source'}"

            # Build note content
            content_parts = [f"## Summary\n\n{summary}"]

            if topics:
                content_parts.append(f"\n## Topics\n\n{', '.join(topics)}")

            content_parts.append(f"\n## Source\n\n- **ID**: {source.id}")
            if source.title:
                content_parts.append(f"- **Title**: {source.title}")

            note_content = "\n".join(content_parts)

            note = Note(
                title=note_title,
                content=note_content,
                note_type="ai"
            )
            await note.save()

            # Link to notebook if specified
            if notebook_id:
                await note.add_to_notebook(notebook_id)
            elif self.config.target_notebook_id:
                await note.add_to_notebook(self.config.target_notebook_id)

            logger.info(f"Created summary note {note.id} for source {source.id}")
            return str(note.id)

        except Exception as e:
            logger.error(f"Failed to create summary note: {e}")
            return None

    async def _save_outline_insight(self, source: Source, outline: str) -> Optional[str]:
        """Save content outline as a source insight."""
        if not outline:
            return None

        try:
            command_id = await source.add_insight("Content Outline", outline)
            if command_id:
                logger.info(f"Saved outline insight for source {source.id}")
            return command_id
        except Exception as e:
            logger.error(f"Failed to save outline insight: {e}")
            return None

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute smart source analysis."""
        logger.info(f"Analyzing {len(self.source_ids)} sources")

        processed_sources: List[Dict[str, Any]] = []
        created_notes: List[str] = []
        errors: List[str] = []

        for source_id in self.source_ids:
            try:
                # Fetch the source
                source = await Source.get(source_id)
                if not source:
                    error_msg = f"Source {source_id} not found"
                    logger.warning(error_msg)
                    errors.append(error_msg)
                    continue

                if not source.full_text:
                    error_msg = f"Source {source_id} has no content"
                    logger.warning(error_msg)
                    errors.append(error_msg)
                    continue

                logger.info(f"Analyzing source {source_id}: {source.title or 'Untitled'}")

                # Perform analysis
                analysis = await self._analyze_content(
                    source.full_text,
                    source.title
                )

                # Update source with topics
                if analysis["topics"]:
                    await self._update_source_topics(source, analysis["topics"])

                # Save outline as insight
                insight_id = None
                if self.generate_outline and analysis["outline"]:
                    insight_id = await self._save_outline_insight(
                        source,
                        analysis["outline"]
                    )

                # Create summary note
                note_id = None
                if self.generate_summary_note and analysis["summary"]:
                    note_id = await self._create_summary_note(
                        source,
                        analysis["summary"],
                        analysis["topics"]
                    )
                    if note_id:
                        created_notes.append(note_id)

                processed_sources.append({
                    "source_id": source_id,
                    "source_title": source.title,
                    "topics_generated": analysis["topics"],
                    "summary_length": len(analysis["summary"]),
                    "has_outline": bool(analysis["outline"]),
                    "note_id": note_id,
                    "insight_id": insight_id
                })

                logger.info(f"Successfully analyzed source {source_id}")

            except Exception as e:
                error_msg = f"Error analyzing source {source_id}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Determine status
        if errors and not processed_sources:
            status = SkillStatus.FAILED
        elif errors:
            status = SkillStatus.SUCCESS
        else:
            status = SkillStatus.SUCCESS

        return SkillResult(
            skill_id=context.skill_id,
            status=status,
            started_at=datetime.utcnow(),
            output={
                "sources_analyzed": len(processed_sources),
                "sources": processed_sources,
                "notes_created": len(created_notes),
                "errors": errors
            },
            error_message="; ".join(errors) if errors else None,
            created_note_ids=created_notes
        )


# Auto-trigger function for integration with source processing
async def analyze_source_on_upload(
    source_id: str,
    notebook_id: Optional[str] = None,
    create_note: bool = True
) -> Optional[SkillResult]:
    """Convenience function to auto-trigger analysis on source upload.

    This function can be called from source processing workflows to
    automatically analyze newly uploaded sources.

    Args:
        source_id: The ID of the source to analyze
        notebook_id: Optional notebook ID to associate notes with
        create_note: Whether to create a summary note

    Returns:
        SkillResult if analysis was performed, None if skipped
    """
    try:
        config = SkillConfig(
            skill_type="smart_analyzer",
            name="Auto Source Analysis",
            parameters={
                "source_ids": [source_id],
                "generate_summary_note": create_note,
                "summary_length": 200,
                "max_topics": 5,
                "generate_outline": True
            },
            target_notebook_id=notebook_id
        )

        analyzer = SmartSourceAnalyzer(config)

        from open_notebook.skills.base import SkillContext
        ctx = SkillContext(
            skill_id=f"auto_analyze_{source_id}",
            trigger_type="event",
            notebook_id=notebook_id,
            source_id=source_id
        )

        result = await analyzer.run(ctx)
        return result

    except Exception as e:
        logger.error(f"Failed to auto-analyze source {source_id}: {e}")
        return None


# Register the skill
register_skill(SmartSourceAnalyzer)
