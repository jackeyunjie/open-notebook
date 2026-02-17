"""Weibo (微博) Platform Connector.

Fetches posts and analytics from Weibo platform.
Uses web scraping approach with cookie authentication.
"""

import asyncio
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx
from loguru import logger

from open_notebook.domain.platform_connector import (
    BasePlatformConnector,
    PlatformAccount,
    PlatformAnalytics,
    PlatformContent,
    PlatformType,
)


class WeiboConnector(BasePlatformConnector):
    """Connector for Weibo platform."""

    BASE_URL = "https://weibo.com"
    API_URL = "https://weibo.com/ajax"

    def __init__(self, account: PlatformAccount):
        super().__init__(account)
        self.client: Optional[httpx.AsyncClient] = None
        self.uid: Optional[str] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with cookies."""
        if self.client is None:
            cookie_str = self.account.auth_data.get("cookie", "")
            cookies = {}

            if cookie_str:
                for cookie in cookie_str.split("; "):
                    if "=" in cookie:
                        key, value = cookie.split("=", 1)
                        cookies[key.strip()] = value.strip()

            # Extract UID from cookie
            if "SUBP" in cookies:
                # Parse SUBP to get UID
                subp = cookies.get("SUBP", "")
                # This is simplified - actual implementation would decode SUBP

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
                timeout=30.0,
                follow_redirects=True,
            )

        return self.client

    async def authenticate(self) -> bool:
        """Authenticate using stored cookies."""
        try:
            if not self.account.auth_data.get("cookie"):
                logger.warning("No cookie found for Weibo account")
                return False

            client = await self._get_client()

            # Fetch config to get uid
            response = await client.get(f"{self.API_URL}/config")
            response.raise_for_status()

            config = response.json()
            if config.get("data", {}).get("login"):
                self.uid = str(config["data"].get("uid", ""))
                self.account.is_authenticated = True

                # Get profile
                profile = await self.get_user_profile()
                if profile:
                    self.account.display_name = profile.get("screen_name", "")
                    self.account.avatar_url = profile.get("avatar_large", "")
                    await self.account.save()

                return True

            return False

        except Exception as e:
            logger.exception(f"Weibo authentication failed: {e}")
            return False

    async def get_user_profile(self) -> Dict[str, Any]:
        """Get user profile information."""
        try:
            if not self.uid:
                return {}

            client = await self._get_client()

            response = await client.get(
                f"{self.API_URL}/profile/info",
                params={"uid": self.uid}
            )
            response.raise_for_status()

            data = response.json()
            if data.get("ok") == 1:
                user = data.get("data", {}).get("user", {})
                return {
                    "screen_name": user.get("screen_name", ""),
                    "description": user.get("description", ""),
                    "avatar_large": user.get("avatar_large", ""),
                    "followers_count": user.get("followers_count", 0),
                    "friends_count": user.get("friends_count", 0),
                    "statuses_count": user.get("statuses_count", 0),
                }

            return {}

        except Exception as e:
            logger.exception(f"Failed to get Weibo profile: {e}")
            return {}

    async def fetch_content_list(
        self,
        since: Optional[datetime] = None,
        limit: int = 50
    ) -> List[PlatformContent]:
        """Fetch list of weibo posts."""
        contents = []

        try:
            if not self.uid:
                await self.authenticate()

            if not self.uid:
                return contents

            client = await self._get_client()

            page = 1
            fetched_count = 0

            while fetched_count < limit:
                response = await client.get(
                    f"{self.API_URL}/statuses/mymblog",
                    params={
                        "uid": self.uid,
                        "page": page,
                        "feature": 0,
                    }
                )
                response.raise_for_status()

                data = response.json()
                if data.get("ok") != 1:
                    break

                weibos = data.get("data", {}).get("list", [])
                if not weibos:
                    break

                for weibo in weibos:
                    content = self._parse_weibo(weibo)

                    # Filter by date
                    if since and content.created_at and content.created_at < since:
                        continue

                    contents.append(content)
                    fetched_count += 1

                    if fetched_count >= limit:
                        break

                page += 1
                await asyncio.sleep(1)

            logger.info(f"Fetched {len(contents)} posts from Weibo")
            return contents

        except Exception as e:
            logger.exception(f"Failed to fetch Weibo content: {e}")
            return contents

    async def fetch_content_detail(self, content_id: str) -> Optional[PlatformContent]:
        """Fetch detailed weibo information."""
        try:
            client = await self._get_client()

            response = await client.get(
                f"{self.API_URL}/statuses/show",
                params={"id": content_id}
            )
            response.raise_for_status()

            data = response.json()
            if data.get("ok") == 1:
                return self._parse_weibo(data.get("data", {}))

            return None

        except Exception as e:
            logger.exception(f"Failed to fetch weibo detail: {e}")
            return None

    async def fetch_analytics(self) -> Optional[PlatformAnalytics]:
        """Fetch account analytics."""
        try:
            profile = await self.get_user_profile()
            if not profile:
                return None

            recent_posts = await self.fetch_content_list(limit=20)

            total_likes = sum(p.likes for p in recent_posts)
            total_comments = sum(p.comments for p in recent_posts)
            total_shares = sum(p.shares for p in recent_posts)
            total_views = sum(p.views for p in recent_posts)

            avg_likes = total_likes / len(recent_posts) if recent_posts else 0
            avg_comments = total_comments / len(recent_posts) if recent_posts else 0

            engagement_rate = 0
            if total_views > 0:
                engagement_rate = (total_likes + total_comments + total_shares) / total_views

            sorted_posts = sorted(recent_posts, key=lambda x: x.likes + x.comments * 2, reverse=True)
            top_posts = [p.content_id for p in sorted_posts[:5]]

            return PlatformAnalytics(
                platform=PlatformType.WEIBO,
                username=self.account.username,
                followers_count=profile.get("followers_count", 0),
                total_posts=profile.get("statuses_count", 0),
                avg_likes=avg_likes,
                avg_comments=avg_comments,
                engagement_rate=engagement_rate,
                top_post_ids=top_posts,
            )

        except Exception as e:
            logger.exception(f"Failed to fetch Weibo analytics: {e}")
            return None

    async def test_connection(self) -> Tuple[bool, str]:
        """Test if connection is working."""
        try:
            is_authenticated = await self.authenticate()
            if is_authenticated:
                return True, "Connection successful"
            else:
                return False, "Authentication failed - cookie may be expired"
        except Exception as e:
            return False, str(e)

    def _parse_weibo(self, weibo_data: Dict[str, Any]) -> PlatformContent:
        """Parse Weibo data to normalized format."""
        # Handle retweeted content
        retweeted = weibo_data.get("retweeted_status")
        if retweeted:
            text = f"转发: {retweeted.get('text', '')}"
        else:
            text = weibo_data.get("text", "")

        # Clean HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Extract media
        media_urls = []
        pic_ids = weibo_data.get("pic_ids", [])
        for pic_id in pic_ids:
            media_urls.append(f"https://wx1.sinaimg.cn/large/{pic_id}.jpg")

        # Parse video
        page_info = weibo_data.get("page_info", {})
        if page_info.get("type") == "video":
            media_urls.append(page_info.get("media_info", {}).get("stream_url", ""))

        # Parse timestamp
        created_at_str = weibo_data.get("created_at", "")
        try:
            created_at = datetime.strptime(created_at_str, "%a %b %d %H:%M:%S %z %Y")
        except:
            created_at = None

        # Get engagement
        attitudes = weibo_data.get("attitudes_count", 0)  # likes
        comments = weibo_data.get("comments_count", 0)
        reposts = weibo_data.get("reposts_count", 0)  # shares
        reads = weibo_data.get("reads_count", 0)

        return PlatformContent(
            content_id=str(weibo_data.get("id", "")),
            platform=PlatformType.WEIBO,
            platform_username=self.account.username,
            title=text[:50] if len(text) > 50 else text,
            content_text=text,
            content_type="video" if pic_ids else "post",
            media_urls=media_urls,
            created_at=created_at,
            updated_at=created_at,
            likes=attitudes,
            comments=comments,
            shares=reposts,
            views=reads,
            platform_url=f"https://weibo.com/{weibo_data.get('user', {}).get('id', '')}/{weibo_data.get('bid', '')}",
            raw_data=weibo_data,
        )

    def normalize_content(self, raw_data: Dict[str, Any]) -> PlatformContent:
        """Normalize raw Weibo data."""
        return self._parse_weibo(raw_data)


# Register connector
from open_notebook.domain.platform_connector import ConnectorRegistry

ConnectorRegistry.register(PlatformType.WEIBO, WeiboConnector)
