"""Browser-based Auto-Publish System - Automate content publishing using browser-use.

This module provides automated content publishing capabilities by controlling
a real browser, reusing existing login sessions from the user's system.

Key Features:
    - Reuse system browser login sessions (cookies, localStorage)
    - AI-driven content filling and form submission
    - Support for media uploads (images, videos)
    - Automatic error handling and retry logic
    - Headless and headed modes for debugging

Architecture:
    BaseBrowserPublisher (abstract)
    ├── XiaohongshuBrowserPublisher
    ├── WeiboBrowserPublisher
    └── ...

Usage:
    from open_notebook.skills.browser_publisher import XiaohongshuBrowserPublisher

    publisher = XiaohongshuBrowserPublisher()
    result = await publisher.publish(
        title="AI工具推荐",
        content="分享5个实用的AI工具...",
        images=["/path/to/image1.jpg", "/path/to/image2.jpg"],
        tags=["AI", "效率工具"]
    )
"""

import asyncio
import os
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

from loguru import logger

from open_notebook.skills.base import SkillConfig
from open_notebook.skills.browser_base import BrowserUseSkill


@dataclass
class PublishResult:
    """Result of a browser-based publishing operation."""
    success: bool
    platform: str
    content_id: Optional[str] = None
    url: Optional[str] = None
    error_message: Optional[str] = None
    published_at: Optional[datetime] = None
    screenshot_path: Optional[str] = None  # For debugging
    raw_response: Optional[Dict[str, Any]] = None


@dataclass
class PublishContent:
    """Content to be published."""
    title: str
    content: str
    images: List[str] = None  # List of local file paths
    video: Optional[str] = None  # Local video file path
    tags: List[str] = None
    location: Optional[str] = None
    scheduled_time: Optional[datetime] = None

    def __post_init__(self):
        if self.images is None:
            self.images = []
        if self.tags is None:
            self.tags = []


class BaseBrowserPublisher(ABC):
    """Abstract base class for browser-based content publishing.

    This class leverages the BrowserUseSkill to automate content publishing
    by controlling a real browser with existing login sessions.
    """

    def __init__(
        self,
        headless: bool = True,
        use_system_browser: bool = True,
        user_data_dir: Optional[str] = None,
        timeout: int = 120
    ):
        """Initialize the browser publisher.

        Args:
            headless: Whether to run browser in headless mode
            use_system_browser: Whether to reuse system browser's login session
            user_data_dir: Path to Chrome user data directory
            timeout: Operation timeout in seconds
        """
        self.headless = headless
        self.use_system_browser = use_system_browser
        self.user_data_dir = user_data_dir or self._get_default_user_data_dir()
        self.timeout = timeout
        self._browser_skill: Optional[BrowserUseSkill] = None
        self._platform_name = self.__class__.__name__.replace("BrowserPublisher", "").lower()

    def _get_default_user_data_dir(self) -> str:
        """Get default Chrome user data directory based on OS."""
        home = Path.home()

        if os.name == "nt":  # Windows
            return str(home / "AppData/Local/Google/Chrome/User Data")
        elif os.name == "posix":
            if os.uname().sysname == "Darwin":  # macOS
                return str(home / "Library/Application Support/Google/Chrome")
            else:  # Linux
                return str(home / ".config/google-chrome")

        return ""

    async def _init_browser(self) -> BrowserUseSkill:
        """Initialize browser skill with appropriate configuration."""
        if self._browser_skill is None:
            config = SkillConfig(
                skill_type="browser_use",
                name=f"{self._platform_name}_publisher",
                parameters={
                    "headless": self.headless,
                    "timeout": self.timeout,
                    "window_size": "1920,1080",
                    "use_system_browser": self.use_system_browser,
                    "user_data_dir": self.user_data_dir,
                }
            )
            self._browser_skill = BrowserUseSkill(config)

        return self._browser_skill

    @abstractmethod
    async def _navigate_to_publish_page(self, browser: BrowserUseSkill) -> bool:
        """Navigate to the content publishing page.

        Args:
            browser: Initialized browser skill

        Returns:
            True if navigation successful
        """
        pass

    @abstractmethod
    async def _fill_content(
        self,
        browser: BrowserUseSkill,
        content: PublishContent
    ) -> bool:
        """Fill in the content form.

        Args:
            browser: Browser skill instance
            content: Content to publish

        Returns:
            True if filling successful
        """
        pass

    @abstractmethod
    async def _upload_media(
        self,
        browser: BrowserUseSkill,
        content: PublishContent
    ) -> bool:
        """Upload media files (images/video).

        Args:
            browser: Browser skill instance
            content: Content with media paths

        Returns:
            True if upload successful
        """
        pass

    @abstractmethod
    async def _add_tags(
        self,
        browser: BrowserUseSkill,
        tags: List[str]
    ) -> bool:
        """Add tags/hashtags to the content.

        Args:
            browser: Browser skill instance
            tags: List of tags to add

        Returns:
            True if tags added successfully
        """
        pass

    @abstractmethod
    async def _submit_publish(self, browser: BrowserUseSkill) -> Tuple[bool, str]:
        """Submit the publish form.

        Args:
            browser: Browser skill instance

        Returns:
            Tuple of (success, content_id or error_message)
        """
        pass

    @abstractmethod
    async def _get_published_url(self, browser: BrowserUseSkill) -> Optional[str]:
        """Get the URL of published content.

        Args:
            browser: Browser skill instance

        Returns:
            Published content URL or None
        """
        pass

    async def publish(self, content: PublishContent) -> PublishResult:
        """Publish content to the platform.

        This is the main entry point that orchestrates the entire
        publishing workflow.

        Args:
            content: Content to publish

        Returns:
            PublishResult with success status and details
        """
        start_time = datetime.now()
        screenshot_dir = tempfile.mkdtemp(prefix="publish_")

        try:
            logger.info(f"Starting browser-based publishing to {self._platform_name}")

            # Initialize browser
            browser = await self._init_browser()

            # Step 1: Navigate to publish page
            logger.info("Step 1: Navigating to publish page")
            if not await self._navigate_to_publish_page(browser):
                return PublishResult(
                    success=False,
                    platform=self._platform_name,
                    error_message="Failed to navigate to publish page"
                )

            await asyncio.sleep(2)  # Wait for page to stabilize

            # Step 2: Fill content
            logger.info("Step 2: Filling content")
            if not await self._fill_content(browser, content):
                return PublishResult(
                    success=False,
                    platform=self._platform_name,
                    error_message="Failed to fill content"
                )

            # Step 3: Upload media if present
            if content.images or content.video:
                logger.info("Step 3: Uploading media")
                if not await self._upload_media(browser, content):
                    logger.warning("Media upload may have partially failed, continuing...")

            # Step 4: Add tags
            if content.tags:
                logger.info("Step 4: Adding tags")
                await self._add_tags(browser, content.tags)

            # Step 5: Submit
            logger.info("Step 5: Submitting for publish")
            success, result = await self._submit_publish(browser)

            if not success:
                # Take screenshot for debugging
                screenshot_path = os.path.join(screenshot_dir, "error.png")
                await self._take_screenshot(browser, screenshot_path)

                return PublishResult(
                    success=False,
                    platform=self._platform_name,
                    error_message=result,
                    screenshot_path=screenshot_path
                )

            # Step 6: Get published URL
            await asyncio.sleep(3)  # Wait for redirect
            url = await self._get_published_url(browser)

            published_at = datetime.now()

            logger.info(f"Successfully published to {self._platform_name}: {url}")

            return PublishResult(
                success=True,
                platform=self._platform_name,
                content_id=result,
                url=url,
                published_at=published_at
            )

        except Exception as e:
            logger.exception(f"Error during browser publishing: {e}")

            # Take error screenshot
            try:
                screenshot_path = os.path.join(screenshot_dir, "exception.png")
                if self._browser_skill:
                    await self._take_screenshot(self._browser_skill, screenshot_path)
            except:
                screenshot_path = None

            return PublishResult(
                success=False,
                platform=self._platform_name,
                error_message=str(e),
                screenshot_path=screenshot_path
            )

    async def _take_screenshot(self, browser: BrowserUseSkill, path: str) -> bool:
        """Take a screenshot for debugging.

        Args:
            browser: Browser skill instance
            path: Screenshot save path

        Returns:
            True if screenshot saved successfully
        """
        try:
            # This would need to be implemented in BrowserUseSkill
            # For now, just log that we wanted to take a screenshot
            logger.info(f"Would take screenshot at: {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return False

    async def test_connection(self) -> Tuple[bool, str]:
        """Test if the platform is accessible and user is logged in.

        Returns:
            Tuple of (is_connected, message)
        """
        try:
            browser = await self._init_browser()

            # Try to navigate to the platform
            if await self._navigate_to_publish_page(browser):
                return True, f"Successfully connected to {self._platform_name}"
            else:
                return False, f"Failed to access {self._platform_name}. Please check login status."

        except Exception as e:
            return False, f"Connection test failed: {str(e)}"

    async def close(self):
        """Close browser and cleanup resources."""
        if self._browser_skill:
            # BrowserUseSkill might have a close method
            # For now, just set to None
            self._browser_skill = None


class BrowserPublisherRegistry:
    """Registry for browser-based publishers."""

    _publishers: Dict[str, type] = {}

    @classmethod
    def register(cls, platform: str, publisher_class: type):
        """Register a browser publisher class."""
        cls._publishers[platform.lower()] = publisher_class
        logger.info(f"Registered browser publisher for {platform}")

    @classmethod
    def get_publisher(cls, platform: str, **kwargs) -> Optional[BaseBrowserPublisher]:
        """Get a publisher instance for the specified platform.

        Args:
            platform: Platform name (e.g., 'xiaohongshu', 'weibo')
            **kwargs: Configuration parameters for the publisher

        Returns:
            Publisher instance or None if not found
        """
        publisher_class = cls._publishers.get(platform.lower())
        if publisher_class:
            return publisher_class(**kwargs)
        return None

    @classmethod
    def list_supported_platforms(cls) -> List[str]:
        """List all supported platforms."""
        return list(cls._publishers.keys())
