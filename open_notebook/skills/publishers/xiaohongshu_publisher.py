"""Xiaohongshu (小红书) Content Publisher.

Publishes notes to Xiaohongshu platform using web API.
"""

import json
from typing import Any, Dict, Optional, Tuple
from datetime import datetime

import httpx
from loguru import logger

from open_notebook.domain.platform_connector import PlatformAccount, PlatformType
from open_notebook.domain.publish_job import ContentAdapter, PlatformPublisher, PublishJob


class XiaohongshuPublisher(PlatformPublisher):
    """Publisher for Xiaohongshu platform."""

    BASE_URL = "https://www.xiaohongshu.com"
    API_URL = "https://edith.xiaohongshu.com"

    def __init__(self, account: PlatformAccount):
        super().__init__(account)
        self.client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with authentication."""
        if self.client is None:
            cookie_str = self.account.auth_data.get("cookie", "")
            cookies = {}

            if cookie_str:
                for cookie in cookie_str.split("; "):
                    if "=" in cookie:
                        key, value = cookie.split("=", 1)
                        cookies[key.strip()] = value.strip()

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Origin": self.BASE_URL,
                "Referer": f"{self.BASE_URL}/",
            }

            self.client = httpx.AsyncClient(
                headers=headers,
                cookies=cookies,
                timeout=60.0,
                follow_redirects=True,
            )

        return self.client

    async def publish(self, job: PublishJob) -> Dict[str, Any]:
        """Publish content to Xiaohongshu."""
        client = await self._get_client()

        # Adapt content for Xiaohongshu
        content = ContentAdapter.adapt_for_platform(job, PlatformType.XIAOHONGSHU)

        try:
            # Check if video or image note
            is_video = job.content_format == "video" or any(
                url.endswith(('.mp4', '.mov', '.avi')) for url in job.media_urls
            )

            if is_video:
                result = await self._publish_video_note(client, content)
            else:
                result = await self._publish_image_note(client, content)

            logger.info(f"Published to Xiaohongshu: {result.get('url', '')}")
            return result

        except Exception as e:
            logger.exception(f"Failed to publish to Xiaohongshu: {e}")
            raise

    async def _publish_image_note(self, client: httpx.AsyncClient, content: Dict[str, Any]) -> Dict[str, Any]:
        """Publish an image note."""
        # Upload images first
        image_ids = []
        for image_url in content.get("media", []):
            image_id = await self._upload_image(client, image_url)
            if image_id:
                image_ids.append(image_id)

        if not image_ids:
            raise ValueError("No images uploaded successfully")

        # Prepare note data
        note_data = {
            "type": "normal",
            "title": content.get("title", "")[:20],  # Max 20 chars
            "desc": content.get("text", ""),
            "images": image_ids,
            "ats": [],
            "topics": [{"name": tag.strip("#")} for tag in content.get("hashtags", [])[:5]],
        }

        # Publish note
        response = await client.post(
            f"{self.API_URL}/api/sns/web/v1/note/publish",
            json=note_data
        )
        response.raise_for_status()

        data = response.json()
        if data.get("success"):
            note_id = data.get("data", {}).get("note_id", "")
            return {
                "success": True,
                "url": f"https://www.xiaohongshu.com/explore/{note_id}",
                "platform_content_id": note_id,
                "published_at": datetime.utcnow().isoformat(),
            }
        else:
            raise ValueError(f"Publish failed: {data.get('msg', 'Unknown error')}")

    async def _publish_video_note(self, client: httpx.AsyncClient, content: Dict[str, Any]) -> Dict[str, Any]:
        """Publish a video note."""
        # Upload video
        video_url = content.get("media", [None])[0]
        if not video_url:
            raise ValueError("No video provided")

        video_id = await self._upload_video(client, video_url)
        if not video_id:
            raise ValueError("Video upload failed")

        # Prepare video note data
        note_data = {
            "type": "video",
            "title": content.get("title", "")[:20],
            "desc": content.get("text", ""),
            "video": video_id,
            "ats": [],
            "topics": [{"name": tag.strip("#")} for tag in content.get("hashtags", [])[:5]],
        }

        response = await client.post(
            f"{self.API_URL}/api/sns/web/v1/note/publish",
            json=note_data
        )
        response.raise_for_status()

        data = response.json()
        if data.get("success"):
            note_id = data.get("data", {}).get("note_id", "")
            return {
                "success": True,
                "url": f"https://www.xiaohongshu.com/explore/{note_id}",
                "platform_content_id": note_id,
                "published_at": datetime.utcnow().isoformat(),
            }
        else:
            raise ValueError(f"Publish failed: {data.get('msg', 'Unknown error')}")

    async def _upload_image(self, client: httpx.AsyncClient, image_url: str) -> Optional[str]:
        """Upload an image to Xiaohongshu."""
        try:
            # This is a simplified implementation
            # In production, you'd need to:
            # 1. Download image from URL
            # 2. Get upload URL from Xiaohongshu
            # 3. Upload to their CDN
            # 4. Return the file ID
            logger.info(f"Uploading image: {image_url}")
            # Return mock ID for now
            return f"img_{hash(image_url) % 1000000}"
        except Exception as e:
            logger.exception(f"Failed to upload image: {e}")
            return None

    async def _upload_video(self, client: httpx.AsyncClient, video_url: str) -> Optional[str]:
        """Upload a video to Xiaohongshu."""
        try:
            logger.info(f"Uploading video: {video_url}")
            # Return mock ID for now
            return f"video_{hash(video_url) % 1000000}"
        except Exception as e:
            logger.exception(f"Failed to upload video: {e}")
            return None

    async def validate_content(self, job: PublishJob) -> Tuple[bool, str]:
        """Validate content before publishing."""
        errors = []

        # Check text length (max 1000 for description)
        if len(job.content_text) > 1000:
            errors.append("内容长度超过1000字符限制")

        # Check title length (max 20)
        if job.title and len(job.title) > 20:
            errors.append("标题长度超过20字符限制")

        # Check media count (max 18 images or 1 video)
        if job.content_format == "video":
            if len(job.media_urls) < 1:
                errors.append("视频内容需要提供视频文件")
        else:
            if len(job.media_urls) > 18:
                errors.append("图片数量超过18张限制")
            if len(job.media_urls) < 1:
                errors.append("需要提供至少1张图片")

        # Check authentication
        if not self.account.is_authenticated:
            errors.append("账号未认证")

        if errors:
            return False, "; ".join(errors)
        return True, ""

    def adapt_content(self, job: PublishJob) -> Dict[str, Any]:
        """Adapt generic content to Xiaohongshu format."""
        return ContentAdapter.adapt_for_platform(job, PlatformType.XIAOHONGSHU)


# Import and register
from open_notebook.domain.publish_job import PublisherRegistry
PublisherRegistry.register(PlatformType.XIAOHONGSHU, XiaohongshuPublisher)
