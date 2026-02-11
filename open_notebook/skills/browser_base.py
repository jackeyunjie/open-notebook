"""Browser automation base skill using browser-use.

This module provides browser automation capabilities for Open Notebook,
enabling AI-driven web scraping, form filling, and content extraction.
"""

import os
from abc import abstractmethod
from typing import Any, Dict, List, Optional

from loguru import logger

from open_notebook.skills.base import Skill, SkillConfig, SkillContext, SkillResult, SkillStatus
from open_notebook.skills.registry import register_skill


class BrowserUseSkill(Skill):
    """Base skill for browser automation using browser-use.
    
    Browser-use is an AI-driven browser automation library that allows
    natural language control of web browsers. This skill provides the
    foundation for web scraping, content extraction, and automated
    interactions.
    
    Requirements:
        - Chrome/Chromium installed in the environment
        - LLM API key configured (OpenAI, Anthropic, etc.)
    
    Parameters:
        - headless: Run browser in headless mode (default: true)
        - timeout: Page load timeout in seconds (default: 30)
        - window_size: Browser window size (default: "1920,1080")
    
    Example:
        config = SkillConfig(
            skill_type="browser_use",
            name="Web Scraper",
            parameters={
                "headless": True,
                "timeout": 30
            }
        )
    """
    
    skill_type = "browser_use"
    name = "Browser Automation Base"
    description = "AI-driven browser automation using browser-use library"
    
    parameters_schema = {
        "headless": {
            "type": "boolean",
            "default": True,
            "description": "Run browser in headless mode"
        },
        "timeout": {
            "type": "integer",
            "default": 30,
            "minimum": 5,
            "maximum": 300,
            "description": "Page load timeout in seconds"
        },
        "window_size": {
            "type": "string",
            "default": "1920,1080",
            "description": "Browser window size (width,height)"
        },
        "chrome_path": {
            "type": "string",
            "default": "/usr/bin/google-chrome",
            "description": "Path to Chrome executable"
        }
    }
    
    def __init__(self, config: SkillConfig):
        # Initialize parameters BEFORE calling super().__init__
        self.headless: bool = config.parameters.get("headless", True)
        self.timeout: int = config.parameters.get("timeout", 30)
        self.window_size: str = config.parameters.get("window_size", "1920,1080")
        self.chrome_path: str = config.parameters.get("chrome_path", "/usr/bin/google-chrome")
        self._browser = None
        self._agent = None
        super().__init__(config)
    
    def _validate_config(self) -> None:
        """Validate browser-use configuration."""
        super()._validate_config()
        
        # Check Chrome is available
        if not os.path.exists(self.chrome_path):
            logger.warning(f"Chrome not found at {self.chrome_path}, will try to auto-detect")
    
    async def before_execute(self, context: SkillContext) -> None:
        """Initialize browser-use agent."""
        try:
            from browser_use import Agent, Browser, BrowserConfig
            from langchain_openai import ChatOpenAI
            
            # Parse window size
            width, height = self.window_size.split(",")
            
            # Configure browser
            browser_config = BrowserConfig(
                headless=self.headless,
                chrome_instance_path=self.chrome_path if os.path.exists(self.chrome_path) else None,
            )
            
            self._browser = Browser(config=browser_config)
            
            # Initialize LLM (will use configured provider)
            # This will be enhanced to support multiple providers
            llm = ChatOpenAI(model="gpt-4o", temperature=0)
            
            self._agent = Agent(
                task="",  # Will be set in execute
                llm=llm,
                browser=self._browser,
            )
            
            logger.info("Browser-use agent initialized")
            
        except ImportError as e:
            logger.error(f"browser-use not installed: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise
    
    async def after_execute(self, context: SkillContext, result: SkillResult) -> None:
        """Clean up browser resources."""
        if self._browser:
            try:
                await self._browser.close()
                logger.info("Browser closed")
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
    
    async def run_browser_task(self, task: str, max_steps: int = 10) -> Dict[str, Any]:
        """Run a browser automation task.
        
        Args:
            task: Natural language description of the task
            max_steps: Maximum number of steps to take
            
        Returns:
            Dict with task results including extracted content
        """
        if not self._agent:
            raise RuntimeError("Browser agent not initialized")
        
        try:
            # Update agent task
            self._agent.task = task
            
            # Run the task
            result = await self._agent.run(max_steps=max_steps)
            
            return {
                "success": True,
                "task": task,
                "result": result,
                "steps_taken": len(result.action_results) if hasattr(result, 'action_results') else 0,
            }
            
        except Exception as e:
            logger.error(f"Browser task failed: {e}")
            return {
                "success": False,
                "task": task,
                "error": str(e),
            }
    
    @abstractmethod
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute browser automation. Must be implemented by subclasses."""
        raise NotImplementedError("BrowserUseSkill subclasses must implement execute()")


class BrowserCrawlerSkill(BrowserUseSkill):
    """Crawl web pages using AI-driven browser automation.
    
    This skill uses browser-use to intelligently navigate websites,
    extract content, and handle dynamic pages that RSS cannot access.
    
    Parameters:
        - urls: List of URLs to crawl
        - extraction_task: Natural language description of what to extract
        - max_pages: Maximum pages to crawl per URL (default: 1)
        - follow_links: Whether to follow links (default: false)
    
    Example:
        config = SkillConfig(
            skill_type="browser_crawler",
            name="Article Crawler",
            parameters={
                "urls": ["https://example.com/blog"],
                "extraction_task": "Extract all article titles and their full content",
                "max_pages": 5
            },
            target_notebook_id="notebook:abc123"
        )
    """
    
    skill_type = "browser_crawler"
    name = "Browser Content Crawler"
    description = "AI-driven web crawling for dynamic content extraction"
    
    parameters_schema = {
        **BrowserUseSkill.parameters_schema,
        "urls": {
            "type": "array",
            "items": {"type": "string", "format": "uri"},
            "description": "List of URLs to crawl"
        },
        "extraction_task": {
            "type": "string",
            "description": "Natural language description of what content to extract"
        },
        "max_pages": {
            "type": "integer",
            "default": 1,
            "minimum": 1,
            "maximum": 50,
            "description": "Maximum pages to crawl per URL"
        },
        "follow_links": {
            "type": "boolean",
            "default": False,
            "description": "Whether to follow links on the page"
        }
    }
    
    def __init__(self, config: SkillConfig):
        super().__init__(config)
        self.urls: List[str] = self.get_param("urls", [])
        self.extraction_task: str = self.get_param("extraction_task", "Extract the main content")
        self.max_pages: int = self.get_param("max_pages", 1)
        self.follow_links: bool = self.get_param("follow_links", False)
    
    def _validate_config(self) -> None:
        """Validate browser crawler configuration."""
        super()._validate_config()
        
        if not self.urls:
            raise ValueError("At least one URL is required")
        
        for url in self.urls:
            if not url.startswith(("http://", "https://")):
                raise ValueError(f"Invalid URL: {url}")
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute browser crawling."""
        from datetime import datetime
        
        logger.info(f"Starting browser crawl for {len(self.urls)} URLs")
        
        crawled_content: List[Dict[str, Any]] = []
        errors: List[str] = []
        
        for url in self.urls:
            try:
                # Build task description
                task = f"Go to {url} and {self.extraction_task}. "
                if self.follow_links:
                    task += f"You may follow up to {self.max_pages} related links. "
                task += "Return the extracted content in a structured format."
                
                # Run browser task
                result = await self.run_browser_task(task, max_steps=self.max_pages * 5)
                
                if result["success"]:
                    crawled_content.append({
                        "url": url,
                        "content": result.get("result"),
                        "steps": result.get("steps_taken", 0)
                    })
                    logger.info(f"Successfully crawled {url}")
                else:
                    error_msg = f"Failed to crawl {url}: {result.get('error')}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    
            except Exception as e:
                error_msg = f"Error crawling {url}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # Determine status
        if errors and not crawled_content:
            status = SkillStatus.FAILED
        elif errors:
            status = SkillStatus.SUCCESS
        else:
            status = SkillStatus.SUCCESS
        
        return SkillResult(
            skill_id=context.skill_id,
            status=status,
            started_at=datetime.utcnow(),
            output={
                "urls_processed": len(self.urls),
                "urls_successful": len(crawled_content),
                "urls_failed": len(errors),
                "content": crawled_content,
                "errors": errors
            },
            error_message="; ".join(errors) if errors else None
        )


# Register skills
register_skill(BrowserUseSkill)
register_skill(BrowserCrawlerSkill)
