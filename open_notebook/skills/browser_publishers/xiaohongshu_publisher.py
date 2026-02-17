"""Xiaohongshu (小红书) Browser-based Publisher.

Automates content publishing to Xiaohongshu using browser automation.
Reuses user's existing login session from system browser.
"""

import asyncio
from typing import List, Optional, Tuple

from loguru import logger

from open_notebook.skills.browser_base import BrowserUseSkill
from open_notebook.skills.browser_publisher import (
    BaseBrowserPublisher,
    BrowserPublisherRegistry,
    PublishContent,
    PublishResult,
)


class XiaohongshuBrowserPublisher(BaseBrowserPublisher):
    """Browser-based publisher for Xiaohongshu platform.

    Uses browser-use to automate the publishing workflow:
    1. Navigate to creator center
    2. Click "Publish Note" button
    3. Upload images/video
    4. Fill title and content
    5. Add hashtags
    6. Submit for publishing
    """

    def __init__(
        self,
        headless: bool = False,  # Use headed mode for better reliability
        use_system_browser: bool = True,
        user_data_dir: Optional[str] = None,
        timeout: int = 120
    ):
        super().__init__(
            headless=headless,
            use_system_browser=use_system_browser,
            user_data_dir=user_data_dir,
            timeout=timeout
        )
        self._platform_name = "xiaohongshu"
        self.base_url = "https://creator.xiaohongshu.com"
        self.publish_url = "https://creator.xiaohongshu.com/publish/publish"

    async def _navigate_to_publish_page(self, browser: BrowserUseSkill) -> bool:
        """Navigate to Xiaohongshu creator center publish page."""
        try:
            logger.info("Navigating to Xiaohongshu creator center...")

            # Navigate to publish page
            result = await browser.execute({
                "action": "navigate",
                "url": self.publish_url,
                "wait_for": "div.publish-container, div.creator-container, #note-container"
            })

            if not result.get("success"):
                logger.error(f"Failed to navigate: {result.get('error')}")
                return False

            # Wait for page to fully load
            await asyncio.sleep(3)

            # Check if we're on the right page
            page_check = await browser.execute({
                "action": "evaluate",
                "script": """
                    () => {
                        const title = document.title;
                        const url = window.location.href;
                        const hasPublishBtn = document.querySelector('[class*="publish"], [class*="发布"], button:contains("发布")') !== null;
                        return { title, url, hasPublishBtn };
                    }
                """
            })

            logger.info(f"Page check result: {page_check}")

            # If not logged in, we might be redirected to login page
            if "login" in str(page_check.get("url", "")).lower():
                logger.error("Not logged in to Xiaohongshu")
                return False

            return True

        except Exception as e:
            logger.exception(f"Error navigating to publish page: {e}")
            return False

    async def _fill_content(
        self,
        browser: BrowserUseSkill,
        content: PublishContent
    ) -> bool:
        """Fill in title and content."""
        try:
            logger.info("Filling title and content...")

            # Fill title (max 20 characters for Xiaohongshu)
            title = content.title[:20] if content.title else ""

            # Try different selectors for title input
            title_result = await browser.execute({
                "action": "fill",
                "selector": "input[placeholder*=\"标题\"], input[placeholder*=\"title\"], textarea[placeholder*=\"标题\"], #title-input, .title-input",
                "value": title,
                "clear_first": True
            })

            if not title_result.get("success"):
                # Try AI-based interaction
                title_result = await browser.execute({
                    "action": "natural_language",
                    "instruction": f"Find the title input field and enter: {title}"
                })

            # Fill main content
            content_text = content.content[:1000] if content.content else ""  # Max 1000 chars

            content_result = await browser.execute({
                "action": "fill",
                "selector": "textarea[placeholder*=\"正文\"], textarea[placeholder*=\"content\"], .content-editor, #content-editor, div[contenteditable=\"true\"]",
                "value": content_text,
                "clear_first": True
            })

            if not content_result.get("success"):
                # Try AI-based interaction
                content_result = await browser.execute({
                    "action": "natural_language",
                    "instruction": f"Find the main content editor and enter: {content_text}"
                })

            await asyncio.sleep(1)
            return True

        except Exception as e:
            logger.exception(f"Error filling content: {e}")
            return False

    async def _upload_media(
        self,
        browser: BrowserUseSkill,
        content: PublishContent
    ) -> bool:
        """Upload images or video."""
        try:
            if content.video:
                logger.info(f"Uploading video: {content.video}")
                return await self._upload_video(browser, content.video)
            elif content.images:
                logger.info(f"Uploading {len(content.images)} images")
                return await self._upload_images(browser, content.images)
            else:
                logger.info("No media to upload")
                return True

        except Exception as e:
            logger.exception(f"Error uploading media: {e}")
            return False

    async def _upload_images(
        self,
        browser: BrowserUseSkill,
        image_paths: List[str]
    ) -> bool:
        """Upload multiple images."""
        try:
            # Click on upload area or drag and drop
            for i, image_path in enumerate(image_paths[:18]):  # Max 18 images
                logger.info(f"Uploading image {i+1}/{len(image_paths)}: {image_path}")

                # Try file input
                upload_result = await browser.execute({
                    "action": "upload_file",
                    "selector": "input[type=\"file\"], .upload-input, [class*=\"upload\"] input",
                    "file_path": image_path
                })

                if not upload_result.get("success"):
                    # Try using natural language
                    upload_result = await browser.execute({
                        "action": "natural_language",
                        "instruction": f"Click on the upload area and select the file: {image_path}"
                    })

                # Wait for upload to complete
                await asyncio.sleep(2)

            return True

        except Exception as e:
            logger.exception(f"Error uploading images: {e}")
            return False

    async def _upload_video(
        self,
        browser: BrowserUseSkill,
        video_path: str
    ) -> bool:
        """Upload a video."""
        try:
            logger.info(f"Uploading video: {video_path}")

            # Switch to video tab if needed
            video_tab = await browser.execute({
                "action": "click",
                "selector": "[class*=\"video\"], button:contains(\"视频\"), .tab:contains(\"视频\")"
            })

            # Upload video file
            upload_result = await browser.execute({
                "action": "upload_file",
                "selector": "input[type=\"file\"][accept*=\"video\"], .video-upload input",
                "file_path": video_path
            })

            if not upload_result.get("success"):
                upload_result = await browser.execute({
                    "action": "natural_language",
                    "instruction": f"Click the video upload button and select: {video_path}"
                })

            # Wait for video processing
            logger.info("Waiting for video upload and processing...")
            await asyncio.sleep(10)

            return True

        except Exception as e:
            logger.exception(f"Error uploading video: {e}")
            return False

    async def _add_tags(
        self,
        browser: BrowserUseSkill,
        tags: List[str]
    ) -> bool:
        """Add hashtags to the note."""
        try:
            logger.info(f"Adding {len(tags)} tags...")

            for tag in tags[:5]:  # Max 5 tags recommended
                tag_text = f"#{tag}#"

                # Try to find and click on topic/tag input
                tag_result = await browser.execute({
                    "action": "natural_language",
                    "instruction": f"Click on the topic/tag input area and type: {tag_text}"
                })

                await asyncio.sleep(0.5)

            return True

        except Exception as e:
            logger.exception(f"Error adding tags: {e}")
            return False

    async def _submit_publish(self, browser: BrowserUseSkill) -> Tuple[bool, str]:
        """Submit the note for publishing."""
        try:
            logger.info("Submitting for publish...")

            # Click publish button
            publish_result = await browser.execute({
                "action": "click",
                "selector": "button:contains(\"发布\"), button:contains(\"Publish\"), [class*=\"publish\"] button, .publish-btn"
            })

            if not publish_result.get("success"):
                # Try natural language
                publish_result = await browser.execute({
                    "action": "natural_language",
                    "instruction": "Click the '发布' (Publish) button to publish the note"
                })

            # Wait for publishing to complete
            logger.info("Waiting for publish to complete...")
            await asyncio.sleep(5)

            # Check for success indicators
            success_check = await browser.execute({
                "action": "evaluate",
                "script": """
                    () => {
                        // Look for success messages
                        const successIndicators = [
                            document.querySelector('[class*="success"]'),
                            document.querySelector('[class*="成功"]'),
                            document.querySelector('.publish-success'),
                            document.body.innerText.includes('发布成功'),
                            document.body.innerText.includes('已发布')
                        ];

                        // Look for error messages
                        const errorIndicators = [
                            document.querySelector('[class*="error"]'),
                            document.querySelector('[class*="失败"]'),
                            document.body.innerText.includes('发布失败'),
                            document.body.innerText.includes('错误')
                        ];

                        return {
                            hasSuccess: successIndicators.some(el => el !== null && el !== false),
                            hasError: errorIndicators.some(el => el !== null && el !== false),
                            currentUrl: window.location.href
                        };
                    }
                """
            })

            logger.info(f"Success check: {success_check}")

            if success_check.get("hasError"):
                return False, "Publishing failed - error message detected"

            # Extract content ID from URL if available
            current_url = success_check.get("currentUrl", "")
            content_id = self._extract_content_id(current_url)

            return True, content_id or "published"

        except Exception as e:
            logger.exception(f"Error submitting publish: {e}")
            return False, str(e)

    async def _get_published_url(self, browser: BrowserUseSkill) -> Optional[str]:
        """Get the URL of the published note."""
        try:
            result = await browser.execute({
                "action": "evaluate",
                "script": """
                    () => {
                        // Try to find link to published note
                        const links = Array.from(document.querySelectorAll('a[href*="/explore/"]'));
                        const noteLink = links.find(a => a.href.includes('/explore/'));
                        return noteLink ? noteLink.href : window.location.href;
                    }
                """
            })

            url = result.get("result", "")
            if "/explore/" in url:
                return url

            return None

        except Exception as e:
            logger.error(f"Error getting published URL: {e}")
            return None

    def _extract_content_id(self, url: str) -> Optional[str]:
        """Extract content ID from URL."""
        import re
        match = re.search(r'/explore/([a-zA-Z0-9]+)', url)
        return match.group(1) if match else None


# Register the publisher
BrowserPublisherRegistry.register("xiaohongshu", XiaohongshuBrowserPublisher)
