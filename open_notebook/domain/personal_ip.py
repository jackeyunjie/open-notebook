"""Personal IP Command Center - 10-Dimensional Framework for Super-Individual Growth.

This module provides the data models for managing personal IP assets,
content calendars, and growth analytics in a unified command center.

10-Dimensional Framework:
    1. Static Identity - Core values, positioning, brand voice
    2. Dynamic Behavior - Content patterns, interaction styles
    3. Value Drivers - Key themes, expertise areas
    4. Relationship Network - Audience segments, connections
    5. Environmental Constraints - Platform rules, market conditions
    6. Dynamic Feedback - Performance data, sentiment
    7. Knowledge Assets - Published content, IP inventory
    8. Tacit Knowledge - Insights, intuitions, patterns
    9. AI Collaboration Config - Agent preferences, automation rules
    10. Cognitive Evolution Logs - Learning journey, pivots
"""

from datetime import datetime, date
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field
from surrealdb import RecordID

from open_notebook.domain.base import ObjectModel


class ContentStatus(Enum):
    """Status of content in calendar."""
    IDEA = "idea"              # Just an idea
    PLANNED = "planned"        # Scheduled
    IN_PROGRESS = "in_progress"  # Being created
    READY = "ready"            # Ready to publish
    PUBLISHED = "published"    # Published
    ARCHIVED = "archived"      # Archived


class ContentQuadrant(Enum):
    """Four-quadrant content classification."""
    Q1_INTENT = "Q1"      # Intent users - problem/solution
    Q2_AWARE = "Q2"       # Aware users - deepen understanding
    Q3_MASS = "Q3"        # Mass users - awareness
    Q4_POTENTIAL = "Q4"   # Potential users - discovery


class PlatformType(Enum):
    """Supported content platforms."""
    # 国内平台
    XIAOHONGSHU = "xiaohongshu"      # 小红书
    WEIBO = "weibo"                   # 微博
    WECHAT_OFFICIAL = "wechat_official"  # 公众号
    WECHAT_CHANNELS = "wechat_channels"  # 视频号
    ZHIHU = "zhihu"                   # 知乎
    JIKE = "jike"                     # 即刻
    BILIBILI = "bilibili"             # B站
    DOUYIN = "douyin"                 # 抖音
    KUAISHOU = "kuaishou"             # 快手

    # 海外平台
    TWITTER = "twitter"               # X/Twitter
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"
    THREADS = "threads"

    # 其他
    WEBSITE = "website"
    NEWSLETTER = "newsletter"
    PODCAST = "podcast"


# =============================================================================
# 10-Dimensional Profile Components
# =============================================================================

class StaticIdentityDimension(BaseModel):
    """D1: Static Identity - Who you are."""
    core_values: List[str] = Field(default_factory=list)
    positioning_statement: str = ""
    brand_voice: str = ""  # e.g., "professional but approachable"
    visual_style: str = ""
    taglines: List[str] = Field(default_factory=list)
    origin_story: str = ""  # How you got here
    mission_statement: str = ""


class DynamicBehaviorDimension(BaseModel):
    """D2: Dynamic Behavior - How you operate."""
    content_frequency: str = ""  # e.g., "daily", "3x/week"
    best_posting_times: Dict[str, List[str]] = Field(default_factory=dict)  # platform -> times
    interaction_patterns: str = ""  # How you engage with audience
    content_formats: List[str] = Field(default_factory=list)  # text, video, carousel
    collaboration_style: str = ""
    decision_making_pattern: str = ""


class ValueDriversDimension(BaseModel):
    """D3: Value Drivers - What you offer."""
    expertise_areas: List[str] = Field(default_factory=list)
    key_themes: List[str] = Field(default_factory=list)
    unique_perspectives: List[str] = Field(default_factory=list)
    proprietary_frameworks: List[Dict[str, Any]] = Field(default_factory=list)
    content_pillars: List[str] = Field(default_factory=list)
    value_proposition: str = ""


class RelationshipNetworkDimension(BaseModel):
    """D4: Relationship Network - Who you connect with."""
    audience_segments: List[Dict[str, Any]] = Field(default_factory=list)
    key_relationships: List[Dict[str, Any]] = Field(default_factory=list)
    community_ties: List[str] = Field(default_factory=list)
    collaboration_history: List[Dict[str, Any]] = Field(default_factory=list)
    mentor_network: List[str] = Field(default_factory=list)
    follower_growth_milestones: List[Dict[str, Any]] = Field(default_factory=list)


class EnvironmentalConstraintsDimension(BaseModel):
    """D5: Environmental Constraints - Context you operate in."""
    platform_policies: Dict[str, Any] = Field(default_factory=dict)
    market_trends: List[str] = Field(default_factory=list)
    competitive_landscape: str = ""
    regulatory_constraints: List[str] = Field(default_factory=list)
    resource_limitations: List[str] = Field(default_factory=list)
    opportunity_windows: List[Dict[str, Any]] = Field(default_factory=list)


class DynamicFeedbackDimension(BaseModel):
    """D6: Dynamic Feedback - What the data says."""
    performance_metrics: Dict[str, float] = Field(default_factory=dict)
    audience_sentiment: str = ""
    content_analytics: Dict[str, Any] = Field(default_factory=dict)
    engagement_patterns: Dict[str, Any] = Field(default_factory=dict)
    conversion_data: Dict[str, Any] = Field(default_factory=dict)
    feedback_summary: str = ""


class KnowledgeAssetsDimension(BaseModel):
    """D7: Knowledge Assets - What you've created."""
    published_content_count: int = 0
    top_performing_content: List[str] = Field(default_factory=list)  # Note IDs
    content_series: List[Dict[str, Any]] = Field(default_factory=list)
    reusable_templates: List[str] = Field(default_factory=list)
    ip_inventory: List[Dict[str, Any]] = Field(default_factory=list)
    evergreen_content: List[str] = Field(default_factory=list)


class TacitKnowledgeDimension(BaseModel):
    """D8: Tacit Knowledge - What you know but can't easily articulate."""
    intuitions: List[str] = Field(default_factory=list)
    pattern_recognitions: List[str] = Field(default_factory=list)
    lessons_learned: List[str] = Field(default_factory=list)
    insider_observations: str = ""
    gut_feelings_tracked: List[Dict[str, Any]] = Field(default_factory=list)
    tacit_insights: str = ""


class AICollaborationConfigDimension(BaseModel):
    """D9: AI Collaboration Config - How you work with AI."""
    preferred_agents: List[str] = Field(default_factory=list)
    automation_rules: List[Dict[str, Any]] = Field(default_factory=list)
    review_preferences: str = ""  # e.g., "review all", "auto-publish low-risk"
    custom_prompts: Dict[str, str] = Field(default_factory=dict)
    ai_collaboration_history: List[Dict[str, Any]] = Field(default_factory=list)
    feedback_to_ai: str = ""


class CognitiveEvolutionLog(BaseModel):
    """D10: Cognitive Evolution - How you've grown."""
    timestamp: datetime
    evolution_type: str  # pivot, growth, insight, mistake
    description: str
    trigger: str
    outcome: str
    lessons: List[str] = Field(default_factory=list)


class CognitiveEvolutionDimension(BaseModel):
    """D10: Cognitive Evolution Logs - Your growth journey."""
    evolution_logs: List[CognitiveEvolutionLog] = Field(default_factory=list)
    pivot_points: List[Dict[str, Any]] = Field(default_factory=list)
    growth_trajectory: str = ""
    mindset_shifts: List[str] = Field(default_factory=list)
    capability_milestones: List[Dict[str, Any]] = Field(default_factory=list)


# =============================================================================
# Main 10-Dimensional Profile Model
# =============================================================================

class PersonalIPProfile(ObjectModel):
    """Complete 10-dimensional profile for personal IP management."""

    table_name: str = "personal_ip_profile"

    # Basic info
    name: str = ""  # Profile name (e.g., "Vikki IP 2024")
    description: str = ""
    is_active: bool = True

    # 10 Dimensions
    d1_static_identity: StaticIdentityDimension = Field(
        default_factory=StaticIdentityDimension
    )
    d2_dynamic_behavior: DynamicBehaviorDimension = Field(
        default_factory=DynamicBehaviorDimension
    )
    d3_value_drivers: ValueDriversDimension = Field(
        default_factory=ValueDriversDimension
    )
    d4_relationship_network: RelationshipNetworkDimension = Field(
        default_factory=RelationshipNetworkDimension
    )
    d5_environmental_constraints: EnvironmentalConstraintsDimension = Field(
        default_factory=EnvironmentalConstraintsDimension
    )
    d6_dynamic_feedback: DynamicFeedbackDimension = Field(
        default_factory=DynamicFeedbackDimension
    )
    d7_knowledge_assets: KnowledgeAssetsDimension = Field(
        default_factory=KnowledgeAssetsDimension
    )
    d8_tacit_knowledge: TacitKnowledgeDimension = Field(
        default_factory=TacitKnowledgeDimension
    )
    d9_ai_collaboration: AICollaborationConfigDimension = Field(
        default_factory=AICollaborationConfigDimension
    )
    d10_cognitive_evolution: CognitiveEvolutionDimension = Field(
        default_factory=CognitiveEvolutionDimension
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1

    async def update_dimension(self, dimension: str, data: Dict[str, Any]):
        """Update a specific dimension."""
        dim_map = {
            "d1": "d1_static_identity",
            "d2": "d2_dynamic_behavior",
            "d3": "d3_value_drivers",
            "d4": "d4_relationship_network",
            "d5": "d5_environmental_constraints",
            "d6": "d6_dynamic_feedback",
            "d7": "d7_knowledge_assets",
            "d8": "d8_tacit_knowledge",
            "d9": "d9_ai_collaboration",
            "d10": "d10_cognitive_evolution",
        }

        attr_name = dim_map.get(dimension)
        if not attr_name:
            raise ValueError(f"Unknown dimension: {dimension}")

        current = getattr(self, attr_name)
        updated_data = {**current.dict(), **data}
        setattr(self, attr_name, current.__class__(**updated_data))
        self.updated_at = datetime.utcnow()
        await self.save()

    def get_dimension_summary(self) -> Dict[str, Any]:
        """Get summary of all 10 dimensions."""
        return {
            "profile_id": str(self.id) if self.id else None,
            "name": self.name,
            "version": self.version,
            "dimensions": {
                "d1_static_identity": {
                    "core_values_count": len(self.d1_static_identity.core_values),
                    "positioning": self.d1_static_identity.positioning_statement[:50] + "..." if len(self.d1_static_identity.positioning_statement) > 50 else self.d1_static_identity.positioning_statement,
                },
                "d2_dynamic_behavior": {
                    "content_frequency": self.d2_dynamic_behavior.content_frequency,
                    "platforms": list(self.d2_dynamic_behavior.best_posting_times.keys()),
                },
                "d3_value_drivers": {
                    "expertise_areas": self.d3_value_drivers.expertise_areas[:5],
                    "content_pillars": self.d3_value_drivers.content_pillars[:3],
                },
                "d4_relationship_network": {
                    "audience_segments": len(self.d4_relationship_network.audience_segments),
                    "key_relationships": len(self.d4_relationship_network.key_relationships),
                },
                "d7_knowledge_assets": {
                    "published_count": self.d7_knowledge_assets.published_content_count,
                    "top_content": len(self.d7_knowledge_assets.top_performing_content),
                },
                "d10_cognitive_evolution": {
                    "evolution_logs_count": len(self.d10_cognitive_evolution.evolution_logs),
                    "pivot_points": len(self.d10_cognitive_evolution.pivot_points),
                },
            },
            "last_updated": self.updated_at.isoformat(),
        }


# =============================================================================
# Content Calendar Model
# =============================================================================

class ContentCalendarEntry(ObjectModel):
    """A single entry in the content calendar."""

    table_name: str = "content_calendar_entry"

    # Content info
    title: str = ""
    description: str = ""
    content_type: str = ""  # post, article, video, thread
    quadrant: ContentQuadrant = ContentQuadrant.Q3_MASS

    # Scheduling
    planned_date: Optional[date] = None
    planned_time: Optional[str] = None
    status: ContentStatus = ContentStatus.IDEA

    # Platform targeting
    target_platforms: List[PlatformType] = Field(default_factory=list)
    platform_specific_notes: Dict[str, str] = Field(default_factory=dict)

    # Content links
    source_note_id: Optional[str] = None  # Linked to existing note
    generated_content_ids: List[str] = Field(default_factory=list)  # Generated variants

    # P0-P3 integration
    p0_signal_id: Optional[str] = None  # Origin signal
    p1_assessment_id: Optional[str] = None  # Value assessment
    p2_plan_id: Optional[str] = None  # Relationship plan

    # Execution tracking
    published_urls: Dict[str, str] = Field(default_factory=dict)  # platform -> URL
    performance_data: Dict[str, Any] = Field(default_factory=dict)
    feedback_collected: bool = False

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    profile_id: Optional[str] = None  # Linked to PersonalIPProfile

    async def mark_as_published(self, platform: PlatformType, url: str):
        """Mark content as published on a platform."""
        self.published_urls[platform.value] = url
        self.status = ContentStatus.PUBLISHED
        self.updated_at = datetime.utcnow()
        await self.save()

    async def update_performance(self, platform: str, metrics: Dict[str, Any]):
        """Update performance metrics."""
        if platform not in self.performance_data:
            self.performance_data[platform] = {}
        self.performance_data[platform].update(metrics)
        self.updated_at = datetime.utcnow()
        await self.save()


class ContentCalendar:
    """Manager for content calendar operations."""

    @staticmethod
    async def get_entries_for_date(target_date: date, profile_id: Optional[str] = None) -> List[ContentCalendarEntry]:
        """Get all entries for a specific date."""
        # This would query the database
        # For now, return empty list - implement with actual DB query
        return []

    @staticmethod
    async def get_entries_by_status(status: ContentStatus, profile_id: Optional[str] = None) -> List[ContentCalendarEntry]:
        """Get entries by status."""
        return []

    @staticmethod
    async def get_upcoming_entries(days: int = 7, profile_id: Optional[str] = None) -> List[ContentCalendarEntry]:
        """Get upcoming entries."""
        return []


# =============================================================================
# IP Dashboard Analytics
# =============================================================================

class IPDashboardMetrics(BaseModel):
    """Metrics for the IP dashboard."""

    # Content metrics
    total_content_published: int = 0
    content_by_quadrant: Dict[str, int] = Field(default_factory=dict)
    content_by_platform: Dict[str, int] = Field(default_factory=dict)

    # Engagement metrics
    total_views: int = 0
    total_engagements: int = 0
    avg_engagement_rate: float = 0.0

    # Growth metrics
    follower_growth_30d: int = 0
    follower_growth_rate: float = 0.0
    top_growing_platform: str = ""

    # P3 evolution metrics
    evolution_generation: int = 0
    strategies_deployed: int = 0
    fitness_improvement: float = 0.0

    # Calendar metrics
    upcoming_content_count: int = 0
    ideas_backlog_count: int = 0
    published_this_month: int = 0

    # 10-dimension health
    dimension_completeness: Dict[str, float] = Field(default_factory=dict)


class IPDashboard:
    """Dashboard for personal IP analytics."""

    @staticmethod
    async def get_metrics(profile_id: str) -> IPDashboardMetrics:
        """Get dashboard metrics for a profile."""
        # This would aggregate data from various sources
        # For now, return empty metrics
        return IPDashboardMetrics()

    @staticmethod
    async def get_quadrant_distribution(profile_id: str) -> Dict[str, Any]:
        """Get content distribution across four quadrants."""
        return {
            "Q1": {"count": 0, "percentage": 0, "avg_performance": 0},
            "Q2": {"count": 0, "percentage": 0, "avg_performance": 0},
            "Q3": {"count": 0, "percentage": 0, "avg_performance": 0},
            "Q4": {"count": 0, "percentage": 0, "avg_performance": 0},
        }

    @staticmethod
    async def get_content_pipeline(profile_id: str) -> Dict[str, int]:
        """Get content pipeline status."""
        return {
            "ideas": 0,
            "planned": 0,
            "in_progress": 0,
            "ready": 0,
            "published": 0,
        }
