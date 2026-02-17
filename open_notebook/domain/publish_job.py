"""Auto-Publish System - Content distribution to social media platforms.

This module provides automated content publishing capabilities,
enabling one-click distribution to multiple platforms.

Architecture:
    Content Source → Format Adapter → Platform Publisher → Queue → Scheduled Publish

Features:
    - Multi-platform publishing (Xiaohongshu, Weibo, etc.)
    - Scheduled publishing
    - Format adaptation per platform
    - Queue management and retry logic
    - Publishing analytics
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
from pydantic import BaseModel, Field

from open_notebook.domain.base import ObjectModel
from open_notebook.domain.platform_connector import PlatformType


class PublishStatus(Enum):
    """Status of a publishing job."""
    PENDING = "pending"           # Waiting to be processed
    SCHEDULED = "scheduled"       # Scheduled for future
    QUEUED = "queued"             # In queue, ready to publish
    PUBLISHING = "publishing"     # Currently publishing
    PUBLISHED = "published"       # Successfully published
    FAILED = "failed"             # Publishing failed
    CANCELLED = "cancelled"       # Cancelled by user
    RETRYING = "retrying"         # Waiting for retry


class ContentFormat(Enum):
    """Content format types."""
    TEXT = "text"
    IMAGE = "image"
    CAROUSEL = "carousel"         # Multiple images
    VIDEO = "video"
    ARTICLE = "article"
    THREAD = "thread"             # Thread/Tweet series


class PublishJob(ObjectModel):
    """A content publishing job.

    Represents a single piece of content to be published to one or more platforms.
    """

    table_name: str = "publish_job"

    # Content identification
    title: str = ""                           # Content title
    content_text: str = ""                    # Main content text
    content_format: str = "text"              # ContentFormat value

    # Source tracking
    source_note_id: Optional[str] = None      # Source note in system
    calendar_entry_id: Optional[str] = None   # Linked calendar entry

    # Platform targeting
    target_platforms: List[str] = Field(default_factory=list)  # PlatformType values
    platform_specific_content: Dict[str, Any] = Field(default_factory=dict)

    # Media
    media_urls: List[str] = Field(default_factory=list)         # Local/remote URLs
    media_captions: List[str] = Field(default_factory=list)

    # Scheduling
    status: str = "pending"
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

    # Retry logic
    retry_count: int = 0
    max_retries: int = 3
    last_error: Optional[str] = None

    # Results
    publish_results: Dict[str, Any] = Field(default_factory=dict)  # platform -> result
    platform_urls: Dict[str, str] = Field(default_factory=dict)    # platform -> published URL

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = "system"  # user_id or "system"

    # Tags and categorization
    tags: List[str] = Field(default_factory=list)
    quadrant: Optional[str] = None  # Q1/Q2/Q3/Q4
    topic: Optional[str] = None

    async def mark_scheduled(self, scheduled_time: datetime):
        """Mark job as scheduled."""
        self.status = PublishStatus.SCHEDULED.value
        self.scheduled_at = scheduled_time
        self.updated_at = datetime.utcnow()
        await self.save()

    async def mark_publishing(self):
        """Mark job as currently publishing."""
        self.status = PublishStatus.PUBLISHING.value
        self.updated_at = datetime.utcnow()
        await self.save()

    async def mark_published(self, platform: str, url: str, platform_data: Dict[str, Any]):
        """Mark successful publish to a platform."""
        self.publish_results[platform] = {
            "status": "success",
            "published_at": datetime.utcnow().isoformat(),
            "data": platform_data,
        }
        self.platform_urls[platform] = url

        # Check if all platforms are done
        if len(self.platform_urls) >= len(self.target_platforms):
            self.status = PublishStatus.PUBLISHED.value
            self.published_at = datetime.utcnow()

        self.updated_at = datetime.utcnow()
        await self.save()

    async def mark_failed(self, error: str, platform: Optional[str] = None):
        """Mark publish as failed."""
        self.last_error = error
        self.retry_count += 1

        if platform:
            self.publish_results[platform] = {
                "status": "failed",
                "error": error,
                "failed_at": datetime.utcnow().isoformat(),
            }

        if self.retry_count >= self.max_retries:
            self.status = PublishStatus.FAILED.value
        else:
            self.status = PublishStatus.RETRYING.value

        self.updated_at = datetime.utcnow()
        await self.save()

    async def mark_cancelled(self):
        """Mark job as cancelled."""
        self.status = PublishStatus.CANCELLED.value
        self.updated_at = datetime.utcnow()
        await self.save()

    def is_ready_to_publish(self) -> bool:
        """Check if job is ready to be published."""
        if self.status not in [PublishStatus.PENDING.value, PublishStatus.QUEUED.value, PublishStatus.RETRYING.value]:
            return False

        if self.scheduled_at:
            return datetime.utcnow() >= self.scheduled_at

        return True

    def get_platforms_pending(self) -> List[str]:
        """Get list of platforms that haven't been published yet."""
        return [p for p in self.target_platforms if p not in self.platform_urls]


class PublishTemplate(ObjectModel):
    """Template for platform-specific content formatting.

    Stores formatting rules for adapting content to different platforms.
    """

    table_name: str = "publish_template"

    name: str = ""
    description: str = ""
    platform: str = ""  # PlatformType or "universal"
    content_format: str = ""  # ContentFormat

    # Formatting rules
    max_length: Optional[int] = None
    hashtag_limit: Optional[int] = None
    mention_limit: Optional[int] = None
    media_count_limit: Optional[int] = None

    # Template strings
    title_template: str = "{{title}}"  # Jinja2 template
    content_template: str = "{{content}}"
    hashtag_template: str = "#{{tag}}"

    # Platform-specific settings
    platform_settings: Dict[str, Any] = Field(default_factory=dict)

    # Default hashtags/topics for this platform
    default_hashtags: List[str] = Field(default_factory=list)
    default_mentions: List[str] = Field(default_factory=list)

    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PublisherRegistry:
    """Registry for platform publishers."""

    _publishers: Dict[PlatformType, type] = {}

    @classmethod
    def register(cls, platform: PlatformType, publisher_class: type):
        """Register a publisher class."""
        cls._publishers[platform] = publisher_class

    @classmethod
    def get_publisher(cls, account: 'PlatformAccount') -> Optional['PlatformPublisher']:
        """Get publisher instance for account."""
        platform = PlatformType(account.platform)
        publisher_class = cls._publishers.get(platform)
        if publisher_class:
            return publisher_class(account)
        return None

    @classmethod
    def list_supported_platforms(cls) -> List[PlatformType]:
        """List all supported platforms for publishing."""
        return list(cls._publishers.keys())


class PlatformPublisher(ABC):
    """Abstract base class for platform publishers."""

    def __init__(self, account: 'PlatformAccount'):
        self.account = account
        self.platform = PlatformType(account.platform)

    @abstractmethod
    async def publish(self, job: PublishJob) -> Dict[str, Any]:
        """Publish content to platform. Returns result with URL."""
        pass

    @abstractmethod
    async def validate_content(self, job: PublishJob) -> Tuple[bool, str]:
        """Validate content before publishing."""
        pass

    @abstractmethod
    def adapt_content(self, job: PublishJob) -> Dict[str, Any]:
        """Adapt generic content to platform-specific format."""
        pass

    async def publish_with_retry(self, job: PublishJob) -> Dict[str, Any]:
        """Publish with automatic retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = await self.publish(job)
                return result
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5  # Exponential backoff
                    await asyncio.sleep(wait_time)
                else:
                    raise


class PublishQueue:
    """Manages the publishing queue."""

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the publish queue processor."""
        self._running = True
        self._task = asyncio.create_task(self._process_loop())
        logger.info("Publish queue started")

    async def stop(self):
        """Stop the publish queue processor."""
        self._running = False
        if self._task:
            self._task.cancel()
        logger.info("Publish queue stopped")

    async def _process_loop(self):
        """Main processing loop."""
        while self._running:
            try:
                # Get jobs ready to publish
                jobs = await self._get_ready_jobs(limit=5)

                for job in jobs:
                    await self._process_job(job)

                # Wait before next check
                await asyncio.sleep(10)

            except Exception as e:
                logger.exception(f"Error in publish queue: {e}")
                await asyncio.sleep(30)

    async def _get_ready_jobs(self, limit: int = 10) -> List[PublishJob]:
        """Get jobs that are ready to be published."""
        # Query database for pending jobs
        # This would be implemented with actual DB query
        return []

    async def _process_job(self, job: PublishJob):
        """Process a single publish job."""
        await job.mark_publishing()

        platforms_pending = job.get_platforms_pending()

        for platform_str in platforms_pending:
            try:
                # Get platform account
                from open_notebook.domain.platform_connector import PlatformAccount
                accounts = await PlatformAccount.get_all()
                account = next(
                    (a for a in accounts if a.platform == platform_str and a.is_authenticated),
                    None
                )

                if not account:
                    await job.mark_failed(f"No authenticated account for {platform_str}", platform_str)
                    continue

                # Get publisher
                from open_notebook.skills.publishers import PublisherRegistry
                publisher = PublisherRegistry.get_publisher(account)

                if not publisher:
                    await job.mark_failed(f"No publisher available for {platform_str}", platform_str)
                    continue

                # Validate content
                valid, error = await publisher.validate_content(job)
                if not valid:
                    await job.mark_failed(error, platform_str)
                    continue

                # Publish
                result = await publisher.publish_with_retry(job)

                await job.mark_published(
                    platform=platform_str,
                    url=result.get("url", ""),
                    platform_data=result
                )

            except Exception as e:
                logger.exception(f"Failed to publish to {platform_str}: {e}")
                await job.mark_failed(str(e), platform_str)

    async def schedule_job(self, job: PublishJob, scheduled_time: datetime) -> str:
        """Schedule a job for future publishing."""
        await job.mark_scheduled(scheduled_time)
        return str(job.id)

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a scheduled job."""
        job = await PublishJob.get(job_id)
        if job and job.status in [PublishStatus.PENDING.value, PublishStatus.SCHEDULED.value]:
            await job.mark_cancelled()
            return True
        return False


# Global publish queue instance
publish_queue = PublishQueue()


class ContentAdapter:
    """Adapts content for different platforms.

    Handles format conversion, length limits, hashtag conversion, etc.
    """

    # Platform-specific limits
    PLATFORM_LIMITS = {
        PlatformType.XIAOHONGSHU: {
            "text_max": 1000,
            "images_max": 18,
            "video_max_seconds": 600,
            "title_max": 20,
        },
        PlatformType.WEIBO: {
            "text_max": 5000,
            "images_max": 18,
            "video_max_seconds": None,
            "title_max": None,
        },
        PlatformType.WECHAT_OFFICIAL: {
            "text_max": None,  # No limit for articles
            "images_max": 50,
            "video_max_seconds": None,
            "title_max": 64,
        },
        PlatformType.ZHIHU: {
            "text_max": None,
            "images_max": 100,
            "video_max_seconds": None,
            "title_max": None,
        },
        PlatformType.TWITTER: {
            "text_max": 280,
            "images_max": 4,
            "video_max_seconds": 140,
            "title_max": None,
        },
    }

    @classmethod
    def adapt_for_platform(cls, job: PublishJob, platform: PlatformType) -> Dict[str, Any]:
        """Adapt content for a specific platform."""
        limits = cls.PLATFORM_LIMITS.get(platform, {})

        # Get platform-specific content if available
        platform_content = job.platform_specific_content.get(platform.value, {})

        text = platform_content.get("text", job.content_text)
        title = platform_content.get("title", job.title)

        # Apply length limits
        if limits.get("text_max"):
            text = cls._truncate_text(text, limits["text_max"])

        if limits.get("title_max"):
            title = cls._truncate_text(title, limits["title_max"])

        # Adapt hashtags
        hashtags = cls._adapt_hashtags(job.tags, platform)

        # Adapt media
        media = job.media_urls[:limits.get("images_max", 999)]

        return {
            "title": title,
            "text": text,
            "hashtags": hashtags,
            "media": media,
            "media_captions": job.media_captions[:len(media)],
            "platform": platform.value,
            "original_job_id": str(job.id),
        }

    @classmethod
    def _truncate_text(cls, text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate text to fit within limit."""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix

    @classmethod
    def _adapt_hashtags(cls, tags: List[str], platform: PlatformType) -> List[str]:
        """Adapt hashtags for platform format."""
        if platform in [PlatformType.XIAOHONGSHU, PlatformType.WEIBO]:
            # Chinese platforms use #话题# format
            return [f"#{tag}#" for tag in tags if tag]
        elif platform in [PlatformType.TWITTER, PlatformType.INSTAGRAM]:
            # Western platforms use #hashtag format
            return [f"#{tag.replace(' ', '')}" for tag in tags if tag]
        else:
            return tags

    @classmethod
    def generate_platform_variants(cls, job: PublishJob) -> Dict[str, Dict[str, Any]]:
        """Generate content variants for all target platforms."""
        variants = {}
        for platform_str in job.target_platforms:
            try:
                platform = PlatformType(platform_str)
                variants[platform_str] = cls.adapt_for_platform(job, platform)
            except ValueError:
                continue
        return variants
