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
from open_notebook.skills.weekly_evolution_analyzer import WeeklyEvolutionAnalyzer, analyze_evolution
from open_notebook.skills.weekly_evolution_scheduler import (
    WeeklyEvolutionScheduler,
    run_weekly_evolution,
    start_weekly_scheduler,
)
from open_notebook.skills.performance_tracker import (
    PerformanceTracker,
    track_content_performance,
    get_platform_stats,
    compare_platforms,
)
from open_notebook.skills.report_generator import (
    ReportGenerator,
    generate_visualized_report,
)
from open_notebook.skills.one_click_report_generator import (
    OneClickReportGenerator,
    create_study_guide,
    create_literature_review,
    create_research_digest,
    create_weekly_trends,
    create_concept_map,
)
from open_notebook.skills.cross_document_insights import (
    CrossDocumentAnalyzer,
    analyze_cross_document_themes,
    detect_contradictions,
    identify_research_trends,
    generate_weekly_trends_report,
)
from open_notebook.skills.visual_knowledge_graph import (
    VisualKnowledgeGraphGenerator,
    create_mind_map,
    create_timeline,
    create_network_graph,
    create_topic_chart,
)
from open_notebook.skills.batch_importer import (
    BatchImporter,
    batch_import_files,
    batch_import_urls,
    import_zotero_library,
    import_mendeley_library,
)
from open_notebook.skills.performance_optimizer import (
    PerformanceOptimizer,
    PerformanceMonitor,
    DatabaseOptimizer,
    AsyncTaskQueue,
    LRUCache,
    cached,
    optimize_database_queries,
    create_task_queue,
    get_performance_report,
)
from open_notebook.skills.ui_integration import (
    UIManager,
    NotificationManager,
    ActionType,
    get_ui_actions,
    execute_ui_action,
    send_notification,
    get_task_progress,
)
from open_notebook.skills.collaboration_tools import (
    CollaborationManager,
    SessionManager,
    Permission,
    ChangeType,
    share_with_user,
    accept_share_invite,
    can_access,
    get_notebook_collaborators,
    add_comment_to_notebook,
    get_notebook_comments,
    create_collaboration_session,
)
from open_notebook.skills.multi_platform_ai_researcher import (
    MultiPlatformAIResearcher,
    collect_multi_platform_ai_tools,
)
from open_notebook.skills.multi_platform_ai_researcher.daily_report_generator import DailyReportGenerator, generate_daily_report
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
    # Weekly Evolution System
    "WeeklyEvolutionAnalyzer",
    "analyze_evolution",
    "WeeklyEvolutionScheduler",
    "run_weekly_evolution",
    "start_weekly_scheduler",
    # Performance Tracking
    "PerformanceTracker",
    "track_content_performance",
    "get_platform_stats",
    "compare_platforms",
    # Report Generation
    "ReportGenerator",
    "generate_visualized_report",
    # One-Click Report Generator (P0)
    "OneClickReportGenerator",
    "create_study_guide",
    "create_literature_review",
    "create_research_digest",
    "create_weekly_trends",
    "create_concept_map",
    # Cross-Document Insights (P0)
    "CrossDocumentAnalyzer",
    "analyze_cross_document_themes",
    "detect_contradictions",
    "identify_research_trends",
    "generate_weekly_trends_report",
    # Visual Knowledge Graph (P1)
    "VisualKnowledgeGraphGenerator",
    "create_mind_map",
    "create_timeline",
    "create_network_graph",
    "create_topic_chart",
    # Batch Importer (P1)
    "BatchImporter",
    "batch_import_files",
    "batch_import_urls",
    "import_zotero_library",
    "import_mendeley_library",
    # Performance Optimizer (C)
    "PerformanceOptimizer",
    "PerformanceMonitor",
    "DatabaseOptimizer",
    "AsyncTaskQueue",
    "LRUCache",
    "cached",
    "optimize_database_queries",
    "create_task_queue",
    "get_performance_report",
    # UI Integration (B)
    "UIManager",
    "NotificationManager",
    "ActionType",
    "get_ui_actions",
    "execute_ui_action",
    "send_notification",
    "get_task_progress",
    # Collaboration Tools (A - P2)
    "CollaborationManager",
    "SessionManager",
    "Permission",
    "ChangeType",
    "share_with_user",
    "accept_share_invite",
    "can_access",
    "get_notebook_collaborators",
    "add_comment_to_notebook",
    "get_notebook_comments",
    "create_collaboration_session",
    # Multi-Platform AI Researcher
    "MultiPlatformAIResearcher",
    "collect_multi_platform_ai_tools",
    # Daily Report Generator
    "DailyReportGenerator",
    "generate_daily_report",
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
