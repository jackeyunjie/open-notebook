"""Data models for Work Logger Skill."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import json


class SessionType(str, Enum):
    """Types of work sessions."""
    CODING = "coding"
    RESEARCH = "research"
    WRITING = "writing"
    MEETING = "meeting"
    REVIEW = "review"
    PLANNING = "planning"
    OTHER = "other"


class SessionStatus(str, Enum):
    """Status of a work session."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    INTERRUPTED = "interrupted"


@dataclass
class GitActivity:
    """Git activity record."""
    commit_hash: str
    message: str
    files_changed: List[str]
    insertions: int
    deletions: int
    timestamp: datetime
    branch: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "commit_hash": self.commit_hash,
            "message": self.message,
            "files_changed": self.files_changed,
            "insertions": self.insertions,
            "deletions": self.deletions,
            "timestamp": self.timestamp.isoformat(),
            "branch": self.branch,
        }


@dataclass
class FileActivity:
    """File modification record."""
    file_path: str
    change_type: str  # created, modified, deleted
    line_count: int
    timestamp: datetime
    project: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "change_type": self.change_type,
            "line_count": self.line_count,
            "timestamp": self.timestamp.isoformat(),
            "project": self.project,
        }


@dataclass
class WorkSession:
    """A work session record."""
    session_id: str
    start_time: datetime
    session_type: SessionType
    title: str
    description: str = ""
    project: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    status: SessionStatus = SessionStatus.ACTIVE
    end_time: Optional[datetime] = None
    git_activities: List[GitActivity] = field(default_factory=list)
    file_activities: List[FileActivity] = field(default_factory=list)
    related_files: List[str] = field(default_factory=list)
    context_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "session_type": self.session_type.value,
            "title": self.title,
            "description": self.description,
            "project": self.project,
            "tags": self.tags,
            "status": self.status.value,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "git_activities": [g.to_dict() for g in self.git_activities],
            "file_activities": [f.to_dict() for f in self.file_activities],
            "related_files": self.related_files,
            "context_notes": self.context_notes,
        }

    @property
    def duration_minutes(self) -> Optional[float]:
        """Calculate session duration in minutes."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() / 60
        return None


@dataclass
class DailySummary:
    """Daily work summary."""
    date: str
    sessions: List[WorkSession] = field(default_factory=list)
    total_commits: int = 0
    files_modified: int = 0
    lines_added: int = 0
    lines_deleted: int = 0
    projects_worked: List[str] = field(default_factory=list)
    key_achievements: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    next_day_plan: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            "sessions": [s.to_dict() for s in self.sessions],
            "total_commits": self.total_commits,
            "files_modified": self.files_modified,
            "lines_added": self.lines_added,
            "lines_deleted": self.lines_deleted,
            "projects_worked": self.projects_worked,
            "key_achievements": self.key_achievements,
            "blockers": self.blockers,
            "next_day_plan": self.next_day_plan,
        }


@dataclass
class ReviewTemplate:
    """Review template definition."""
    name: str
    schedule: str  # cron-like expression
    questions: List[str] = field(default_factory=list)
    output_format: str = "markdown"

    # Predefined templates
    DAILY = None
    WEEKLY = None
    MONTHLY = None


# Initialize predefined templates
ReviewTemplate.DAILY = ReviewTemplate(
    name="daily",
    schedule="0 18 * * *",  # 6 PM daily
    questions=[
        "今天完成了什么？",
        "遇到了哪些挑战？",
        "学到了什么新东西？",
        "明天的优先事项是什么？",
        "有什么需要记录的经验教训？",
    ],
)

ReviewTemplate.WEEKLY = ReviewTemplate(
    name="weekly",
    schedule="0 17 * * 5",  # 5 PM Friday
    questions=[
        "本周的主要成果是什么？",
        "哪些目标达成了，哪些没有？",
        "时间分配是否合理？",
        "有什么模式或趋势值得注意？",
        "下周的3个优先事项是什么？",
        "需要什么支持或资源？",
    ],
)

ReviewTemplate.MONTHLY = ReviewTemplate(
    name="monthly",
    schedule="0 10 1 * *",  # 10 AM first day of month
    questions=[
        "本月最大的成就是什么？",
        "技能和能力有什么提升？",
        "项目进展是否符合预期？",
        "有什么需要改进的工作流程？",
        "下月的战略重点是什么？",
    ],
)