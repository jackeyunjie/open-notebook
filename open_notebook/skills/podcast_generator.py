"""Podcast Generator Skill - AI-powered podcast creation for Open Notebook.

This skill provides comprehensive podcast generation capabilities:
1. Content analysis and format selection
2. Speaker configuration and role assignment
3. Outline and transcript generation
4. Audio synthesis via TTS
5. Multi-format support (solo, interview, panel, debate, etc.)

Usage:
    config = SkillConfig(
        skill_type="podcast_generator",
        name="Trading Podcast Generator",
        parameters={
            "content": "交易知识库内容...",
            "format": "educational",
            "speakers": 2,
            "duration": 15,
            "style": "professional"
        }
    )
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

from open_notebook.skills.base import Skill, SkillConfig, SkillContext, SkillResult, SkillStatus
from open_notebook.skills.registry import register_skill


class PodcastFormat(Enum):
    """Podcast format types."""
    SOLO = "solo"                    # Single narrator
    INTERVIEW = "interview"          # Host + guest
    PANEL = "panel"                  # Multiple experts
    DEBATE = "debate"                # Two sides
    STORYTELLING = "storytelling"    # Narrative style
    EDUCATIONAL = "educational"      # Tutorial style
    TRADING_ANALYSIS = "trading_analysis"  # Market commentary


class PodcastStyle(Enum):
    """Podcast presentation styles."""
    PROFESSIONAL = "professional"    # Formal, analytical
    CONVERSATIONAL = "conversational"  # Casual, friendly
    ENTHUSIASTIC = "enthusiastic"    # Energetic, engaging
    CALM = "calm"                    # Relaxed, thoughtful
    TRADING_MENTOR = "trading_mentor"  # Experienced guide


@dataclass
class SpeakerConfig:
    """Speaker configuration."""
    name: str
    role: str  # host, expert, novice, skeptic, narrator
    personality: str
    voice_type: Optional[str] = None
    speaking_style: str = "conversational"


@dataclass
class PodcastConfig:
    """Complete podcast configuration."""
    title: str
    format: PodcastFormat
    style: PodcastStyle
    duration_minutes: int
    speakers: List[SpeakerConfig]
    hook: str = ""  # Opening hook
    outline: List[Dict] = field(default_factory=list)
    target_audience: str = "general"
    language: str = "zh-CN"


class PodcastGeneratorSkill(Skill):
    """Generate professional podcasts from content.

    Creates engaging audio content from text sources with:
    - Smart format selection based on content type
    - Multi-speaker conversation design
    - Trading-specific optimizations
    - Integration with ON podcast service

    Parameters:
        - content: Source text content or notebook_id
        - title: Podcast episode title
        - format: Podcast format (solo/interview/panel/debate/storytelling/educational)
        - style: Presentation style (professional/conversational/enthusiastic/calm)
        - duration: Target duration in minutes (default: 15)
        - speakers: Number of speakers (default: auto-detect)
        - target_audience: Audience level (beginner/intermediate/advanced)
        - language: Output language (zh-CN/en-US)
        - generate_audio: Whether to generate audio file (default: True)

    Example:
        config = SkillConfig(
            skill_type="podcast_generator",
            name="交易播客生成",
            parameters={
                "content": "趋势交易核心原则...",
                "title": "趋势交易入门指南",
                "format": "educational",
                "style": "trading_mentor",
                "duration": 20,
                "target_audience": "beginner"
            }
        )
    """

    skill_type = "podcast_generator"
    name = "Podcast Generator"
    description = "Generate professional podcasts from content with multiple formats and styles"

    parameters_schema = {
        "content": {
            "type": "string",
            "description": "Source content text or notebook_id"
        },
        "title": {
            "type": "string",
            "description": "Podcast episode title"
        },
        "format": {
            "type": "string",
            "enum": ["solo", "interview", "panel", "debate", "storytelling", "educational", "trading_analysis"],
            "default": "educational",
            "description": "Podcast format type"
        },
        "style": {
            "type": "string",
            "enum": ["professional", "conversational", "enthusiastic", "calm", "trading_mentor"],
            "default": "conversational",
            "description": "Presentation style"
        },
        "duration": {
            "type": "integer",
            "default": 15,
            "description": "Target duration in minutes"
        },
        "speakers": {
            "type": "integer",
            "default": 2,
            "description": "Number of speakers (1-4)"
        },
        "target_audience": {
            "type": "string",
            "enum": ["beginner", "intermediate", "advanced"],
            "default": "intermediate",
            "description": "Target audience level"
        },
        "language": {
            "type": "string",
            "default": "zh-CN",
            "description": "Output language"
        },
        "generate_audio": {
            "type": "boolean",
            "default": True,
            "description": "Generate audio file"
        },
        "on_api_url": {
            "type": "string",
            "default": "http://localhost:5055",
            "description": "Open Notebook API URL"
        }
    }

    # Trading-specific speaker templates
    TRADING_SPEAKERS = {
        "mentor": {
            "name": "老张",
            "role": "expert",
            "personality": "20年交易经验，稳健型选手，善于把复杂概念简单化",
            "speaking_style": "耐心、循循善诱、常举例说明"
        },
        "host": {
            "name": "小李",
            "role": "host",
            "personality": "好奇、善于提问、代表新手视角",
            "speaking_style": "活泼、经常追问、表达疑惑"
        },
        "skeptic": {
            "name": "老王",
            "role": "skeptic",
            "personality": "谨慎、风控意识强、喜欢挑战观点",
            "speaking_style": "直接、质疑、强调风险"
        },
        "analyst": {
            "name": "陈老师",
            "role": "analyst",
            "personality": "数据驱动、逻辑严密、量化背景",
            "speaking_style": "严谨、喜欢用数据说话"
        }
    }

    def __init__(self, config: SkillConfig):
        self.content: str = config.parameters.get("content", "")
        self.title: str = config.parameters.get("title", "Untitled Podcast")
        self.format: str = config.parameters.get("format", "educational")
        self.style: str = config.parameters.get("style", "conversational")
        self.duration: int = config.parameters.get("duration", 15)
        self.speakers_count: int = config.parameters.get("speakers", 2)
        self.target_audience: str = config.parameters.get("target_audience", "intermediate")
        self.language: str = config.parameters.get("language", "zh-CN")
        self.generate_audio: bool = config.parameters.get("generate_audio", True)
        self.on_api_url: str = config.parameters.get("on_api_url", "http://localhost:5055")
        super().__init__(config)

    def _validate_config(self) -> None:
        """Validate configuration."""
        super()._validate_config()

        if not self.content:
            raise ValueError("content is required for podcast generation")

        if self.speakers_count < 1 or self.speakers_count > 4:
            raise ValueError("speakers must be between 1 and 4")

    def _detect_format(self) -> PodcastFormat:
        """Auto-detect best format from content."""
        content_lower = self.content.lower()

        # Check content characteristics
        has_opposing_views = any(kw in content_lower for kw in ["vs", "对比", "优劣", "正反"])
        has_story = any(kw in content_lower for kw in ["案例", "故事", "经历", "从...到"])
        has_tutorial = any(kw in content_lower for kw in ["步骤", "方法", "如何", "教程"])
        is_trading = any(kw in content_lower for kw in ["交易", "股票", "期货", "策略"])

        if has_opposing_views:
            return PodcastFormat.DEBATE
        elif has_story:
            return PodcastFormat.STORYTELLING
        elif has_tutorial:
            return PodcastFormat.EDUCATIONAL
        elif is_trading and self.speakers_count == 1:
            return PodcastFormat.TRADING_ANALYSIS
        elif self.speakers_count == 1:
            return PodcastFormat.SOLO
        elif self.speakers_count == 2:
            return PodcastFormat.INTERVIEW
        else:
            return PodcastFormat.PANEL

    def _create_speakers(self) -> List[SpeakerConfig]:
        """Create speaker configurations."""
        speakers = []

        if self.format == "trading_analysis" or self.style == "trading_mentor":
            # Use trading-specific speakers
            if self.speakers_count == 1:
                speakers.append(SpeakerConfig(**self.TRADING_SPEAKERS["mentor"]))
            elif self.speakers_count == 2:
                speakers.append(SpeakerConfig(**self.TRADING_SPEAKERS["mentor"]))
                speakers.append(SpeakerConfig(**self.TRADING_SPEAKERS["host"]))
            elif self.speakers_count == 3:
                speakers.append(SpeakerConfig(**self.TRADING_SPEAKERS["mentor"]))
                speakers.append(SpeakerConfig(**self.TRADING_SPEAKERS["host"]))
                speakers.append(SpeakerConfig(**self.TRADING_SPEAKERS["skeptic"]))
            else:
                speakers.append(SpeakerConfig(**self.TRADING_SPEAKERS["mentor"]))
                speakers.append(SpeakerConfig(**self.TRADING_SPEAKERS["host"]))
                speakers.append(SpeakerConfig(**self.TRADING_SPEAKERS["skeptic"]))
                speakers.append(SpeakerConfig(**self.TRADING_SPEAKERS["analyst"]))
        else:
            # Generic speakers
            roles = ["Host", "Guest 1", "Guest 2", "Guest 3"]
            for i in range(self.speakers_count):
                speakers.append(SpeakerConfig(
                    name=roles[i],
                    role="host" if i == 0 else "expert",
                    personality=f"Speaker {i+1}",
                    speaking_style="conversational"
                ))

        return speakers

    def _generate_hook(self) -> str:
        """Generate opening hook."""
        hooks = {
            "trading_analysis": [
                "你有没有想过，为什么同样的市场，有人赚有人亏？",
                "今天我们要聊一个让无数交易员彻夜难眠的话题。",
                "如果有一种方法，能让你在市场中少踩80%的坑，你想知道吗？"
            ],
            "educational": [
                "今天我们来彻底搞懂一个很多人搞错的概念。",
                "新手最容易在这件事上栽跟头，今天一次性说清楚。",
                "这可能是你交易生涯中最重要的15分钟。"
            ],
            "interview": [
                "今天我们请来了一位真正经历过市场大风大浪的老手。",
                "我旁边这位，用10年时间摸索出一套自己的方法。"
            ],
            "debate": [
                "关于这个话题，市场上一直有两种声音，今天我们让它们碰撞一下。",
                "有人认为这是机会，有人认为是陷阱，你怎么看？"
            ]
        }

        import random
        format_hooks = hooks.get(self.format, hooks["educational"])
        return random.choice(format_hooks)

    def _create_outline(self) -> List[Dict]:
        """Create podcast outline."""
        # Calculate segment durations
        intro_time = 1
        outro_time = 1
        main_time = self.duration - intro_time - outro_time

        outline = [
            {
                "segment": "intro",
                "duration": intro_time,
                "content": f"开场钩子 + 主题介绍 - {self.title}",
                "speaker": "host"
            },
            {
                "segment": "main_content",
                "duration": main_time,
                "content": "核心内容展开，互动讨论",
                "speaker": "all"
            },
            {
                "segment": "outro",
                "duration": outro_time,
                "content": "总结要点 + 行动建议 + 结束语",
                "speaker": "host"
            }
        ]

        return outline

    async def _call_on_podcast_api(self, config: PodcastConfig) -> Dict:
        """Call ON podcast generation API."""
        try:
            # Map to ON episode profile
            episode_profile = self._map_to_on_profile(config)

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.on_api_url}/podcasts/generate",
                    json={
                        "episode_profile": episode_profile,
                        "content": self.content,
                        "title": config.title,
                        "language": config.language
                    },
                    timeout=300.0  # 5 minutes for generation
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"ON API error: {response.status_code} - {response.text}")
                    return {"error": f"API error: {response.status_code}"}

        except Exception as e:
            logger.error(f"Failed to call ON API: {e}")
            return {"error": str(e)}

    def _map_to_on_profile(self, config: PodcastConfig) -> str:
        """Map our config to ON episode profile name."""
        # Use ON's predefined profiles
        if config.format == PodcastFormat.EDUCATIONAL:
            return "educational" if self.language == "en-US" else "教育讲解"
        elif config.format == PodcastFormat.INTERVIEW:
            return "interview" if self.language == "en-US" else "深度访谈"
        elif config.format == PodcastFormat.DEBATE:
            return "debate" if self.language == "en-US" else "观点辩论"
        elif config.format == PodcastFormat.SOLO:
            return "solo" if self.language == "en-US" else "专家独白"
        else:
            return "default"

    async def _generate_transcript(self, config: PodcastConfig) -> str:
        """Generate podcast transcript using LLM."""
        # Create prompt for transcript generation
        prompt = self._build_transcript_prompt(config)

        # Call LLM (simplified - would use ON's model provision)
        # For now, return a structured template
        return f"""# {config.title}

## 开场 ({config.speakers[0].name})
{config.hook}

大家好，欢迎收听今天的节目。我是{config.speakers[0].name}。
{f"今天和我一起的是{config.speakers[1].name}。" if len(config.speakers) > 1 else ""}

今天我们要聊的话题是：{self.title}

## 主要内容

[基于以下内容生成对话：]

{self.content[:1000]}...

## 总结与行动建议

今天我们讨论了{self.title}的核心要点：
1. [要点1]
2. [要点2]
3. [要点3]

希望对你有所帮助，我们下期再见！
"""

    def _build_transcript_prompt(self, config: PodcastConfig) -> str:
        """Build prompt for transcript generation."""
        speakers_desc = "\n".join([
            f"- {s.name} ({s.role}): {s.personality}, 说话风格：{s.speaking_style}"
            for s in config.speakers
        ])

        return f"""请根据以下内容，生成一段{config.duration_minutes}分钟的播客对话。

主题：{config.title}
格式：{config.format.value}
风格：{config.style.value}
目标听众：{config.target_audience}

说话人设定：
{speakers_desc}

原始内容：
{self.content}

要求：
1. 用中文对话形式呈现
2. 要有自然的互动和提问
3. 包含具体例子和数据
4. 结尾给出可执行的行动建议
5. 总字数约{config.duration_minutes * 150}字
"""

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute podcast generation."""
        logger.info(f"Starting podcast generation: {self.title}")
        start_time = datetime.utcnow()

        try:
            # Step 1: Auto-detect format if not specified
            if self.format == "educational" and len(self.content) > 500:
                detected_format = self._detect_format()
                logger.info(f"Auto-detected format: {detected_format.value}")
            else:
                detected_format = PodcastFormat(self.format)

            # Step 2: Create speaker configuration
            speakers = self._create_speakers()

            # Step 3: Generate hook and outline
            hook = self._generate_hook()
            outline = self._create_outline()

            # Step 4: Build podcast config
            config = PodcastConfig(
                title=self.title,
                format=detected_format,
                style=PodcastStyle(self.style),
                duration_minutes=self.duration,
                speakers=speakers,
                hook=hook,
                outline=outline,
                target_audience=self.target_audience,
                language=self.language
            )

            # Step 5: Generate transcript
            logger.info("Generating transcript...")
            transcript = await self._generate_transcript(config)

            # Step 6: Call ON API for audio generation (if enabled)
            audio_result = None
            if self.generate_audio:
                logger.info("Requesting audio generation...")
                audio_result = await self._call_on_podcast_api(config)

            # Build output
            output = {
                "title": config.title,
                "format": config.format.value,
                "style": config.style.value,
                "duration": config.duration_minutes,
                "speakers": [
                    {
                        "name": s.name,
                        "role": s.role,
                        "personality": s.personality
                    }
                    for s in config.speakers
                ],
                "hook": config.hook,
                "outline": config.outline,
                "transcript": transcript,
                "audio_job": audio_result,
                "target_audience": config.target_audience,
                "language": config.language
            }

            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.SUCCESS,
                started_at=start_time,
                completed_at=datetime.utcnow(),
                output=output
            )

        except Exception as e:
            logger.error(f"Podcast generation failed: {e}")
            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.FAILED,
                started_at=start_time,
                completed_at=datetime.utcnow(),
                error_message=str(e)
            )


# Convenience function for direct usage
async def generate_podcast(
    content: str,
    title: str,
    format: str = "educational",
    style: str = "trading_mentor",
    duration: int = 15,
    speakers: int = 2,
    language: str = "zh-CN"
) -> Dict:
    """Quick podcast generation function.

    Args:
        content: Source content
        title: Podcast title
        format: Podcast format
        style: Presentation style
        duration: Duration in minutes
        speakers: Number of speakers
        language: Language code

    Returns:
        Podcast generation result
    """
    config = SkillConfig(
        skill_type="podcast_generator",
        name="Quick Podcast Generator",
        parameters={
            "content": content,
            "title": title,
            "format": format,
            "style": style,
            "duration": duration,
            "speakers": speakers,
            "language": language
        }
    )

    skill = PodcastGeneratorSkill(config)

    from open_notebook.skills.base import SkillContext
    ctx = SkillContext(
        skill_id=f"podcast_{datetime.utcnow().timestamp()}",
        trigger_type="manual"
    )

    result = await skill.run(ctx)
    return result.output if result.success else {"error": result.error_message}


# Register the skill
register_skill(PodcastGeneratorSkill)
