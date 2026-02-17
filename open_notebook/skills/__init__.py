"""Skill system for Open Notebook automation.

This module provides a lightweight skill framework based on LangChain,
enabling automated content processing and intelligent note organization.
"""

from open_notebook.skills.base import Skill, SkillConfig, SkillContext, SkillResult, SkillStatus
from open_notebook.skills.registry import SkillRegistry, register_skill
from open_notebook.skills.runner import SkillRunner, get_skill_runner

# Import all skills to ensure registration
from open_notebook.skills.content_crawler import RssCrawlerSkill
from open_notebook.skills.browser_base import BrowserUseSkill, BrowserCrawlerSkill
from open_notebook.skills.browser_task import BrowserTaskSkill, BrowserMonitorSkill
from open_notebook.skills.note_organizer import NoteSummarizerSkill, NoteTaggerSkill
from open_notebook.skills.vikki_content_ops import (
    ContentAdaptorSkill,
    CycleDiagnosticianSkill,
    PainpointScannerSkill,
    QuadrantClassifierSkill,
    RatioMonitorSkill,
    TopicEvaluatorSkill,
    TopicGeneratorSkill,
)
from open_notebook.skills.yuanbao_converter import YuanbaoConverterSkill
from open_notebook.skills.p0_agents import (
    PainScannerAgent,
    EmotionWatcherAgent,
    TrendHunterAgent,
    SceneDiscoverAgent,
)
from open_notebook.skills.p0_orchestrator import P0OrchestratorAgent, SharedMemory
from open_notebook.skills.p0_scheduler import (
    P0SyncScheduler,
    P0ScheduleConfig,
    SyncExecutionRecord,
    SyncStatus,
    p0_sync_scheduler,
    setup_default_p0_schedule,
)
from open_notebook.skills.p1_agents import (
    PainpointValueAgent,
    EmotionAlignmentAgent,
    TrendValueAgent,
    DemandAssessmentAgent,
    ValueAssessment,
    ValueJudgmentReport,
    ValuePriority,
)
from open_notebook.skills.p2_agents import (
    TrustBuilderAgent,
    CommunityBinderAgent,
    ViralEngineAgent,
    InfluenceNetworkAgent,
    RelationshipPlan,
    RelationshipReport,
    TrustLevel,
)
from open_notebook.skills.feedback_loop import (
    FeedbackCollector,
    PatternAnalyzer,
    LearningEngine,
    FeedbackLoopOrchestrator,
    FeedbackRecord,
    LearningInsight,
    SystemLearningState,
    FeedbackType,
    LearningAction,
)
from open_notebook.skills.p3_evolution import (
    EvolutionOrchestrator,
    StrategyPopulation,
    MetaLearningEngine,
    LongTermMemory,
    AgentStrategy,
    StrategyGene,
    EvolutionReport,
    MetaLearningRecord,
    EvolutionType,
    MutationType,
    evolution_orchestrator,
    initialize_p3_evolution,
    run_evolution_cycle,
)
from open_notebook.skills.p3_scheduler import (
    P3EvolutionScheduler,
    EvolutionScheduleConfig,
    EvolutionExecutionRecord,
    EvolutionScheduleType,
    p3_evolution_scheduler,
    setup_default_p3_schedule,
)
# Note: xiaohongshu_researcher is loaded lazily to avoid circular dependency
# from open_notebook.skills.xiaohongshu_researcher import XiaohongshuResearcherSkill, research_xiaohongshu

__all__ = [
    "Skill",
    "SkillConfig",
    "SkillContext",
    "SkillResult",
    "SkillStatus",
    "SkillRegistry",
    "register_skill",
    "SkillRunner",
    "get_skill_runner",
    # Core skill implementations
    "RssCrawlerSkill",
    "BrowserUseSkill",
    "BrowserCrawlerSkill",
    "BrowserTaskSkill",
    "BrowserMonitorSkill",
    "NoteSummarizerSkill",
    "NoteTaggerSkill",
    # Vikki content operations skills
    "PainpointScannerSkill",
    "QuadrantClassifierSkill",
    "TopicGeneratorSkill",
    "ContentAdaptorSkill",
    # Phase C: Multi-agent content strategy skills
    "CycleDiagnosticianSkill",
    "TopicEvaluatorSkill",
    "RatioMonitorSkill",
    # Yuanbao converter skill
    "YuanbaoConverterSkill",
    # P0 Perception Layer Agents (Organic Growth System)
    "PainScannerAgent",
    "EmotionWatcherAgent",
    "TrendHunterAgent",
    "SceneDiscoverAgent",
    # P0 Orchestrator
    "P0OrchestratorAgent",
    "SharedMemory",
    # P0 Scheduler
    "P0SyncScheduler",
    "P0ScheduleConfig",
    "SyncExecutionRecord",
    "SyncStatus",
    "p0_sync_scheduler",
    "setup_default_p0_schedule",
    # P1 Value Judgment Layer Agents
    "PainpointValueAgent",
    "EmotionAlignmentAgent",
    "TrendValueAgent",
    "DemandAssessmentAgent",
    "ValueAssessment",
    "ValueJudgmentReport",
    "ValuePriority",
    # P2 Relationship Layer Agents
    "TrustBuilderAgent",
    "CommunityBinderAgent",
    "ViralEngineAgent",
    "InfluenceNetworkAgent",
    "RelationshipPlan",
    "RelationshipReport",
    "TrustLevel",
    # P3 Feedback Loop System
    "FeedbackCollector",
    "PatternAnalyzer",
    "LearningEngine",
    "FeedbackLoopOrchestrator",
    "FeedbackRecord",
    "LearningInsight",
    "SystemLearningState",
    "FeedbackType",
    "LearningAction",
    # P3 Evolution Layer
    "EvolutionOrchestrator",
    "StrategyPopulation",
    "MetaLearningEngine",
    "LongTermMemory",
    "AgentStrategy",
    "StrategyGene",
    "EvolutionReport",
    "MetaLearningRecord",
    "EvolutionType",
    "MutationType",
    "evolution_orchestrator",
    "initialize_p3_evolution",
    "run_evolution_cycle",
    # P3 Scheduler
    "P3EvolutionScheduler",
    "EvolutionScheduleConfig",
    "EvolutionExecutionRecord",
    "EvolutionScheduleType",
    "p3_evolution_scheduler",
    "setup_default_p3_schedule",
    # Xiaohongshu researcher skill (lazy loaded)
    # "XiaohongshuResearcherSkill",
    # "research_xiaohongshu",
]


def __getattr__(name):
    """Lazy loading of xiaohongshu_researcher to avoid circular dependency."""
    if name in ("XiaohongshuResearcherSkill", "research_xiaohongshu"):
        from open_notebook.skills.xiaohongshu_researcher import (
            XiaohongshuResearcherSkill,
            research_xiaohongshu,
        )
        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
