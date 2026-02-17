"""Publish Workflow Orchestrator - Complete content publishing pipeline.

This module orchestrates the entire content publishing workflow:
    1. Content Preparation - Validate and format content
    2. Publish Decision - Determine when and where to publish
    3. Auto-Publish - Use browser automation for hands-free publishing
    4. Data Collection - Gather publish results and URLs
    5. Feedback Loop - Send results back to P3 evolution layer

Workflow:
    Content -> Validation -> Platform Selection ->
    Browser Publish -> Result Collection -> P3 Feedback
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from open_notebook.domain.platform_connector import PlatformAccount
from open_notebook.domain.publish_job import PublishContent, PublishResult
from open_notebook.skills.browser_publisher import (
    BaseBrowserPublisher,
    BrowserPublisherRegistry,
)
from open_notebook.skills.feedback_loop import FeedbackLoopOrchestrator


@dataclass
class WorkflowStep:
    """A step in the publishing workflow."""
    step_name: str
    status: str  # pending, running, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error_message: Optional[str] = None


@dataclass
class WorkflowContext:
    """Context for a publishing workflow execution."""
    workflow_id: str
    content: PublishContent
    target_platforms: List[str]
    scheduled_time: Optional[datetime] = None
    auto_publish: bool = True  # If False, requires manual confirmation
    steps: List[WorkflowStep] = None
    results: Dict[str, PublishResult] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.steps is None:
            self.steps = []
        if self.results is None:
            self.results = {}
        if self.created_at is None:
            self.created_at = datetime.now()


class PublishWorkflowOrchestrator:
    """Orchestrates the complete content publishing workflow.

    This is the main entry point for automated content publishing.
    It coordinates all steps from content validation to P3 feedback.
    """

    def __init__(self):
        self.feedback_orchestrator = FeedbackLoopOrchestrator()
        self.active_workflows: Dict[str, WorkflowContext] = {}

    async def execute_workflow(
        self,
        content: PublishContent,
        target_platforms: List[str],
        scheduled_time: Optional[datetime] = None,
        auto_publish: bool = True
    ) -> WorkflowContext:
        """Execute the complete publishing workflow.

        Args:
            content: Content to publish
            target_platforms: List of platform identifiers
            scheduled_time: When to publish (None for immediate)
            auto_publish: Whether to auto-publish or wait for confirmation

        Returns:
            WorkflowContext with execution results
        """
        workflow_id = f"pub_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        context = WorkflowContext(
            workflow_id=workflow_id,
            content=content,
            target_platforms=target_platforms,
            scheduled_time=scheduled_time,
            auto_publish=auto_publish
        )

        self.active_workflows[workflow_id] = context

        logger.info(f"Starting publish workflow {workflow_id}")

        try:
            # Step 1: Content Validation
            await self._run_step(context, "content_validation", self._validate_content)

            # Step 2: Platform Verification
            await self._run_step(context, "platform_verification", self._verify_platforms)

            # Step 3: Publish Decision
            await self._run_step(context, "publish_decision", self._make_publish_decision)

            # Step 4: Auto-Publish
            if context.auto_publish:
                await self._run_step(context, "auto_publish", self._execute_publish)
            else:
                logger.info("Auto-publish disabled, waiting for manual confirmation")
                context.steps.append(WorkflowStep(
                    step_name="auto_publish",
                    status="waiting_confirmation",
                    result={"message": "Waiting for manual confirmation"}
                ))

            # Step 5: Data Collection
            await self._run_step(context, "data_collection", self._collect_results)

            # Step 6: P3 Feedback
            await self._run_step(context, "p3_feedback", self._send_p3_feedback)

            logger.info(f"Workflow {workflow_id} completed")
            return context

        except Exception as e:
            logger.exception(f"Workflow {workflow_id} failed: {e}")
            context.steps.append(WorkflowStep(
                step_name="workflow",
                status="failed",
                error_message=str(e),
                completed_at=datetime.now()
            ))
            return context

    async def _run_step(
        self,
        context: WorkflowContext,
        step_name: str,
        step_func
    ):
        """Run a workflow step with tracking."""
        step = WorkflowStep(
            step_name=step_name,
            status="running",
            started_at=datetime.now()
        )
        context.steps.append(step)

        try:
            result = await step_func(context)
            step.status = "completed"
            step.result = result
            step.completed_at = datetime.now()
            logger.info(f"Step '{step_name}' completed successfully")
        except Exception as e:
            step.status = "failed"
            step.error_message = str(e)
            step.completed_at = datetime.now()
            logger.error(f"Step '{step_name}' failed: {e}")
            raise

    async def _validate_content(self, context: WorkflowContext) -> Dict[str, Any]:
        """Validate content for publishing."""
        content = context.content

        validation_results = {
            "title_valid": len(content.title) > 0,
            "content_valid": len(content.content) > 0,
            "media_valid": True,
            "warnings": []
        }

        # Check title length (different platforms have different limits)
        if len(content.title) > 100:
            validation_results["warnings"].append("Title may be too long for some platforms")

        # Check content length
        if len(content.content) < 10:
            validation_results["content_valid"] = False
            raise ValueError("Content is too short (minimum 10 characters)")

        # Check media files exist
        if content.images:
            for img_path in content.images:
                if not img_path.startswith("http") and not img_path.startswith("/"):
                    validation_results["media_valid"] = False
                    raise ValueError(f"Invalid image path: {img_path}")

        if content.video:
            if not content.video.startswith("http") and not content.video.startswith("/"):
                validation_results["media_valid"] = False
                raise ValueError(f"Invalid video path: {content.video}")

        return validation_results

    async def _verify_platforms(self, context: WorkflowContext) -> Dict[str, Any]:
        """Verify that target platforms are available and authenticated."""
        available_platforms = []
        unavailable_platforms = []

        for platform in context.target_platforms:
            # Check if we have browser publisher support
            publisher = BrowserPublisherRegistry.get_publisher(platform)

            if not publisher:
                unavailable_platforms.append({
                    "platform": platform,
                    "reason": "No browser publisher available"
                })
                continue

            # Test connection
            try:
                is_connected, message = await publisher.test_connection()
                if is_connected:
                    available_platforms.append(platform)
                else:
                    unavailable_platforms.append({
                        "platform": platform,
                        "reason": message
                    })
            except Exception as e:
                unavailable_platforms.append({
                    "platform": platform,
                    "reason": f"Connection test failed: {str(e)}"
                })

        # Update target platforms to only available ones
        context.target_platforms = available_platforms

        return {
            "available": available_platforms,
            "unavailable": unavailable_platforms
        }

    async def _make_publish_decision(self, context: WorkflowContext) -> Dict[str, Any]:
        """Make decision about when and how to publish."""
        decision = {
            "should_publish_now": context.scheduled_time is None,
            "scheduled_time": context.scheduled_time,
            "platforms": context.target_platforms,
            "requires_confirmation": not context.auto_publish
        }

        # If scheduled time is provided, calculate wait time
        if context.scheduled_time:
            now = datetime.now()
            if context.scheduled_time > now:
                wait_seconds = (context.scheduled_time - now).total_seconds()
                decision["wait_seconds"] = wait_seconds
                decision["should_publish_now"] = False

                logger.info(f"Content scheduled for {context.scheduled_time}, waiting {wait_seconds}s")

                # Wait until scheduled time
                await asyncio.sleep(min(wait_seconds, 300))  # Max 5 min per iteration
            else:
                decision["should_publish_now"] = True
                decision["scheduled_time_passed"] = True

        return decision

    async def _execute_publish(self, context: WorkflowContext) -> Dict[str, PublishResult]:
        """Execute publishing to all target platforms."""
        results = {}

        for platform in context.target_platforms:
            try:
                logger.info(f"Publishing to {platform}...")

                # Get publisher
                publisher = BrowserPublisherRegistry.get_publisher(platform)
                if not publisher:
                    results[platform] = PublishResult(
                        success=False,
                        platform=platform,
                        error_message="Publisher not available"
                    )
                    continue

                # Publish
                result = await publisher.publish(context.content)
                results[platform] = result

                if result.success:
                    logger.info(f"Successfully published to {platform}: {result.url}")
                else:
                    logger.error(f"Failed to publish to {platform}: {result.error_message}")

            except Exception as e:
                logger.exception(f"Error publishing to {platform}: {e}")
                results[platform] = PublishResult(
                    success=False,
                    platform=platform,
                    error_message=str(e)
                )

        context.results = results
        return results

    async def _collect_results(self, context: WorkflowContext) -> Dict[str, Any]:
        """Collect and store publish results."""
        collection = {
            "successful": [],
            "failed": [],
            "total": len(context.results)
        }

        for platform, result in context.results.items():
            if result.success:
                collection["successful"].append({
                    "platform": platform,
                    "url": result.url,
                    "content_id": result.content_id
                })
            else:
                collection["failed"].append({
                    "platform": platform,
                    "error": result.error_message
                })

        return collection

    async def _send_p3_feedback(self, context: WorkflowContext) -> Dict[str, Any]:
        """Send publish results back to P3 evolution layer for learning."""
        feedback_data = {
            "workflow_id": context.workflow_id,
            "content_title": context.content.title,
            "platforms_attempted": list(context.results.keys()),
            "platforms_succeeded": [
                p for p, r in context.results.items() if r.success
            ],
            "platforms_failed": [
                p for p, r in context.results.items() if not r.success
            ]
        }

        # Send to feedback loop
        try:
            self.feedback_orchestrator.collect_and_learn(
                plan_id=f"publish_{context.workflow_id}",
                quadrant="Q3" if len(context.target_platforms) > 1 else "Q1",
                metrics={
                    "platforms_count": len(context.target_platforms),
                    "success_count": sum(1 for r in context.results.values() if r.success),
                    "fail_count": sum(1 for r in context.results.values() if not r.success)
                },
                outcome_value=100 if all(r.success for r in context.results.values()) else 50
            )

            feedback_data["sent_to_p3"] = True
        except Exception as e:
            logger.error(f"Failed to send P3 feedback: {e}")
            feedback_data["sent_to_p3"] = False

        return feedback_data

    def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowContext]:
        """Get the status of a running or completed workflow."""
        return self.active_workflows.get(workflow_id)

    def list_active_workflows(self) -> List[WorkflowContext]:
        """List all active workflows."""
        return [
            ctx for ctx in self.active_workflows.values()
            if any(s.status == "running" for s in ctx.steps)
        ]


# Global orchestrator instance
publish_workflow_orchestrator = PublishWorkflowOrchestrator()


async def publish_content(
    title: str,
    content: str,
    platforms: List[str],
    images: Optional[List[str]] = None,
    video: Optional[str] = None,
    tags: Optional[List[str]] = None,
    scheduled_time: Optional[datetime] = None,
    auto_publish: bool = True
) -> WorkflowContext:
    """High-level function to publish content.

    Args:
        title: Content title
        content: Content body
        platforms: List of target platforms
        images: List of image file paths
        video: Video file path
        tags: List of tags/hashtags
        scheduled_time: When to publish
        auto_publish: Whether to auto-publish

    Returns:
        WorkflowContext with execution results
    """
    publish_content = PublishContent(
        title=title,
        content=content,
        images=images or [],
        video=video,
        tags=tags or []
    )

    return await publish_workflow_orchestrator.execute_workflow(
        content=publish_content,
        target_platforms=platforms,
        scheduled_time=scheduled_time,
        auto_publish=auto_publish
    )
