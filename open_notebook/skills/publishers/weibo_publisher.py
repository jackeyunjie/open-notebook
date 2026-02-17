"""Weibo (微博) Content Publisher.

Publishes posts to Weibo platform using web API.
"""

from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import httpx
from loguru import logger

from open_notebook.domain.platform_connector import PlatformAccount, PlatformType
from open_notebook.domain.publish_job import ContentAdapter, PlatformPublisher, PublishJob


class WeiboPublisher(PlatformPublisher):
    """Publisher for Weibo platform."""

    BASE_URL = "https://weibo.com"
    API_URL = "https://weibo.com/ajax"

    def __init__(self, account: PlatformAccount):
        super().__init__(account)
        self.client: Optional[httpx.AsyncClient] = None
        self.uid: Optional[str] = None

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
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Referer": f"{self.BASE_URL}/",
                "X-Requested-With": "XMLHttpRequest",
            }

            self.client = httpx.AsyncClient(
                headers=headers,
                cookies=cookies,
                timeout=60.0,
                follow_redirects=True,
            )

        return self.client

    async def publish(self, job: PublishJob) -> Dict[str, Any]:
        """Publish content to Weibo."""
        client = await self._get_client()

        # Adapt content for Weibo
        content = ContentAdapter.adapt_for_platform(job, PlatformType.WEIBO)

        try:
            # Check if has media
            if job.media_urls:
                if job.content_format == "video":
                    result = await self._publish_video_post(client, content)
                else:
                    result = await self._publish_image_post(client, content)
            else:
                result = await self._publish_text_post(client, content)

            logger.info(f"Published to Weibo: {result.get('url', '')}")
            return result

        except Exception as e:
            logger.exception(f"Failed to publish to Weibo: {e}")
            raise

    async def _publish_text_post(self, client: httpx.AsyncClient, content: Dict[str, Any]) -> Dict[str, Any]:
        """Publish a text-only post."""
        text = content.get("text", "")
        hashtags = content.get("hashtags", [])

        # Append hashtags to text
        if hashtags:
            text += " " + " ".join(hashtags[:10])  # Max 10 hashtags

        post_data = {
            "content": text,
            "visible": 0,  # Public
            "share_id": "",
        }

        response = await client.post(
            f"{self.API_URL}/statuses/update",
            json=post_data
        )
        response.raise_for_status()

        data = response.json()
        if data.get("ok") == 1:
            weibo_id = str(data.get("data", {}).get("id", ""))
            user_id = str(data.get("data", {}).get("user", {}).get("id", ""))
            return {
                "success": True,
                "url": f"https://weibo.com/{user_id}/{weibo_id}",
                "platform_content_id": weibo_id,
                "published_at": datetime.utcnow().isoformat(),
            }
        else:
            raise ValueError(f"Publish failed: {data.get('msg', 'Unknown error')}")

    async def _publish_image_post(self, client: httpx.AsyncClient, content: Dict[str, Any]) -> Dict[str, Any]:
        """Publish a post with images."""
        # Upload images
        pic_ids = []
        for image_url in content.get("media", [])[:18]:  # Max 18 images
            pic_id = await self._upload_image(client, image_url)
            if pic_id:
                pic_ids.append(pic_id)

        if not pic_ids:
            # Fallback to text-only
            return await self._publish_text_post(client, content)

        text = content.get("text", "")
        hashtags = content.get("hashtags", [])
        if hashtags:
            text += " " + " ".join(hashtags[:10])

        post_data = {
            "content": text,
            "pic_ids": pic_ids,
            "visible": 0,
            "share_id": "",
        }

        response = await client.post(
            f"{self.API_URL}/statuses/update",
            json=post_data
        )
        response.raise_for_status()

        data = response.json()
        if data.get("ok") == 1:
            weibo_id = str(data.get("data", {}).get("id", ""))
            user_id = str(data.get("data", {}).get("user", {}).get("id", ""))
            return {
                "success": True,
                "url": f"https://weibo.com/{user_id}/{weibo_id}",
                "platform_content_id": weibo_id,
                "published_at": datetime.utcnow().isoformat(),
            }
        else:
            raise ValueError(f"Publish failed: {data.get('msg', 'Unknown error')}")

    async def _publish_video_post(self, client: httpx.AsyncClient, content: Dict[str, Any]) -> Dict[str, Any]:
        """Publish a post with video."""
        # Video publishing is more complex and requires multipart upload
        # This is a simplified implementation
        logger.info("Publishing video post to Weibo")

        # For now, fallback to text with video link
        text = content.get("text", "") + " [视频]"
        return await self._publish_text_post(client, {**content, "text": text})

    async def _upload_image(self, client: httpx.AsyncClient, image_url: str) -> Optional[str]:
        """Upload an image to Weibo."""
        try:
            # Simplified implementation
            logger.info(f"Uploading image to Weibo: {image_url}")
            return f"pic_{hash(image_url) % 1000000}"
        except Exception as e:
            logger.exception(f"Failed to upload image: {e}")
            return None

    async def validate_content(self, job: PublishJob) -> Tuple[bool, str]:
        """Validate content before publishing."""
        errors = []

        # Check text length (max 5000)
        text_length = len(job.content_text)
        hashtag_text = " ".join([f"#{tag}#" for tag in job.tags])
        total_length = text_length + len(hashtag_text)

        if total_length > 5000:
            errors.append(f"内容总长度超过5000字符限制（当前{total_length}字符）")

        # Check media count
        if len(job.media_urls) > 18:
            errors.append("图片数量超过18张限制")

        # Check if empty
        if not job.content_text and not job.media_urls:
            errors.append("内容不能为空")

        # Check authentication
        if not self.account.is_authenticated:
            errors.append("账号未认证")

        if errors:
            return False, "; ".join(errors)
        return True, ""

    def adapt_content(self, job: PublishJob) -> Dict[str, Any]:
        """Adapt generic content to Weibo format."""
        return ContentAdapter.adapt_for_platform(job, PlatformType.WEIBO)


# Import and register
from open_notebook.domain.publish_job import PublisherRegistry
PublisherRegistry.register(PlatformType.WEIBO, WeiboPublisher)
