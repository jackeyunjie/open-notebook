"""Platform Publishers for automated content publishing.

This package provides publishers to post content to various social media platforms.

Available publishers:
- XiaohongshuPublisher (小红书)
- WeiboPublisher (微博)

Usage:
    from open_notebook.skills.publishers import PublisherRegistry
    from open_notebook.domain.platform_connector import PlatformAccount
    from open_notebook.domain.publish_job import PublishJob

    # Get publisher for account
    account = await PlatformAccount.get(account_id)
    publisher = PublisherRegistry.get_publisher(account)

    # Publish content
    result = await publisher.publish(job)
"""

# Import publishers to register them
from open_notebook.skills.publishers.xiaohongshu_publisher import XiaohongshuPublisher
from open_notebook.skills.publishers.weibo_publisher import WeiboPublisher

__all__ = [
    "XiaohongshuPublisher",
    "WeiboPublisher",
]
