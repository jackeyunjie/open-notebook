"""P3 Evolution Scheduler - Automated evolution cycles for the Organic Growth System.

This module provides scheduling capabilities for the P3 evolution layer,
enabling automatic strategy evolution and meta-learning at configurable intervals.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

from loguru import logger

from open_notebook.skills.p3_evolution import (
    EvolutionOrchestrator,
    EvolutionReport,
    initialize_p3_evolution,
    run_evolution_cycle,
)
from open_notebook.skills.p0_orchestrator import SharedMemory


class EvolutionScheduleType(Enum):
    """Types of evolution schedules."""
    DAILY = "daily"           # Run once per day
    WEEKLY = "weekly"         # Run once per week
    FEEDBACK_DRIVEN = "feedback"  # Run when feedback threshold reached
    MANUAL = "manual"         # Only run on demand


@dataclass
class EvolutionScheduleConfig:
    """Configuration for evolution scheduling."""
    schedule_type: EvolutionScheduleType = EvolutionScheduleType.DAILY
    run_time: str = "02:00"   # Default 2 AM (after P0/P1/P2 cycles)
    day_of_week: int = 0      # 0 = Monday (for weekly)
    feedback_threshold: int = 50  # Run after N feedback records
    enable_auto_deploy: bool = False  # Auto-deploy evolved strategies
    min_fitness_for_deploy: float = 0.7
    max_generations_per_run: int = 5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schedule_type": self.schedule_type.value,
            "run_time": self.run_time,
            "day_of_week": self.day_of_week,
            "feedback_threshold": self.feedback_threshold,
            "enable_auto_deploy": self.enable_auto_deploy,
            "min_fitness_for_deploy": self.min_fitness_for_deploy,
            "max_generations_per_run": self.max_generations_per_run
        }


@dataclass
class EvolutionExecutionRecord:
    """Record of an evolution execution."""
    execution_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "pending"  # pending, running, completed, failed
    report: Optional[Dict[str, Any]] = None
    strategies_deployed: int = 0
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "report": self.report,
            "strategies_deployed": self.strategies_deployed,
            "error_message": self.error_message
        }


class P3EvolutionScheduler:
    """Scheduler for automated P3 evolution cycles."""

    def __init__(self):
        self.config = EvolutionScheduleConfig()
        self.shared_memory = SharedMemory()
        self.execution_history: List[EvolutionExecutionRecord] = []
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._orchestrator: Optional[EvolutionOrchestrator] = None
        self._feedback_count_last_check = 0

    def initialize(self):
        """Initialize the evolution system."""
        self._orchestrator = initialize_p3_evolution()
        logger.info("P3 Evolution Scheduler initialized")

    async def start(self):
        """Start the evolution scheduler."""
        if self._running:
            logger.warning("P3 Scheduler already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._scheduling_loop())
        logger.info(f"P3 Evolution Scheduler started ({self.config.schedule_type.value})")

    async def stop(self):
        """Stop the evolution scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("P3 Evolution Scheduler stopped")

    async def _scheduling_loop(self):
        """Main scheduling loop."""
        while self._running:
            try:
                if self.config.schedule_type == EvolutionScheduleType.DAILY:
                    await self._wait_for_daily_time()
                    await self._run_evolution()

                elif self.config.schedule_type == EvolutionScheduleType.WEEKLY:
                    await self._wait_for_weekly_time()
                    await self._run_evolution()

                elif self.config.schedule_type == EvolutionScheduleType.FEEDBACK_DRIVEN:
                    await self._wait_for_feedback_threshold()
                    await self._run_evolution()

                elif self.config.schedule_type == EvolutionScheduleType.MANUAL:
                    # Just sleep, wait for manual trigger
                    await asyncio.sleep(60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in P3 scheduling loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry

    async def _wait_for_daily_time(self):
        """Wait until the scheduled daily time."""
        now = datetime.now()
        hour, minute = map(int, self.config.run_time.split(":"))

        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)

        wait_seconds = (target - now).total_seconds()
        logger.info(f"Next P3 evolution scheduled at {target} (in {wait_seconds/3600:.1f} hours)")
        await asyncio.sleep(wait_seconds)

    async def _wait_for_weekly_time(self):
        """Wait until the scheduled weekly time."""
        now = datetime.now()
        hour, minute = map(int, self.config.run_time.split(":"))

        # Find next occurrence of day_of_week
        days_ahead = self.config.day_of_week - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7

        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        target += timedelta(days=days_ahead)

        wait_seconds = (target - now).total_seconds()
        logger.info(f"Next P3 evolution scheduled at {target} (in {wait_seconds/86400:.1f} days)")
        await asyncio.sleep(wait_seconds)

    async def _wait_for_feedback_threshold(self):
        """Wait until enough feedback has been collected."""
        while self._running:
            # Get current feedback count
            feedback_data = self.shared_memory.get("feedback:count")
            current_count = feedback_data.get("total", 0) if feedback_data else 0

            new_feedback = current_count - self._feedback_count_last_check

            if new_feedback >= self.config.feedback_threshold:
                self._feedback_count_last_check = current_count
                logger.info(f"Feedback threshold reached ({new_feedback} new records)")
                return

            # Check every 5 minutes
            await asyncio.sleep(300)

    async def _run_evolution(self):
        """Execute one evolution cycle."""
        execution_id = f"evo_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        record = EvolutionExecutionRecord(
            execution_id=execution_id,
            started_at=datetime.utcnow(),
            status="running"
        )
        self.execution_history.append(record)

        logger.info(f"Starting evolution cycle: {execution_id}")

        try:
            # Run multiple generations
            best_report = None
            for generation in range(self.config.max_generations_per_run):
                report = run_evolution_cycle()
                if not best_report or report.fitness_improvement > best_report.fitness_improvement:
                    best_report = report

                logger.info(f"Generation {generation + 1} complete, fitness improvement: {report.fitness_improvement:.3f}")

                # Early stop if no improvement
                if report.fitness_improvement < 0.01:
                    logger.info("Early stopping - no significant improvement")
                    break

            # Auto-deploy if enabled
            strategies_deployed = 0
            if self.config.enable_auto_deploy and best_report:
                strategies_deployed = self._orchestrator.deploy_evolved_strategies(best_report)
                logger.info(f"Auto-deployed {strategies_deployed} strategies")

            # Update record
            record.status = "completed"
            record.completed_at = datetime.utcnow()
            record.report = best_report.to_dict() if best_report else None
            record.strategies_deployed = strategies_deployed

            # Store to shared memory
            self.shared_memory.store(
                f"p3:execution:{execution_id}",
                record.to_dict(),
                ttl_seconds=86400 * 30
            )

            logger.info(f"Evolution cycle {execution_id} completed successfully")

        except Exception as e:
            logger.exception(f"Evolution cycle {execution_id} failed: {e}")
            record.status = "failed"
            record.completed_at = datetime.utcnow()
            record.error_message = str(e)

    def trigger_manual_evolution(self) -> str:
        """Manually trigger an evolution cycle."""
        if not self._orchestrator:
            self.initialize()

        # Run in background
        asyncio.create_task(self._run_evolution())
        return f"evo_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status."""
        recent_executions = [e.to_dict() for e in self.execution_history[-10:]]

        return {
            "running": self._running,
            "schedule_type": self.config.schedule_type.value,
            "config": self.config.to_dict(),
            "total_executions": len(self.execution_history),
            "recent_executions": recent_executions,
            "evolution_summary": self._orchestrator.get_evolution_summary() if self._orchestrator else None
        }

    def update_config(self, **kwargs):
        """Update scheduler configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"Updated config: {key} = {value}")


# Global scheduler instance
p3_evolution_scheduler = P3EvolutionScheduler()


def setup_default_p3_schedule(schedule_type: str = "daily", run_time: str = "02:00"):
    """Set up default P3 evolution schedule.

    Args:
        schedule_type: "daily", "weekly", "feedback", or "manual"
        run_time: Time to run in "HH:MM" format
    """
    type_map = {
        "daily": EvolutionScheduleType.DAILY,
        "weekly": EvolutionScheduleType.WEEKLY,
        "feedback": EvolutionScheduleType.FEEDBACK_DRIVEN,
        "manual": EvolutionScheduleType.MANUAL
    }

    p3_evolution_scheduler.config.schedule_type = type_map.get(schedule_type, EvolutionScheduleType.DAILY)
    p3_evolution_scheduler.config.run_time = run_time

    logger.info(f"Default P3 schedule: {schedule_type} at {run_time}")
    return p3_evolution_scheduler.config
