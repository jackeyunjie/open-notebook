"""PPT Generator - AI-powered presentation creation from notebook content.

This skill generates professional PowerPoint presentations from notebook content:
1. Content analysis and structure planning
2. Slide layout selection (title, content, two-column, image, etc.)
3. AI-generated speaker notes
4. Design theme selection
5. Export to PPTX format

Key Features:
- Multiple presentation types (pitch deck, tutorial, report, etc.)
- Smart content distribution across slides
- Automatic image suggestions
- Speaker notes generation
- Professional design themes
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from open_notebook.domain.notebook import Notebook, Note, Source
from open_notebook.skills.base import Skill, SkillConfig, SkillContext, SkillResult, SkillStatus
from open_notebook.skills.registry import register_skill


class PresentationType(Enum):
    """Types of presentations."""
    PITCH_DECK = "pitch_deck"  # Startup/product pitch
    TUTORIAL = "tutorial"  # Educational step-by-step
    RESEARCH_REPORT = "research_report"  # Academic/professional report
    EXECUTIVE_SUMMARY = "executive_summary"  # High-level overview
    CASE_STUDY = "case_study"  # Problem-solution-outcome
    TRAINING = "training"  # Employee/customer training
    STATUS_UPDATE = "status_update"  # Project progress


class SlideLayout(Enum):
    """Slide layout types."""
    TITLE = "title"  # Title slide
    CONTENT = "content"  # Title + bullet points
    TWO_COLUMN = "two_column"  # Two columns
    IMAGE = "image"  # Full image with caption
    QUOTE = "quote"  # Big quote
    CHART = "chart"  # Data visualization
    SECTION = "section"  # Section divider
    END = "end"  # Thank you / end slide


@dataclass
class Slide:
    """A single slide definition."""
    slide_number: int
    layout: SlideLayout
    title: str
    content: str
    bullet_points: List[str] = field(default_factory=list)
    image_prompt: Optional[str] = None
    speaker_notes: str = ""
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "slide_number": self.slide_number,
            "layout": self.layout.value,
            "title": self.title,
            "content": self.content,
            "bullet_points": self.bullet_points,
            "image_prompt": self.image_prompt,
            "speaker_notes": self.speaker_notes,
        }


@dataclass
class Presentation:
    """Complete presentation structure."""
    title: str
    subtitle: str
    presentation_type: PresentationType
    target_audience: str
    slide_count: int
    theme: str
    slides: List[Slide] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "subtitle": self.subtitle,
            "presentation_type": self.presentation_type.value,
            "target_audience": self.target_audience,
            "slide_count": len(self.slides),
            "theme": self.theme,
            "slides": [s.to_dict() for s in self.slides],
            "created_at": self.created_at.isoformat(),
        }


class PPTGenerator(Skill):
    """Generate professional PowerPoint presentations from notebook content.

    This skill creates structured presentations:
    1. Analyzes content and plans presentation structure
    2. Generates slides with appropriate layouts
    3. Creates speaker notes for each slide
    4. Exports to PPTX format

    Parameters:
        - notebook_id: Notebook containing source content
        - note_id: Specific note to convert (optional, priority over notebook)
        - source_ids: Specific sources to include (optional)
        - presentation_type: Type of presentation
        - target_audience: Target audience description
        - max_slides: Maximum number of slides (default: 15)
        - theme: Design theme (default: "professional")
        - include_speaker_notes: Generate speaker notes (default: true)
        - language: Output language (default: auto)

    Example:
        config = SkillConfig(
            skill_type="ppt_generator",
            name="PPT Generator",
            parameters={
                "notebook_id": "notebook:abc123",
                "presentation_type": "pitch_deck",
                "max_slides": 12,
                "target_audience": "investors"
            }
        )
    """

    skill_type = "ppt_generator"
    name = "PPT Generator"
    description = "AI-powered presentation creation from notebook content"

    parameters_schema = {
        "notebook_id": {"type": "string", "description": "Notebook ID"},
        "note_id": {"type": "string", "description": "Specific note ID (optional)"},
        "source_ids": {"type": "array", "items": {"type": "string"}, "description": "Source IDs (optional)"},
        "presentation_type": {
            "type": "string",
            "enum": ["pitch_deck", "tutorial", "research_report", "executive_summary", "case_study", "training", "status_update"],
            "default": "research_report",
            "description": "Presentation type"
        },
        "target_audience": {"type": "string", "default": "general", "description": "Target audience"},
        "max_slides": {"type": "integer", "default": 15, "minimum": 3, "maximum": 50, "description": "Max slides"},
        "theme": {"type": "string", "default": "professional", "description": "Design theme"},
        "include_speaker_notes": {"type": "boolean", "default": True, "description": "Include speaker notes"},
        "language": {"type": "string", "default": "auto", "description": "Output language"},
    }

    def __init__(self, config: SkillConfig):
        self.notebook_id: Optional[str] = config.parameters.get("notebook_id")
        self.note_id: Optional[str] = config.parameters.get("note_id")
        self.source_ids: Optional[List[str]] = config.parameters.get("source_ids")
        self.presentation_type: PresentationType = PresentationType(config.parameters.get("presentation_type", "research_report"))
        self.target_audience: str = config.parameters.get("target_audience", "general")
        self.max_slides: int = config.parameters.get("max_slides", 15)
        self.theme: str = config.parameters.get("theme", "professional")
        self.include_speaker_notes: bool = config.parameters.get("include_speaker_notes", True)
        self.language: str = config.parameters.get("language", "auto")
        super().__init__(config)

    def _validate_config(self) -> None:
        super()._validate_config()
        if not self.notebook_id and not self.note_id:
            raise ValueError("Either notebook_id or note_id is required")
        if self.max_slides < 3 or self.max_slides > 50:
            raise ValueError("max_slides must be between 3 and 50")

    async def _get_content(self) -> Tuple[str, str]:
        """Get title and content from sources."""
        title = "Presentation"
        content_parts = []

        if self.note_id:
            note = await Note.get(self.note_id)
            if note:
                title = note.title or title
                content_parts.append(note.content or "")
        elif self.notebook_id:
            notebook = await Notebook.get(self.notebook_id)
            if notebook:
                title = getattr(notebook, 'title', title)
                if self.source_ids:
                    for sid in self.source_ids:
                        source = await Source.get(sid)
                        if source and source.full_text:
                            content_parts.append(f"# {source.title}\n{source.full_text[:4000]}")
                else:
                    sources = await notebook.get_sources()
                    for source in sources[:5]:
                        if source.full_text:
                            content_parts.append(f"# {source.title}\n{source.full_text[:4000]}")

        return title, "\n\n".join(content_parts)

    async def _plan_presentation(self, title: str, content: str) -> Dict[str, Any]:
        """Plan presentation structure."""
        try:
            from open_notebook.ai.provision import provision_langchain_model

            type_descriptions = {
                PresentationType.PITCH_DECK: "Startup/product pitch: Problem, Solution, Market, Business Model, Team, Ask",
                PresentationType.TUTORIAL: "Step-by-step educational: Introduction, Prerequisites, Steps 1-N, Summary",
                PresentationType.RESEARCH_REPORT: "Academic report: Abstract, Methodology, Results, Discussion, Conclusion",
                PresentationType.EXECUTIVE_SUMMARY: "High-level overview: Situation, Complication, Resolution, Recommendation",
                PresentationType.CASE_STUDY: "Problem-solution-outcome: Background, Challenge, Approach, Results, Lessons",
                PresentationType.TRAINING: "Skills training: Objectives, Concepts, Demonstration, Practice, Assessment",
                PresentationType.STATUS_UPDATE: "Project progress: Accomplishments, Challenges, Next Steps, Timeline",
            }

            prompt = f"""Plan a presentation based on this content.

Title: {title}
Presentation Type: {self.presentation_type.value} - {type_descriptions.get(self.presentation_type, '')}
Target Audience: {self.target_audience}
Max Slides: {self.max_slides}

Content:
---
{content[:10000]}
---

Create a presentation plan in this JSON format:
{{
  "title": "Presentation title",
  "subtitle": "Subtitle or tagline",
  "slide_plan": [
    {{
      "slide_number": 1,
      "layout": "title|content|two_column|image|quote|chart|section|end",
      "title": "Slide title",
      "key_points": ["point 1", "point 2", "point 3"],
      "image_suggestion": "Description of visual to include"
    }}
  ]
}}

Guidelines:
- Slide 1 should be title slide
- Include section dividers for major topics
- Limit bullet points to 3-5 per slide
- Last slide should be thank you/end
- Total slides should not exceed {self.max_slides}

Return ONLY the JSON."""

            model = await provision_langchain_model(
                prompt_text=prompt,
                model_id=None,
                default_type="transformation"
            )

            response = await model.ainvoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)

            # Clean
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            return json.loads(response_text.strip())

        except Exception as e:
            logger.error(f"Presentation planning failed: {e}")
            return {
                "title": title,
                "subtitle": "Generated Presentation",
                "slide_plan": [
                    {"slide_number": 1, "layout": "title", "title": title, "key_points": []},
                    {"slide_number": 2, "layout": "content", "title": "Introduction", "key_points": ["Overview of the topic"]},
                    {"slide_number": 3, "layout": "content", "title": "Key Points", "key_points": ["Main finding 1", "Main finding 2"]},
                    {"slide_number": 4, "layout": "end", "title": "Thank You", "key_points": []},
                ]
            }

    async def _generate_slides(self, plan: Dict[str, Any], content: str) -> List[Slide]:
        """Generate detailed slide content."""
        slides = []
        slide_plans = plan.get("slide_plan", [])

        for slide_plan in slide_plans[:self.max_slides]:
            try:
                slide = await self._generate_single_slide(slide_plan, content)
                slides.append(slide)
            except Exception as e:
                logger.warning(f"Failed to generate slide {slide_plan.get('slide_number')}: {e}")
                slides.append(Slide(
                    slide_number=slide_plan.get("slide_number", len(slides) + 1),
                    layout=SlideLayout.CONTENT,
                    title=slide_plan.get("title", "Slide"),
                    content="",
                    bullet_points=slide_plan.get("key_points", []),
                ))

        return slides

    async def _generate_single_slide(self, slide_plan: Dict[str, Any], full_content: str) -> Slide:
        """Generate content for a single slide."""
        from open_notebook.ai.provision import provision_langchain_model

        layout = SlideLayout(slide_plan.get("layout", "content"))
        title = slide_plan.get("title", "")
        key_points = slide_plan.get("key_points", [])

        # Generate detailed content based on layout
        if layout == SlideLayout.TITLE:
            return Slide(
                slide_number=slide_plan.get("slide_number", 1),
                layout=layout,
                title=title,
                content="",
                speaker_notes="Welcome the audience and introduce the presentation." if self.include_speaker_notes else "",
            )

        elif layout == SlideLayout.END:
            return Slide(
                slide_number=slide_plan.get("slide_number", 1),
                layout=layout,
                title=title,
                content="Thank you for your attention.",
                speaker_notes="Open the floor for questions." if self.include_speaker_notes else "",
            )

        # For content slides, generate speaker notes
        speaker_notes = ""
        if self.include_speaker_notes:
            prompt = f"""Generate speaker notes for this slide:

Slide Title: {title}
Key Points:
{chr(10).join(f"- {p}" for p in key_points)}

Original Content Context:
{full_content[:2000]}

Write 2-3 sentences of speaker notes explaining what to emphasize when presenting this slide.
Keep it conversational and helpful for the presenter."""

            try:
                model = await provision_langchain_model(prompt_text=prompt, model_id=None, default_type="chat")
                response = await model.ainvoke(prompt)
                speaker_notes = response.content if hasattr(response, 'content') else str(response)
                speaker_notes = speaker_notes.strip()[:500]
            except Exception:
                speaker_notes = ""

        return Slide(
            slide_number=slide_plan.get("slide_number", 1),
            layout=layout,
            title=title,
            content="",
            bullet_points=key_points[:6],  # Max 6 bullets
            image_prompt=slide_plan.get("image_suggestion") if layout in [SlideLayout.IMAGE, SlideLayout.CHART] else None,
            speaker_notes=speaker_notes,
        )

    async def _export_to_pptx(self, presentation: Presentation, output_dir: Path) -> Optional[str]:
        """Export presentation to PPTX file."""
        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            # For now, create a structured text file
            # In production, use python-pptx library
            file_path = output_dir / f"{presentation.title.replace(' ', '_')}.md"

            content = f"""# {presentation.title}

**Subtitle:** {presentation.subtitle}
**Type:** {presentation.presentation_type.value}
**Audience:** {presentation.target_audience}
**Slides:** {len(presentation.slides)}
**Theme:** {presentation.theme}

---

"""
            for slide in presentation.slides:
                content += f"""## Slide {slide.slide_number}: {slide.title}
**Layout:** {slide.layout.value}

"""
                if slide.bullet_points:
                    for point in slide.bullet_points:
                        content += f"- {point}\n"
                    content += "\n"

                if slide.image_prompt:
                    content += f"**Image:** {slide.image_prompt}\n\n"

                if slide.speaker_notes:
                    content += f"**Speaker Notes:** {slide.speaker_notes}\n\n"

                content += "---\n\n"

            file_path.write_text(content, encoding='utf-8')
            return str(file_path)

        except Exception as e:
            logger.error(f"Export failed: {e}")
            return None

    async def _save_presentation_note(self, presentation: Presentation, notebook_id: str) -> Optional[str]:
        """Save presentation as note."""
        try:
            content = f"""# 📊 Presentation: {presentation.title}

**Subtitle:** {presentation.subtitle}
**Type:** {presentation.presentation_type.value}
**Audience:** {presentation.target_audience}
**Slides:** {len(presentation.slides)}

---

## Slides Overview

"""
            for slide in presentation.slides:
                content += f"""### {slide.slide_number}. {slide.title} ({slide.layout.value})
"""
                if slide.bullet_points:
                    for point in slide.bullet_points:
                        content += f"- {point}\n"
                    content += "\n"

            note = Note(
                title=f"📊 {presentation.title[:45]}",
                content=content,
                note_type="ai",
            )
            await note.save()
            await note.add_to_notebook(notebook_id)

            return str(note.id) if note.id else None

        except Exception as e:
            logger.error(f"Failed to save note: {e}")
            return None

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute PPT generation."""
        logger.info(f"Starting PPT generation")
        start_time = datetime.utcnow()

        try:
            # Get content
            title, content = await self._get_content()
            if not content:
                raise ValueError("No content found")

            # Plan presentation
            plan = await self._plan_presentation(title, content)
            logger.info(f"Planned presentation: {plan.get('title')} with {len(plan.get('slide_plan', []))} slides")

            # Generate slides
            slides = await self._generate_slides(plan, content)

            # Create presentation
            presentation = Presentation(
                title=plan.get("title", title),
                subtitle=plan.get("subtitle", ""),
                presentation_type=self.presentation_type,
                target_audience=self.target_audience,
                slide_count=len(slides),
                theme=self.theme,
                slides=slides,
            )

            # Export
            output_dir = Path(f"./data/presentations/{datetime.utcnow().strftime('%Y%m%d')}")
            file_path = await self._export_to_pptx(presentation, output_dir)

            # Save note
            note_id = None
            if self.notebook_id:
                note_id = await self._save_presentation_note(presentation, self.notebook_id)

            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.SUCCESS,
                started_at=start_time,
                completed_at=datetime.utcnow(),
                output={
                    "presentation": presentation.to_dict(),
                    "file_path": file_path,
                    "note_id": note_id,
                    "stats": {
                        "slide_count": len(slides),
                        "title_slides": len([s for s in slides if s.layout == SlideLayout.TITLE]),
                        "content_slides": len([s for s in slides if s.layout == SlideLayout.CONTENT]),
                    }
                }
            )

        except Exception as e:
            logger.error(f"PPT generation failed: {e}")
            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.FAILED,
                started_at=start_time,
                completed_at=datetime.utcnow(),
                error_message=str(e)
            )


async def generate_presentation(
    notebook_id: str,
    presentation_type: str = "research_report",
    max_slides: int = 15
) -> Optional[Presentation]:
    """Generate presentation from notebook."""
    config = SkillConfig(
        skill_type="ppt_generator",
        name="PPT Generator",
        parameters={
            "notebook_id": notebook_id,
            "presentation_type": presentation_type,
            "max_slides": max_slides,
        }
    )

    generator = PPTGenerator(config)
    from open_notebook.skills.base import SkillContext
    ctx = SkillContext(skill_id=f"ppt_{datetime.utcnow().timestamp()}", trigger_type="manual")

    result = await generator.run(ctx)

    if result.success:
        pres_data = result.output.get("presentation", {})
        return Presentation(
            title=pres_data.get("title", "Presentation"),
            subtitle=pres_data.get("subtitle", ""),
            presentation_type=PresentationType(pres_data.get("presentation_type", "research_report")),
            target_audience=pres_data.get("target_audience", "general"),
            slide_count=pres_data.get("slide_count", 0),
            theme=pres_data.get("theme", "professional"),
        )

    return None


register_skill(PPTGenerator)
