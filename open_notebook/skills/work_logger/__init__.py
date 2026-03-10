"""Work Logger Skill - Automatic work tracking and periodic review system.

This skill provides:
1. Automatic work session recording
2. Git activity tracking
3. Context-aware logging
4. Scheduled review prompts
5. Mood tracking
6. Task scheduling
7. Goal management (OKR/KPI)
8. AI insights
9. Export capabilities

Usage:
    config = SkillConfig(
        skill_type="work_logger",
        name="Daily Work Logger",
        parameters={
            "workspace_path": "~/work_logs",
            "auto_git_track": True,
            "review_schedule": "daily:18:00,weekly:friday:17:00"
        }
    )
"""

from open_notebook.skills.work_logger.work_logger import WorkLoggerSkill
from open_notebook.skills.work_logger.context_engine import ContextEngine
from open_notebook.skills.work_logger.review_scheduler import ReviewScheduler
from open_notebook.skills.work_logger.task_scheduler import WorkLoggerScheduler, ScheduleType
from open_notebook.skills.work_logger.mood_tracker import (
    MoodTracker,
    MoodLevel,
    EnergyLevel,
    FocusLevel,
    MoodEntry,
    MoodInsights,
)
from open_notebook.skills.work_logger.goal_tracker import (
    GoalTracker,
    Goal,
    GoalType,
    GoalStatus,
    GoalProgress,
    WeeklyPlan,
)
from open_notebook.skills.work_logger.ai_insights import (
    AIInsightsEngine,
    WorkPattern,
    EfficiencyInsight,
    ProductivityMetrics,
)
from open_notebook.skills.work_logger.export_manager import (
    ExportManager,
    EmailConfig,
)
from open_notebook.skills.registry import register_skill

# Register the skill
register_skill(WorkLoggerSkill)

__all__ = [
    # Core
    "WorkLoggerSkill",
    "ContextEngine",
    "ReviewScheduler",
    # Scheduler
    "WorkLoggerScheduler",
    "ScheduleType",
    # Mood
    "MoodTracker",
    "MoodLevel",
    "EnergyLevel",
    "FocusLevel",
    "MoodEntry",
    "MoodInsights",
    # Goals (G)
    "GoalTracker",
    "Goal",
    "GoalType",
    "GoalStatus",
    "GoalProgress",
    "WeeklyPlan",
    # AI Insights (F)
    "AIInsightsEngine",
    "WorkPattern",
    "EfficiencyInsight",
    "ProductivityMetrics",
    # Export (H)
    "ExportManager",
    "EmailConfig",
]
