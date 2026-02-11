"""Skill execution engine for running skills asynchronously.

The SkillRunner handles:
- Executing skills with proper context
- Managing execution lifecycle
- Logging execution history
- Handling errors and retries
"""

from datetime import datetime
from typing import Any, Dict, Optional

from loguru import logger

from open_notebook.domain.skill import SkillExecution, SkillInstance
from open_notebook.skills.base import SkillConfig, SkillContext, SkillResult, SkillStatus
from open_notebook.skills.registry import SkillRegistry


class SkillRunner:
    """Execute skills with full lifecycle management.
    
    Usage:
        runner = SkillRunner()
        
        # Run by skill instance ID
        result = await runner.run_by_instance(
            instance_id="skill_instance:abc123",
            trigger_type="manual",
            triggered_by="user_123"
        )
        
        # Run skill directly
        result = await runner.run_skill(
            skill_type="rss_crawler",
            parameters={"feed_url": "https://example.com/rss"},
            context=context
        )
    """
    
    async def run_by_instance(
        self,
        instance_id: str,
        trigger_type: str = "manual",
        triggered_by: Optional[str] = None,
        extra_parameters: Optional[Dict[str, Any]] = None,
    ) -> SkillResult:
        """Execute a skill by its instance ID.
        
        Args:
            instance_id: The skill instance ID
            trigger_type: How the skill was triggered
            triggered_by: Who/what triggered the skill
            extra_parameters: Additional parameters to merge
            
        Returns:
            SkillResult with execution details
        """
        # Load skill instance
        try:
            instance = await SkillInstance.get(instance_id)
        except Exception as e:
            logger.error(f"Failed to load skill instance {instance_id}: {e}")
            return SkillResult(
                skill_id=instance_id,
                status=SkillStatus.FAILED,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                error_message=f"Failed to load skill instance: {e}",
            )
        
        if not instance.enabled:
            return SkillResult(
                skill_id=instance_id,
                status=SkillStatus.FAILED,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                error_message="Skill instance is disabled",
            )
        
        # Create execution record
        execution = SkillExecution(
            skill_instance_id=instance_id,
            status="running",
            trigger_type=trigger_type,
            triggered_by=triggered_by,
        )
        await execution.save()
        
        # Merge parameters
        parameters = dict(instance.parameters)
        if extra_parameters:
            parameters.update(extra_parameters)
        
        # Build context
        context = SkillContext(
            skill_id=execution.id,
            trigger_type=trigger_type,
            notebook_id=instance.target_notebook_id,
            user_id=triggered_by,
            parameters=parameters,
        )
        
        # Create skill config
        config = SkillConfig(
            skill_type=instance.skill_type,
            name=instance.name,
            description=instance.description or "",
            parameters=parameters,
            target_notebook_id=instance.target_notebook_id,
        )
        
        # Execute
        try:
            skill = SkillRegistry.create(config)
            result = await skill.run(context)
            
            # Update execution record
            execution.mark_completed(
                status=result.status.value,
                output=result.output,
                error=result.error_message,
            )
            execution.created_source_ids = result.created_source_ids
            execution.created_note_ids = result.created_note_ids
            await execution.save()
            
            logger.info(
                f"Skill {instance.skill_type} ({instance.name}) completed with status: {result.status.value}"
            )
            return result
            
        except Exception as e:
            logger.exception(f"Skill execution failed: {e}")
            
            # Update execution record with failure
            execution.mark_completed(
                status="failed",
                error=str(e),
            )
            await execution.save()
            
            return SkillResult(
                skill_id=execution.id,
                status=SkillStatus.FAILED,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                error_message=str(e),
            )
    
    async def run_skill(
        self,
        skill_type: str,
        parameters: Dict[str, Any],
        context: Optional[SkillContext] = None,
        name: str = "Ad-hoc Execution",
        description: str = "",
    ) -> SkillResult:
        """Run a skill directly without a stored instance.
        
        Args:
            skill_type: The type of skill to run
            parameters: Parameters for the skill
            context: Optional execution context
            name: Name for this execution
            description: Description for this execution
            
        Returns:
            SkillResult with execution details
        """
        if context is None:
            context = SkillContext(
                skill_id=f"adhoc_{datetime.utcnow().isoformat()}",
                trigger_type="manual",
                parameters=parameters,
            )
        
        config = SkillConfig(
            skill_type=skill_type,
            name=name,
            description=description,
            parameters=parameters,
        )
        
        try:
            skill = SkillRegistry.create(config)
            return await skill.run(context)
        except Exception as e:
            logger.exception(f"Direct skill execution failed: {e}")
            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.FAILED,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                error_message=str(e),
            )
    
    async def get_execution_status(self, execution_id: str) -> Optional[SkillExecution]:
        """Get the status of a skill execution.
        
        Args:
            execution_id: The execution ID
            
        Returns:
            SkillExecution or None if not found
        """
        try:
            return await SkillExecution.get(execution_id)
        except Exception:
            return None
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running skill execution.
        
        Note: This marks the execution as cancelled in the database,
        but doesn't actually stop the running process (that would require
        more complex process management).
        
        Args:
            execution_id: The execution ID to cancel
            
        Returns:
            True if cancelled, False if not found or already completed
        """
        try:
            execution = await SkillExecution.get(execution_id)
            if execution.status != "running":
                return False
            
            execution.mark_completed(
                status="cancelled",
                error="Execution was cancelled",
            )
            await execution.save()
            return True
        except Exception:
            return False


# Global runner instance
_skill_runner: Optional[SkillRunner] = None


def get_skill_runner() -> SkillRunner:
    """Get the global skill runner instance."""
    global _skill_runner
    if _skill_runner is None:
        _skill_runner = SkillRunner()
    return _skill_runner
