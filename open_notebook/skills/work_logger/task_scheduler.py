"""Task Scheduler - Background scheduler for work logger reviews and reminders.

Provides scheduled execution of:
- Daily review prompts
- Weekly review prompts
- Session reminders (if working too long)
- Mood check-ins
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional, Any

from loguru import logger


class ScheduleType(str, Enum):
    """Types of scheduled tasks."""
    DAILY_REVIEW = "daily_review"
    WEEKLY_REVIEW = "weekly_review"
    MONTHLY_REVIEW = "monthly_review"
    MOOD_CHECK = "mood_check"
    SESSION_REMINDER = "session_reminder"


@dataclass
class ScheduledTask:
    """A scheduled task definition."""
    task_id: str
    task_type: ScheduleType
    schedule: str  # cron-like or "HH:MM" for daily
    callback: Optional[Callable] = None
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkLoggerScheduler:
    """Background scheduler for work logger tasks.

    Manages scheduled review prompts and reminders.
    Runs in the background and triggers callbacks at scheduled times.

    Usage:
        scheduler = WorkLoggerScheduler(workspace_path="~/.work_logs")

        # Register a callback
        scheduler.on_daily_review(lambda: print("Time for daily review!"))

        # Start scheduler
        await scheduler.start()
    """

    def __init__(self, workspace_path: str):
        """Initialize scheduler.

        Args:
            workspace_path: Path to work logger workspace
        """
        self.workspace_path = Path(workspace_path).expanduser()
        self.scheduler_file = self.workspace_path / ".scheduler_config.json"
        self.tasks: Dict[str, ScheduledTask] = {}
        self._callbacks: Dict[ScheduleType, List[Callable]] = {
            st: [] for st in ScheduleType
        }
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._load_config()

    def _load_config(self) -> None:
        """Load scheduler configuration."""
        if self.scheduler_file.exists():
            try:
                with open(self.scheduler_file, "r", encoding="utf-8") as f:
                    config = json.load(f)

                # Restore tasks (callbacks will be None, need to be re-registered)
                for task_data in config.get("tasks", []):
                    task = ScheduledTask(
                        task_id=task_data["task_id"],
                        task_type=ScheduleType(task_data["task_type"]),
                        schedule=task_data["schedule"],
                        enabled=task_data.get("enabled", True),
                        last_run=datetime.fromisoformat(task_data["last_run"]) if task_data.get("last_run") else None,
                        next_run=datetime.fromisoformat(task_data["next_run"]) if task_data.get("next_run") else None,
                        metadata=task_data.get("metadata", {}),
                    )
                    self.tasks[task.task_id] = task
            except Exception as e:
                logger.error(f"Failed to load scheduler config: {e}")

        # Add default tasks if none exist
        if not self.tasks:
            self._add_default_tasks()

    def _add_default_tasks(self) -> None:
        """Add default scheduled tasks."""
        defaults = [
            ("daily_review_18h", ScheduleType.DAILY_REVIEW, "18:00"),
            ("weekly_review_fri", ScheduleType.WEEKLY_REVIEW, "fri:17:00"),
            ("monthly_review_1st", ScheduleType.MONTHLY_REVIEW, "1:10:00"),
            ("mood_check_15h", ScheduleType.MOOD_CHECK, "15:00"),
        ]

        for task_id, task_type, schedule in defaults:
            self.tasks[task_id] = ScheduledTask(
                task_id=task_id,
                task_type=task_type,
                schedule=schedule,
                enabled=True,
            )

        self._save_config()

    def _save_config(self) -> None:
        """Save scheduler configuration."""
        try:
            config = {
                "tasks": [
                    {
                        "task_id": t.task_id,
                        "task_type": t.task_type.value,
                        "schedule": t.schedule,
                        "enabled": t.enabled,
                        "last_run": t.last_run.isoformat() if t.last_run else None,
                        "next_run": t.next_run.isoformat() if t.next_run else None,
                        "metadata": t.metadata,
                    }
                    for t in self.tasks.values()
                ]
            }
            self.scheduler_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.scheduler_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save scheduler config: {e}")

    def on(self, task_type: ScheduleType, callback: Callable) -> None:
        """Register a callback for a task type.

        Args:
            task_type: Type of scheduled task
            callback: Function to call when task triggers
        """
        self._callbacks[task_type].append(callback)
        logger.info(f"Registered callback for {task_type.value}")

    def on_daily_review(self, callback: Callable) -> None:
        """Register daily review callback."""
        self.on(ScheduleType.DAILY_REVIEW, callback)

    def on_weekly_review(self, callback: Callable) -> None:
        """Register weekly review callback."""
        self.on(ScheduleType.WEEKLY_REVIEW, callback)

    def on_monthly_review(self, callback: Callable) -> None:
        """Register monthly review callback."""
        self.on(ScheduleType.MONTHLY_REVIEW, callback)

    def on_mood_check(self, callback: Callable) -> None:
        """Register mood check callback."""
        self.on(ScheduleType.MOOD_CHECK, callback)

    def _parse_schedule(self, schedule: str, base_time: datetime) -> Optional[datetime]:
        """Parse schedule string to next occurrence.

        Args:
            schedule: Schedule string ("HH:MM", "fri:HH:MM", "D:HH:MM")
            base_time: Base time to calculate from

        Returns:
            Next scheduled datetime or None
        """
        now = base_time

        try:
            # Format: "HH:MM" - daily at specific time
            if ":" in schedule and len(schedule.split(":")) == 2:
                hour, minute = map(int, schedule.split(":"))
                next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if next_run <= now:
                    next_run += timedelta(days=1)
                return next_run

            # Format: "fri:HH:MM" - weekly on specific day
            elif schedule.startswith("fri:"):
                time_part = schedule[4:]  # "HH:MM"
                hour, minute = map(int, time_part.split(":"))
                # Find next Friday (weekday 4)
                days_until_friday = (4 - now.weekday()) % 7
                if days_until_friday == 0 and now.hour >= hour:
                    days_until_friday = 7
                next_run = (now + timedelta(days=days_until_friday)).replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )
                return next_run

            # Format: "1:HH:MM" - monthly on specific day
            elif ":" in schedule and len(schedule.split(":")) == 3:
                parts = schedule.split(":")
                day = int(parts[0])
                hour = int(parts[1])
                minute = int(parts[2])

                # Try this month
                try:
                    next_run = now.replace(day=day, hour=hour, minute=minute, second=0, microsecond=0)
                    if next_run <= now:
                        # Move to next month
                        if now.month == 12:
                            next_run = now.replace(year=now.year + 1, month=1, day=day,
                                                    hour=hour, minute=minute, second=0, microsecond=0)
                        else:
                            next_run = now.replace(month=now.month + 1, day=day,
                                                    hour=hour, minute=minute, second=0, microsecond=0)
                    return next_run
                except ValueError:
                    # Day doesn't exist in this month
                    return None

        except Exception as e:
            logger.error(f"Failed to parse schedule '{schedule}': {e}")
            return None

    def _check_and_trigger(self) -> None:
        """Check tasks and trigger callbacks if due."""
        now = datetime.now()

        for task in self.tasks.values():
            if not task.enabled:
                continue

            # Calculate next run if not set
            if task.next_run is None:
                task.next_run = self._parse_schedule(task.schedule, now)
            elif task.next_run < now:
                # Task is overdue - if within 1 hour grace period, trigger it
                # otherwise, reschedule to next occurrence
                overdue_minutes = (now - task.next_run).total_seconds() / 60
                if overdue_minutes <= 60 and task.last_run is None:
                    # First run and within grace period - trigger now
                    logger.debug(f"Task {task.task_id} is {overdue_minutes:.0f}min overdue, triggering")
                else:
                    # Too old or already ran - reschedule
                    task.next_run = self._parse_schedule(task.schedule, now)
                    continue

            # Check if task is due
            if task.next_run and task.next_run <= now:
                # Trigger callbacks
                callbacks = self._callbacks.get(task.task_type, [])
                for callback in callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            # Schedule async callback
                            asyncio.create_task(callback())
                        else:
                            # Call sync callback
                            callback()
                    except Exception as e:
                        logger.error(f"Callback failed for {task.task_id}: {e}")

                # Update task state
                task.last_run = now
                task.next_run = self._parse_schedule(task.schedule, now)
                logger.info(f"Triggered task: {task.task_id}")

        self._save_config()

    async def start(self) -> None:
        """Start the scheduler background loop."""
        if self._running:
            logger.warning("Scheduler already running")
            return

        self._running = True
        logger.info("Work Logger Scheduler started")

        while self._running:
            self._check_and_trigger()
            await asyncio.sleep(60)  # Check every minute

    async def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
        logger.info("Work Logger Scheduler stopped")

    def enable_task(self, task_id: str) -> None:
        """Enable a scheduled task."""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = True
            self._save_config()

    def disable_task(self, task_id: str) -> None:
        """Disable a scheduled task."""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = False
            self._save_config()

    def get_schedule_info(self) -> Dict[str, Any]:
        """Get current schedule information."""
        now = datetime.now()
        return {
            "running": self._running,
            "tasks": [
                {
                    "task_id": t.task_id,
                    "task_type": t.task_type.value,
                    "schedule": t.schedule,
                    "enabled": t.enabled,
                    "last_run": t.last_run.isoformat() if t.last_run else None,
                    "next_run": t.next_run.isoformat() if t.next_run else None,
                    "due": t.next_run <= now if t.next_run else False,
                }
                for t in self.tasks.values()
            ]
        }


# Global scheduler instance
_scheduler_instance: Optional[WorkLoggerScheduler] = None


def get_scheduler(workspace_path: str = "~/.claude/work_logs") -> WorkLoggerScheduler:
    """Get or create global scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = WorkLoggerScheduler(workspace_path)
    return _scheduler_instance


async def start_scheduler_daemon(workspace_path: str = "~/.claude/work_logs") -> WorkLoggerScheduler:
    """Start scheduler daemon with default callbacks.

    Args:
        workspace_path: Path to work logger workspace

    Returns:
        Running scheduler instance
    """
    scheduler = get_scheduler(workspace_path)

    # Register default callbacks
    scheduler.on_daily_review(lambda: print("[Work Logger] Time for daily review!"))
    scheduler.on_weekly_review(lambda: print("[Work Logger] Time for weekly review!"))
    scheduler.on_mood_check(lambda: print("[Work Logger] How are you feeling?"))

    # Start in background
    asyncio.create_task(scheduler.start())

    return scheduler