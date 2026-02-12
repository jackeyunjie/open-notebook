"""Skill Scheduler - APScheduler-based task scheduling for Skills.

This module provides cron-based scheduling for Skill instances,
enabling automated, periodic execution of content crawling,
note organization, and other automated tasks.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from open_notebook.skills.runner import SkillRunner
from open_notebook.workflows.service import WorkflowService


class SkillScheduler:
    """Scheduler for automated Skill execution.
    
    Uses APScheduler for cron-based task scheduling.
    Supports async execution and job management.
    """
    
    def __init__(self):
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._runner: Optional[SkillRunner] = None
        self._workflow_service: Optional[WorkflowService] = None
        self._running = False
        self._job_ids: set = set()  # Both skill and workflow job IDs
    
    async def start(
        self,
        runner: SkillRunner,
        workflow_service: Optional[WorkflowService] = None
    ) -> None:
        """Start the scheduler.

        Args:
            runner: SkillRunner instance for executing skills
            workflow_service: Optional WorkflowService for executing workflows
        """
        if self._running:
            logger.warning("Scheduler already running")
            return

        self._runner = runner
        self._workflow_service = workflow_service or WorkflowService()
        self._scheduler = AsyncIOScheduler()
        self._scheduler.start()
        self._running = True

        logger.info("Skill scheduler started")
    
    async def stop(self) -> None:
        """Stop the scheduler and clean up jobs."""
        if not self._running or not self._scheduler:
            return
        
        self._scheduler.shutdown(wait=True)
        self._scheduler = None
        self._running = False
        self._job_ids.clear()
        
        logger.info("Skill scheduler stopped")
    
    async def schedule_skill(
        self, 
        skill_instance_id: str, 
        cron_expression: str
    ) -> bool:
        """Schedule a skill instance with cron expression.
        
        Args:
            skill_instance_id: ID of the skill instance to schedule
            cron_expression: Cron expression (e.g., "0 9 * * *" for daily at 9am)
            
        Returns:
            True if scheduled successfully, False otherwise
        """
        if not self._running or not self._scheduler:
            logger.error("Scheduler not running")
            return False
        
        # Remove existing job if any
        await self.unschedule_skill(skill_instance_id)
        
        job_id = f"skill_{skill_instance_id}"
        
        try:
            # Parse cron expression
            # Standard cron: minute hour day month day_of_week
            parts = cron_expression.split()
            if len(parts) != 5:
                logger.error(f"Invalid cron expression: {cron_expression}")
                return False
            
            trigger = CronTrigger(
                minute=parts[0],
                hour=parts[1],
                day=parts[2],
                month=parts[3],
                day_of_week=parts[4],
            )
            
            # Add job
            self._scheduler.add_job(
                func=self._execute_skill_job,
                trigger=trigger,
                id=job_id,
                args=[skill_instance_id],
                replace_existing=True,
                max_instances=1,  # Prevent overlapping executions
            )
            
            self._job_ids.add(job_id)
            logger.info(f"Scheduled skill {skill_instance_id} with cron: {cron_expression}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to schedule skill {skill_instance_id}: {e}")
            return False
    
    async def unschedule_skill(self, skill_instance_id: str) -> bool:
        """Remove a skill from the schedule.
        
        Args:
            skill_instance_id: ID of the skill instance to unschedule
            
        Returns:
            True if unscheduled successfully, False otherwise
        """
        if not self._scheduler:
            return False
        
        job_id = f"skill_{skill_instance_id}"
        
        try:
            self._scheduler.remove_job(job_id)
            self._job_ids.discard(job_id)
            logger.info(f"Unscheduled skill {skill_instance_id}")
            return True
        except Exception:
            # Job may not exist, that's ok
            return False
    
    async def get_next_run_time(self, skill_instance_id: str) -> Optional[datetime]:
        """Get the next scheduled run time for a skill.
        
        Args:
            skill_instance_id: ID of the skill instance
            
        Returns:
            Next run time or None if not scheduled
        """
        if not self._scheduler:
            return None
        
        job_id = f"skill_{skill_instance_id}"
        job = self._scheduler.get_job(job_id)
        
        if job and job.next_run_time:
            return job.next_run_time
        return None
    
    def get_all_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """Get list of all scheduled jobs.
        
        Returns:
            List of job information dictionaries
        """
        if not self._scheduler:
            return []
        
        jobs = []
        for job_id in self._job_ids:
            job = self._scheduler.get_job(job_id)
            if job:
                jobs.append({
                    "job_id": job_id,
                    "skill_instance_id": job_id.replace("skill_", ""),
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger),
                })
        return jobs
    
    async def _execute_skill_job(self, skill_instance_id: str) -> None:
        """Execute a skill job (called by scheduler).
        
        Args:
            skill_instance_id: ID of the skill instance to execute
        """
        if not self._runner:
            logger.error("No runner available for skill execution")
            return
        
        logger.info(f"Executing scheduled skill: {skill_instance_id}")
        
        try:
            result = await self._runner.run_by_instance(
                instance_id=skill_instance_id,
                trigger_type="scheduled"
            )
            
            if result.status == "success":
                logger.info(f"Scheduled skill {skill_instance_id} completed successfully")
            else:
                logger.warning(f"Scheduled skill {skill_instance_id} failed: {result.error_message}")
                
        except Exception as e:
            logger.error(f"Error executing scheduled skill {skill_instance_id}: {e}")
    
    # ==========================================================================
    # Workflow Scheduling
    # ==========================================================================

    async def schedule_workflow(
        self,
        workflow_id: str,
        cron_expression: str,
        input_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Schedule a workflow with cron expression.

        Args:
            workflow_id: ID of the workflow definition to schedule
            cron_expression: Cron expression (e.g., "0 9 * * *" for daily at 9am)
            input_data: Optional input data to pass to workflow on each run

        Returns:
            True if scheduled successfully, False otherwise
        """
        if not self._running or not self._scheduler:
            logger.error("Scheduler not running")
            return False

        # Remove existing job if any
        await self.unschedule_workflow(workflow_id)

        job_id = f"workflow_{workflow_id}"

        try:
            # Parse cron expression
            parts = cron_expression.split()
            if len(parts) != 5:
                logger.error(f"Invalid cron expression: {cron_expression}")
                return False

            trigger = CronTrigger(
                minute=parts[0],
                hour=parts[1],
                day=parts[2],
                month=parts[3],
                day_of_week=parts[4],
            )

            # Add job
            self._scheduler.add_job(
                func=self._execute_workflow_job,
                trigger=trigger,
                id=job_id,
                args=[workflow_id, input_data],
                replace_existing=True,
                max_instances=1,  # Prevent overlapping executions
            )

            self._job_ids.add(job_id)
            logger.info(f"Scheduled workflow {workflow_id} with cron: {cron_expression}")
            return True

        except Exception as e:
            logger.error(f"Failed to schedule workflow {workflow_id}: {e}")
            return False

    async def unschedule_workflow(self, workflow_id: str) -> bool:
        """Remove a workflow from the schedule.

        Args:
            workflow_id: ID of the workflow to unschedule

        Returns:
            True if unscheduled successfully, False otherwise
        """
        if not self._scheduler:
            return False

        job_id = f"workflow_{workflow_id}"

        try:
            self._scheduler.remove_job(job_id)
            self._job_ids.discard(job_id)
            logger.info(f"Unscheduled workflow {workflow_id}")
            return True
        except Exception:
            # Job may not exist, that's ok
            return False

    async def get_workflow_next_run_time(self, workflow_id: str) -> Optional[datetime]:
        """Get the next scheduled run time for a workflow.

        Args:
            workflow_id: ID of the workflow

        Returns:
            Next run time or None if not scheduled
        """
        if not self._scheduler:
            return None

        job_id = f"workflow_{workflow_id}"
        job = self._scheduler.get_job(job_id)

        if job and job.next_run_time:
            return job.next_run_time
        return None

    async def _execute_workflow_job(
        self,
        workflow_id: str,
        input_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Execute a workflow job (called by scheduler).

        Args:
            workflow_id: ID of the workflow to execute
            input_data: Input data for the workflow
        """
        if not self._workflow_service:
            logger.error("No workflow service available for execution")
            return

        logger.info(f"Executing scheduled workflow: {workflow_id}")

        try:
            execution = await self._workflow_service.execute_workflow(
                workflow_id=workflow_id,
                input_data=input_data,
                trigger_type="schedule"
            )

            if execution and execution.status.value == "success":
                logger.info(f"Scheduled workflow {workflow_id} completed successfully")
            else:
                status = execution.status.value if execution else "unknown"
                error = execution.error_message if execution else "No execution result"
                logger.warning(f"Scheduled workflow {workflow_id} failed: {status} - {error}")

        except Exception as e:
            logger.error(f"Error executing scheduled workflow {workflow_id}: {e}")

    # ==========================================================================
    # Database Loading
    # ==========================================================================

    async def load_schedules_from_database(self) -> int:
        """Load and schedule all enabled skill instances and workflows with schedules.

        Returns:
            Number of items scheduled
        """
        from open_notebook.domain.skill import SkillInstance
        from open_notebook.domain.workflow import WorkflowDefinition

        count = 0

        # Load skill schedules
        try:
            instances = await SkillInstance.get_enabled()
            for instance in instances:
                if instance.schedule:
                    success = await self.schedule_skill(instance.id, instance.schedule)
                    if success:
                        count += 1
            logger.info(f"Loaded {count} scheduled skills from database")
        except Exception as e:
            logger.error(f"Failed to load skill schedules from database: {e}")

        # Load workflow schedules
        try:
            workflows = await WorkflowDefinition.get_enabled()
            workflow_count = 0
            for workflow in workflows:
                if workflow.schedule:
                    success = await self.schedule_workflow(workflow.id, workflow.schedule)
                    if success:
                        workflow_count += 1
            logger.info(f"Loaded {workflow_count} scheduled workflows from database")
            count += workflow_count
        except Exception as e:
            logger.error(f"Failed to load workflow schedules from database: {e}")

        return count

    def get_all_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """Get list of all scheduled jobs (skills and workflows).

        Returns:
            List of job information dictionaries
        """
        if not self._scheduler:
            return []

        jobs = []
        for job_id in self._job_ids:
            job = self._scheduler.get_job(job_id)
            if job:
                job_info = {
                    "job_id": job_id,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger),
                }

                # Determine type and extract ID
                if job_id.startswith("skill_"):
                    job_info["type"] = "skill"
                    job_info["skill_instance_id"] = job_id.replace("skill_", "")
                elif job_id.startswith("workflow_"):
                    job_info["type"] = "workflow"
                    job_info["workflow_id"] = job_id.replace("workflow_", "")

                jobs.append(job_info)

        return jobs


# Global scheduler instance
skill_scheduler = SkillScheduler()
