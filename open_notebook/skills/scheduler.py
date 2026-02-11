"""Skill Scheduler - Cron-based scheduling for automated Skill execution.

This module provides asynchronous scheduling capabilities for Skills using
APScheduler. Skills can be configured with cron expressions for automatic
periodic execution.

Usage:
    from open_notebook.skills.scheduler import skill_scheduler

    # Start scheduler on app startup
    await skill_scheduler.start()

    # Schedule a skill instance
    await skill_scheduler.schedule_skill(skill_instance_id, cron_expression)

    # Stop scheduler on shutdown
    await skill_scheduler.shutdown()
"""

import asyncio
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from open_notebook.skills.skill import SkillExecution, SkillInstance


class SkillScheduler:
    """Scheduler for automatic Skill execution based on cron expressions.

    This class manages the lifecycle of scheduled Skill executions.
    It uses APScheduler for cron-based triggering and integrates with
    the Skill system for execution.

    Attributes:
        scheduler: APScheduler AsyncIOScheduler instance
        job_prefix: Prefix for scheduled job IDs
        _running: Flag indicating if scheduler is running
    """

    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.job_prefix = "skill_"
        self._running = False

    async def start(self) -> None:
        """Start the scheduler.

        Initializes APScheduler and loads all enabled Skill instances
        with schedule configurations.
        """
        if self._running:
            logger.debug("Skill scheduler already running")
            return

        try:
            self.scheduler = AsyncIOScheduler()
            self.scheduler.start()
            self._running = True

            # Load and schedule all enabled skill instances with schedules
            await self._load_scheduled_skills()

            logger.info("Skill scheduler started successfully")
        except Exception as e:
            logger.error(f"Failed to start skill scheduler: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown the scheduler gracefully."""
        if not self._running or not self.scheduler:
            return

        try:
            self.scheduler.shutdown(wait=True)
            self._running = False
            logger.info("Skill scheduler shut down successfully")
        except Exception as e:
            logger.error(f"Error shutting down skill scheduler: {e}")

    def _get_job_id(self, skill_instance_id: str) -> str:
        """Generate job ID for a skill instance."""
        return f"{self.job_prefix}{skill_instance_id}"

    async def _load_scheduled_skills(self) -> None:
        """Load all enabled skill instances with schedule configurations."""
        try:
            instances = await SkillInstance.get_all()
            scheduled_count = 0

            for instance in instances:
                if instance.enabled and instance.schedule:
                    try:
                        await self.schedule_skill(instance.id, instance.schedule)
                        scheduled_count += 1
                    except Exception as e:
                        logger.warning(
                            f"Failed to schedule skill {instance.id}: {e}"
                        )

            if scheduled_count > 0:
                logger.info(f"Loaded {scheduled_count} scheduled skills")
        except Exception as e:
            logger.error(f"Error loading scheduled skills: {e}")

    async def schedule_skill(
        self, skill_instance_id: str, cron_expression: str
    ) -> bool:
        """Schedule a skill instance for periodic execution.

        Args:
            skill_instance_id: ID of the SkillInstance to schedule
            cron_expression: Cron expression (e.g., "0 * * * *" for hourly)

        Returns:
            True if scheduled successfully, False otherwise
        """
        if not self._running or not self.scheduler:
            logger.warning("Cannot schedule skill: scheduler not running")
            return False

        try:
            # Remove existing job if any
            await self.unschedule_skill(skill_instance_id)

            # Parse cron expression
            trigger = CronTrigger.from_crontab(cron_expression)

            # Add job
            job_id = self._get_job_id(skill_instance_id)
            self.scheduler.add_job(
                func=self._execute_skill_wrapper,
                trigger=trigger,
                id=job_id,
                args=[skill_instance_id],
                replace_existing=True,
                max_instances=1,  # Prevent overlapping executions
            )

            logger.info(
                f"Scheduled skill {skill_instance_id} with cron: {cron_expression}"
            )
            return True
        except Exception as e:
            logger.error(
                f"Failed to schedule skill {skill_instance_id}: {e}"
            )
            return False

    async def unschedule_skill(self, skill_instance_id: str) -> bool:
        """Remove a skill instance from the schedule.

        Args:
            skill_instance_id: ID of the SkillInstance to unschedule

        Returns:
            True if unscheduled successfully or job didn't exist
        """
        if not self._running or not self.scheduler:
            return True

        try:
            job_id = self._get_job_id(skill_instance_id)
            self.scheduler.remove_job(job_id)
            logger.debug(f"Unscheduled skill {skill_instance_id}")
            return True
        except Exception:
            # Job probably doesn't exist
            return True

    async def update_schedule(
        self, skill_instance_id: str, cron_expression: Optional[str]
    ) -> bool:
        """Update or remove a skill's schedule.

        Args:
            skill_instance_id: ID of the SkillInstance
            cron_expression: New cron expression or None to remove schedule

        Returns:
            True if updated successfully
        """
        if cron_expression:
            return await self.schedule_skill(skill_instance_id, cron_expression)
        else:
            return await self.unschedule_skill(skill_instance_id)

    async def get_next_run_time(self, skill_instance_id: str) -> Optional[datetime]:
        """Get the next scheduled run time for a skill.

        Args:
            skill_instance_id: ID of the SkillInstance

        Returns:
            Next run time or None if not scheduled
        """
        if not self._running or not self.scheduler:
            return None

        try:
            job_id = self._get_job_id(skill_instance_id)
            job = self.scheduler.get_job(job_id)
            if job and job.next_run_time:
                return job.next_run_time
        except Exception:
            pass

        return None

    async def _execute_skill_wrapper(self, skill_instance_id: str) -> None:
        """Wrapper for skill execution that handles errors and logging.

        This is the actual function called by APScheduler. It runs the
        skill execution in an async context and handles any errors.
        """
        try:
            logger.info(f"Executing scheduled skill: {skill_instance_id}")

            # Import here to avoid circular imports
            from open_notebook.skills.runner import SkillRunner

            runner = SkillRunner()
            result = await runner.execute_instance(skill_instance_id)

            if result.success:
                logger.info(
                    f"Scheduled skill {skill_instance_id} executed successfully: "
                    f"{result.message}"
                )
            else:
                logger.error(
                    f"Scheduled skill {skill_instance_id} failed: {result.message}"
                )

        except Exception as e:
            logger.exception(f"Error executing scheduled skill {skill_instance_id}: {e}")

    def get_all_scheduled_jobs(self) -> list[dict]:
        """Get information about all scheduled jobs.

        Returns:
            List of job information dictionaries
        """
        if not self._running or not self.scheduler:
            return []

        jobs = []
        for job in self.scheduler.get_jobs():
            if job.id.startswith(self.job_prefix):
                skill_id = job.id[len(self.job_prefix) :]
                jobs.append(
                    {
                        "skill_instance_id": skill_id,
                        "next_run_time": job.next_run_time,
                        "trigger": str(job.trigger),
                    }
                )

        return jobs


# Global scheduler instance
skill_scheduler = SkillScheduler()
