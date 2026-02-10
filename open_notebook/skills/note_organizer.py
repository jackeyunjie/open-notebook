"""Note organization skills for intelligent content processing.

This module provides skills for automatically organizing notes:
- Summarization
- Tag generation
- Knowledge graph connections
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from open_notebook.domain.notebook import Note, Source
from open_notebook.skills.base import Skill, SkillConfig, SkillContext, SkillResult, SkillStatus
from open_notebook.skills.registry import register_skill


class NoteSummarizerSkill(Skill):
    """Automatically summarize notes using AI.
    
    This skill reads note content and generates concise summaries,
    storing them as new notes or updating existing ones.
    
    Parameters:
        - source_note_ids: List of note IDs to summarize
        - summary_length: Target summary length in words (default: 100)
        - summary_style: Style of summary (default: "concise")
            Options: "concise", "detailed", "bullet_points", "executive"
        - create_new_note: Whether to create a new note or update existing (default: true)
    
    Example:
        config = SkillConfig(
            skill_type="note_summarizer",
            name="Auto Summarizer",
            parameters={
                "source_note_ids": ["note:abc123"],
                "summary_length": 150,
                "summary_style": "bullet_points"
            },
            target_notebook_id="notebook:xyz789"
        )
    """
    
    skill_type = "note_summarizer"
    name = "Note Summarizer"
    description = "Automatically generate AI-powered summaries of notes"
    
    parameters_schema = {
        "source_note_ids": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of note IDs to summarize"
        },
        "summary_length": {
            "type": "integer",
            "default": 100,
            "minimum": 50,
            "maximum": 1000,
            "description": "Target summary length in words"
        },
        "summary_style": {
            "type": "string",
            "enum": ["concise", "detailed", "bullet_points", "executive"],
            "default": "concise",
            "description": "Style of summary to generate"
        },
        "create_new_note": {
            "type": "boolean",
            "default": True,
            "description": "Create a new note vs update existing"
        }
    }
    
    def __init__(self, config: SkillConfig):
        super().__init__(config)
        self.source_note_ids: List[str] = self.get_param("source_note_ids", [])
        self.summary_length: int = self.get_param("summary_length", 100)
        self.summary_style: str = self.get_param("summary_style", "concise")
        self.create_new_note: bool = self.get_param("create_new_note", True)
    
    def _validate_config(self) -> None:
        """Validate summarizer configuration."""
        super()._validate_config()
        
        if not self.source_note_ids:
            raise ValueError("At least one source note ID is required")
    
    def _build_prompt(self, content: str) -> str:
        """Build summarization prompt based on style."""
        style_instructions = {
            "concise": f"Provide a concise summary in about {self.summary_length} words.",
            "detailed": f"Provide a detailed summary covering key points, approximately {self.summary_length} words.",
            "bullet_points": f"Summarize as bullet points, approximately {self.summary_length // 10} key points.",
            "executive": f"Provide an executive summary suitable for busy decision makers, about {self.summary_length} words."
        }
        
        instruction = style_instructions.get(self.summary_style, style_instructions["concise"])
        
        return f"""Please summarize the following content.

{instruction}

Content to summarize:
---
{content}
---

Summary:"""
    
    async def _generate_summary(self, content: str) -> str:
        """Generate summary using AI."""
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            from open_notebook.ai.provision import provision_langchain_model
            
            prompt = self._build_prompt(content)
            
            # Use the project's existing AI provisioning
            messages = [
                SystemMessage(content="You are an expert at summarizing content accurately and concisely."),
                HumanMessage(content=prompt)
            ]
            
            # Get model from config or use default
            chain = await provision_langchain_model(
                prompt_text=prompt,
                model_id=None,  # Use default
                feature_type="summarization"
            )
            
            response = await chain.ainvoke(messages)
            
            summary = response.content if hasattr(response, 'content') else str(response)
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            raise
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute note summarization."""
        logger.info(f"Summarizing {len(self.source_note_ids)} notes")
        
        created_notes: List[str] = []
        errors: List[str] = []
        
        for note_id in self.source_note_ids:
            try:
                # Fetch the note
                note = await Note.get(note_id)
                if not note:
                    error_msg = f"Note {note_id} not found"
                    logger.warning(error_msg)
                    errors.append(error_msg)
                    continue
                
                if not note.content:
                    error_msg = f"Note {note_id} has no content"
                    logger.warning(error_msg)
                    errors.append(error_msg)
                    continue
                
                # Generate summary
                logger.info(f"Generating summary for note {note_id}")
                summary = await self._generate_summary(note.content)
                
                # Create or update note
                if self.create_new_note:
                    summary_note = Note(
                        title=f"Summary: {note.title or 'Untitled'}",
                        content=summary,
                        note_type="ai"
                    )
                    await summary_note.save()
                    
                    # Link to target notebook
                    if self.config.target_notebook_id:
                        await summary_note.add_to_notebook(self.config.target_notebook_id)
                    
                    created_notes.append(str(summary_note.id))
                    logger.info(f"Created summary note {summary_note.id}")
                else:
                    # Update existing note
                    note.content = f"{summary}\n\n---\n\nOriginal:\n{note.content}"
                    await note.save()
                    created_notes.append(note_id)
                    logger.info(f"Updated note {note_id} with summary")
                    
            except Exception as e:
                error_msg = f"Error summarizing note {note_id}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # Determine status
        if errors and not created_notes:
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
                "notes_processed": len(self.source_note_ids),
                "summaries_created": len(created_notes),
                "errors": errors
            },
            error_message="; ".join(errors) if errors else None,
            created_note_ids=created_notes
        )


class NoteTaggerSkill(Skill):
    """Automatically generate tags for notes using AI.
    
    This skill analyzes note content and suggests relevant tags,
    which can be applied to notes or sources.
    
    Parameters:
        - target_ids: List of note or source IDs to tag
        - target_type: Type of targets ("note" or "source")
        - max_tags: Maximum tags to generate per item (default: 5)
        - tag_categories: Optional categories for tags (e.g., ["topic", "type", "priority"])
    
    Example:
        config = SkillConfig(
            skill_type="note_tagger",
            name="Auto Tagger",
            parameters={
                "target_ids": ["note:abc123"],
                "target_type": "note",
                "max_tags": 5
            }
        )
    """
    
    skill_type = "note_tagger"
    name = "Note Tagger"
    description = "Automatically generate AI-powered tags for notes and sources"
    
    parameters_schema = {
        "target_ids": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of note or source IDs to tag"
        },
        "target_type": {
            "type": "string",
            "enum": ["note", "source"],
            "default": "note",
            "description": "Type of targets"
        },
        "max_tags": {
            "type": "integer",
            "default": 5,
            "minimum": 1,
            "maximum": 20,
            "description": "Maximum tags per item"
        },
        "tag_categories": {
            "type": "array",
            "items": {"type": "string"},
            "default": [],
            "description": "Optional tag categories"
        }
    }
    
    def __init__(self, config: SkillConfig):
        super().__init__(config)
        self.target_ids: List[str] = self.get_param("target_ids", [])
        self.target_type: str = self.get_param("target_type", "note")
        self.max_tags: int = self.get_param("max_tags", 5)
        self.tag_categories: List[str] = self.get_param("tag_categories", [])
    
    async def _generate_tags(self, content: str, title: Optional[str] = None) -> List[str]:
        """Generate tags using AI."""
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            from open_notebook.ai.provision import provision_langchain_model
            
            categories_instruction = ""
            if self.tag_categories:
                categories_instruction = f"Organize tags into these categories: {', '.join(self.tag_categories)}. "
            
            prompt = f"""Generate {self.max_tags} relevant tags for the following content.
{categories_instruction}
Return only the tags as a comma-separated list, no explanations.

Title: {title or 'Untitled'}

Content:
---
{content[:2000]}  # Limit content length
---

Tags:"""
            
            messages = [
                SystemMessage(content="You are an expert at categorizing and tagging content."),
                HumanMessage(content=prompt)
            ]
            
            chain = await provision_langchain_model(
                prompt_text=prompt,
                model_id=None,
                feature_type="tagging"
            )
            
            response = await chain.ainvoke(messages)
            
            # Parse tags from response
            tags_text = response.content if hasattr(response, 'content') else str(response)
            tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
            
            return tags[:self.max_tags]
            
        except Exception as e:
            logger.error(f"Failed to generate tags: {e}")
            raise
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute note tagging."""
        logger.info(f"Tagging {len(self.target_ids)} {self.target_type}s")
        
        tagged_items: List[Dict[str, Any]] = []
        errors: List[str] = []
        
        for target_id in self.target_ids:
            try:
                # Fetch target
                if self.target_type == "note":
                    target = await Note.get(target_id)
                    content = target.content if target else None
                    title = target.title if target else None
                else:  # source
                    target = await Source.get(target_id)
                    content = target.full_text if target else None
                    title = target.title if target else None
                
                if not target:
                    error_msg = f"{self.target_type} {target_id} not found"
                    logger.warning(error_msg)
                    errors.append(error_msg)
                    continue
                
                if not content:
                    error_msg = f"{self.target_type} {target_id} has no content"
                    logger.warning(error_msg)
                    errors.append(error_msg)
                    continue
                
                # Generate tags
                logger.info(f"Generating tags for {self.target_type} {target_id}")
                tags = await self._generate_tags(content, title)
                
                # Update target with tags
                if hasattr(target, 'topics'):
                    # Merge with existing tags
                    existing_tags = set(target.topics or [])
                    new_tags = existing_tags.union(set(tags))
                    target.topics = list(new_tags)
                    await target.save()
                
                tagged_items.append({
                    "id": target_id,
                    "type": self.target_type,
                    "tags": tags
                })
                
                logger.info(f"Tagged {self.target_type} {target_id} with {len(tags)} tags")
                
            except Exception as e:
                error_msg = f"Error tagging {self.target_type} {target_id}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # Determine status
        if errors and not tagged_items:
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
                "items_processed": len(self.target_ids),
                "items_tagged": len(tagged_items),
                "tagged_items": tagged_items,
                "errors": errors
            },
            error_message="; ".join(errors) if errors else None
        )


# Register skills
register_skill(NoteSummarizerSkill)
register_skill(NoteTaggerSkill)
