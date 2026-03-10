"""Goal Tracker - OKR/KPI and weekly goal management.

Provides goal setting, progress tracking, and automatic progress reports.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any

from loguru import logger


class GoalType(str, Enum):
    """Types of goals."""
    OKR_OBJECTIVE = "okr_objective"  # OKR Objectives
    OKR_KEY_RESULT = "okr_key_result"  # OKR Key Results
    WEEKLY_GOAL = "weekly_goal"  # Weekly goals
    DAILY_TASK = "daily_task"  # Daily tasks
    KPI_METRIC = "kpi_metric"  # KPI metrics
    HABIT = "habit"  # Habit tracking


class GoalStatus(str, Enum):
    """Status of a goal."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    AT_RISK = "at_risk"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class Goal:
    """A goal definition."""
    goal_id: str
    title: str
    description: str
    goal_type: GoalType
    status: GoalStatus
    created_at: datetime
    target_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0  # 0-100
    parent_goal_id: Optional[str] = None  # For OKR hierarchy
    related_sessions: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "title": self.title,
            "description": self.description,
            "goal_type": self.goal_type.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.progress,
            "parent_goal_id": self.parent_goal_id,
            "related_sessions": self.related_sessions,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Goal":
        return cls(
            goal_id=data["goal_id"],
            title=data["title"],
            description=data.get("description", ""),
            goal_type=GoalType(data["goal_type"]),
            status=GoalStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            target_date=datetime.fromisoformat(data["target_date"]) if data.get("target_date") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            progress=data.get("progress", 0.0),
            parent_goal_id=data.get("parent_goal_id"),
            related_sessions=data.get("related_sessions", []),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )


@dataclass
class WeeklyPlan:
    """Weekly plan with goals."""
    week_id: str  # YYYY-WW format
    start_date: datetime
    end_date: datetime
    goals: List[Goal] = field(default_factory=list)
    focus_areas: List[str] = field(default_factory=list)
    notes: str = ""
    review_completed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "week_id": self.week_id,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "goals": [g.to_dict() for g in self.goals],
            "focus_areas": self.focus_areas,
            "notes": self.notes,
            "review_completed": self.review_completed,
        }


@dataclass
class GoalProgress:
    """Progress tracking for goals."""
    total_goals: int
    completed_goals: int
    in_progress_goals: int
    at_risk_goals: int
    overall_progress: float
    by_type: Dict[str, Dict[str, Any]]
    weekly_velocity: float  # Goals completed per week
    trend: str  # improving, stable, declining


class GoalTracker:
    """Goal tracking system for OKR/KPI and weekly planning.

    Usage:
        tracker = GoalTracker("~/.claude/work_logs")

        # Create weekly goals
        tracker.create_weekly_goal(
            title="Complete Work Logger Skill",
            description="Implement all features A, B, C",
            week_id="2026-10"
        )

        # Update progress
        tracker.update_progress(goal_id, progress=75)

        # Get weekly report
        report = tracker.get_weekly_report("2026-10")
    """

    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path).expanduser()
        self.goals_dir = self.workspace_path / "goals"
        self.goals_dir.mkdir(parents=True, exist_ok=True)
        self.weekly_dir = self.workspace_path / "weekly_plans"
        self.weekly_dir.mkdir(parents=True, exist_ok=True)

    def _get_goals_file(self, goal_type: GoalType) -> Path:
        """Get goals file for a specific type."""
        return self.goals_dir / f"{goal_type.value}.json"

    def _get_weekly_file(self, week_id: str) -> Path:
        """Get weekly plan file."""
        year, week = week_id.split("-")
        return self.weekly_dir / f"{year}" / f"week_{week}.json"

    def create_goal(
        self,
        title: str,
        description: str,
        goal_type: GoalType,
        target_date: Optional[datetime] = None,
        parent_goal_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Goal:
        """Create a new goal."""
        goal = Goal(
            goal_id=f"goal_{datetime.now().timestamp()}",
            title=title,
            description=description,
            goal_type=goal_type,
            status=GoalStatus.NOT_STARTED,
            created_at=datetime.now(),
            target_date=target_date,
            parent_goal_id=parent_goal_id,
            tags=tags or [],
        )

        self._save_goal(goal)
        logger.info(f"Created goal: {title}")
        return goal

    def create_weekly_goal(
        self,
        title: str,
        description: str = "",
        week_id: Optional[str] = None,
    ) -> Goal:
        """Create a goal for current or specified week."""
        if week_id is None:
            now = datetime.now()
            week_id = f"{now.year}-{now.isocalendar()[1]:02d}"

        goal = self.create_goal(
            title=title,
            description=description,
            goal_type=GoalType.WEEKLY_GOAL,
            tags=[f"week_{week_id}"],
        )

        # Add to weekly plan
        weekly_plan = self.get_or_create_weekly_plan(week_id)
        weekly_plan.goals.append(goal)
        self._save_weekly_plan(weekly_plan)

        return goal

    def create_okr(
        self,
        objective: str,
        key_results: List[str],
        quarter: str,  # e.g., "2026-Q1"
    ) -> List[Goal]:
        """Create OKR with objective and key results."""
        # Create objective
        objective_goal = self.create_goal(
            title=objective,
            description=f"OKR Objective for {quarter}",
            goal_type=GoalType.OKR_OBJECTIVE,
            tags=[quarter],
        )

        # Create key results
        kr_goals = []
        for i, kr in enumerate(key_results, 1):
            kr_goal = self.create_goal(
                title=kr,
                description=f"Key Result {i} for: {objective}",
                goal_type=GoalType.OKR_KEY_RESULT,
                parent_goal_id=objective_goal.goal_id,
                tags=[quarter],
            )
            kr_goals.append(kr_goal)

        return [objective_goal] + kr_goals

    def _save_goal(self, goal: Goal) -> None:
        """Save a goal to disk."""
        goals_file = self._get_goals_file(goal.goal_type)
        goals_file.parent.mkdir(parents=True, exist_ok=True)

        goals = []
        if goals_file.exists():
            try:
                with open(goals_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    goals = [Goal.from_dict(g) for g in data.get("goals", [])]
            except Exception:
                pass

        # Update or add goal
        existing = [g for g in goals if g.goal_id == goal.goal_id]
        if existing:
            goals[goals.index(existing[0])] = goal
        else:
            goals.append(goal)

        with open(goals_file, "w", encoding="utf-8") as f:
            json.dump({"goals": [g.to_dict() for g in goals]}, f, indent=2, ensure_ascii=False)

    def _save_weekly_plan(self, plan: WeeklyPlan) -> None:
        """Save weekly plan to disk."""
        weekly_file = self._get_weekly_file(plan.week_id)
        weekly_file.parent.mkdir(parents=True, exist_ok=True)

        with open(weekly_file, "w", encoding="utf-8") as f:
            json.dump(plan.to_dict(), f, indent=2, ensure_ascii=False)

    def get_or_create_weekly_plan(self, week_id: str) -> WeeklyPlan:
        """Get or create weekly plan."""
        weekly_file = self._get_weekly_file(week_id)

        if weekly_file.exists():
            try:
                with open(weekly_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return WeeklyPlan(
                        week_id=data["week_id"],
                        start_date=datetime.fromisoformat(data["start_date"]),
                        end_date=datetime.fromisoformat(data["end_date"]),
                        goals=[Goal.from_dict(g) for g in data.get("goals", [])],
                        focus_areas=data.get("focus_areas", []),
                        notes=data.get("notes", ""),
                        review_completed=data.get("review_completed", False),
                    )
            except Exception:
                pass

        # Create new weekly plan
        year, week = map(int, week_id.split("-"))
        # Calculate start of week (Monday)
        start = datetime.strptime(f"{year}-W{week}-1", "%Y-W%W-%w")
        end = start + timedelta(days=6)

        return WeeklyPlan(
            week_id=week_id,
            start_date=start,
            end_date=end,
        )

    def update_progress(self, goal_id: str, progress: float) -> Optional[Goal]:
        """Update goal progress."""
        for goal_type in GoalType:
            goals_file = self._get_goals_file(goal_type)
            if not goals_file.exists():
                continue

            try:
                with open(goals_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    goals = [Goal.from_dict(g) for g in data.get("goals", [])]

                for goal in goals:
                    if goal.goal_id == goal_id or goal.goal_id.startswith(goal_id):
                        goal.progress = max(0.0, min(100.0, progress))
                        if goal.progress >= 100:
                            goal.status = GoalStatus.COMPLETED
                            goal.completed_at = datetime.now()
                        elif goal.progress > 0:
                            goal.status = GoalStatus.IN_PROGRESS

                        self._save_goal(goal)
                        return goal
            except Exception:
                continue

        return None

    def link_session_to_goal(self, goal_id: str, session_id: str) -> bool:
        """Link a work session to a goal."""
        for goal_type in GoalType:
            goals_file = self._get_goals_file(goal_type)
            if not goals_file.exists():
                continue

            try:
                with open(goals_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    goals = [Goal.from_dict(g) for g in data.get("goals", [])]

                for goal in goals:
                    if goal.goal_id == goal_id:
                        if session_id not in goal.related_sessions:
                            goal.related_sessions.append(session_id)
                            self._save_goal(goal)
                        return True
            except Exception:
                continue

        return False

    def get_goal_progress(self) -> GoalProgress:
        """Calculate overall goal progress."""
        all_goals = []

        for goal_type in GoalType:
            goals_file = self._get_goals_file(goal_type)
            if goals_file.exists():
                try:
                    with open(goals_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        all_goals.extend([Goal.from_dict(g) for g in data.get("goals", [])])
                except Exception:
                    pass

        if not all_goals:
            return GoalProgress(
                total_goals=0,
                completed_goals=0,
                in_progress_goals=0,
                at_risk_goals=0,
                overall_progress=0.0,
                by_type={},
                weekly_velocity=0.0,
                trend="stable",
            )

        # Calculate stats
        total = len(all_goals)
        completed = sum(1 for g in all_goals if g.status == GoalStatus.COMPLETED)
        in_progress = sum(1 for g in all_goals if g.status == GoalStatus.IN_PROGRESS)
        at_risk = sum(1 for g in all_goals if g.status == GoalStatus.AT_RISK)

        avg_progress = sum(g.progress for g in all_goals) / total

        # Stats by type
        by_type = {}
        for goal_type in GoalType:
            type_goals = [g for g in all_goals if g.goal_type == goal_type]
            if type_goals:
                by_type[goal_type.value] = {
                    "total": len(type_goals),
                    "completed": sum(1 for g in type_goals if g.status == GoalStatus.COMPLETED),
                    "avg_progress": sum(g.progress for g in type_goals) / len(type_goals),
                }

        # Calculate weekly velocity (completed goals in last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        recent_completed = sum(
            1 for g in all_goals
            if g.status == GoalStatus.COMPLETED and g.completed_at and g.completed_at > week_ago
        )

        # Simple trend calculation
        trend = "stable"
        if recent_completed > 2:
            trend = "improving"
        elif recent_completed == 0 and in_progress > 0:
            trend = "declining"

        return GoalProgress(
            total_goals=total,
            completed_goals=completed,
            in_progress_goals=in_progress,
            at_risk_goals=at_risk,
            overall_progress=avg_progress,
            by_type=by_type,
            weekly_velocity=recent_completed,
            trend=trend,
        )

    def get_weekly_report(self, week_id: Optional[str] = None) -> str:
        """Generate weekly progress report."""
        if week_id is None:
            now = datetime.now()
            week_id = f"{now.year}-{now.isocalendar()[1]:02d}"

        plan = self.get_or_create_weekly_plan(week_id)
        progress = self.get_goal_progress()

        report = f"""# Weekly Report - Week {week_id}

## Goals Progress
- **Total Goals**: {progress.total_goals}
- **Completed**: {progress.completed_goals} ({progress.completed_goals/max(progress.total_goals,1)*100:.0f}%)
- **In Progress**: {progress.in_progress_goals}
- **At Risk**: {progress.at_risk_goals}
- **Overall Progress**: {progress.overall_progress:.1f}%
- **Weekly Velocity**: {progress.weekly_velocity} goals/week
- **Trend**: {progress.trend}

## This Week's Goals
"""

        for goal in plan.goals:
            status_icon = "[x]" if goal.status == GoalStatus.COMPLETED else "[ ]"
            if goal.status == GoalStatus.IN_PROGRESS:
                status_icon = "[~]"
            report += f"{status_icon} {goal.title} ({goal.progress:.0f}%)\n"

        if plan.focus_areas:
            report += "\n## Focus Areas\n"
            for area in plan.focus_areas:
                report += f"- {area}\n"

        if plan.notes:
            report += f"\n## Notes\n{plan.notes}\n"

        return report

    def generate_okr_report(self, quarter: str) -> str:
        """Generate OKR progress report."""
        # Load all OKR goals
        all_goals = []
        okr_file = self._get_goals_file(GoalType.OKR_OBJECTIVE)
        if okr_file.exists():
            try:
                with open(okr_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    all_goals.extend([Goal.from_dict(g) for g in data.get("goals", [])])
            except Exception:
                pass

        kr_file = self._get_goals_file(GoalType.OKR_KEY_RESULT)
        if kr_file.exists():
            try:
                with open(kr_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    all_goals.extend([Goal.from_dict(g) for g in data.get("goals", [])])
            except Exception:
                pass

        # Filter by quarter
        quarter_goals = [g for g in all_goals if quarter in g.tags]

        report = f"""# OKR Report - {quarter}

## Objectives
"""

        objectives = [g for g in quarter_goals if g.goal_type == GoalType.OKR_OBJECTIVE]
        for obj in objectives:
            krs = [g for g in quarter_goals if g.parent_goal_id == obj.goal_id]
            avg_kr_progress = sum(kr.progress for kr in krs) / len(krs) if krs else 0

            report += f"\n### {obj.title}\n"
            report += f"**Progress**: {avg_kr_progress:.0f}%\n\n"

            if krs:
                report += "**Key Results**:\n"
                for kr in krs:
                    status = "[x]" if kr.status == GoalStatus.COMPLETED else f"[{kr.progress:.0f}%]"
                    report += f"  {status} {kr.title}\n"

        return report
