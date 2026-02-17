"""Platform Connectors for social media data synchronization.

This package provides connectors to fetch content and analytics
from various social media platforms.

Available connectors:
- XiaohongshuConnector (小红书)
- WeiboConnector (微博)

Usage:
    from open_notebook.skills.connectors import ConnectorRegistry
    from open_notebook.domain.platform_connector import PlatformAccount

    # Get connector for account
    account = await PlatformAccount.get(account_id)
    connector = ConnectorRegistry.get_connector(account)

    # Sync content
    count, error = await connector.sync_content()
"""

# Import connectors to register them
from open_notebook.skills.connectors.xiaohongshu_connector import XiaohongshuConnector
from open_notebook.skills.connectors.weibo_connector import WeiboConnector

__all__ = [
    "XiaohongshuConnector",
    "WeiboConnector",
]
