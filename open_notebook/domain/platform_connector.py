"""Platform Connector System - Data synchronization from social media platforms.

This module provides connectors to fetch content and analytics from various
social media platforms (Xiaohongshu, Weibo, WeChat, etc.) for the IP Command Center.

Architecture:
    BaseConnector (abstract)
    ├── XiaohongshuConnector
    ├── WeiboConnector
    ├── WechatOfficialConnector
    ├── ZhihuConnector
    └── ...

Data Flow:
    Platform API → Connector → Normalized Data → Database → P0/P3 System
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import hashlib
import json

from pydantic import BaseModel, Field
from surrealdb import RecordID

from open_notebook.domain.base import ObjectModel


class PlatformType(Enum):
    """Supported social media platforms."""
    XIAOHONGSHU = "xiaohongshu"
    WEIBO = "weibo"
    WECHAT_OFFICIAL = "wechat_official"
    WECHAT_CHANNELS = "wechat_channels"
    ZHIHU = "zhihu"
    JIKE = "jike"
    BILIBILI = "bilibili"
    DOUYIN = "douyin"
    KUAISHOU = "kuaishou"
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    LINKEDIN = "linkedin"


class AuthType(Enum):
    """Authentication methods."""
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    COOKIE = "cookie"
    QRCODE = "qrcode"
    USERNAME_PASSWORD = "password"


class SyncStatus(Enum):
    """Synchronization status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class PlatformContent:
    """Normalized content data from any platform."""
    content_id: str
    platform: PlatformType
    platform_username: str

    # Content
    title: Optional[str] = None
    content_text: str = ""
    content_type: str = "post"  # post, article, video, thread
    media_urls: List[str] = field(default_factory=list)

    # Metadata
    created_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    topic: Optional[str] = None

    # Engagement (normalized)
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    followers_gained: int = 0

    # URLs
    platform_url: str = ""
    original_url: str = ""

    # Quadrant classification (if determined)
    quadrant: Optional[str] = None

    # Raw data (platform-specific)
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content_id": self.content_id,
            "platform": self.platform.value,
            "platform_username": self.platform_username,
            "title": self.title,
            "content_text": self.content_text[:500] if self.content_text else "",  # Truncate
            "content_type": self.content_type,
            "media_count": len(self.media_urls),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "engagement": {
                "views": self.views,
                "likes": self.likes,
                "comments": self.comments,
                "shares": self.shares,
                "saves": self.saves,
            },
            "platform_url": self.platform_url,
            "quadrant": self.quadrant,
        }


@dataclass
class PlatformAnalytics:
    """Analytics data for a platform account."""
    platform: PlatformType
    username: str

    # Followers
    followers_count: int = 0
    followers_change_24h: int = 0
    followers_change_7d: int = 0

    # Content
    total_posts: int = 0
    posts_change_7d: int = 0

    # Engagement rates
    avg_likes: float = 0.0
    avg_comments: float = 0.0
    avg_shares: float = 0.0
    engagement_rate: float = 0.0  # (likes + comments + shares) / views

    # Top content
    top_post_ids: List[str] = field(default_factory=list)

    # Timestamp
    collected_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform.value,
            "username": self.username,
            "followers": {
                "total": self.followers_count,
                "change_24h": self.followers_change_24h,
                "change_7d": self.followers_change_7d,
            },
            "content": {
                "total_posts": self.total_posts,
                "posts_change_7d": self.posts_change_7d,
            },
            "engagement": {
                "avg_likes": self.avg_likes,
                "avg_comments": self.avg_comments,
                "avg_shares": self.avg_shares,
                "engagement_rate": self.engagement_rate,
            },
            "collected_at": self.collected_at.isoformat(),
        }


class PlatformAccount(ObjectModel):
    """Connected platform account."""

    table_name: str = "platform_account"

    # Basic info
    platform: str = ""  # PlatformType value
    username: str = ""
    display_name: str = ""
    profile_url: str = ""
    avatar_url: str = ""

    # Authentication
    auth_type: str = ""  # AuthType value
    auth_data: Dict[str, Any] = Field(default_factory=dict)  # Encrypted credentials
    is_authenticated: bool = False
    auth_expires_at: Optional[datetime] = None

    # Profile ID link
    personal_ip_profile_id: Optional[str] = None

    # Sync settings
    auto_sync: bool = True
    sync_frequency_hours: int = 24
    last_sync_at: Optional[datetime] = None
    last_sync_status: str = "pending"
    last_sync_error: Optional[str] = None

    # Stats
    total_content_fetched: int = 0
    last_content_at: Optional[datetime] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    async def mark_sync_attempt(self):
        """Mark that a sync was attempted."""
        self.last_sync_at = datetime.utcnow()
        self.last_sync_status = "running"
        await self.save()

    async def mark_sync_success(self, content_count: int):
        """Mark sync as successful."""
        self.last_sync_status = "success"
        self.total_content_fetched += content_count
        self.last_content_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        await self.save()

    async def mark_sync_failed(self, error: str):
        """Mark sync as failed."""
        self.last_sync_status = "failed"
        self.last_sync_error = error
        self.updated_at = datetime.utcnow()
        await self.save()

    def needs_sync(self) -> bool:
        """Check if account needs synchronization."""
        if not self.auto_sync:
            return False

        if not self.last_sync_at:
            return True

        next_sync = self.last_sync_at + timedelta(hours=self.sync_frequency_hours)
        return datetime.utcnow() >= next_sync


class PlatformContentData(ObjectModel):
    """Synchronized content from platforms."""

    table_name: str = "platform_content"

    # Link to account
    account_id: str = ""
    platform: str = ""

    # Content
    platform_content_id: str = ""
    title: Optional[str] = None
    content_text: str = ""
    content_type: str = "post"
    media_urls: List[str] = Field(default_factory=list)

    # Timestamps
    platform_created_at: Optional[datetime] = None
    platform_updated_at: Optional[datetime] = None
    synced_at: datetime = Field(default_factory=datetime.utcnow)

    # Engagement
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0

    # URLs
    platform_url: str = ""

    # Classification
    quadrant: Optional[str] = None
    topics: List[str] = Field(default_factory=list)

    # Raw data
    raw_data: Dict[str, Any] = Field(default_factory=dict)

    # P0-P3 integration
    p0_signal_id: Optional[str] = None
    processed_by_p1: bool = False
    processed_by_p2: bool = False

    @classmethod
    def from_platform_content(cls, content: PlatformContent, account_id: str) -> "PlatformContentData":
        """Create from normalized PlatformContent."""
        return cls(
            account_id=account_id,
            platform=content.platform.value,
            platform_content_id=content.content_id,
            title=content.title,
            content_text=content.content_text,
            content_type=content.content_type,
            media_urls=content.media_urls,
            platform_created_at=content.created_at,
            platform_updated_at=content.updated_at,
            views=content.views,
            likes=content.likes,
            comments=content.comments,
            shares=content.shares,
            saves=content.saves,
            platform_url=content.platform_url,
            quadrant=content.quadrant,
            raw_data=content.raw_data,
        )


class BasePlatformConnector(ABC):
    """Abstract base class for platform connectors."""

    def __init__(self, account: PlatformAccount):
        self.account = account
        self.platform = PlatformType(account.platform)

    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the platform."""
        pass

    @abstractmethod
    async def get_user_profile(self) -> Dict[str, Any]:
        """Get user profile information."""
        pass

    @abstractmethod
    async def fetch_content_list(
        self,
        since: Optional[datetime] = None,
        limit: int = 50
    ) -> List[PlatformContent]:
        """Fetch list of content items."""
        pass

    @abstractmethod
    async def fetch_content_detail(self, content_id: str) -> Optional[PlatformContent]:
        """Fetch detailed content information."""
        pass

    @abstractmethod
    async def fetch_analytics(self) -> Optional[PlatformAnalytics]:
        """Fetch account analytics."""
        pass

    @abstractmethod
    async def test_connection(self) -> Tuple[bool, str]:
        """Test if connection is working."""
        pass

    def normalize_content(self, raw_data: Dict[str, Any]) -> PlatformContent:
        """Normalize raw platform data to standard format."""
        # Default implementation - subclasses should override
        return PlatformContent(
            content_id=str(raw_data.get("id", "")),
            platform=self.platform,
            platform_username=self.account.username,
            content_text=raw_data.get("text", ""),
            created_at=datetime.utcnow(),
            raw_data=raw_data,
        )

    async def sync_content(self, since: Optional[datetime] = None) -> Tuple[int, Optional[str]]:
        """Synchronize content to database."""
        try:
            await self.account.mark_sync_attempt()

            # Fetch content
            contents = await self.fetch_content_list(since=since)

            # Save to database
            saved_count = 0
            for content in contents:
                content_data = PlatformContentData.from_platform_content(
                    content,
                    str(self.account.id)
                )
                await content_data.save()
                saved_count += 1

            await self.account.mark_sync_success(saved_count)
            return saved_count, None

        except Exception as e:
            error_msg = str(e)
            await self.account.mark_sync_failed(error_msg)
            return 0, error_msg


class ConnectorRegistry:
    """Registry for platform connectors."""

    _connectors: Dict[PlatformType, type] = {}

    @classmethod
    def register(cls, platform: PlatformType, connector_class: type):
        """Register a connector class."""
        cls._connectors[platform] = connector_class

    @classmethod
    def get_connector(cls, account: PlatformAccount) -> Optional[BasePlatformConnector]:
        """Get connector instance for account."""
        platform = PlatformType(account.platform)
        connector_class = cls._connectors.get(platform)
        if connector_class:
            return connector_class(account)
        return None

    @classmethod
    def list_supported_platforms(cls) -> List[PlatformType]:
        """List all supported platforms."""
        return list(cls._connectors.keys())


# Platform-specific configuration
PLATFORM_CONFIGS: Dict[PlatformType, Dict[str, Any]] = {
    PlatformType.XIAOHONGSHU: {
        "name": "小红书",
        "name_en": "Xiaohongshu",
        "auth_type": AuthType.QRCODE,
        "content_types": ["note", "video"],
        "rate_limit": "100/hour",
        "features": ["content_sync", "analytics", "engagement"],
    },
    PlatformType.WEIBO: {
        "name": "微博",
        "name_en": "Weibo",
        "auth_type": AuthType.COOKIE,
        "content_types": ["post", "article", "video"],
        "rate_limit": "300/hour",
        "features": ["content_sync", "analytics", "engagement"],
    },
    PlatformType.WECHAT_OFFICIAL: {
        "name": "微信公众号",
        "name_en": "WeChat Official",
        "auth_type": AuthType.API_KEY,
        "content_types": ["article"],
        "rate_limit": "5000/day",
        "features": ["content_sync", "analytics"],
    },
    PlatformType.ZHIHU: {
        "name": "知乎",
        "name_en": "Zhihu",
        "auth_type": AuthType.COOKIE,
        "content_types": ["answer", "article", "idea"],
        "rate_limit": "100/hour",
        "features": ["content_sync", "analytics", "engagement"],
    },
    PlatformType.JIKE: {
        "name": "即刻",
        "name_en": "Jike",
        "auth_type": AuthType.API_KEY,
        "content_types": ["post"],
        "rate_limit": "1000/day",
        "features": ["content_sync", "analytics"],
    },
    PlatformType.BILIBILI: {
        "name": "哔哩哔哩",
        "name_en": "Bilibili",
        "auth_type": AuthType.COOKIE,
        "content_types": ["video", "article"],
        "rate_limit": "100/hour",
        "features": ["content_sync", "analytics", "engagement"],
    },
    PlatformType.TWITTER: {
        "name": "X / Twitter",
        "name_en": "Twitter",
        "auth_type": AuthType.OAUTH2,
        "content_types": ["tweet", "thread"],
        "rate_limit": "300/15min",
        "features": ["content_sync", "analytics", "engagement"],
    },
    PlatformType.INSTAGRAM: {
        "name": "Instagram",
        "name_en": "Instagram",
        "auth_type": AuthType.OAUTH2,
        "content_types": ["post", "reel", "story"],
        "rate_limit": "200/hour",
        "features": ["content_sync", "analytics", "engagement"],
    },
    PlatformType.YOUTUBE: {
        "name": "YouTube",
        "name_en": "YouTube",
        "auth_type": AuthType.OAUTH2,
        "content_types": ["video", "short"],
        "rate_limit": "10000/day",
        "features": ["content_sync", "analytics", "engagement"],
    },
}


def get_platform_config(platform: PlatformType) -> Dict[str, Any]:
    """Get configuration for a platform."""
    return PLATFORM_CONFIGS.get(platform, {})
