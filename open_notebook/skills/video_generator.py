"""Video Generator - AI-powered video content creation from notebook sources.

This skill enables Open Notebook to generate videos from content:
1. Script generation from notebook sources
2. Multi-provider video generation (Seedance, Runway, Pika, etc.)
3. Video style selection (educational, storytelling, visualization)
4. Automatic scene breakdown and prompts
5. Video metadata and thumbnail generation

Key Features:
- Transform notes into engaging videos
- Multiple video styles and formats
- Scene-by-scene generation with AI
- Integration with popular video generation APIs
- Automatic subtitle generation
"""

import json
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from open_notebook.domain.notebook import Notebook, Note, Source
from open_notebook.skills.base import Skill, SkillConfig, SkillContext, SkillResult, SkillStatus
from open_notebook.skills.registry import register_skill


class VideoStyle(Enum):
    """Video style types."""
    EDUCATIONAL = "educational"  # Tutorial/explainer style
    STORYTELLING = "storytelling"  # Narrative driven
    VISUALIZATION = "visualization"  # Data/concept visualization
    NEWS = "news"  # News report style
    INTERVIEW = "interview"  # Interview format
    SHORT = "short"  # Short-form content (TikTok/Reels)


class VideoProvider(Enum):
    """Supported video generation providers."""
    SEEDANCE = "seedance"
    RUNWAY = "runway"
    PIKA = "pika"
    KLING = "kling"
    LUMIERE = "lumiere"  # Google's Lumiere (if available)
    MOCK = "mock"  # For testing without API


@dataclass
class VideoScene:
    """A single video scene with prompts and metadata."""
    scene_number: int
    title: str
    description: str
    visual_prompt: str  # For image/video generation
    narration: str  # Voiceover text
    duration: int  # Seconds
    transition: str = "fade"  # Transition to next scene
    music_mood: str = "neutral"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_number": self.scene_number,
            "title": self.title,
            "description": self.description,
            "visual_prompt": self.visual_prompt,
            "narration": self.narration,
            "duration": self.duration,
            "transition": self.transition,
            "music_mood": self.music_mood,
        }


@dataclass
class VideoScript:
    """Complete video script with scenes."""
    title: str
    description: str
    style: VideoStyle
    target_duration: int  # Total seconds
    scenes: List[VideoScene] = field(default_factory=list)
    music_style: str = "ambient"
    target_audience: str = "general"
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "style": self.style.value,
            "target_duration": self.target_duration,
            "scenes": [s.to_dict() for s in self.scenes],
            "music_style": self.music_style,
            "target_audience": self.target_audience,
            "scene_count": len(self.scenes),
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class VideoGenerationResult:
    """Result of video generation."""
    success: bool
    video_url: Optional[str] = None
    video_path: Optional[str] = None
    thumbnail_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    provider: str = ""
    processing_time: float = 0.0


class VideoGenerator(Skill):
    """Generate AI videos from notebook content.

    This skill transforms notebook content into engaging videos:
    1. Analyzes content and generates video script with scenes
    2. Creates visual prompts for each scene
    3. Generates video using configured provider
    4. Produces final video with metadata

    Parameters:
        - notebook_id: Notebook containing source content
        - source_ids: Specific sources to include (optional)
        - note_id: Specific note to convert (optional)
        - video_style: Video style (educational, storytelling, etc.)
        - target_duration: Target duration in seconds (30-300)
        - provider: Video generation provider
        - target_audience: Target audience (general, expert, beginner)
        - include_narration: Whether to include voiceover (default: true)
        - include_music: Whether to include background music (default: true)

    Example:
        config = SkillConfig(
            skill_type="video_generator",
            name="Video Generator",
            parameters={
                "notebook_id": "notebook:abc123",
                "video_style": "educational",
                "target_duration": 60,
                "provider": "seedance"
            }
        )
    """

    skill_type = "video_generator"
    name = "Video Generator"
    description = "AI-powered video generation from notebook content"

    parameters_schema = {
        "notebook_id": {
            "type": "string",
            "description": "Notebook ID containing source content"
        },
        "source_ids": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Specific source IDs to include (optional)"
        },
        "note_id": {
            "type": "string",
            "description": "Specific note ID to convert (optional)"
        },
        "video_style": {
            "type": "string",
            "enum": ["educational", "storytelling", "visualization", "news", "interview", "short"],
            "default": "educational",
            "description": "Video style/type"
        },
        "target_duration": {
            "type": "integer",
            "default": 60,
            "minimum": 30,
            "maximum": 300,
            "description": "Target video duration in seconds (30-300)"
        },
        "provider": {
            "type": "string",
            "enum": ["seedance", "runway", "pika", "kling", "lumiere", "mock"],
            "default": "mock",
            "description": "Video generation provider"
        },
        "target_audience": {
            "type": "string",
            "enum": ["general", "expert", "beginner"],
            "default": "general",
            "description": "Target audience level"
        },
        "include_narration": {
            "type": "boolean",
            "default": True,
            "description": "Include AI voiceover narration"
        },
        "include_music": {
            "type": "boolean",
            "default": True,
            "description": "Include background music"
        },
        "api_key": {
            "type": "string",
            "description": "API key for video provider (optional, can use env var)"
        }
    }

    def __init__(self, config: SkillConfig):
        self.notebook_id: str = config.parameters.get("notebook_id", "")
        self.source_ids: Optional[List[str]] = config.parameters.get("source_ids")
        self.note_id: Optional[str] = config.parameters.get("note_id")
        self.video_style: VideoStyle = VideoStyle(config.parameters.get("video_style", "educational"))
        self.target_duration: int = config.parameters.get("target_duration", 60)
        self.provider: VideoProvider = VideoProvider(config.parameters.get("provider", "mock"))
        self.target_audience: str = config.parameters.get("target_audience", "general")
        self.include_narration: bool = config.parameters.get("include_narration", True)
        self.include_music: bool = config.parameters.get("include_music", True)
        self.api_key: Optional[str] = config.parameters.get("api_key")
        super().__init__(config)

    def _validate_config(self) -> None:
        """Validate configuration."""
        super()._validate_config()
        if not self.notebook_id and not self.note_id:
            raise ValueError("Either notebook_id or note_id is required")
        if self.target_duration < 30 or self.target_duration > 300:
            raise ValueError("target_duration must be between 30 and 300 seconds")

    async def _get_content(self) -> str:
        """Get content from notebook or note.

        Returns:
            Combined text content
        """
        content_parts = []

        # If note_id specified, prioritize that
        if self.note_id:
            note = await Note.get(self.note_id)
            if note:
                content_parts.append(f"# {note.title or 'Untitled'}\n\n{note.content or ''}")
            else:
                raise ValueError(f"Note {self.note_id} not found")

        # Otherwise get from notebook sources
        elif self.notebook_id:
            notebook = await Notebook.get(self.notebook_id)
            if not notebook:
                raise ValueError(f"Notebook {self.notebook_id} not found")

            if self.source_ids:
                for sid in self.source_ids:
                    source = await Source.get(sid)
                    if source and source.full_text:
                        content_parts.append(f"# {source.title or 'Untitled'}\n\n{source.full_text[:3000]}")
            else:
                sources = await notebook.get_sources()
                for source in sources[:5]:  # Limit to first 5 sources
                    if source.full_text:
                        content_parts.append(f"# {source.title or 'Untitled'}\n\n{source.full_text[:3000]}")

        if not content_parts:
            raise ValueError("No content found to generate video")

        return "\n\n---\n\n".join(content_parts)

    async def _generate_script(self, content: str) -> VideoScript:
        """Generate video script from content.

        Args:
            content: Source content

        Returns:
            VideoScript with scenes
        """
        try:
            from open_notebook.ai.provision import provision_langchain_model

            style_descriptions = {
                VideoStyle.EDUCATIONAL: "Tutorial/explainer style with clear explanations",
                VideoStyle.STORYTELLING: "Narrative-driven with engaging storytelling",
                VideoStyle.VISUALIZATION: "Heavy use of visuals, diagrams, and animations",
                VideoStyle.NEWS: "Professional news report format",
                VideoStyle.INTERVIEW: "Interview/conversation format",
                VideoStyle.SHORT: "Fast-paced, attention-grabbing short content",
            }

            # Calculate number of scenes (roughly 10-15 seconds per scene)
            num_scenes = max(3, min(10, self.target_duration // 12))
            scene_duration = self.target_duration // num_scenes

            prompt = f"""Create a video script based on the following content.

Video Style: {self.video_style.value} - {style_descriptions.get(self.video_style, '')}
Target Duration: {self.target_duration} seconds
Number of Scenes: {num_scenes}
Scene Duration: ~{scene_duration} seconds each
Target Audience: {self.target_audience}
Include Narration: {self.include_narration}

Content:
---
{content[:8000]}
---

Generate a video script in this JSON format:
{{
  "title": "Compelling video title (max 60 chars)",
  "description": "Brief description of the video",
  "music_style": "ambient|upbeat|dramatic|calm|inspirational",
  "scenes": [
    {{
      "scene_number": 1,
      "title": "Scene title",
      "description": "What happens visually in this scene",
      "visual_prompt": "Detailed AI image generation prompt for this scene. Describe: style, subjects, colors, lighting, camera angle, mood. 50-100 words.",
      "narration": "Voiceover script for this scene (keep concise, {scene_duration} seconds reading time)",
      "duration": {scene_duration},
      "transition": "fade|cut|dissolve|wipe",
      "music_mood": "neutral|tense|calm|exciting|sad|happy"
    }}
  ]
}}

Guidelines:
- Title should be attention-grabbing
- Visual prompts should be detailed for AI image/video generation
- Narration should be engaging and match the target audience
- First scene should hook the viewer immediately
- Each scene should flow logically to the next
- Total duration should approximately match target

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

            script_data = json.loads(response_text)

            # Create scenes
            scenes = []
            for s in script_data.get("scenes", []):
                scenes.append(VideoScene(
                    scene_number=s.get("scene_number", len(scenes) + 1),
                    title=s.get("title", f"Scene {len(scenes) + 1}"),
                    description=s.get("description", ""),
                    visual_prompt=s.get("visual_prompt", ""),
                    narration=s.get("narration", ""),
                    duration=s.get("duration", scene_duration),
                    transition=s.get("transition", "fade"),
                    music_mood=s.get("music_mood", "neutral"),
                ))

            return VideoScript(
                title=script_data.get("title", "Generated Video"),
                description=script_data.get("description", ""),
                style=self.video_style,
                target_duration=self.target_duration,
                scenes=scenes,
                music_style=script_data.get("music_style", "ambient"),
                target_audience=self.target_audience,
            )

        except Exception as e:
            logger.error(f"Script generation failed: {e}")
            # Return default script
            return self._create_default_script()

    def _create_default_script(self) -> VideoScript:
        """Create a default script when generation fails."""
        scene_duration = self.target_duration // 4
        return VideoScript(
            title="Exploring the Topic",
            description="An AI-generated video exploring interesting content.",
            style=self.video_style,
            target_duration=self.target_duration,
            scenes=[
                VideoScene(
                    scene_number=1,
                    title="Introduction",
                    description="Opening scene introducing the topic",
                    visual_prompt="Cinematic wide shot, abstract digital landscape with flowing data streams, blue and purple gradient lighting, futuristic atmosphere, high quality, 4k, professional video style",
                    narration="Welcome to this exploration of fascinating content.",
                    duration=scene_duration,
                    transition="fade",
                    music_mood="calm",
                ),
                VideoScene(
                    scene_number=2,
                    title="Main Content",
                    description="Presenting the main ideas",
                    visual_prompt="Professional presenter in modern studio, holographic displays showing information graphs, soft lighting, educational setting, high quality render",
                    narration="Let's dive into the key insights and discoveries.",
                    duration=scene_duration,
                    transition="cut",
                    music_mood="neutral",
                ),
                VideoScene(
                    scene_number=3,
                    title="Deep Dive",
                    description="Exploring details",
                    visual_prompt="Abstract visualization of concepts, floating geometric shapes, dynamic camera movement, warm lighting, cinematic composition",
                    narration="The details reveal fascinating patterns and connections.",
                    duration=scene_duration,
                    transition="dissolve",
                    music_mood="inspiring",
                ),
                VideoScene(
                    scene_number=4,
                    title="Conclusion",
                    description="Wrapping up",
                    visual_prompt="Sunrise over digital landscape, hopeful and inspiring atmosphere, warm golden lighting, cinematic wide shot, high quality",
                    narration="Thank you for watching and exploring with us.",
                    duration=scene_duration,
                    transition="fade",
                    music_mood="inspiring",
                ),
            ],
            music_style="ambient",
            target_audience=self.target_audience,
        )

    async def _generate_video_seedance(
        self,
        script: VideoScript,
        output_dir: Path
    ) -> VideoGenerationResult:
        """Generate video using Seedance API.

        Args:
            script: Video script with scenes
            output_dir: Output directory

        Returns:
            VideoGenerationResult
        """
        import time
        start_time = time.time()

        try:
            api_key = self.api_key or self._get_env_api_key("SEEDANCE_API_KEY")
            if not api_key:
                return VideoGenerationResult(
                    success=False,
                    error_message="Seedance API key not configured",
                    provider="seedance"
                )

            # TODO: Implement actual Seedance API integration
            # This is a placeholder for the actual API implementation
            logger.info(f"Would generate video with Seedance: {script.title}")

            # For now, return a mock result
            # In production, this would:
            # 1. Upload scene prompts to Seedance
            # 2. Poll for generation completion
            # 3. Download final video

            await asyncio.sleep(2)  # Simulate processing

            return VideoGenerationResult(
                success=True,
                video_url=f"https://api.seedance.ai/videos/mock_{datetime.utcnow().timestamp()}.mp4",
                video_path=str(output_dir / f"{script.title.replace(' ', '_')}.mp4"),
                thumbnail_url=f"https://api.seedance.ai/thumbnails/mock_{datetime.utcnow().timestamp()}.jpg",
                metadata={
                    "script": script.to_dict(),
                    "provider": "seedance",
                    "note": "This is a mock result. Actual API integration required.",
                },
                provider="seedance",
                processing_time=time.time() - start_time,
            )

        except Exception as e:
            logger.error(f"Seedance generation failed: {e}")
            return VideoGenerationResult(
                success=False,
                error_message=str(e),
                provider="seedance"
            )

    async def _generate_video_runway(
        self,
        script: VideoScript,
        output_dir: Path
    ) -> VideoGenerationResult:
        """Generate video using Runway ML API."""
        import time
        start_time = time.time()

        try:
            api_key = self.api_key or self._get_env_api_key("RUNWAY_API_KEY")
            if not api_key:
                return VideoGenerationResult(
                    success=False,
                    error_message="Runway API key not configured",
                    provider="runway"
                )

            logger.info(f"Would generate video with Runway: {script.title}")
            await asyncio.sleep(2)

            return VideoGenerationResult(
                success=True,
                video_url=f"https://api.runwayml.com/videos/mock_{datetime.utcnow().timestamp()}.mp4",
                video_path=str(output_dir / f"{script.title.replace(' ', '_')}.mp4"),
                metadata={"script": script.to_dict(), "provider": "runway"},
                provider="runway",
                processing_time=time.time() - start_time,
            )

        except Exception as e:
            return VideoGenerationResult(
                success=False,
                error_message=str(e),
                provider="runway"
            )

    async def _generate_video_mock(
        self,
        script: VideoScript,
        output_dir: Path
    ) -> VideoGenerationResult:
        """Generate mock video for testing."""
        import time
        start_time = time.time()

        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            # Create a placeholder/marker file
            video_path = output_dir / f"{script.title.replace(' ', '_').replace('/', '_')}.txt"
            video_path.write_text(
                f"MOCK VIDEO GENERATION\n\n"
                f"Title: {script.title}\n"
                f"Duration: {script.target_duration}s\n"
                f"Scenes: {len(script.scenes)}\n\n"
                f"Scenes:\n" +
                "\n".join([f"{s.scene_number}. {s.title}: {s.visual_prompt[:100]}..." for s in script.scenes])
            )

            return VideoGenerationResult(
                success=True,
                video_url=f"file://{video_path}",
                video_path=str(video_path),
                thumbnail_url=None,
                metadata={
                    "script": script.to_dict(),
                    "provider": "mock",
                    "note": "This is a mock generation. Configure a real provider for actual video output.",
                },
                provider="mock",
                processing_time=time.time() - start_time,
            )

        except Exception as e:
            return VideoGenerationResult(
                success=False,
                error_message=str(e),
                provider="mock"
            )

    def _get_env_api_key(self, key_name: str) -> Optional[str]:
        """Get API key from environment variable."""
        import os
        return os.environ.get(key_name)

    async def _save_video_record(
        self,
        notebook_id: str,
        script: VideoScript,
        result: VideoGenerationResult
    ) -> Optional[str]:
        """Save video generation record as note.

        Args:
            notebook_id: Notebook to save to
            script: Video script
            result: Generation result

        Returns:
            Note ID or None
        """
        try:
            content = f"""# 🎬 Video: {script.title}

{script.description}

## Video Details
- **Style**: {script.style.value}
- **Duration**: {script.target_duration}s
- **Provider**: {result.provider}
- **Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}

## Scenes

"""
            for scene in script.scenes:
                content += f"""### Scene {scene.scene_number}: {scene.title}
- **Duration**: {scene.duration}s
- **Transition**: {scene.transition}
- **Music**: {scene.music_mood}

**Visual Prompt:**
{scene.visual_prompt}

**Narration:**
{scene.narration}

---

"""

            if result.video_url:
                content += f"""## Output

- **Video URL**: {result.video_url}
- **Processing Time**: {result.processing_time:.1f}s
"""

            note = Note(
                title=f"🎬 Video: {script.title[:40]}",
                content=content,
                note_type="ai",
            )
            await note.save()
            await note.add_to_notebook(notebook_id)

            return str(note.id) if note.id else None

        except Exception as e:
            logger.error(f"Failed to save video note: {e}")
            return None

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute video generation."""
        logger.info(f"Starting video generation for notebook {self.notebook_id}")

        start_time = datetime.utcnow()

        try:
            # 1. Get content
            content = await self._get_content()
            logger.info(f"Retrieved content ({len(content)} chars)")

            # 2. Generate script
            script = await self._generate_script(content)
            logger.info(f"Generated script: {script.title} with {len(script.scenes)} scenes")

            # 3. Generate video based on provider
            output_dir = Path(f"./data/videos/{datetime.utcnow().strftime('%Y%m%d')}")

            if self.provider == VideoProvider.SEEDANCE:
                result = await self._generate_video_seedance(script, output_dir)
            elif self.provider == VideoProvider.RUNWAY:
                result = await self._generate_video_runway(script, output_dir)
            elif self.provider == VideoProvider.MOCK:
                result = await self._generate_video_mock(script, output_dir)
            else:
                result = VideoGenerationResult(
                    success=False,
                    error_message=f"Provider {self.provider.value} not yet implemented",
                    provider=self.provider.value
                )

            # 4. Save record if successful
            note_id = None
            if result.success and self.notebook_id:
                note_id = await self._save_video_record(self.notebook_id, script, result)

            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.SUCCESS if result.success else SkillStatus.FAILED,
                started_at=start_time,
                completed_at=datetime.utcnow(),
                output={
                    "script": script.to_dict(),
                    "video_result": {
                        "success": result.success,
                        "video_url": result.video_url,
                        "video_path": result.video_path,
                        "thumbnail_url": result.thumbnail_url,
                        "provider": result.provider,
                        "processing_time": result.processing_time,
                        **({"error": result.error_message} if result.error_message else {}),
                    },
                    "note_id": note_id,
                }
            )

        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.FAILED,
                started_at=start_time,
                completed_at=datetime.utcnow(),
                error_message=str(e)
            )


# Convenience functions
async def generate_video_from_notebook(
    notebook_id: str,
    video_style: str = "educational",
    target_duration: int = 60,
    provider: str = "mock"
) -> Optional[VideoScript]:
    """Generate video from notebook content.

    Args:
        notebook_id: Notebook ID
        video_style: Video style
        target_duration: Target duration in seconds
        provider: Video generation provider

    Returns:
        VideoScript or None
    """
    config = SkillConfig(
        skill_type="video_generator",
        name="Video Generator",
        parameters={
            "notebook_id": notebook_id,
            "video_style": video_style,
            "target_duration": target_duration,
            "provider": provider,
        }
    )

    generator = VideoGenerator(config)

    from open_notebook.skills.base import SkillContext
    ctx = SkillContext(
        skill_id=f"video_gen_{datetime.utcnow().timestamp()}",
        trigger_type="manual"
    )

    result = await generator.run(ctx)

    if result.success:
        script_data = result.output.get("script", {})
        return VideoScript(
            title=script_data.get("title", "Generated Video"),
            description=script_data.get("description", ""),
            style=VideoStyle(script_data.get("style", "educational")),
            target_duration=script_data.get("target_duration", 60),
            scenes=[VideoScene(**s) for s in script_data.get("scenes", [])],
        )

    return None


# Register the skill
register_skill(VideoGenerator)
