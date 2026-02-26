"""Auto Podcast Planner - AI-powered podcast design and optimization.

This skill enhances Open Notebook's podcast generation with intelligent planning:
1. Content analysis for optimal podcast format selection
2. Speaker count recommendation (1-4 speakers)
3. Episode outline generation with "hook" openings
4. Format adaptation based on content type (educational, storytelling, debate, etc.)
5. Speaker personality matching to content

Key Features:
- Goes beyond NotebookLM's fixed 2-speaker format
- Content-aware format selection (solo, interview, panel, debate)
- AI-generated engaging openings/hooks
- Smart speaker-role assignment
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from loguru import logger

from open_notebook.domain.notebook import Notebook, Source
from open_notebook.podcasts.models import EpisodeProfile, SpeakerProfile
from open_notebook.skills.base import Skill, SkillConfig, SkillContext, SkillResult, SkillStatus
from open_notebook.skills.registry import register_skill


class PodcastFormat(Enum):
    """Podcast format types based on content characteristics."""
    SOLO_MONOLOGUE = "solo_monologue"  # Single expert narrator
    INTERVIEW = "interview"  # Host + expert guest
    PANEL_DISCUSSION = "panel_discussion"  # Multiple experts discussing
    DEBATE = "debate"  # Two sides of an argument
    STORYTELLING = "storytelling"  # Narrative-driven content
    EDUCATIONAL = "educational"  # Tutorial/explainer style
    NEWS_ANALYSIS = "news_analysis"  # Current events discussion


class ContentType(Enum):
    """Content classification for format matching."""
    TECHNICAL = "technical"
    STORY = "story"
    NEWS = "news"
    ACADEMIC = "academic"
    OPINION = "opinion"
    TUTORIAL = "tutorial"
    RESEARCH = "research"


@dataclass
class SpeakerRole:
    """Role definition for a podcast speaker."""
    name: str
    role_type: str  # host, expert, narrator, skeptic, enthusiast
    personality: str
    backstory: str
    voice_characteristics: str
    speaking_style: str


@dataclass
class PodcastPlan:
    """Complete podcast episode plan."""
    format_type: PodcastFormat
    content_type: ContentType
    num_speakers: int
    title: str
    hook: str  # Opening hook to grab attention
    description: str
    estimated_duration: int  # minutes
    segments: List[Dict[str, Any]] = field(default_factory=list)
    speakers: List[SpeakerRole] = field(default_factory=list)
    tone: str = "conversational"
    pacing: str = "moderate"
    music_suggestions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "format_type": self.format_type.value,
            "content_type": self.content_type.value,
            "num_speakers": self.num_speakers,
            "title": self.title,
            "hook": self.hook,
            "description": self.description,
            "estimated_duration": self.estimated_duration,
            "segments": self.segments,
            "speakers": [
                {
                    "name": s.name,
                    "role_type": s.role_type,
                    "personality": s.personality,
                    "backstory": s.backstory,
                    "voice_characteristics": s.voice_characteristics,
                    "speaking_style": s.speaking_style,
                }
                for s in self.speakers
            ],
            "tone": self.tone,
            "pacing": self.pacing,
            "music_suggestions": self.music_suggestions,
            "created_at": self.created_at.isoformat(),
        }


class AutoPodcastPlanner(Skill):
    """Automatically design optimal podcast episodes based on content analysis.

    This skill analyzes source content and recommends:
    - Best podcast format (solo, interview, panel, debate, storytelling)
    - Optimal speaker count (1-4) and roles
    - Engaging title and hook
    - Episode structure and segment outline
    - Speaker personality matching

    Parameters:
        - notebook_id: Notebook containing source content
        - source_ids: Specific sources to include (optional, all if not provided)
        - preferred_duration: Target duration in minutes (default: 15)
        - preferred_format: Force specific format (optional, auto-detect if not provided)
        - audience: Target audience (general, expert, beginner)
        - language: Content language (default: auto-detect)

    Example:
        config = SkillConfig(
            skill_type="auto_podcast_planner",
            name="Auto Podcast Planner",
            parameters={
                "notebook_id": "notebook:abc123",
                "preferred_duration": 20,
                "audience": "general"
            }
        )
    """

    skill_type = "auto_podcast_planner"
    name = "Auto Podcast Planner"
    description = "AI-powered podcast design with format selection and speaker optimization"

    parameters_schema = {
        "notebook_id": {
            "type": "string",
            "description": "Notebook ID to analyze"
        },
        "source_ids": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Specific source IDs to include (optional)"
        },
        "preferred_duration": {
            "type": "integer",
            "default": 15,
            "minimum": 5,
            "maximum": 60,
            "description": "Target episode duration in minutes"
        },
        "preferred_format": {
            "type": "string",
            "enum": ["solo_monologue", "interview", "panel_discussion", "debate", "storytelling", "educational", "news_analysis"],
            "description": "Force specific format (optional)"
        },
        "audience": {
            "type": "string",
            "enum": ["general", "expert", "beginner"],
            "default": "general",
            "description": "Target audience level"
        },
        "language": {
            "type": "string",
            "default": "auto",
            "description": "Content language (auto-detect if not specified)"
        }
    }

    def __init__(self, config: SkillConfig):
        self.notebook_id: str = config.parameters.get("notebook_id", "")
        self.source_ids: Optional[List[str]] = config.parameters.get("source_ids")
        self.preferred_duration: int = config.parameters.get("preferred_duration", 15)
        self.preferred_format: Optional[str] = config.parameters.get("preferred_format")
        self.audience: str = config.parameters.get("audience", "general")
        self.language: str = config.parameters.get("language", "auto")
        super().__init__(config)

    def _validate_config(self) -> None:
        """Validate configuration."""
        super()._validate_config()
        if not self.notebook_id:
            raise ValueError("notebook_id is required")
        if self.preferred_duration < 5 or self.preferred_duration > 60:
            raise ValueError("preferred_duration must be between 5 and 60 minutes")

    async def _analyze_content(
        self,
        sources: List[Source]
    ) -> Dict[str, Any]:
        """Analyze content to determine type and characteristics.

        Args:
            sources: List of sources to analyze

        Returns:
            Content analysis results
        """
        combined_text = ""
        for source in sources:
            if source.full_text:
                combined_text += f"\n\n=== {source.title or 'Untitled'} ===\n"
                combined_text += source.full_text[:3000]  # Limit per source

        if not combined_text:
            return {"content_type": "general", "complexity": "medium", "topics": []}

        try:
            from open_notebook.ai.provision import provision_langchain_model

            prompt = f"""Analyze the following content and determine its characteristics.

Content Sample (first ~{len(combined_text)} chars):
---
{combined_text[:8000]}
---

Analyze and return JSON:
{{
  "content_type": "technical|story|news|academic|opinion|tutorial|research",
  "complexity": "beginner|intermediate|advanced",
  "topics": ["topic1", "topic2", "topic3"],
  "has_arguments": true/false,
  "has_data": true/false,
  "narrative_style": true/false,
  "key_insights": ["insight1", "insight2"],
  "controversial_elements": true/false,
  "emotional_appeal": "low|medium|high"
}}

Return ONLY the JSON, no other text."""

            model = await provision_langchain_model(
                prompt_text=prompt,
                model_id=None,
                default_type="transformation"
            )

            response = await model.ainvoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)

            # Clean and parse JSON
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            return json.loads(response_text)

        except Exception as e:
            logger.error(f"Content analysis failed: {e}")
            return {"content_type": "general", "complexity": "medium", "topics": []}

    def _determine_format(
        self,
        analysis: Dict[str, Any],
        preferred_format: Optional[str] = None
    ) -> PodcastFormat:
        """Determine optimal podcast format based on content analysis.

        Args:
            analysis: Content analysis results
            preferred_format: User-specified format preference

        Returns:
            Recommended podcast format
        """
        if preferred_format:
            try:
                return PodcastFormat(preferred_format)
            except ValueError:
                pass

        content_type = analysis.get("content_type", "general")
        has_arguments = analysis.get("has_arguments", False)
        narrative_style = analysis.get("narrative_style", False)
        controversial = analysis.get("controversial_elements", False)

        # Format selection logic
        if narrative_style and content_type in ["story", "news"]:
            return PodcastFormat.STORYTELLING
        elif has_arguments and controversial:
            return PodcastFormat.DEBATE
        elif content_type == "tutorial":
            return PodcastFormat.EDUCATIONAL
        elif content_type == "technical":
            return PodcastFormat.PANEL_DISCUSSION
        elif content_type == "opinion":
            return PodcastFormat.INTERVIEW
        elif content_type == "news":
            return PodcastFormat.NEWS_ANALYSIS
        else:
            return PodcastFormat.INTERVIEW  # Default

    def _recommend_speaker_count(self, format_type: PodcastFormat) -> int:
        """Recommend optimal speaker count for format.

        Args:
            format_type: Podcast format type

        Returns:
            Recommended number of speakers (1-4)
        """
        recommendations = {
            PodcastFormat.SOLO_MONOLOGUE: 1,
            PodcastFormat.INTERVIEW: 2,
            PodcastFormat.PANEL_DISCUSSION: 3,
            PodcastFormat.DEBATE: 2,
            PodcastFormat.STORYTELLING: 2,
            PodcastFormat.EDUCATIONAL: 1,
            PodcastFormat.NEWS_ANALYSIS: 2,
        }
        return recommendations.get(format_type, 2)

    async def _generate_podcast_plan(
        self,
        sources: List[Source],
        analysis: Dict[str, Any],
        format_type: PodcastFormat
    ) -> PodcastPlan:
        """Generate complete podcast plan with AI.

        Args:
            sources: Source content
            analysis: Content analysis
            format_type: Selected format

        Returns:
            Complete podcast plan
        """
        try:
            from open_notebook.ai.provision import provision_langchain_model

            num_speakers = self._recommend_speaker_count(format_type)
            topics = analysis.get("topics", [])
            complexity = analysis.get("complexity", "medium")
            key_insights = analysis.get("key_insights", [])

            # Build content summary
            content_summary = ""
            for source in sources[:3]:  # Limit to first 3 sources
                if source.full_text:
                    content_summary += f"\nSource: {source.title or 'Untitled'}\n"
                    content_summary += source.full_text[:2000]

            format_descriptions = {
                PodcastFormat.SOLO_MONOLOGUE: "Single expert narrator delivering insights",
                PodcastFormat.INTERVIEW: "Host interviews an expert guest",
                PodcastFormat.PANEL_DISCUSSION: "Multiple experts discuss and debate topics",
                PodcastFormat.DEBATE: "Two speakers present opposing viewpoints",
                PodcastFormat.STORYTELLING: "Narrative-driven exploration of content",
                PodcastFormat.EDUCATIONAL: "Structured explanation like a lesson",
                PodcastFormat.NEWS_ANALYSIS: "Discussion of current events and implications",
            }

            prompt = f"""Design a compelling podcast episode based on the following content.

Format: {format_type.value} - {format_descriptions.get(format_type, '')}
Number of Speakers: {num_speakers}
Target Duration: {self.preferred_duration} minutes
Target Audience: {self.audience}
Topics: {', '.join(topics)}
Key Insights: {', '.join(key_insights)}

Content Summary:
---
{content_summary[:6000]}
---

Create a podcast plan in this JSON format:
{{
  "title": "Compelling episode title (max 60 chars)",
  "hook": "Attention-grabbing opening (1-2 sentences, max 200 chars)",
  "description": "Episode description (2-3 sentences)",
  "tone": "conversational|formal|enthusiastic|thoughtful|dramatic",
  "pacing": "fast|moderate|slow",
  "segments": [
    {{
      "name": "Segment name",
      "duration": 3,
      "description": "What happens in this segment",
      "key_points": ["point1", "point2"]
    }}
  ],
  "speakers": [
    {{
      "name": "Speaker name",
      "role_type": "host|expert|narrator|skeptic|enthusiast",
      "personality": "Brief personality description",
      "backstory": "Speaker's background/context",
      "voice_characteristics": "Voice description for TTS",
      "speaking_style": "conversational|formal|animated|measured"
    }}
  ],
  "music_suggestions": ["intro_style", "transition_style", "outro_style"]
}}

Guidelines:
- Title should be catchy but informative
- Hook must grab attention in the first 10 seconds
- Segments should total approximately {self.preferred_duration} minutes
- Each speaker needs distinct personality and role
- Speaking style should match format and audience

Return ONLY the JSON, no other text."""

            model = await provision_langchain_model(
                prompt_text=prompt,
                model_id=None,
                default_type="creative"
            )

            response = await model.ainvoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)

            # Clean and parse
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            plan_data = json.loads(response_text)

            # Create speaker roles
            speakers = []
            for s in plan_data.get("speakers", [])[:num_speakers]:
                speakers.append(SpeakerRole(
                    name=s.get("name", f"Speaker {len(speakers)+1}"),
                    role_type=s.get("role_type", "expert"),
                    personality=s.get("personality", "knowledgeable and engaging"),
                    backstory=s.get("backstory", "An expert in the field"),
                    voice_characteristics=s.get("voice_characteristics", "clear and professional"),
                    speaking_style=s.get("speaking_style", "conversational"),
                ))

            # Ensure we have the right number of speakers
            while len(speakers) < num_speakers:
                default_roles = {
                    PodcastFormat.SOLO_MONOLOGUE: [("Host", "host")],
                    PodcastFormat.INTERVIEW: [("Host", "host"), ("Guest Expert", "expert")],
                    PodcastFormat.PANEL_DISCUSSION: [("Moderator", "host"), ("Expert A", "expert"), ("Expert B", "expert")],
                    PodcastFormat.DEBATE: [("Speaker For", "enthusiast"), ("Speaker Against", "skeptic")],
                    PodcastFormat.STORYTELLING: [("Narrator", "narrator"), ("Analyst", "expert")],
                    PodcastFormat.EDUCATIONAL: [("Instructor", "host")],
                    PodcastFormat.NEWS_ANALYSIS: [("Anchor", "host"), ("Correspondent", "expert")],
                }
                idx = len(speakers)
                defaults = default_roles.get(format_type, [("Speaker", "expert")])
                if idx < len(defaults):
                    name, role_type = defaults[idx]
                    speakers.append(SpeakerRole(
                        name=name,
                        role_type=role_type,
                        personality="knowledgeable and engaging",
                        backstory="An expert in the field",
                        voice_characteristics="clear and professional",
                        speaking_style="conversational",
                    ))
                else:
                    break

            return PodcastPlan(
                format_type=format_type,
                content_type=ContentType(analysis.get("content_type", "general")),
                num_speakers=num_speakers,
                title=plan_data.get("title", "Untitled Episode"),
                hook=plan_data.get("hook", "Welcome to this episode."),
                description=plan_data.get("description", ""),
                estimated_duration=self.preferred_duration,
                segments=plan_data.get("segments", []),
                speakers=speakers,
                tone=plan_data.get("tone", "conversational"),
                pacing=plan_data.get("pacing", "moderate"),
                music_suggestions=plan_data.get("music_suggestions", []),
            )

        except Exception as e:
            logger.error(f"Podcast plan generation failed: {e}")
            # Return default plan
            return PodcastPlan(
                format_type=format_type,
                content_type=ContentType.GENERAL,
                num_speakers=self._recommend_speaker_count(format_type),
                title="Exploring the Content",
                hook="Welcome to an engaging discussion about fascinating content.",
                description="An insightful exploration of the source material.",
                estimated_duration=self.preferred_duration,
                segments=[
                    {"name": "Introduction", "duration": 2, "description": "Opening and overview", "key_points": ["Welcome", "Topic introduction"]},
                    {"name": "Main Discussion", "duration": self.preferred_duration - 4, "description": "Core content exploration", "key_points": ["Key insights"]},
                    {"name": "Conclusion", "duration": 2, "description": "Summary and closing", "key_points": ["Recap", "Final thoughts"]},
                ],
                speakers=[
                    SpeakerRole(
                        name="Host",
                        role_type="host",
                        personality="warm and knowledgeable",
                        backstory="Experienced podcast host",
                        voice_characteristics="clear and friendly",
                        speaking_style="conversational",
                    )
                ] if format_type == PodcastFormat.SOLO_MONOLOGUE else [
                    SpeakerRole(
                        name="Host",
                        role_type="host",
                        personality="warm and curious",
                        backstory="Experienced interviewer",
                        voice_characteristics="clear and friendly",
                        speaking_style="conversational",
                    ),
                    SpeakerRole(
                        name="Expert",
                        role_type="expert",
                        personality="knowledgeable and articulate",
                        backstory="Subject matter expert",
                        voice_characteristics="authoritative and clear",
                        speaking_style="measured",
                    ),
                ],
            )

    async def _create_episode_profile(
        self,
        plan: PodcastPlan,
        sources: List[Source]
    ) -> Dict[str, Any]:
        """Create episode profile from plan.

        Args:
            plan: Podcast plan
            sources: Source content

        Returns:
            Episode profile configuration
        """
        # Build briefing from plan
        briefing = f"""# {plan.title}

{plan.description}

## Format
{plan.format_type.value.replace('_', ' ').title()}

## Tone and Pacing
- Tone: {plan.tone}
- Pacing: {plan.pacing}

## Opening Hook
{plan.hook}

## Episode Structure
"""
        for segment in plan.segments:
            briefing += f"\n### {segment.get('name', 'Segment')}\n"
            briefing += f"Duration: ~{segment.get('duration', 5)} minutes\n"
            briefing += f"{segment.get('description', '')}\n"
            if segment.get('key_points'):
                briefing += "Key points:\n"
                for point in segment.get('key_points', []):
                    briefing += f"- {point}\n"

        briefing += f"\n## Content Sources\n"
        for source in sources:
            briefing += f"- {source.title or 'Untitled'}\n"

        num_segments = len(plan.segments) if plan.segments else 5

        return {
            "name": f"auto_{plan.format_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "description": f"Auto-generated profile for {plan.title}",
            "speaker_config": f"auto_speakers_{plan.num_speakers}",
            "outline_provider": "openai",
            "outline_model": "gpt-4o",
            "transcript_provider": "openai",
            "transcript_model": "gpt-4o",
            "default_briefing": briefing,
            "num_segments": num_segments,
        }

    async def _create_speaker_profile(
        self,
        plan: PodcastPlan
    ) -> Dict[str, Any]:
        """Create speaker profile from plan.

        Args:
            plan: Podcast plan

        Returns:
            Speaker profile configuration
        """
        speakers_config = []
        voice_ids = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

        for i, speaker in enumerate(plan.speakers):
            voice_id = voice_ids[i % len(voice_ids)]
            speakers_config.append({
                "name": speaker.name,
                "voice_id": voice_id,
                "backstory": speaker.backstory,
                "personality": f"{speaker.personality}. Speaking style: {speaker.speaking_style}",
            })

        return {
            "name": f"auto_speakers_{plan.num_speakers}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "description": f"Auto-generated speaker profile for {plan.format_type.value}",
            "tts_provider": "openai",
            "tts_model": "tts-1",
            "speakers": speakers_config,
        }

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute podcast planning."""
        logger.info(f"Planning podcast for notebook {self.notebook_id}")

        start_time = datetime.utcnow()

        try:
            # 1. Get notebook and sources
            notebook = await Notebook.get(self.notebook_id)
            if not notebook:
                raise ValueError(f"Notebook {self.notebook_id} not found")

            if self.source_ids:
                sources = []
                for sid in self.source_ids:
                    source = await Source.get(sid)
                    if source:
                        sources.append(source)
            else:
                sources = await notebook.get_sources()

            if not sources:
                return SkillResult(
                    skill_id=context.skill_id,
                    status=SkillStatus.FAILED,
                    started_at=start_time,
                    error_message="No sources found in notebook"
                )

            logger.info(f"Analyzing {len(sources)} sources for podcast planning")

            # 2. Analyze content
            analysis = await self._analyze_content(sources)
            content_type = analysis.get("content_type", "general")
            logger.info(f"Detected content type: {content_type}")

            # 3. Determine format
            format_type = self._determine_format(analysis, self.preferred_format)
            logger.info(f"Selected format: {format_type.value}")

            # 4. Generate podcast plan
            plan = await self._generate_podcast_plan(sources, analysis, format_type)
            logger.info(f"Generated plan: {plan.title} with {plan.num_speakers} speakers")

            # 5. Create profiles
            episode_profile = await self._create_episode_profile(plan, sources)
            speaker_profile = await self._create_speaker_profile(plan)

            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.SUCCESS,
                started_at=start_time,
                completed_at=datetime.utcnow(),
                output={
                    "podcast_plan": plan.to_dict(),
                    "episode_profile": episode_profile,
                    "speaker_profile": speaker_profile,
                    "recommendations": {
                        "format": format_type.value,
                        "num_speakers": plan.num_speakers,
                        "estimated_duration": plan.estimated_duration,
                        "target_audience": self.audience,
                    },
                    "next_steps": [
                        "Save episode_profile to database",
                        "Save speaker_profile to database",
                        "Use profiles with podcast generation API"
                    ]
                }
            )

        except Exception as e:
            logger.error(f"Podcast planning failed: {e}")
            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.FAILED,
                started_at=start_time,
                completed_at=datetime.utcnow(),
                error_message=str(e)
            )


# Convenience functions
async def plan_podcast(
    notebook_id: str,
    preferred_duration: int = 15,
    preferred_format: Optional[str] = None,
    audience: str = "general"
) -> Optional[PodcastPlan]:
    """Plan a podcast episode for a notebook.

    Args:
        notebook_id: Notebook ID
        preferred_duration: Target duration in minutes
        preferred_format: Force specific format (optional)
        audience: Target audience level

    Returns:
        PodcastPlan or None if failed
    """
    config = SkillConfig(
        skill_type="auto_podcast_planner",
        name="Plan Podcast",
        parameters={
            "notebook_id": notebook_id,
            "preferred_duration": preferred_duration,
            "preferred_format": preferred_format,
            "audience": audience,
        }
    )

    planner = AutoPodcastPlanner(config)

    from open_notebook.skills.base import SkillContext
    ctx = SkillContext(
        skill_id=f"podcast_plan_{datetime.utcnow().timestamp()}",
        trigger_type="manual"
    )

    result = await planner.run(ctx)

    if result.success and result.output.get("podcast_plan"):
        plan_data = result.output["podcast_plan"]
        return PodcastPlan(
            format_type=PodcastFormat(plan_data["format_type"]),
            content_type=ContentType(plan_data["content_type"]),
            num_speakers=plan_data["num_speakers"],
            title=plan_data["title"],
            hook=plan_data["hook"],
            description=plan_data["description"],
            estimated_duration=plan_data["estimated_duration"],
            segments=plan_data.get("segments", []),
            speakers=[
                SpeakerRole(**s) for s in plan_data.get("speakers", [])
            ],
            tone=plan_data.get("tone", "conversational"),
            pacing=plan_data.get("pacing", "moderate"),
            music_suggestions=plan_data.get("music_suggestions", []),
        )

    return None


async def suggest_podcast_formats(
    notebook_id: str
) -> List[Dict[str, Any]]:
    """Suggest suitable podcast formats for notebook content.

    Args:
        notebook_id: Notebook ID

    Returns:
        List of format suggestions with scores
    """
    notebook = await Notebook.get(notebook_id)
    if not notebook:
        return []

    sources = await notebook.get_sources()
    if not sources:
        return []

    config = SkillConfig(
        skill_type="auto_podcast_planner",
        name="Suggest Formats",
        parameters={"notebook_id": notebook_id}
    )

    planner = AutoPodcastPlanner(config)
    analysis = await planner._analyze_content(sources)

    # Score each format
    content_type = analysis.get("content_type", "general")
    has_arguments = analysis.get("has_arguments", False)
    narrative_style = analysis.get("narrative_style", False)
    controversial = analysis.get("controversial_elements", False)

    format_scores = [
        {
            "format": "interview",
            "score": 0.9 if content_type == "opinion" else 0.7,
            "speakers": 2,
            "description": "Host interviews an expert - great for opinion and analysis content"
        },
        {
            "format": "panel_discussion",
            "score": 0.9 if content_type == "technical" else 0.6,
            "speakers": 3,
            "description": "Multiple experts discuss topics - ideal for technical and complex subjects"
        },
        {
            "format": "debate",
            "score": 0.9 if has_arguments and controversial else 0.5,
            "speakers": 2,
            "description": "Two sides present opposing views - perfect for controversial topics"
        },
        {
            "format": "storytelling",
            "score": 0.9 if narrative_style else 0.5,
            "speakers": 2,
            "description": "Narrative-driven exploration - great for stories and news"
        },
        {
            "format": "solo_monologue",
            "score": 0.8 if content_type in ["tutorial", "educational"] else 0.6,
            "speakers": 1,
            "description": "Single expert narrator - ideal for tutorials and explanations"
        },
        {
            "format": "educational",
            "score": 0.9 if content_type == "tutorial" else 0.6,
            "speakers": 1,
            "description": "Structured lesson format - perfect for learning content"
        },
    ]

    # Sort by score
    format_scores.sort(key=lambda x: x["score"], reverse=True)
    return format_scores


# Register the skill
register_skill(AutoPodcastPlanner)
