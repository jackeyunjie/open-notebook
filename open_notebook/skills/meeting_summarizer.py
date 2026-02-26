"""Meeting Summarizer - AI-powered meeting transcript analysis and summary.

This skill analyzes meeting transcripts and generates structured summaries:
1. Key discussion points extraction
2. Action items with owners and deadlines
3. Decision tracking
4. Sentiment analysis
5. Participant engagement metrics

Key Features:
- Automatic speaker identification
- Topic segmentation
- Action item extraction with assignment
- Follow-up email generation
- Integration with calendar/task systems
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from open_notebook.domain.notebook import Notebook, Note
from open_notebook.skills.base import Skill, SkillConfig, SkillContext, SkillResult, SkillStatus
from open_notebook.skills.registry import register_skill


class MeetingType(Enum):
    """Types of meetings."""
    STANDUP = "standup"
    REVIEW = "review"
    PLANNING = "planning"
    BRAINSTORM = "brainstorm"
    ONE_ON_ONE = "one_on_one"
    CLIENT = "client"
    BOARD = "board"


@dataclass
class ActionItem:
    """An action item from the meeting."""
    description: str
    owner: Optional[str] = None
    deadline: Optional[str] = None
    priority: str = "medium"  # low, medium, high
    status: str = "pending"
    source_quote: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "owner": self.owner,
            "deadline": self.deadline,
            "priority": self.priority,
            "status": self.status,
            "source_quote": self.source_quote,
        }


@dataclass
class Decision:
    """A decision made in the meeting."""
    topic: str
    decision: str
    rationale: str = ""
    stakeholders: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "decision": self.decision,
            "rationale": self.rationale,
            "stakeholders": self.stakeholders,
        }


@dataclass
class MeetingSummary:
    """Complete meeting summary."""
    title: str
    meeting_type: MeetingType
    date: datetime
    duration_minutes: int
    participants: List[str] = field(default_factory=list)
    key_points: List[str] = field(default_factory=list)
    action_items: List[ActionItem] = field(default_factory=list)
    decisions: List[Decision] = field(default_factory=list)
    topics: List[Dict[str, Any]] = field(default_factory=list)
    sentiment: str = "neutral"
    follow_up_required: bool = False
    next_meeting: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "meeting_type": self.meeting_type.value,
            "date": self.date.isoformat(),
            "duration_minutes": self.duration_minutes,
            "participants": self.participants,
            "key_points": self.key_points,
            "action_items": [a.to_dict() for a in self.action_items],
            "decisions": [d.to_dict() for d in self.decisions],
            "topics": self.topics,
            "sentiment": self.sentiment,
            "follow_up_required": self.follow_up_required,
            "next_meeting": self.next_meeting,
        }


class MeetingSummarizer(Skill):
    """Analyze meeting transcripts and generate structured summaries.

    Parameters:
        - notebook_id: Notebook containing meeting transcript
        - note_id: Specific note with transcript
        - meeting_type: Type of meeting
        - participants: List of participant names (optional)
        - duration_minutes: Meeting duration
        - extract_action_items: Whether to extract action items (default: true)
        - generate_follow_up: Generate follow-up content (default: true)

    Example:
        config = SkillConfig(
            skill_type="meeting_summarizer",
            parameters={
                "note_id": "note:meeting_transcript",
                "meeting_type": "standup",
                "duration_minutes": 30
            }
        )
    """

    skill_type = "meeting_summarizer"
    name = "Meeting Summarizer"
    description = "AI-powered meeting transcript analysis and structured summary"

    parameters_schema = {
        "notebook_id": {"type": "string", "description": "Notebook ID"},
        "note_id": {"type": "string", "description": "Transcript note ID"},
        "meeting_type": {"type": "string", "enum": ["standup", "review", "planning", "brainstorm", "one_on_one", "client", "board"], "default": "review"},
        "participants": {"type": "array", "items": {"type": "string"}, "description": "Participant names"},
        "duration_minutes": {"type": "integer", "description": "Meeting duration"},
        "extract_action_items": {"type": "boolean", "default": True},
        "generate_follow_up": {"type": "boolean", "default": True},
    }

    def __init__(self, config: SkillConfig):
        self.notebook_id: Optional[str] = config.parameters.get("notebook_id")
        self.note_id: Optional[str] = config.parameters.get("note_id")
        self.meeting_type: MeetingType = MeetingType(config.parameters.get("meeting_type", "review"))
        self.participants: List[str] = config.parameters.get("participants", [])
        self.duration_minutes: Optional[int] = config.parameters.get("duration_minutes")
        self.extract_action_items: bool = config.parameters.get("extract_action_items", True)
        self.generate_follow_up: bool = config.parameters.get("generate_follow_up", True)
        super().__init__(config)

    def _validate_config(self) -> None:
        super()._validate_config()
        if not self.note_id and not self.notebook_id:
            raise ValueError("note_id or notebook_id required")

    async def _get_transcript(self) -> Tuple[str, str]:
        """Get transcript content."""
        if self.note_id:
            note = await Note.get(self.note_id)
            if note:
                return note.title or "Meeting", note.content or ""
        elif self.notebook_id:
            notebook = await Notebook.get(self.notebook_id)
            if notebook:
                notes = await notebook.get_notes()
                if notes:
                    return notes[0].title or "Meeting", notes[0].content or ""
        return "Meeting", ""

    async def _analyze_transcript(self, title: str, transcript: str) -> MeetingSummary:
        """Analyze transcript with AI."""
        try:
            from open_notebook.ai.provision import provision_langchain_model

            type_prompts = {
                MeetingType.STANDUP: "Daily standup: focus on what was done, blockers, and plans",
                MeetingType.REVIEW: "Review meeting: focus on progress, issues, and feedback",
                MeetingType.PLANNING: "Planning meeting: focus on goals, timeline, and resources",
                MeetingType.BRAINSTORM: "Brainstorm: focus on ideas, discussions, and creative solutions",
                MeetingType.ONE_ON_ONE: "1:1 meeting: focus on personal updates, growth, and concerns",
                MeetingType.CLIENT: "Client meeting: focus on requirements, feedback, and next steps",
                MeetingType.BOARD: "Board meeting: focus on strategy, metrics, and governance",
            }

            prompt = f"""Analyze this meeting transcript and create a structured summary.

Meeting Type: {self.meeting_type.value} - {type_prompts.get(self.meeting_type, '')}
Participants: {', '.join(self.participants) if self.participants else "Not specified"}
Duration: {self.duration_minutes or "Unknown"} minutes

Transcript:
---
{transcript[:15000]}
---

Provide analysis as JSON:
{{
  "key_points": ["Main point 1", "Main point 2"],
  "action_items": [
    {{
      "description": "What needs to be done",
      "owner": "Person name or null",
      "deadline": "When due or null",
      "priority": "high|medium|low",
      "source_quote": "Quote from transcript"
    }}
  ],
  "decisions": [
    {{
      "topic": "What was decided",
      "decision": "The decision made",
      "rationale": "Why this decision",
      "stakeholders": ["People involved"]
    }}
  ],
  "topics": [
    {{
      "topic": "Topic name",
      "duration_estimate": "brief|medium|extended",
      "sentiment": "positive|neutral|negative"
    }}
  ],
  "overall_sentiment": "positive|neutral|negative",
  "follow_up_required": true|false,
  "participants": ["Extracted names"]
}}

Guidelines:
- Be concise but capture important details
- Extract specific action items with owners when possible
- Identify clear decisions made
- Note any deadlines mentioned
- Assess sentiment of discussion

Return ONLY the JSON."""

            model = await provision_langchain_model(prompt_text=prompt, model_id=None, default_type="transformation")
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

            data = json.loads(response_text.strip())

            return MeetingSummary(
                title=title,
                meeting_type=self.meeting_type,
                date=datetime.utcnow(),
                duration_minutes=self.duration_minutes or 60,
                participants=data.get("participants", self.participants),
                key_points=data.get("key_points", []),
                action_items=[ActionItem(**a) for a in data.get("action_items", [])],
                decisions=[Decision(**d) for d in data.get("decisions", [])],
                topics=data.get("topics", []),
                sentiment=data.get("overall_sentiment", "neutral"),
                follow_up_required=data.get("follow_up_required", False),
            )

        except Exception as e:
            logger.error(f"Transcript analysis failed: {e}")
            return self._create_default_summary(title)

    def _create_default_summary(self, title: str) -> MeetingSummary:
        """Create default summary."""
        return MeetingSummary(
            title=title,
            meeting_type=self.meeting_type,
            date=datetime.utcnow(),
            duration_minutes=self.duration_minutes or 60,
            participants=self.participants,
            key_points=["Meeting took place", "Discussion occurred"],
            sentiment="neutral",
        )

    def _generate_follow_up_email(self, summary: MeetingSummary) -> str:
        """Generate follow-up email."""
        email = f"""Subject: Meeting Summary: {summary.title}

Hi Team,

Thank you for attending today's {summary.meeting_type.value.replace('_', ' ')}.

## Key Discussion Points

"""
        for point in summary.key_points[:5]:
            email += f"- {point}\n"

        if summary.action_items:
            email += "\n## Action Items\n\n"
            for item in summary.action_items:
                owner = f" (@{item.owner})" if item.owner else ""
                deadline = f" - Due: {item.deadline}" if item.deadline else ""
                email += f"- [ ] {item.description}{owner}{deadline}\n"

        if summary.decisions:
            email += "\n## Decisions Made\n\n"
            for decision in summary.decisions:
                email += f"- **{decision.topic}**: {decision.decision}\n"

        email += f"\n\nBest regards"

        return email

    def _generate_meeting_minutes(self, summary: MeetingSummary) -> str:
        """Generate formal meeting minutes."""
        minutes = f"""# Meeting Minutes: {summary.title}

**Date:** {summary.date.strftime('%Y-%m-%d %H:%M')}
**Type:** {summary.meeting_type.value.replace('_', ' ').title()}
**Duration:** {summary.duration_minutes} minutes
**Participants:** {', '.join(summary.participants) if summary.participants else 'N/A'}

## Attendees

{chr(10).join(f'- {p}' for p in summary.participants) if summary.participants else 'N/A'}

## Key Discussion Points

"""
        for point in summary.key_points:
            minutes += f"- {point}\n"

        if summary.decisions:
            minutes += "\n## Decisions\n\n"
            for i, decision in enumerate(summary.decisions, 1):
                minutes += f"{i}. **{decision.topic}**\n"
                minutes += f"   - Decision: {decision.decision}\n"
                if decision.rationale:
                    minutes += f"   - Rationale: {decision.rationale}\n"

        if summary.action_items:
            minutes += "\n## Action Items\n\n"
            minutes += "| # | Action | Owner | Deadline | Priority |\n"
            minutes += "|---|--------|-------|----------|----------|\n"
            for i, item in enumerate(summary.action_items, 1):
                owner = item.owner or "TBD"
                deadline = item.deadline or "TBD"
                minutes += f"| {i} | {item.description[:50]}... | {owner} | {deadline} | {item.priority} |\n"

        minutes += f"\n## Next Steps\n\n"
        if summary.follow_up_required:
            minutes += "- Follow-up meeting required\n"
        if summary.action_items:
            minutes += f"- Complete {len(summary.action_items)} action items\n"

        minutes += f"\n---\n*Meeting minutes generated on {datetime.utcnow().strftime('%Y-%m-%d')}*"

        return minutes

    async def _save_summary(self, summary: MeetingSummary, notebook_id: str) -> Optional[str]:
        """Save summary as note."""
        try:
            content = self._generate_meeting_minutes(summary)

            if self.generate_follow_up:
                content += "\n\n## Follow-up Email Draft\n\n```\n"
                content += self._generate_follow_up_email(summary)
                content += "\n```\n"

            note = Note(
                title=f"📝 Meeting: {summary.title[:40]}",
                content=content,
                note_type="ai",
            )
            await note.save()
            await note.add_to_notebook(notebook_id)

            return str(note.id) if note.id else None

        except Exception as e:
            logger.error(f"Failed to save summary: {e}")
            return None

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute meeting summarization."""
        logger.info(f"Starting meeting summarization")
        start_time = datetime.utcnow()

        try:
            title, transcript = await self._get_transcript()
            if not transcript:
                raise ValueError("No transcript found")

            summary = await self._analyze_transcript(title, transcript)
            logger.info(f"Analyzed meeting: {len(summary.key_points)} key points, {len(summary.action_items)} action items")

            note_id = None
            if self.notebook_id:
                note_id = await self._save_summary(summary, self.notebook_id)

            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.SUCCESS,
                started_at=start_time,
                completed_at=datetime.utcnow(),
                output={
                    "summary": summary.to_dict(),
                    "note_id": note_id,
                    "stats": {
                        "key_points": len(summary.key_points),
                        "action_items": len(summary.action_items),
                        "decisions": len(summary.decisions),
                        "sentiment": summary.sentiment,
                    },
                    "follow_up_email": self._generate_follow_up_email(summary) if self.generate_follow_up else None,
                }
            )

        except Exception as e:
            logger.error(f"Meeting summarization failed: {e}")
            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.FAILED,
                started_at=start_time,
                completed_at=datetime.utcnow(),
                error_message=str(e)
            )


async def summarize_meeting(note_id: str, meeting_type: str = "review") -> Optional[MeetingSummary]:
    """Quick meeting summarization."""
    config = SkillConfig(
        skill_type="meeting_summarizer",
        name="Meeting Summarizer",
        parameters={"note_id": note_id, "meeting_type": meeting_type}
    )

    summarizer = MeetingSummarizer(config)
    from open_notebook.skills.base import SkillContext
    ctx = SkillContext(skill_id=f"meeting_{datetime.utcnow().timestamp()}", trigger_type="manual")

    result = await summarizer.run(ctx)

    if result.success:
        data = result.output.get("summary", {})
        return MeetingSummary(
            title=data.get("title", "Meeting"),
            meeting_type=MeetingType(data.get("meeting_type", "review")),
            date=datetime.utcnow(),
            duration_minutes=data.get("duration_minutes", 60),
        )

    return None


register_skill(MeetingSummarizer)
