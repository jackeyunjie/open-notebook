"""Xiaohongshu (小红书) Platform Connector.

Fetches notes and analytics from Xiaohongshu platform.
Uses web scraping approach with cookie authentication.

Note: This is a reference implementation. In production, you should:
1. Use official APIs when available
2. Implement proper rate limiting
3. Handle anti-bot measures
4. Store credentials securely
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import httpx
from loguru import logger

from open_notebook.domain.platform_connector import (
    BasePlatformConnector,
    PlatformAccount,
    PlatformAnalytics,
    PlatformContent,
    PlatformType,
)


class XiaohongshuConnector(BasePlatformConnector):
    """Connector for Xiaohongshu platform."""

    BASE_URL = "https://www.xiaohongshu.com"
    API_URL = "https://edith.xiaohongshu.com"

    def __init__(self, account: PlatformAccount):
        super().__init__(account)
        self.client: Optional[httpx.AsyncClient] = None
        self.cookies: Dict[str, str] = {}

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with cookies."""
        if self.client is None:
            # Parse cookies from auth_data
            cookie_str = self.account.auth_data.get("cookie", "")
            if cookie_str:
                for cookie in cookie_str.split("; "):
                    if "=" in cookie:
                        key, value = cookie.split("=", 1)
                        self.cookies[key.strip()] = value.strip()

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Origin": self.BASE_URL,
                "Referer": f"{self.BASE_URL}/",
                "X-Sign": "",
            }

            self.client = httpx.AsyncClient(
                headers=headers,
                cookies=self.cookies,
                timeout=30.0,
                follow_redirects=True,
            )

        return self.client

    async def authenticate(self) -> bool:
        """Authenticate using stored cookies."""
        try:
            if not self.account.auth_data.get("cookie"):
                logger.warning("No cookie found for Xiaohongshu account")
                return False

            client = await self._get_client()

            # Test authentication by fetching user profile
            profile = await self.get_user_profile()
            is_valid = bool(profile and profile.get("nickname"))

            self.account.is_authenticated = is_valid
            if is_valid:
                self.account.display_name = profile.get("nickname", "")
                self.account.avatar_url = profile.get("image", "")
                await self.account.save()

            return is_valid

        except Exception as e:
            logger.exception(f"Xiaohongshu authentication failed: {e}")
            return False

    async def get_user_profile(self) -> Dict[str, Any]:
        """Get user profile information."""
        try:
            client = await self._get_client()

            # Fetch user profile
            response = await client.get(
                f"{self.API_URL}/api/sns/web/v1/user/selfinfo"
            )
            response.raise_for_status()

            data = response.json()
            if data.get("success"):
                user_data = data.get("data", {})
                return {
                    "nickname": user_data.get("nickname", ""),
                    "username": user_data.get("red_id", ""),
                    "image": user_data.get("images", ""),
                    "followers": user_data.get("followers", 0),
                    "following": user_data.get("followings", 0),
                    "notes_count": user_data.get("notes", 0),
                }

            return {}

        except Exception as e:
            logger.exception(f"Failed to get Xiaohongshu profile: {e}")
            return {}

    async def fetch_content_list(
        self,
        since: Optional[datetime] = None,
        limit: int = 50
    ) -> List[PlatformContent]:
        """Fetch list of notes."""
        contents = []

        try:
            client = await self._get_client()

            # Fetch user's notes
            cursor = ""
            fetched_count = 0

            while fetched_count < limit:
                params = {
                    "num": min(20, limit - fetched_count),
                    "cursor": cursor,
                }

                response = await client.get(
                    f"{self.API_URL}/api/sns/web/v1/user/selfnotes",
                    params=params
                )
                response.raise_for_status()

                data = response.json()
                if not data.get("success"):
                    break

                notes_data = data.get("data", {}).get("notes", [])
                if not notes_data:
                    break

                for note in notes_data:
                    content = self._parse_note(note)

                    # Filter by date if specified
                    if since and content.created_at and content.created_at < since:
                        continue

                    contents.append(content)
                    fetched_count += 1

                    if fetched_count >= limit:
                        break

                # Get next cursor
                cursor = data.get("data", {}).get("cursor", "")
                if not cursor:
                    break

                # Rate limiting
                await asyncio.sleep(1)

            logger.info(f"Fetched {len(contents)} notes from Xiaohongshu")
            return contents

        except Exception as e:
            logger.exception(f"Failed to fetch Xiaohongshu content: {e}")
            return contents

    async def fetch_content_detail(self, content_id: str) -> Optional[PlatformContent]:
        """Fetch detailed note information."""
        try:
            client = await self._get_client()

            response = await client.get(
                f"{self.API_URL}/api/sns/web/v1/feed",
                params={"note_id": content_id}
            )
            response.raise_for_status()

            data = response.json()
            if data.get("success"):
                note = data.get("data", {}).get("items", [{}])[0]
                return self._parse_note(note)

            return None

        except Exception as e:
            logger.exception(f"Failed to fetch note detail: {e}")
            return None

    async def fetch_analytics(self) -> Optional[PlatformAnalytics]:
        """Fetch account analytics."""
        try:
            profile = await self.get_user_profile()
            if not profile:
                return None

            # Calculate engagement from recent notes
            recent_notes = await self.fetch_content_list(limit=20)

            total_likes = sum(n.likes for n in recent_notes)
            total_comments = sum(n.comments for n in recent_notes)
            total_shares = sum(n.shares for n in recent_notes)
            total_views = sum(n.views for n in recent_notes)

            avg_likes = total_likes / len(recent_notes) if recent_notes else 0
            avg_comments = total_comments / len(recent_notes) if recent_notes else 0
            avg_shares = total_shares / len(recent_notes) if recent_notes else 0

            engagement_rate = 0
            if total_views > 0:
                engagement_rate = (total_likes + total_comments + total_shares) / total_views

            # Top performing notes
            sorted_notes = sorted(recent_notes, key=lambda x: x.likes + x.comments * 2, reverse=True)
            top_notes = [n.content_id for n in sorted_notes[:5]]

            return PlatformAnalytics(
                platform=PlatformType.XIAOHONGSHU,
                username=self.account.username,
                followers_count=profile.get("followers", 0),
                total_posts=profile.get("notes_count", 0),
                avg_likes=avg_likes,
                avg_comments=avg_comments,
                avg_shares=avg_shares,
                engagement_rate=engagement_rate,
                top_post_ids=top_notes,
            )

        except Exception as e:
            logger.exception(f"Failed to fetch Xiaohongshu analytics: {e}")
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

    def _parse_note(self, note_data: Dict[str, Any]) -> PlatformContent:
        """Parse Xiaohongshu note data to normalized format."""
        note = note_data.get("note_card", note_data)

        # Extract media URLs
        media_urls = []
        if "image_list" in note:
            media_urls = [img.get("url_default", "") for img in note["image_list"]]
        elif "video" in note:
            media_urls = [note["video"].get("url", "")]

        # Parse timestamps
        create_time = note.get("time", 0)
        created_at = datetime.fromtimestamp(create_time) if create_time else None

        # Extract engagement metrics
        interact_info = note.get("interact_info", {})

        return PlatformContent(
            content_id=note.get("note_id", ""),
            platform=PlatformType.XIAOHONGSHU,
            platform_username=self.account.username,
            title=note.get("title", ""),
            content_text=note.get("desc", ""),
            content_type="video" if note.get("type") == "video" else "note",
            media_urls=media_urls,
            created_at=created_at,
            updated_at=created_at,
            likes=int(interact_info.get("liked_count", 0) or 0),
            comments=int(interact_info.get("comment_count", 0) or 0),
            shares=int(interact_info.get("share_count", 0) or 0),
            saves=int(interact_info.get("collected_count", 0) or 0),
            views=int(interact_info.get("view_count", 0) or 0),
            platform_url=f"https://www.xiaohongshu.com/explore/{note.get('note_id', '')}",
            raw_data=note_data,
        )

    def normalize_content(self, raw_data: Dict[str, Any]) -> PlatformContent:
        """Normalize raw Xiaohongshu data."""
        return self._parse_note(raw_data)


# Register connector
from open_notebook.domain.platform_connector import ConnectorRegistry

ConnectorRegistry.register(PlatformType.XIAOHONGSHU, XiaohongshuConnector)
