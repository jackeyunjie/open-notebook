"""P0 Daily Sync Scheduler - Automated scheduling for P0 layer orchestration.

This module provides automated, scheduled execution of the P0 Daily Sync,
enabling the organic growth system to run continuously without manual intervention.

Features:
    - Daily automated sync at configurable time
    - Retry mechanism for failed syncs
    - Execution history tracking
    - Health monitoring and alerting
    - Manual trigger support

Schedule Formats:
    - "00:00" - Daily at midnight (default)
    - "06:00" - Daily at 6 AM
    - "0 */6 * * *" - Every 6 hours (cron format)

Usage:
    # Start automatic daily sync at 6 AM
    scheduler = P0SyncScheduler()
    await scheduler.start(runner, sync_time="06:00")

    # Or run every 6 hours
    await scheduler.start(runner, cron_expression="0 */6 * * *")
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from open_notebook.skills.base import SkillConfig, SkillContext
from open_notebook.skills.runner import SkillRunner
from open_notebook.skills.p0_orchestrator import P0OrchestratorAgent, SyncSession


class SyncStatus(Enum):
    """Status of a sync execution."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class SyncExecutionRecord:
    """Record of a single sync execution."""
    execution_id: str
    scheduled_time: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: SyncStatus = SyncStatus.PENDING
    error_message: Optional[str] = None
    retry_count: int = 0
    signals_generated: int = 0
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "scheduled_time": self.scheduled_time.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status.value,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "signals_generated": self.signals_generated,
            "session_id": self.session_id
        }


@dataclass
class P0ScheduleConfig:
    """Configuration for P0 Daily Sync scheduling."""
    enabled: bool = True
    cron_expression: str = "0 0 * * *"  # Daily at midnight
    timezone: str = "UTC"
    max_retries: int = 3
    retry_delay_minutes: int = 30
    timeout_minutes: int = 30
    target_notebook_id: str = ""
    agents_to_run: List[str] = field(default_factory=lambda: ["Q1P0", "Q2P0", "Q3P0", "Q4P0"])
    enable_notifications: bool = True

    @classmethod
    def from_simple_time(cls, time_str: str = "00:00", **kwargs) -> "P0ScheduleConfig":
        """Create config from simple time string like '06:00'."""
        try:
            hour, minute = map(int, time_str.split(":"))
            cron = f"{minute} {hour} * * *"
            return cls(cron_expression=cron, **kwargs)
        except ValueError:
            logger.error(f"Invalid time format: {time_str}, using default")
            return cls(**kwargs)


class P0SyncScheduler:
    """Scheduler for automated P0 Daily Sync execution.

    Manages the lifecycle of scheduled Daily Sync operations:
    - Schedule configuration and updates
    - Execution with retry logic
    - History tracking and health monitoring
    - Manual trigger support

    Example:
        scheduler = P0SyncScheduler()

        # Method 1: Simple daily time
        await scheduler.start(runner, sync_time="06:00")

        # Method 2: Cron expression
        await scheduler.start(runner, cron_expression="0 */6 * * *")

        # Method 3: Full config
        config = P0ScheduleConfig.from_simple_time("08:00", max_retries=5)
        await scheduler.start_with_config(runner, config)

        # Check status
        status = scheduler.get_status()
        print(f"Next sync: {status['next_run_time']}")
        print(f"Last sync: {status['last_execution']}")

        # Manual trigger
        result = await scheduler.trigger_sync_now()
    """

    def __init__(self):
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._runner: Optional[SkillRunner] = None
        self._config: Optional[P0ScheduleConfig] = None
        self._job_id: str = "p0_daily_sync"
        self._running: bool = False

        # Execution tracking
        self._execution_history: List[SyncExecutionRecord] = []
        self._current_execution: Optional[SyncExecutionRecord] = None
        self._last_successful_sync: Optional[datetime] = None

        # Callbacks
        self._on_sync_start: Optional[Callable] = None
        self._on_sync_complete: Optional[Callable] = None
        self._on_sync_error: Optional[Callable] = None

    async def start(
        self,
        runner: SkillRunner,
        sync_time: str = "00:00",
        target_notebook_id: str = ""
    ) -> bool:
        """Start scheduled Daily Sync with simple time format.

        Args:
            runner: SkillRunner instance for executing sync
            sync_time: Time to run daily (HH:MM format, default "00:00")
            target_notebook_id: Notebook to store sync reports

        Returns:
            True if started successfully
        """
        config = P0ScheduleConfig.from_simple_time(
            time_str=sync_time,
            target_notebook_id=target_notebook_id
        )
        return await self.start_with_config(runner, config)

    async def start_with_config(
        self,
        runner: SkillRunner,
        config: P0ScheduleConfig
    ) -> bool:
        """Start scheduled Daily Sync with full configuration.

        Args:
            runner: SkillRunner instance
            config: P0ScheduleConfig with all scheduling options

        Returns:
            True if started successfully
        """
        if self._running:
            logger.warning("P0 Sync Scheduler already running, stopping first")
            await self.stop()

        try:
            self._runner = runner
            self._config = config
            self._scheduler = AsyncIOScheduler()

            # Parse cron expression
            parts = config.cron_expression.split()
            if len(parts) != 5:
                logger.error(f"Invalid cron expression: {config.cron_expression}")
                return False

            trigger = CronTrigger(
                minute=parts[0],
                hour=parts[1],
                day=parts[2],
                month=parts[3],
                day_of_week=parts[4],
                timezone=config.timezone
            )

            # Add job
            self._scheduler.add_job(
                func=self._execute_scheduled_sync,
                trigger=trigger,
                id=self._job_id,
                replace_existing=True,
                max_instances=1,
                coalesce=True  # Catch up missed runs
            )

            self._scheduler.start()
            self._running = True

            logger.info(
                f"P0 Daily Sync scheduled with cron: {config.cron_expression} "
                f"({config.timezone})"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to start P0 Sync Scheduler: {e}")
            return False

    async def stop(self) -> None:
        """Stop the scheduler."""
        if not self._running or not self._scheduler:
            return

        self._scheduler.remove_job(self._job_id)
        self._scheduler.shutdown(wait=False)
        self._scheduler = None
        self._running = False
        self._current_execution = None

        logger.info("P0 Sync Scheduler stopped")

    async def _execute_scheduled_sync(self) -> None:
        """Execute the scheduled Daily Sync (called by APScheduler)."""
        execution_id = f"sync-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        record = SyncExecutionRecord(
            execution_id=execution_id,
            scheduled_time=datetime.utcnow()
        )
        self._current_execution = record
        self._execution_history.append(record)

        # Trim history to last 100 records
        if len(self._execution_history) > 100:
            self._execution_history = self._execution_history[-100:]

        logger.info(f"=== Starting scheduled P0 Daily Sync: {execution_id} ===")

        try:
            # Call on_start callback
            if self._on_sync_start:
                await self._on_sync_start(execution_id)

            # Execute with retry
            result = await self._execute_with_retry(record)

            if result:
                record.status = SyncStatus.SUCCESS
                record.signals_generated = result.get("cross_quadrant_signals", 0)
                record.session_id = result.get("session_id")
                self._last_successful_sync = datetime.utcnow()

                logger.info(
                    f"P0 Daily Sync completed: {record.signals_generated} signals"
                )

                # Call on_complete callback
                if self._on_sync_complete:
                    await self._on_sync_complete(execution_id, result)
            else:
                record.status = SyncStatus.FAILED
                record.error_message = "Sync returned no result after retries"

                logger.error(f"P0 Daily Sync failed: {record.error_message}")

                # Call on_error callback
                if self._on_sync_error:
                    await self._on_sync_error(execution_id, record.error_message)

        except Exception as e:
            record.status = SyncStatus.FAILED
            record.error_message = str(e)
            logger.exception(f"P0 Daily Sync failed: {e}")

            if self._on_sync_error:
                await self._on_sync_error(execution_id, str(e))

        finally:
            record.completed_at = datetime.utcnow()
            self._current_execution = None

    async def _execute_with_retry(
        self,
        record: SyncExecutionRecord
    ) -> Optional[Dict[str, Any]]:
        """Execute sync with retry logic."""
        max_retries = self._config.max_retries if self._config else 3
        retry_delay = (self._config.retry_delay_minutes if self._config else 30) * 60

        for attempt in range(max_retries + 1):
            record.retry_count = attempt

            if attempt > 0:
                record.status = SyncStatus.RETRYING
                logger.info(f"Retrying P0 Daily Sync (attempt {attempt + 1}/{max_retries + 1})")
                await asyncio.sleep(retry_delay)

            try:
                result = await self._execute_single_sync()
                if result:
                    return result

            except Exception as e:
                logger.warning(f"Sync attempt {attempt + 1} failed: {e}")
                if attempt == max_retries:
                    raise

        return None

    async def _execute_single_sync(self) -> Optional[Dict[str, Any]]:
        """Execute a single sync without retry."""
        if not self._runner:
            raise RuntimeError("No runner available")

        # Create orchestrator
        config = SkillConfig(
            skill_type="p0_orchestrator",
            name="P0 Daily Sync Orchestrator",
            parameters={
                "agents_to_run": self._config.agents_to_run if self._config else ["Q1P0"],
                "target_notebook_id": self._config.target_notebook_id if self._config else "",
                "enable_cross_synthesis": True
            }
        )

        orchestrator = P0OrchestratorAgent(config)
        context = SkillContext(
            skill_id=f"p0_sync_{datetime.utcnow().isoformat()}",
            trigger_type="scheduled"
        )

        # Execute with timeout
        timeout = (self._config.timeout_minutes if self._config else 30) * 60

        result = await asyncio.wait_for(
            orchestrator.execute(context),
            timeout=timeout
        )

        if result.status.value == "success":
            return result.output
        else:
            raise RuntimeError(f"Sync failed: {result.error_message}")

    async def trigger_sync_now(self) -> Optional[Dict[str, Any]]:
        """Manually trigger a sync immediately.

        Returns:
            Sync result or None if failed
        """
        if not self._runner:
            logger.error("Cannot trigger sync: runner not available")
            return None

        execution_id = f"manual-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        logger.info(f"Manually triggering P0 Daily Sync: {execution_id}")

        record = SyncExecutionRecord(
            execution_id=execution_id,
            scheduled_time=datetime.utcnow(),
            started_at=datetime.utcnow()
        )
        self._current_execution = record
        self._execution_history.append(record)

        try:
            result = await self._execute_with_retry(record)

            if result:
                record.status = SyncStatus.SUCCESS
                record.signals_generated = result.get("cross_quadrant_signals", 0)
                self._last_successful_sync = datetime.utcnow()
            else:
                record.status = SyncStatus.FAILED
                record.error_message = "Manual sync failed"

            record.completed_at = datetime.utcnow()
            return result

        except Exception as e:
            record.status = SyncStatus.FAILED
            record.error_message = str(e)
            record.completed_at = datetime.utcnow()
            logger.exception(f"Manual sync failed: {e}")
            return None

        finally:
            self._current_execution = None

    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status."""
        status = {
            "running": self._running,
            "schedule_config": None,
            "next_run_time": None,
            "last_execution": None,
            "current_execution": None,
            "execution_history_count": len(self._execution_history),
            "last_successful_sync": self._last_successful_sync.isoformat() if self._last_successful_sync else None,
            "health_status": "unknown"
        }

        if self._config:
            status["schedule_config"] = {
                "cron_expression": self._config.cron_expression,
                "timezone": self._config.timezone,
                "max_retries": self._config.max_retries
            }

        if self._scheduler and self._running:
            job = self._scheduler.get_job(self._job_id)
            if job and job.next_run_time:
                status["next_run_time"] = job.next_run_time.isoformat()

        if self._execution_history:
            last = self._execution_history[-1]
            status["last_execution"] = last.to_dict()

        if self._current_execution:
            status["current_execution"] = self._current_execution.to_dict()

        # Health check
        if not self._running:
            status["health_status"] = "stopped"
        elif self._last_successful_sync:
            hours_since_sync = (datetime.utcnow() - self._last_successful_sync).total_seconds() / 3600
            if hours_since_sync < 26:  # Normal daily cycle + 2h buffer
                status["health_status"] = "healthy"
            elif hours_since_sync < 48:
                status["health_status"] = "warning"  # Overdue
            else:
                status["health_status"] = "critical"  # Very overdue
        else:
            status["health_status"] = "unknown"  # No sync yet

        return status

    def get_execution_history(
        self,
        limit: int = 10,
        status_filter: Optional[SyncStatus] = None
    ) -> List[Dict[str, Any]]:
        """Get execution history with optional filtering.

        Args:
            limit: Maximum number of records to return
            status_filter: Filter by status (optional)

        Returns:
            List of execution records
        """
        records = self._execution_history

        if status_filter:
            records = [r for r in records if r.status == status_filter]

        # Sort by scheduled time descending
        records = sorted(records, key=lambda r: r.scheduled_time, reverse=True)

        return [r.to_dict() for r in records[:limit]]

    def get_health_metrics(self) -> Dict[str, Any]:
        """Get health metrics for monitoring."""
        total = len(self._execution_history)
        successful = sum(1 for r in self._execution_history if r.status == SyncStatus.SUCCESS)
        failed = sum(1 for r in self._execution_history if r.status == SyncStatus.FAILED)

        # Calculate success rate
        success_rate = (successful / total * 100) if total > 0 else 0

        # Calculate average duration
        durations = []
        for r in self._execution_history:
            if r.started_at and r.completed_at:
                durations.append((r.completed_at - r.started_at).total_seconds())

        avg_duration = sum(durations) / len(durations) if durations else 0

        # Average signals generated
        signals = [r.signals_generated for r in self._execution_history if r.signals_generated > 0]
        avg_signals = sum(signals) / len(signals) if signals else 0

        return {
            "total_executions": total,
            "successful": successful,
            "failed": failed,
            "success_rate_percent": round(success_rate, 2),
            "average_duration_seconds": round(avg_duration, 2),
            "average_signals_generated": round(avg_signals, 2),
            "last_24h_executions": sum(
                1 for r in self._execution_history
                if r.scheduled_time > datetime.utcnow() - timedelta(hours=24)
            )
        }

    def set_callbacks(
        self,
        on_sync_start: Optional[Callable] = None,
        on_sync_complete: Optional[Callable] = None,
        on_sync_error: Optional[Callable] = None
    ) -> None:
        """Set callback functions for sync events.

        Args:
            on_sync_start: Called when sync starts (execution_id)
            on_sync_complete: Called when sync completes (execution_id, result)
            on_sync_error: Called when sync fails (execution_id, error)
        """
        self._on_sync_start = on_sync_start
        self._on_sync_complete = on_sync_complete
        self._on_sync_error = on_sync_error

    async def update_schedule(self, new_time: str) -> bool:
        """Update the sync schedule to a new time.

        Args:
            new_time: New time in HH:MM format

        Returns:
            True if updated successfully
        """
        if not self._running or not self._scheduler:
            logger.error("Cannot update schedule: scheduler not running")
            return False

        try:
            # Remove existing job
            self._scheduler.remove_job(self._job_id)

            # Parse new time
            hour, minute = map(int, new_time.split(":"))
            new_cron = f"{minute} {hour} * * *"

            # Update config
            if self._config:
                self._config.cron_expression = new_cron

            # Add new job
            trigger = CronTrigger(
                minute=minute,
                hour=hour,
                day="*",
                month="*",
                day_of_week="*"
            )

            self._scheduler.add_job(
                func=self._execute_scheduled_sync,
                trigger=trigger,
                id=self._job_id,
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )

            logger.info(f"Updated P0 Daily Sync schedule to: {new_time}")
            return True

        except Exception as e:
            logger.error(f"Failed to update schedule: {e}")
            return False


# Global scheduler instance
p0_sync_scheduler = P0SyncScheduler()


async def setup_default_p0_schedule(
    runner: SkillRunner,
    sync_time: str = "06:00",
    target_notebook_id: str = ""
) -> bool:
    """Convenience function to set up default P0 Daily Sync schedule.

    Args:
        runner: SkillRunner instance
        sync_time: Time to run daily (default "06:00")
        target_notebook_id: Notebook for sync reports

    Returns:
        True if setup successfully
    """
    return await p0_sync_scheduler.start(runner, sync_time, target_notebook_id)
