"""Browser Task Skill - General purpose browser automation.

This module provides a flexible browser automation skill that can
execute arbitrary tasks described in natural language.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from open_notebook.skills.base import SkillConfig, SkillContext, SkillResult, SkillStatus
from open_notebook.skills.browser_base import BrowserUseSkill
from open_notebook.skills.registry import register_skill


@register_skill
class BrowserTaskSkill(BrowserUseSkill):
    """Execute arbitrary browser tasks using natural language.
    
    This skill allows you to automate any browser-based task by describing
    it in natural language. The AI will figure out the steps needed.
    
    Use cases:
        - Form filling and submission
        - Data entry automation
        - Website monitoring
        - Automated testing
        - Content extraction with custom logic
    
    Parameters:
        - task: Natural language description of the task to perform
        - url: Starting URL (optional, can be in task description)
        - max_steps: Maximum steps to take (default: 20)
        - save_screenshot: Whether to save final screenshot (default: false)
        - extract_data: Data to extract after task completion (optional)
    
    Example:
        config = SkillConfig(
            skill_type="browser_task",
            name="Login Automation",
            parameters={
                "task": "Go to example.com, login with username 'admin' and password 'secret', then navigate to the dashboard and extract the user count",
                "max_steps": 15
            }
        )
    """
    
    skill_type = "browser_task"
    name = "Browser Task Automation"
    description = "Execute arbitrary browser tasks using natural language instructions"
    
    parameters_schema = {
        **BrowserUseSkill.parameters_schema,
        "task": {
            "type": "string",
            "description": "Natural language description of the task to perform"
        },
        "url": {
            "type": "string",
            "format": "uri",
            "description": "Starting URL (optional, can be included in task)"
        },
        "max_steps": {
            "type": "integer",
            "default": 20,
            "minimum": 1,
            "maximum": 100,
            "description": "Maximum number of steps to take"
        },
        "save_screenshot": {
            "type": "boolean",
            "default": False,
            "description": "Whether to save a screenshot of the final state"
        },
        "extract_data": {
            "type": "string",
            "description": "Description of data to extract after task completion (optional)"
        }
    }
    
    def __init__(self, config: SkillConfig):
        super().__init__(config)
        self.task: str = self.get_param("task", "")
        self.url: Optional[str] = self.get_param("url")
        self.max_steps: int = self.get_param("max_steps", 20)
        self.save_screenshot: bool = self.get_param("save_screenshot", False)
        self.extract_data: Optional[str] = self.get_param("extract_data")
    
    def _validate_config(self) -> None:
        """Validate browser task configuration."""
        super()._validate_config()
        
        if not self.task:
            raise ValueError("Task description is required")
        
        if self.url and not self.url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid URL: {self.url}")
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute browser automation task."""
        logger.info(f"Starting browser task: {self.task[:100]}...")
        
        # Build the full task description
        full_task = self.task
        if self.url and self.url not in self.task:
            full_task = f"Go to {self.url} and {full_task}"
        
        if self.extract_data:
            full_task += f"\n\nAfter completing the task, extract the following data: {self.extract_data}"
        
        try:
            # Run the browser task
            result = await self.run_browser_task(full_task, max_steps=self.max_steps)
            
            if result["success"]:
                logger.info("Browser task completed successfully")
                
                output = {
                    "task": self.task,
                    "steps_taken": result.get("steps_taken", 0),
                    "result": result.get("result"),
                }
                
                # Add screenshot info if enabled
                if self.save_screenshot:
                    output["screenshot_saved"] = False  # Would be implemented with actual screenshot
                
                return SkillResult(
                    skill_id=context.skill_id,
                    status=SkillStatus.SUCCESS,
                    started_at=datetime.utcnow(),
                    output=output
                )
            else:
                error_msg = result.get("error", "Unknown error")
                logger.error(f"Browser task failed: {error_msg}")
                
                return SkillResult(
                    skill_id=context.skill_id,
                    status=SkillStatus.FAILED,
                    started_at=datetime.utcnow(),
                    output={
                        "task": self.task,
                        "error": error_msg,
                        "partial_result": result.get("result")
                    },
                    error_message=error_msg
                )
                
        except Exception as e:
            error_msg = f"Browser task execution error: {str(e)}"
            logger.error(error_msg)
            
            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.FAILED,
                started_at=datetime.utcnow(),
                output={"task": self.task},
                error_message=error_msg
            )


@register_skill
class BrowserMonitorSkill(BrowserUseSkill):
    """Monitor a webpage for changes.
    
    This skill periodically checks a webpage and reports changes.
    Useful for monitoring prices, availability, news, etc.
    
    Parameters:
        - url: URL to monitor
        - check_task: Description of what to check on the page
        - expected_value: Expected value (optional, for alerting when changed)
    
    Example:
        config = SkillConfig(
            skill_type="browser_monitor",
            name="Price Monitor",
            parameters={
                "url": "https://example.com/product",
                "check_task": "Extract the current price of the product"
            },
            schedule="0 */6 * * *"  # Every 6 hours
        )
    """
    
    skill_type = "browser_monitor"
    name = "Webpage Monitor"
    description = "Monitor webpages for changes and send alerts"
    
    parameters_schema = {
        **BrowserUseSkill.parameters_schema,
        "url": {
            "type": "string",
            "format": "uri",
            "description": "URL to monitor"
        },
        "check_task": {
            "type": "string",
            "description": "Description of what to check/extract from the page"
        },
        "expected_value": {
            "type": "string",
            "description": "Expected value (optional, alerts when changed)"
        }
    }
    
    def __init__(self, config: SkillConfig):
        super().__init__(config)
        self.url: str = self.get_param("url", "")
        self.check_task: str = self.get_param("check_task", "")
        self.expected_value: Optional[str] = self.get_param("expected_value")
    
    def _validate_config(self) -> None:
        """Validate monitor configuration."""
        super()._validate_config()
        
        if not self.url:
            raise ValueError("URL is required for monitoring")
        
        if not self.check_task:
            raise ValueError("Check task description is required")
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute webpage monitoring."""
        logger.info(f"Monitoring {self.url}")
        
        task = f"Go to {self.url} and {self.check_task}. Return only the extracted value."
        
        try:
            result = await self.run_browser_task(task, max_steps=10)
            
            if result["success"]:
                current_value = str(result.get("result", ""))
                
                # Check if value changed from expected
                changed = False
                if self.expected_value and current_value != self.expected_value:
                    changed = True
                    logger.info(f"Value changed! Expected: {self.expected_value}, Got: {current_value}")
                
                return SkillResult(
                    skill_id=context.skill_id,
                    status=SkillStatus.SUCCESS,
                    started_at=datetime.utcnow(),
                    output={
                        "url": self.url,
                        "current_value": current_value,
                        "expected_value": self.expected_value,
                        "changed": changed
                    }
                )
            else:
                return SkillResult(
                    skill_id=context.skill_id,
                    status=SkillStatus.FAILED,
                    started_at=datetime.utcnow(),
                    output={"url": self.url},
                    error_message=result.get("error", "Monitoring failed")
                )
                
        except Exception as e:
            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.FAILED,
                started_at=datetime.utcnow(),
                output={"url": self.url},
                error_message=str(e)
            )
