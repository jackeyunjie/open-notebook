"""Work Logger Skill - Main skill implementation.

Provides automatic work tracking, context building, and conversation-driven reviews.
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from loguru import logger

from open_notebook.skills.base import Skill, SkillConfig, SkillContext, SkillResult, SkillStatus
from open_notebook.skills.work_logger.models import (
    WorkSession, DailySummary, GitActivity, FileActivity,
    SessionType, SessionStatus, ReviewTemplate
)
from open_notebook.skills.work_logger.context_engine import ContextEngine
from open_notebook.skills.work_logger.review_scheduler import ReviewScheduler
from open_notebook.skills.work_logger.mood_tracker import (
    MoodTracker, MoodLevel, EnergyLevel, FocusLevel
)
from open_notebook.skills.work_logger.task_scheduler import WorkLoggerScheduler, ScheduleType


class WorkLoggerSkill(Skill):
    """Work logging and review skill.

    Automatically tracks work activity, maintains structured logs,
    and facilitates periodic reviews through conversation.

    Features:
    - Automatic git and file tracking
    - Structured work sessions
    - Daily/weekly/monthly review prompts
    - Context-aware conversation
    - Markdown export

    Parameters:
        - workspace_path: Where to store work logs (default: ~/.work_logger)
        - project_paths: List of project paths to monitor
        - auto_git_track: Enable automatic git tracking
        - auto_file_track: Enable automatic file tracking
        - review_schedule: Review schedule configuration
        - current_action: Action to perform (start_session, end_session, get_daily, review, etc.)

    Example:
        config = SkillConfig(
            skill_type="work_logger",
            name="My Work Logger",
            parameters={
                "workspace_path": "~/work_logs",
                "project_paths": ["~/projects/open-notebook"],
                "current_action": "start_session",
                "session_title": "Implementing new feature"
            }
        )
    """

    skill_type = "work_logger"
    name = "Work Logger"
    description = "Automatic work tracking and periodic review system"

    parameters_schema = {
        "workspace_path": {
            "type": "string",
            "default": "~/.work_logger",
            "description": "Path to store work logs"
        },
        "project_paths": {
            "type": "array",
            "items": {"type": "string"},
            "default": [],
            "description": "List of project paths to monitor"
        },
        "auto_git_track": {
            "type": "boolean",
            "default": True,
            "description": "Enable automatic git tracking"
        },
        "auto_file_track": {
            "type": "boolean",
            "default": True,
            "description": "Enable automatic file tracking"
        },
        "current_action": {
            "type": "string",
            "enum": [
                "start_session", "end_session", "pause_session", "resume_session",
                "get_daily", "get_weekly", "get_sessions",
                "review_daily", "review_weekly", "review_monthly",
                "check_reviews", "export_daily", "get_context",
                "log_mood", "get_mood_report", "mood_check_in"
            ],
            "description": "Action to perform"
        },
        "session_title": {
            "type": "string",
            "description": "Title for new session"
        },
        "session_type": {
            "type": "string",
            "enum": ["coding", "research", "writing", "meeting", "review", "planning", "other"],
            "default": "coding",
            "description": "Type of work session"
        },
        "session_project": {
            "type": "string",
            "description": "Project name for session"
        },
        "session_tags": {
            "type": "array",
            "items": {"type": "string"},
            "default": [],
            "description": "Tags for session"
        },
        "review_answers": {
            "type": "object",
            "description": "Answers to review questions"
        },
        "mood": {
            "type": "string",
            "enum": ["excellent", "good", "neutral", "tired", "stressed"],
            "description": "Mood level for log_mood action"
        },
        "energy": {
            "type": "integer",
            "minimum": 1,
            "maximum": 5,
            "description": "Energy level (1-5)"
        },
        "focus": {
            "type": "integer",
            "minimum": 1,
            "maximum": 5,
            "description": "Focus level (1-5)"
        },
        "stress": {
            "type": "integer",
            "minimum": 1,
            "maximum": 10,
            "description": "Stress level (1-10)"
        },
        "satisfaction": {
            "type": "integer",
            "minimum": 1,
            "maximum": 10,
            "description": "Satisfaction level (1-10)"
        },
        "mood_notes": {
            "type": "string",
            "description": "Notes for mood entry"
        }
    }

    def __init__(self, config: SkillConfig):
        super().__init__(config)
        self.workspace_path = Path(self.get_param("workspace_path", "~/.work_logger")).expanduser()
        self.project_paths = [Path(p).expanduser() for p in self.get_param("project_paths", [])]
        self.auto_git_track = self.get_param("auto_git_track", True)
        self.auto_file_track = self.get_param("auto_file_track", True)

        # Initialize workspace structure
        self._init_workspace()

        # Initialize components
        self.context_engines = [ContextEngine(str(p)) for p in self.project_paths if p.exists()]
        self.review_scheduler = ReviewScheduler(str(self.workspace_path))
        self.mood_tracker = MoodTracker(str(self.workspace_path))
        self.task_scheduler = WorkLoggerScheduler(str(self.workspace_path))

        # Track active session
        self._active_session: Optional[WorkSession] = None

    def _init_workspace(self) -> None:
        """Initialize workspace directory structure."""
        # Create directory structure
        (self.workspace_path / "sessions").mkdir(parents=True, exist_ok=True)
        (self.workspace_path / "daily").mkdir(parents=True, exist_ok=True)
        (self.workspace_path / "weekly").mkdir(parents=True, exist_ok=True)
        (self.workspace_path / "projects").mkdir(parents=True, exist_ok=True)
        (self.workspace_path / "templates").mkdir(parents=True, exist_ok=True)

        # Create default templates
        self._create_default_templates()

    def _create_default_templates(self) -> None:
        """Create default review templates."""
        templates_dir = self.workspace_path / "templates"

        # Daily template
        daily_template = templates_dir / "daily.md"
        if not daily_template.exists():
            daily_template.write_text("""# Daily Work Log - {{date}}

## Sessions
{{sessions}}

## Git Activity
{{git_activity}}

## Summary
{{summary}}

## Tomorrow's Plan
{{next_plan}}
""", encoding="utf-8")

        # Weekly template
        weekly_template = templates_dir / "weekly.md"
        if not weekly_template.exists():
            weekly_template.write_text("""# Weekly Review - Week {{week}}

## Daily Summaries
{{daily_summaries}}

## Key Achievements
{{achievements}}

## Challenges & Solutions
{{challenges}}

## Next Week Goals
{{next_goals}}
""", encoding="utf-8")

    def _get_session_file_path(self, session: WorkSession) -> Path:
        """Get file path for a session."""
        date_dir = self.workspace_path / "sessions" / session.start_time.strftime("%Y/%m/%d")
        date_dir.mkdir(parents=True, exist_ok=True)
        return date_dir / f"{session.start_time.strftime('%H-%M')}-{session.session_id[:8]}.json"

    def _get_daily_file_path(self, date: datetime) -> Path:
        """Get file path for daily summary."""
        return self.workspace_path / "daily" / f"{date.strftime('%Y-%m-%d')}.json"

    def _save_session(self, session: WorkSession) -> None:
        """Save session to disk."""
        session_file = self._get_session_file_path(session)
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)

    def _load_session(self, session_id: str) -> Optional[WorkSession]:
        """Load session from disk by partial ID."""
        sessions_dir = self.workspace_path / "sessions"
        for session_file in sessions_dir.rglob("*.json"):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("session_id", "").startswith(session_id):
                    # Reconstruct session (simplified)
                    return self._dict_to_session(data)
            except Exception:
                continue
        return None

    def _dict_to_session(self, data: Dict) -> WorkSession:
        """Convert dictionary to WorkSession."""
        return WorkSession(
            session_id=data["session_id"],
            start_time=datetime.fromisoformat(data["start_time"]),
            session_type=SessionType(data.get("session_type", "other")),
            title=data.get("title", "Untitled"),
            description=data.get("description", ""),
            project=data.get("project"),
            tags=data.get("tags", []),
            status=SessionStatus(data.get("status", "completed")),
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            related_files=data.get("related_files", []),
            context_notes=data.get("context_notes", ""),
        )

    def _save_daily_summary(self, summary: DailySummary) -> None:
        """Save daily summary to disk."""
        daily_file = self._get_daily_file_path(datetime.strptime(summary.date, "%Y-%m-%d"))
        with open(daily_file, "w", encoding="utf-8") as f:
            json.dump(summary.to_dict(), f, indent=2, ensure_ascii=False)

    def _load_daily_summary(self, date: datetime) -> Optional[DailySummary]:
        """Load daily summary from disk."""
        daily_file = self._get_daily_file_path(date)
        if daily_file.exists():
            try:
                with open(daily_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return DailySummary(**data)
            except Exception as e:
                logger.error(f"Failed to load daily summary: {e}")
        return None

    def _get_today_sessions(self) -> List[WorkSession]:
        """Get all sessions for today."""
        today = datetime.now()
        sessions_dir = self.workspace_path / "sessions" / today.strftime("%Y/%m/%d")

        sessions = []
        if sessions_dir.exists():
            for session_file in sessions_dir.glob("*.json"):
                try:
                    with open(session_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    sessions.append(self._dict_to_session(data))
                except Exception:
                    continue

        return sorted(sessions, key=lambda s: s.start_time)

    def _build_daily_summary(self, date: datetime) -> DailySummary:
        """Build daily summary from sessions."""
        sessions = self._get_today_sessions()

        # Calculate statistics
        total_commits = sum(len(s.git_activities) for s in sessions)
        files_modified = len(set(
            f.file_path for s in sessions for f in s.file_activities
        ))
        lines_added = sum(
            sum(ga.insertions for ga in s.git_activities) for s in sessions
        )
        lines_deleted = sum(
            sum(ga.deletions for ga in s.git_activities) for s in sessions
        )
        projects = list(set(s.project for s in sessions if s.project))

        return DailySummary(
            date=date.strftime("%Y-%m-%d"),
            sessions=sessions,
            total_commits=total_commits,
            files_modified=files_modified,
            lines_added=lines_added,
            lines_deleted=lines_deleted,
            projects_worked=projects,
        )

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute work logger action."""
        action = self.get_param("current_action", "get_daily")
        start_time = datetime.utcnow()

        try:
            if action == "start_session":
                return await self._action_start_session(context)
            elif action == "end_session":
                return await self._action_end_session(context)
            elif action == "get_daily":
                return await self._action_get_daily(context)
            elif action == "get_weekly":
                return await self._action_get_weekly(context)
            elif action == "check_reviews":
                return await self._action_check_reviews(context)
            elif action == "review_daily":
                return await self._action_review_daily(context)
            elif action == "export_daily":
                return await self._action_export_daily(context)
            elif action == "get_context":
                return await self._action_get_context(context)
            elif action == "log_mood":
                return await self._action_log_mood(context)
            elif action == "get_mood_report":
                return await self._action_get_mood_report(context)
            elif action == "mood_check_in":
                return await self._action_mood_check_in(context)
            else:
                return SkillResult(
                    skill_id=context.skill_id,
                    status=SkillStatus.FAILED,
                    started_at=start_time,
                    completed_at=datetime.utcnow(),
                    error_message=f"Unknown action: {action}"
                )

        except Exception as e:
            logger.error(f"Work logger action failed: {e}")
            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.FAILED,
                started_at=start_time,
                completed_at=datetime.utcnow(),
                error_message=str(e)
            )

    async def _action_start_session(self, context: SkillContext) -> SkillResult:
        """Start a new work session."""
        title = self.get_param("session_title", "Untitled Session")
        session_type = SessionType(self.get_param("session_type", "coding"))
        project = self.get_param("session_project")
        tags = self.get_param("session_tags", [])

        # Build context from all project engines
        git_activities = []
        file_activities = []
        context_snapshots = []

        for engine in self.context_engines:
            snapshot = engine.build_context_snapshot()
            context_snapshots.append(snapshot)
            # Get recent activity
            git_activities.extend(engine.get_git_activity(since_hours=1))
            file_activities.extend(engine.get_file_activity(since_hours=1))

        # Create session
        session = WorkSession(
            session_id=str(uuid.uuid4()),
            start_time=datetime.now(),
            session_type=session_type,
            title=title,
            project=project,
            tags=tags,
            status=SessionStatus.ACTIVE,
            git_activities=git_activities,
            file_activities=file_activities,
        )

        self._active_session = session
        self._save_session(session)

        # Build response
        recent_commits = len(git_activities)
        recent_files = len(file_activities)

        return SkillResult(
            skill_id=context.skill_id,
            status=SkillStatus.SUCCESS,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            output={
                "session_id": session.session_id,
                "action": "started",
                "title": title,
                "type": session_type.value,
                "recent_commits": recent_commits,
                "recent_files": recent_files,
                "projects": [e.project_path.name for e in self.context_engines],
                "message": f"[开始] 工作会话: {title}\n最近1小时: {recent_commits}次提交, {recent_files}个文件修改"
            }
        )

    async def _action_end_session(self, context: SkillContext) -> SkillResult:
        """End the current work session."""
        if not self._active_session:
            # Try to load last active session
            sessions = self._get_today_sessions()
            active_sessions = [s for s in sessions if s.status == SessionStatus.ACTIVE]
            if active_sessions:
                self._active_session = active_sessions[-1]
            else:
                return SkillResult(
                    skill_id=context.skill_id,
                    status=SkillStatus.FAILED,
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    error_message="No active session to end"
                )

        session = self._active_session
        session.end_time = datetime.now()
        session.status = SessionStatus.COMPLETED

        # Update with latest activity
        for engine in self.context_engines:
            session.git_activities.extend(engine.get_git_activity(since_hours=1))
            session.file_activities.extend(engine.get_file_activity(since_hours=1))

        self._save_session(session)
        self._active_session = None

        duration = session.duration_minutes

        return SkillResult(
            skill_id=context.skill_id,
            status=SkillStatus.SUCCESS,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            output={
                "session_id": session.session_id,
                "action": "ended",
                "title": session.title,
                "duration_minutes": duration,
                "total_commits": len(session.git_activities),
                "message": f"[结束] 工作会话: {session.title}\n时长: {duration:.0f}分钟\n提交: {len(session.git_activities)}次"
            }
        )

    async def _action_get_daily(self, context: SkillContext) -> SkillResult:
        """Get daily summary."""
        today = datetime.now()
        summary = self._build_daily_summary(today)

        # Build readable output
        sessions_info = []
        for s in summary.sessions:
            duration = f"{s.duration_minutes:.0f}min" if s.duration_minutes else "ongoing"
            sessions_info.append(f"  • {s.title} ({s.session_type.value}, {duration})")

        output_text = f"""# 今日工作 ({summary.date})

## 统计
- 工作会话: {len(summary.sessions)} 个
- Git提交: {summary.total_commits} 次
- 文件修改: {summary.files_modified} 个
- 代码行: +{summary.lines_added}/-{summary.lines_deleted}
- 项目: {', '.join(summary.projects_worked) or 'N/A'}

## 会话详情
{chr(10).join(sessions_info) or "  (暂无会话)"}

## 关键成果
{chr(10).join(f"  - {a}" for a in summary.key_achievements) or "  (待填写)"}

## 阻碍
{chr(10).join(f"  - {b}" for b in summary.blockers) or "  (无)"}
"""

        return SkillResult(
            skill_id=context.skill_id,
            status=SkillStatus.SUCCESS,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            output={
                "date": summary.date,
                "summary": summary.to_dict(),
                "formatted": output_text
            }
        )

    async def _action_get_weekly(self, context: SkillContext) -> SkillResult:
        """Get weekly summary."""
        # Get last 7 days
        summaries = []
        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            daily = self._load_daily_summary(date)
            if daily:
                summaries.append(daily)

        total_sessions = sum(len(s.sessions) for s in summaries)
        total_commits = sum(s.total_commits for s in summaries)

        return SkillResult(
            skill_id=context.skill_id,
            status=SkillStatus.SUCCESS,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            output={
                "days_tracked": len(summaries),
                "total_sessions": total_sessions,
                "total_commits": total_commits,
                "daily_summaries": [s.to_dict() for s in summaries],
                "message": f"近7天: {len(summaries)}天有记录, {total_sessions}个会话, {total_commits}次提交"
            }
        )

    async def _action_check_reviews(self, context: SkillContext) -> SkillResult:
        """Check which reviews are due."""
        review_info = self.review_scheduler.get_next_review_info()

        due_reviews = []
        for review_type, info in review_info.items():
            if info["due"]:
                due_reviews.append(review_type)

        return SkillResult(
            skill_id=context.skill_id,
            status=SkillStatus.SUCCESS,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            output={
                "review_info": review_info,
                "due_reviews": due_reviews,
                "has_due_reviews": len(due_reviews) > 0,
                "message": f"待复盘: {', '.join(due_reviews) if due_reviews else '无'}"
            }
        )

    async def _action_review_daily(self, context: SkillContext) -> SkillResult:
        """Generate daily review prompt."""
        today = datetime.now()
        summary = self._build_daily_summary(today)

        # Build context for review
        review_context = {
            "sessions": summary.sessions,
            "date": summary.date,
        }

        prompt = self.review_scheduler.generate_review_prompt("daily", review_context)

        # Create template file
        daily_dir = self.workspace_path / "daily"
        self.review_scheduler.create_review_template_file("daily", daily_dir)

        return SkillResult(
            skill_id=context.skill_id,
            status=SkillStatus.SUCCESS,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            output={
                "review_type": "daily",
                "prompt": prompt,
                "questions": ReviewTemplate.DAILY.questions,
                "message": "已生成每日复盘模板"
            }
        )

    async def _action_export_daily(self, context: SkillContext) -> SkillResult:
        """Export daily summary to markdown."""
        today = datetime.now()
        summary = self._build_daily_summary(today)

        # Generate markdown
        md_content = f"""# Work Log - {summary.date}

## Overview
- **Sessions**: {len(summary.sessions)}
- **Commits**: {summary.total_commits}
- **Files Modified**: {summary.files_modified}
- **Lines**: +{summary.lines_added} / -{summary.lines_deleted}

## Sessions
"""

        for session in summary.sessions:
            duration = f"{session.duration_minutes:.0f}min" if session.duration_minutes else "ongoing"
            md_content += f"""
### {session.title}
- **Type**: {session.session_type.value}
- **Duration**: {duration}
- **Project**: {session.project or 'N/A'}
- **Tags**: {', '.join(session.tags) or 'N/A'}

{session.description}

"""

        # Save to file
        export_dir = self.workspace_path / "exports"
        export_dir.mkdir(exist_ok=True)
        export_file = export_dir / f"{summary.date}.md"
        export_file.write_text(md_content, encoding="utf-8")

        return SkillResult(
            skill_id=context.skill_id,
            status=SkillStatus.SUCCESS,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            output={
                "export_path": str(export_file),
                "content": md_content
            }
        )

    async def _action_get_context(self, context: SkillContext) -> SkillResult:
        """Get current context snapshot."""
        snapshots = []
        for engine in self.context_engines:
            snapshots.append(engine.build_context_snapshot())

        return SkillResult(
            skill_id=context.skill_id,
            status=SkillStatus.SUCCESS,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            output={
                "projects": len(snapshots),
                "snapshots": snapshots,
                "active_session": self._active_session.to_dict() if self._active_session else None
            }
        )

    async def _action_log_mood(self, context: SkillContext) -> SkillResult:
        """Log a mood entry."""
        mood = MoodLevel(self.get_param("mood", "neutral"))
        energy = EnergyLevel(self.get_param("energy", 3))
        focus = FocusLevel(self.get_param("focus", 3))
        stress = self.get_param("stress", 5)
        satisfaction = self.get_param("satisfaction", 5)
        notes = self.get_param("mood_notes", "")

        entry = self.mood_tracker.log_mood(
            mood=mood,
            energy=energy,
            focus=focus,
            stress=stress,
            satisfaction=satisfaction,
            notes=notes,
            session_id=self._active_session.session_id if self._active_session else None
        )

        return SkillResult(
            skill_id=context.skill_id,
            status=SkillStatus.SUCCESS,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            output={
                "entry_id": entry.entry_id,
                "mood": entry.mood.value,
                "energy": entry.energy.value,
                "focus": entry.focus.value,
                "message": f"Mood logged: {entry.mood.value}, Energy: {entry.energy.value}/5"
            }
        )

    async def _action_get_mood_report(self, context: SkillContext) -> SkillResult:
        """Get mood report."""
        report = self.mood_tracker.generate_mood_report(days=7)
        insights = self.mood_tracker.get_weekly_insights()

        return SkillResult(
            skill_id=context.skill_id,
            status=SkillStatus.SUCCESS,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            output={
                "report": report,
                "insights": {
                    "avg_mood": insights.avg_mood,
                    "avg_energy": insights.avg_energy,
                    "avg_focus": insights.avg_focus,
                    "avg_stress": insights.avg_stress,
                    "avg_satisfaction": insights.avg_satisfaction,
                    "recommendations": insights.recommendations,
                }
            }
        )

    async def _action_mood_check_in(self, context: SkillContext) -> SkillResult:
        """Get mood check-in prompts."""
        check_in = self.mood_tracker.quick_check_in()

        return SkillResult(
            skill_id=context.skill_id,
            status=SkillStatus.SUCCESS,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            output=check_in
        )


# Convenience functions for direct usage
async def start_work_session(
    title: str,
    project_path: str,
    session_type: str = "coding",
    tags: Optional[List[str]] = None
) -> Dict:
    """Quick function to start a work session.

    Args:
        title: Session title
        project_path: Path to project
        session_type: Type of session
        tags: Optional tags

    Returns:
        Session start result
    """
    config = SkillConfig(
        skill_type="work_logger",
        name="Quick Logger",
        parameters={
            "workspace_path": "~/.work_logger",
            "project_paths": [project_path],
            "current_action": "start_session",
            "session_title": title,
            "session_type": session_type,
            "session_tags": tags or []
        }
    )

    skill = WorkLoggerSkill(config)
    ctx = SkillContext(
        skill_id=f"work_{datetime.now().timestamp()}",
        trigger_type="manual"
    )

    result = await skill.run(ctx)
    return result.output if result.success else {"error": result.error_message}


async def get_daily_summary(workspace_path: str = "~/.work_logger") -> Dict:
    """Get today's work summary.

    Args:
        workspace_path: Path to work logger workspace

    Returns:
        Daily summary
    """
    config = SkillConfig(
        skill_type="work_logger",
        name="Daily Summary",
        parameters={
            "workspace_path": workspace_path,
            "current_action": "get_daily"
        }
    )

    skill = WorkLoggerSkill(config)
    ctx = SkillContext(
        skill_id=f"daily_{datetime.now().timestamp()}",
        trigger_type="manual"
    )

    result = await skill.run(ctx)
    return result.output if result.success else {"error": result.error_message}


async def check_pending_reviews(workspace_path: str = "~/.work_logger") -> Dict:
    """Check for pending reviews.

    Args:
        workspace_path: Path to work logger workspace

    Returns:
        Review status
    """
    config = SkillConfig(
        skill_type="work_logger",
        name="Review Checker",
        parameters={
            "workspace_path": workspace_path,
            "current_action": "check_reviews"
        }
    )

    skill = WorkLoggerSkill(config)
    ctx = SkillContext(
        skill_id=f"review_{datetime.now().timestamp()}",
        trigger_type="schedule"
    )

    result = await skill.run(ctx)
    return result.output if result.success else {"error": result.error_message}