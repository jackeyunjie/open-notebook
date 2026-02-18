"""Content Creation Workflow - Topic Selection, Material Collection, Copywriting, Distribution.

This module provides a complete workflow for content creation:
1. Topic Selection (选题) - AI-assisted topic discovery and selection
2. Material Collection (素材) - Gather relevant content and references
3. Copywriting (文案) - Generate platform-optimized copy
4. Distribution (分发) - Multi-platform content distribution
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

from loguru import logger

from .platform_content_optimizer import PlatformContentOptimizer, PlatformType


class WorkflowStage(Enum):
    """Content creation workflow stages."""
    TOPIC_SELECTION = "topic_selection"
    MATERIAL_COLLECTION = "material_collection"
    COPYWRITING = "copywriting"
    DISTRIBUTION = "distribution"
    ANALYSIS = "analysis"


@dataclass
class Topic:
    """Content topic."""
    id: str
    title: str
    description: str
    category: str
    keywords: List[str]
    target_audience: str
    estimated_engagement: str
    trend_score: float  # 0-100
    competition_level: str  # low/medium/high
    source_platforms: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Material:
    """Content material/reference."""
    id: str
    source: str
    source_platform: str
    title: str
    content: str
    url: str
    author: str = ""
    engagement_metrics: Dict[str, int] = field(default_factory=dict)
    relevance_score: float = 0.0
    tags: List[str] = field(default_factory=list)
    collected_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Copywriting:
    """Generated copy for a platform."""
    platform: str
    platform_name: str
    title: str
    content: str
    hashtags: List[str]
    call_to_action: str
    media_suggestions: List[str]
    posting_time: str
    expected_engagement: str
    version: int = 1
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class DistributionPlan:
    """Content distribution plan."""
    platform: str
    platform_name: str
    scheduled_time: str
    content: Copywriting
    status: str = "pending"  # pending/scheduled/published/failed
    published_url: str = ""
    engagement_preview: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContentProject:
    """Complete content creation project."""
    id: str
    name: str
    topic: Optional[Topic] = None
    materials: List[Material] = field(default_factory=list)
    copywritings: List[Copywriting] = field(default_factory=list)
    distribution_plans: List[DistributionPlan] = field(default_factory=list)
    status: str = "draft"  # draft/in_progress/completed
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class TopicSelector:
    """AI-assisted topic discovery and selection."""

    # Hot topic templates based on research data
    TOPIC_TEMPLATES = {
        "ai_tools": [
            {
                "title": "{tool_name}实战：{use_case}完全指南",
                "description": "详细介绍{tool_name}在{use_case}中的应用方法和技巧",
                "categories": ["教程", "工具测评"]
            },
            {
                "title": "我用{tool_name}{time_period}，{result}",
                "description": "真实使用体验分享，包含前后对比和心得",
                "categories": ["经验分享", "案例"]
            },
            {
                "title": "{number}个{adjective}的{tool_category}工具",
                "description": "工具合集推荐，满足不同场景需求",
                "categories": ["合集", "推荐"]
            }
        ],
        "solopreneur": [
            {
                "title": "一人公司{time_period}：我如何{achievement}",
                "description": "个人创业真实记录和经验总结",
                "categories": ["创业", "经验"]
            },
            {
                "title": "{number}个{adjective}的一人公司AI工具",
                "description": "适合独立创作者的效率工具推荐",
                "categories": ["工具", "效率"]
            }
        ]
    }

    # Trending keywords from research
    TRENDING_KEYWORDS = [
        "ChatGPT", "Midjourney", "Kimi", "Claude", "Notion AI",
        "AI绘画", "AI写作", "AI视频", "AI办公", "效率工具",
        "一人公司", "副业", "自由职业", "数字游民"
    ]

    def __init__(self):
        self.platform_optimizer = PlatformContentOptimizer()

    async def discover_topics(
        self,
        category: str = "ai_tools",
        count: int = 10,
        research_data: Optional[List[Dict]] = None
    ) -> List[Topic]:
        """Discover trending topics based on research data.

        Args:
            category: Topic category
            count: Number of topics to generate
            research_data: Optional research data from multi-platform collector

        Returns:
            List of topic suggestions
        """
        topics = []

        # Generate from templates
        templates = self.TOPIC_TEMPLATES.get(category, [])

        for i, template in enumerate(templates[:count]):
            topic = self._generate_topic_from_template(template, i)
            topics.append(topic)

        # If research data provided, extract real trending topics
        if research_data:
            trending_topics = self._extract_trending_topics(research_data)
            topics.extend(trending_topics)

        # Sort by trend score
        topics.sort(key=lambda x: x.trend_score, reverse=True)

        return topics[:count]

    def _generate_topic_from_template(self, template: Dict, index: int) -> Topic:
        """Generate a topic from template."""
        import random

        # Fill template variables
        tool_name = random.choice(["ChatGPT", "Midjourney", "Kimi", "Claude", "Notion AI"])
        use_case = random.choice(["内容创作", "数据分析", "图像设计", "代码编写"])
        time_period = random.choice(["30天", "3个月", "半年", "一年"])
        result = random.choice(["效率提升300%", "收入增长5倍", "节省50%时间", "实现自动化"])
        number = random.choice(["5", "10", "15", "20"])
        adjective = random.choice(["好用", "实用", "高效", "免费", "小众但强大"])
        tool_category = random.choice(["AI写作", "AI绘画", "效率", "办公"])
        achievement = random.choice(["月入过万", "实现自由职业", "建立被动收入", "打造个人品牌"])

        title = template["title"].format(
            tool_name=tool_name,
            use_case=use_case,
            time_period=time_period,
            result=result,
            number=number,
            adjective=adjective,
            tool_category=tool_category,
            achievement=achievement
        )

        description = template["description"].format(
            tool_name=tool_name,
            use_case=use_case
        )

        return Topic(
            id=f"topic_{index}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            title=title,
            description=description,
            category=template["categories"][0],
            keywords=[tool_name.lower(), use_case, "AI工具"],
            target_audience="对AI工具感兴趣的职场人士、创作者",
            estimated_engagement="中高",
            trend_score=random.uniform(60, 95),
            competition_level=random.choice(["low", "medium", "high"]),
            source_platforms=["xiaohongshu", "zhihu", "weibo"]
        )

    def _extract_trending_topics(self, research_data: List[Dict]) -> List[Topic]:
        """Extract trending topics from research data."""
        topics = []

        # Group by keywords
        keyword_counts = {}
        for item in research_data:
            for kw in item.get("matched_keywords", []):
                keyword_counts[kw] = keyword_counts.get(kw, 0) + 1

        # Generate topics from top keywords
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)

        for i, (keyword, count) in enumerate(sorted_keywords[:5]):
            topic = Topic(
                id=f"trending_{i}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                title=f"{keyword}深度解析：{count}个实战案例",
                description=f"基于多平台数据，深度分析{keyword}的应用场景和最佳实践",
                category="趋势分析",
                keywords=[keyword, "深度解析", "实战"],
                target_audience=f"对{keyword}感兴趣的用户",
                estimated_engagement="高",
                trend_score=min(95, 60 + count * 5),
                competition_level="medium",
                source_platforms=["xiaohongshu", "zhihu"]
            )
            topics.append(topic)

        return topics

    def select_topic(self, topics: List[Topic], criteria: Optional[Dict] = None) -> Topic:
        """Select the best topic based on criteria.

        Args:
            topics: List of candidate topics
            criteria: Selection criteria (engagement, competition, etc.)

        Returns:
            Selected topic
        """
        if not topics:
            raise ValueError("No topics provided")

        if criteria is None:
            criteria = {"min_trend_score": 70, "max_competition": "high"}

        # Filter by criteria
        filtered = topics
        if "min_trend_score" in criteria:
            filtered = [t for t in filtered if t.trend_score >= criteria["min_trend_score"]]

        if "max_competition" in criteria:
            competition_order = {"low": 0, "medium": 1, "high": 2}
            max_level = competition_order.get(criteria["max_competition"], 2)
            filtered = [t for t in filtered if competition_order.get(t.competition_level, 2) <= max_level]

        # Sort by composite score
        def composite_score(topic: Topic) -> float:
            competition_penalty = {"low": 1.0, "medium": 0.8, "high": 0.6}
            return topic.trend_score * competition_penalty.get(topic.competition_level, 0.8)

        filtered.sort(key=composite_score, reverse=True)

        return filtered[0] if filtered else topics[0]


class MaterialCollector:
    """Collect and organize content materials."""

    def __init__(self):
        self.materials: List[Material] = []

    async def collect_from_platforms(
        self,
        topic: Topic,
        platforms: List[str],
        max_per_platform: int = 10
    ) -> List[Material]:
        """Collect materials from multiple platforms.

        Args:
            topic: Selected topic
            platforms: List of platforms to collect from
            max_per_platform: Max materials per platform

        Returns:
            List of collected materials
        """
        all_materials = []

        for platform in platforms:
            try:
                materials = await self._collect_from_platform(
                    topic, platform, max_per_platform
                )
                all_materials.extend(materials)
                logger.info(f"Collected {len(materials)} materials from {platform}")
            except Exception as e:
                logger.error(f"Failed to collect from {platform}: {e}")

        # Sort by relevance
        all_materials.sort(key=lambda m: m.relevance_score, reverse=True)

        self.materials = all_materials
        return all_materials

    async def _collect_from_platform(
        self,
        topic: Topic,
        platform: str,
        max_results: int
    ) -> List[Material]:
        """Collect materials from a specific platform."""
        # This integrates with the existing multi-platform researcher
        from .multi_platform_ai_researcher import MultiPlatformAIResearcher

        researcher = MultiPlatformAIResearcher()
        items = await researcher.collect_from_platform(
            platform, topic.keywords, max_results
        )

        materials = []
        for i, item in enumerate(items):
            material = Material(
                id=f"mat_{platform}_{i}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                source=item.get("url", ""),
                source_platform=platform,
                title=item.get("title", ""),
                content=item.get("content", ""),
                url=item.get("url", ""),
                author=item.get("author", ""),
                engagement_metrics={
                    "likes": item.get("like_count", 0),
                    "collects": item.get("collect_count", 0),
                    "comments": item.get("comment_count", 0)
                },
                relevance_score=self._calculate_relevance(item, topic),
                tags=item.get("matched_keywords", [])
            )
            materials.append(material)

        return materials

    def _calculate_relevance(self, item: Dict, topic: Topic) -> float:
        """Calculate relevance score between item and topic."""
        score = 0.0

        # Keyword matching
        title = item.get("title", "").lower()
        content = item.get("content", "").lower()

        for keyword in topic.keywords:
            if keyword.lower() in title:
                score += 0.3
            if keyword.lower() in content:
                score += 0.2

        # Engagement boost
        likes = item.get("like_count", 0)
        if likes > 1000:
            score += 0.2
        elif likes > 100:
            score += 0.1

        return min(1.0, score)

    def organize_materials(self, materials: Optional[List[Material]] = None) -> Dict[str, List[Material]]:
        """Organize materials by category.

        Returns:
            Dictionary of categorized materials
        """
        if materials is None:
            materials = self.materials

        organized = {
            "high_relevance": [],
            "medium_relevance": [],
            "low_relevance": [],
            "by_platform": {},
            "by_tag": {}
        }

        for material in materials:
            # By relevance
            if material.relevance_score >= 0.7:
                organized["high_relevance"].append(material)
            elif material.relevance_score >= 0.4:
                organized["medium_relevance"].append(material)
            else:
                organized["low_relevance"].append(material)

            # By platform
            platform = material.source_platform
            if platform not in organized["by_platform"]:
                organized["by_platform"][platform] = []
            organized["by_platform"][platform].append(material)

            # By tag
            for tag in material.tags:
                if tag not in organized["by_tag"]:
                    organized["by_tag"][tag] = []
                organized["by_tag"][tag].append(material)

        return organized

    def generate_insights(self, materials: Optional[List[Material]] = None) -> Dict[str, Any]:
        """Generate insights from collected materials."""
        if materials is None:
            materials = self.materials

        if not materials:
            return {"error": "No materials to analyze"}

        # Calculate statistics
        total_likes = sum(m.engagement_metrics.get("likes", 0) for m in materials)
        total_collects = sum(m.engagement_metrics.get("collects", 0) for m in materials)
        avg_relevance = sum(m.relevance_score for m in materials) / len(materials)

        # Find top platforms
        platform_counts = {}
        for m in materials:
            platform_counts[m.source_platform] = platform_counts.get(m.source_platform, 0) + 1

        # Find common tags
        tag_counts = {}
        for m in materials:
            for tag in m.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return {
            "total_materials": len(materials),
            "total_engagement": {
                "likes": total_likes,
                "collects": total_collects
            },
            "average_relevance": round(avg_relevance, 2),
            "top_platforms": sorted(platform_counts.items(), key=lambda x: x[1], reverse=True)[:3],
            "trending_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "key_insights": [
                f"共收集 {len(materials)} 条素材",
                f"总互动量：{total_likes} 赞，{total_collects} 收藏",
                f"平均相关度：{avg_relevance:.0%}"
            ]
        }


class CopywritingGenerator:
    """Generate platform-optimized copywriting."""

    def __init__(self):
        self.platform_optimizer = PlatformContentOptimizer()

    async def generate_copy(
        self,
        topic: Topic,
        materials: List[Material],
        platform: str,
        style: str = "informative"
    ) -> Copywriting:
        """Generate copy for a specific platform.

        Args:
            topic: Content topic
            materials: Reference materials
            platform: Target platform
            style: Writing style (informative/persuasive/storytelling)

        Returns:
            Generated copywriting
        """
        # Get platform characteristics
        char = self.platform_optimizer.get_platform_characteristics(platform)
        if not char:
            raise ValueError(f"Unknown platform: {platform}")

        # Generate content based on style and materials
        content = self._compose_content(topic, materials, char, style)

        # Generate title
        title = self._generate_title(topic, char, style)

        # Select hashtags
        hashtags = self._select_hashtags(topic, materials, char)

        # Select CTA
        cta = self._select_cta(char)

        # Determine posting time
        posting_time = char.best_posting_times[0] if char.best_posting_times else ""

        return Copywriting(
            platform=platform,
            platform_name=char.name_cn,
            title=title,
            content=content,
            hashtags=hashtags,
            call_to_action=cta,
            media_suggestions=self._suggest_media(char),
            posting_time=posting_time,
            expected_engagement=self._estimate_engagement(materials)
        )

    async def generate_multi_platform_copies(
        self,
        topic: Topic,
        materials: List[Material],
        platforms: Optional[List[str]] = None,
        style: str = "informative"
    ) -> List[Copywriting]:
        """Generate copies for multiple platforms.

        Args:
            topic: Content topic
            materials: Reference materials
            platforms: Target platforms (default: all)
            style: Writing style

        Returns:
            List of copywritings for each platform
        """
        if platforms is None:
            platforms = [p.value for p in PlatformType]

        copies = []
        for platform in platforms:
            try:
                copy = await self.generate_copy(topic, materials, platform, style)
                copies.append(copy)
            except Exception as e:
                logger.error(f"Failed to generate copy for {platform}: {e}")

        return copies

    def _compose_content(
        self,
        topic: Topic,
        materials: List[Material],
        char: Any,
        style: str
    ) -> str:
        """Compose content based on materials and platform style."""
        # Extract key points from materials
        key_points = []
        for mat in materials[:5]:
            if mat.content:
                key_points.append(mat.content[:200])

        # Build content based on platform template
        template = char.structure_template

        # Fill in content (simplified version - in production, use LLM)
        content_parts = []

        # Opening
        if style == "storytelling":
            content_parts.append(f"最近我一直在研究{topic.title}，发现了一个很有意思的现象...\n")
        else:
            content_parts.append(f"今天和大家分享{topic.title}。\n")

        # Body - key points
        content_parts.append("【核心要点】\n")
        for i, point in enumerate(key_points[:3], 1):
            content_parts.append(f"{i}. {point[:100]}...\n")

        # Platform-specific formatting
        if char.name == "xiaohongshu":
            # Add emojis and formatting
            content_parts.append("\n✨ 总结要点：\n")
            content_parts.append(f"💡 {topic.description}\n")
        elif char.name == "zhihu":
            # More structured, analytical
            content_parts.append("\n## 详细分析\n")
            content_parts.append("基于以上观察，我有以下几点看法：\n")
            content_parts.append("1. 趋势明显：AI工具正在改变工作方式\n")
            content_parts.append("2. 效率提升：使用AI工具可节省大量时间\n")
            content_parts.append("3. 学习成本：上手简单，但需要持续探索\n")

        # Closing
        content_parts.append(f"\n{'='*20}\n")
        content_parts.append("希望对你有帮助！")

        return "\n".join(content_parts)

    def _generate_title(self, topic: Topic, char: Any, style: str) -> str:
        """Generate optimized title."""
        base_title = topic.title

        # Platform-specific title optimization
        if char.name == "xiaohongshu":
            # Add emoji and make it catchy
            emojis = ["✨", "🔥", "💡", "📌"]
            import random
            emoji = random.choice(emojis)
            return f"{emoji} {base_title}｜亲测有效"
        elif char.name == "zhihu":
            # More descriptive
            return f"如何{base_title}？万字长文深度解析"
        elif char.name == "weibo":
            # Short and punchy
            return f"#{topic.keywords[0]}# {base_title}"
        else:
            return base_title

    def _select_hashtags(self, topic: Topic, materials: List[Material], char: Any) -> List[str]:
        """Select appropriate hashtags."""
        base_tags = char.hashtag_strategy.get("examples", [])

        # Add topic-specific tags
        topic_tags = [f"#{kw}" for kw in topic.keywords[:3]]

        # Combine and limit
        all_tags = topic_tags + base_tags
        max_tags = 5 if char.name in ["xiaohongshu", "douyin"] else 3

        return all_tags[:max_tags]

    def _select_cta(self, char: Any) -> str:
        """Select call to action."""
        ctas = char.call_to_action
        import random
        return random.choice(ctas) if ctas else ""

    def _suggest_media(self, char: Any) -> List[str]:
        """Suggest media types for the platform."""
        specs = char.image_video_specs
        suggestions = []

        if "image_count" in specs:
            suggestions.append(f"配图：{specs['image_count']}")
        if "video_length" in specs:
            suggestions.append(f"视频时长：{specs['video_length']}")
        if "ratio" in specs:
            suggestions.append(f"比例：{specs['ratio']}")

        return suggestions

    def _estimate_engagement(self, materials: List[Material]) -> str:
        """Estimate expected engagement based on materials."""
        if not materials:
            return "medium"

        avg_likes = sum(m.engagement_metrics.get("likes", 0) for m in materials) / len(materials)

        if avg_likes > 1000:
            return "high"
        elif avg_likes > 100:
            return "medium-high"
        else:
            return "medium"


class DistributionManager:
    """Manage content distribution across platforms."""

    def __init__(self):
        self.distribution_plans: List[DistributionPlan] = []

    def create_distribution_plan(
        self,
        copywritings: List[Copywriting],
        schedule: Optional[Dict[str, str]] = None
    ) -> List[DistributionPlan]:
        """Create distribution plan for all platforms.

        Args:
            copywritings: List of copywritings for each platform
            schedule: Optional custom schedule {"platform": "time"}

        Returns:
            List of distribution plans
        """
        plans = []

        for copy in copywritings:
            # Determine posting time
            if schedule and copy.platform in schedule:
                posting_time = schedule[copy.platform]
            else:
                # Use platform's best time
                posting_time = self._get_best_posting_time(copy.platform)

            plan = DistributionPlan(
                platform=copy.platform,
                platform_name=copy.platform_name,
                scheduled_time=posting_time,
                content=copy
            )
            plans.append(plan)

        self.distribution_plans = plans
        return plans

    def _get_best_posting_time(self, platform: str) -> str:
        """Get optimal posting time for platform."""
        best_times = {
            "xiaohongshu": "19:00",
            "zhihu": "21:00",
            "weibo": "12:00",
            "video_account": "20:00",
            "official_account": "21:00",
            "douyin": "18:00"
        }
        return best_times.get(platform, "19:00")

    def optimize_schedule(self, plans: Optional[List[DistributionPlan]] = None) -> List[DistributionPlan]:
        """Optimize posting schedule to avoid conflicts.

        Args:
            plans: Distribution plans to optimize

        Returns:
            Optimized plans with adjusted times
        """
        if plans is None:
            plans = self.distribution_plans

        # Sort by priority (platforms with higher engagement potential first)
        priority_order = {
            "xiaohongshu": 1,
            "douyin": 2,
            "video_account": 3,
            "official_account": 4,
            "zhihu": 5,
            "weibo": 6
        }

        sorted_plans = sorted(
            plans,
            key=lambda p: priority_order.get(p.platform, 99)
        )

        # Stagger posting times (30 minutes apart)
        base_hour = 19
        for i, plan in enumerate(sorted_plans):
            hour = base_hour + (i * 30) // 60
            minute = (i * 30) % 60
            plan.scheduled_time = f"{hour:02d}:{minute:02d}"

        return sorted_plans

    def generate_distribution_report(self) -> Dict[str, Any]:
        """Generate distribution plan report."""
        if not self.distribution_plans:
            return {"error": "No distribution plans"}

        report = {
            "total_platforms": len(self.distribution_plans),
            "scheduled_posts": [
                {
                    "platform": plan.platform_name,
                    "time": plan.scheduled_time,
                    "title": plan.content.title[:50] + "..." if len(plan.content.title) > 50 else plan.content.title,
                    "status": plan.status
                }
                for plan in self.distribution_plans
            ],
            "timeline": self._generate_timeline(),
            "estimated_reach": self._estimate_reach()
        }

        return report

    def _generate_timeline(self) -> List[Dict]:
        """Generate posting timeline."""
        timeline = []
        for plan in sorted(self.distribution_plans, key=lambda p: p.scheduled_time):
            timeline.append({
                "time": plan.scheduled_time,
                "platform": plan.platform_name,
                "action": "发布内容"
            })
        return timeline

    def _estimate_reach(self) -> Dict[str, int]:
        """Estimate potential reach."""
        # Platform-specific audience estimates
        audience_sizes = {
            "xiaohongshu": 5000,
            "douyin": 10000,
            "video_account": 3000,
            "official_account": 2000,
            "zhihu": 3000,
            "weibo": 2000
        }

        total = sum(
            audience_sizes.get(plan.platform, 1000)
            for plan in self.distribution_plans
        )

        return {
            "estimated_total_reach": total,
            "by_platform": {
                plan.platform_name: audience_sizes.get(plan.platform, 1000)
                for plan in self.distribution_plans
            }
        }


class ContentCreationWorkflow:
    """Complete content creation workflow."""

    def __init__(self):
        self.topic_selector = TopicSelector()
        self.material_collector = MaterialCollector()
        self.copywriting_generator = CopywritingGenerator()
        self.distribution_manager = DistributionManager()
        self.projects: List[ContentProject] = []

    async def execute_full_workflow(
        self,
        topic_criteria: Optional[Dict] = None,
        platforms: Optional[List[str]] = None,
        style: str = "informative"
    ) -> ContentProject:
        """Execute complete content creation workflow.

        Args:
            topic_criteria: Criteria for topic selection
            platforms: Target platforms
            style: Writing style

        Returns:
            Complete content project
        """
        project_id = f"project_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        project = ContentProject(id=project_id, name="AI Tools Content Creation")

        logger.info(f"Starting content creation workflow: {project_id}")

        # Stage 1: Topic Selection
        logger.info("Stage 1: Topic Selection")
        topics = await self.topic_selector.discover_topics(count=10)
        selected_topic = self.topic_selector.select_topic(topics, topic_criteria)
        project.topic = selected_topic
        logger.info(f"Selected topic: {selected_topic.title}")

        # Stage 2: Material Collection
        logger.info("Stage 2: Material Collection")
        if platforms is None:
            platforms = ["xiaohongshu", "zhihu", "weibo"]

        materials = await self.material_collector.collect_from_platforms(
            selected_topic, platforms, max_per_platform=10
        )
        project.materials = materials
        logger.info(f"Collected {len(materials)} materials")

        # Stage 3: Copywriting
        logger.info("Stage 3: Copywriting Generation")
        copies = await self.copywriting_generator.generate_multi_platform_copies(
            selected_topic, materials, platforms, style
        )
        project.copywritings = copies
        logger.info(f"Generated {len(copies)} copies")

        # Stage 4: Distribution Planning
        logger.info("Stage 4: Distribution Planning")
        plans = self.distribution_manager.create_distribution_plan(copies)
        optimized_plans = self.distribution_manager.optimize_schedule(plans)
        project.distribution_plans = optimized_plans
        logger.info(f"Created distribution plan for {len(plans)} platforms")

        # Complete
        project.status = "completed"
        self.projects.append(project)

        logger.info(f"Workflow completed: {project_id}")
        return project

    def generate_project_report(self, project: ContentProject) -> Dict[str, Any]:
        """Generate comprehensive project report."""
        return {
            "project_id": project.id,
            "project_name": project.name,
            "status": project.status,
            "topic": {
                "title": project.topic.title if project.topic else "",
                "description": project.topic.description if project.topic else "",
                "keywords": project.topic.keywords if project.topic else []
            },
            "materials_summary": {
                "total": len(project.materials),
                "by_platform": self._count_by_platform(project.materials)
            },
            "copywritings": [
                {
                    "platform": copy.platform_name,
                    "title": copy.title,
                    "hashtags": copy.hashtags,
                    "posting_time": copy.posting_time
                }
                for copy in project.copywritings
            ],
            "distribution_schedule": [
                {
                    "platform": plan.platform_name,
                    "time": plan.scheduled_time,
                    "content_preview": plan.content.content[:100] + "..."
                }
                for plan in project.distribution_plans
            ]
        }

    def _count_by_platform(self, materials: List[Material]) -> Dict[str, int]:
        """Count materials by platform."""
        counts = {}
        for mat in materials:
            counts[mat.source_platform] = counts.get(mat.source_platform, 0) + 1
        return counts


# Convenience functions
async def create_content_project(
    topic_keywords: Optional[List[str]] = None,
    platforms: Optional[List[str]] = None,
    style: str = "informative"
) -> Dict[str, Any]:
    """Create a complete content project.

    Args:
        topic_keywords: Keywords for topic discovery
        platforms: Target platforms
        style: Writing style

    Returns:
        Project report
    """
    workflow = ContentCreationWorkflow()
    project = await workflow.execute_full_workflow(
        topic_criteria={"min_trend_score": 70} if topic_keywords else None,
        platforms=platforms,
        style=style
    )
    return workflow.generate_project_report(project)


async def generate_platform_content(
    topic_title: str,
    topic_description: str,
    platform: str,
    reference_materials: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Generate content for a specific platform.

    Args:
        topic_title: Content topic title
        topic_description: Topic description
        platform: Target platform
        reference_materials: Optional reference content

    Returns:
        Generated content
    """
    topic = Topic(
        id=f"manual_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        title=topic_title,
        description=topic_description,
        category="manual",
        keywords=["AI工具", "效率"],
        target_audience="通用",
        estimated_engagement="medium",
        trend_score=70,
        competition_level="medium"
    )

    generator = CopywritingGenerator()

    # Create dummy materials if none provided
    materials = []
    if reference_materials:
        for i, ref in enumerate(reference_materials):
            materials.append(Material(
                id=f"ref_{i}",
                source="manual",
                source_platform="manual",
                title=f"Reference {i+1}",
                content=ref,
                url="",
                relevance_score=0.8
            ))

    copy = await generator.generate_copy(topic, materials, platform)

    return {
        "platform": copy.platform_name,
        "title": copy.title,
        "content": copy.content,
        "hashtags": copy.hashtags,
        "call_to_action": copy.call_to_action,
        "media_suggestions": copy.media_suggestions,
        "posting_time": copy.posting_time
    }


def get_platform_comparison() -> Dict[str, Any]:
    """Get comparison of all platforms."""
    optimizer = PlatformContentOptimizer()
    return optimizer.compare_platforms()


if __name__ == "__main__":
    # Test workflow
    async def test():
        workflow = ContentCreationWorkflow()

        # Execute workflow
        project = await workflow.execute_full_workflow(
            platforms=["xiaohongshu", "zhihu", "weibo"],
            style="informative"
        )

        # Generate report
        report = workflow.generate_project_report(project)
        print(json.dumps(report, ensure_ascii=False, indent=2))

    asyncio.run(test())
