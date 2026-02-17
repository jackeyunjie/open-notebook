"""Feishu (Lark) Sync Service.

Synchronizes research reports and data to Feishu (Lark) platform
via webhooks and bot API.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger


class FeishuSyncService:
    """Service for syncing data to Feishu."""

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None
    ):
        """Initialize Feishu sync service.
        
        Args:
            webhook_url: Feishu bot webhook URL
            app_id: Feishu app ID (for advanced API calls)
            app_secret: Feishu app secret (for advanced API calls)
        """
        self.webhook_url = webhook_url
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

    async def send_daily_report(
        self,
        report: Dict[str, Any],
        chat_webhook: Optional[str] = None
    ) -> bool:
        """Send daily report to Feishu chat.
        
        Args:
            report: Daily research report
            chat_webhook: Specific chat webhook (overrides default)
            
        Returns:
            True if successful
        """
        webhook = chat_webhook or self.webhook_url
        
        if not webhook:
            logger.error("Feishu webhook URL not configured")
            return False
        
        try:
            # Format report as rich text message
            message = self._format_report_message(report)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook,
                    json=message,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('StatusCode') == 0 or result.get('code') == 0:
                        logger.info("Daily report sent to Feishu successfully")
                        return True
                    else:
                        logger.error(f"Feishu API error: {result}")
                        return False
                else:
                    logger.error(f"Feishu webhook failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to send report to Feishu: {e}")
            return False

    def _format_report_message(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Format report as Feishu message.
        
        Args:
            report: Daily research report
            
        Returns:
            Feishu message payload
        """
        date = report.get('date', datetime.now().strftime("%Y-%m-%d"))
        summary = report.get('summary', {})
        trending_tools = report.get('trending_tools', [])[:5]
        insights = report.get('insights', [])[:3]
        
        # Build rich text content
        elements = [
            {"tag": "h1", "text": {"content": f"🤖 AI 工具集日报 - {date}", "type": "plain_text"}},
            {"tag": "hr"},
            {"tag": "p", "text": {"content": "", "type": "plain_text"}},
            
            # Summary section
            {"tag": "h2", "text": {"content": "📊 今日概览", "type": "plain_text"}},
            {"tag": "p", "text": {
                "content": f"• 内容总数：{summary.get('total_items', 0)} 条\n"
                          f"• 覆盖平台：{summary.get('platforms_covered', 0)} 个\n"
                          f"• 总互动量：{summary.get('total_engagement', 0)}",
                "type": "plain_text"
            }},
            {"tag": "p", "text": {"content": "", "type": "plain_text"}},
            
            # Trending tools section
            {"tag": "h2", "text": {"content": "🔥 热门 AI 工具", "type": "plain_text"}},
        ]
        
        for i, tool in enumerate(trending_tools, 1):
            elements.append({
                "tag": "p",
                "text": {
                    "content": f"{i}. {tool['tool_name']} ({tool['mention_count']}次提及)",
                    "type": "plain_text"
                }
            })
        
        elements.extend([
            {"tag": "p", "text": {"content": "", "type": "plain_text"}},
            
            # Insights section
            {"tag": "h2", "text": {"content": "💡 核心洞察", "type": "plain_text"}},
        ])
        
        for insight in insights:
            elements.append({
                "tag": "p",
                "text": {
                    "content": f"• {insight}",
                    "type": "plain_text"
                }
            })
        
        elements.extend([
            {"tag": "p", "text": {"content": "", "type": "plain_text"}},
            {"tag": "hr"},
            {"tag": "p", "text": {
                "content": "数据已同步到 Open Notebook 知识库",
                "type": "plain_text"
            }}
        ])
        
        return {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"AI 工具集日报 - {date}"
                    },
                    "template": "blue"
                },
                "elements": elements
            }
        }

    async def upload_data_to_cloud_sheet(
        self,
        items: List[Dict[str, Any]],
        sheet_token: str
    ) -> bool:
        """Upload collected data to Feishu Cloud Sheet (Multidimensional Table).
        
        Args:
            items: List of collected items
            sheet_token: Feishu cloud sheet token
            app_id: Feishu app ID
            app_secret: Feishu app secret
            
        Returns:
            True if successful
        """
        if not self.app_id or not self.app_secret:
            logger.error("Feishu app credentials not configured")
            return False
        
        try:
            # Get access token
            await self._get_access_token()
            
            if not self.access_token:
                return False
            
            # Prepare records for upload
            records = []
            for item in items:
                record = {
                    "fields": {
                        "标题": item.get('title', '')[:200],
                        "作者": item.get('author', ''),
                        "平台": item.get('platform', ''),
                        "链接": item.get('url', ''),
                        "点赞数": item.get('like_count', 0),
                        "收藏数": item.get('collect_count', 0),
                        "采集时间": item.get('collected_at', '')[:19].replace('T', ' ')
                    }
                }
                records.append(record)
            
            # Batch upload (100 records per request)
            batch_size = 100
            for i in range(0, len(records), batch_size):
                batch_records = records[i:i + batch_size]
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"https://open.feishu.cn/open-apis/bitable/v1/apps/{sheet_token}/tables/tblXXX/records",
                        json={"records": batch_records},
                        headers={
                            "Authorization": f"Bearer {self.access_token}",
                            "Content-Type": "application/json"
                        },
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('code') == 0:
                            logger.info(f"Uploaded batch {i//batch_size + 1} to Feishu cloud sheet")
                        else:
                            logger.error(f"Feishu cloud sheet upload error: {result}")
                            return False
                    else:
                        logger.error(f"Feishu cloud sheet upload failed: {response.status_code}")
                        return False
            
            logger.info(f"Successfully uploaded {len(records)} records to Feishu cloud sheet")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload to Feishu cloud sheet: {e}")
            return False

    async def _get_access_token(self) -> Optional[str]:
        """Get Feishu access token using app credentials.
        
        Returns:
            Access token string or None
        """
        # Check if we have a valid cached token
        if self.access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at:
                return self.access_token
        
        # Request new token
        if not self.app_id or not self.app_secret:
            logger.error("Cannot get access token: missing app credentials")
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal",
                    json={
                        "app_id": self.app_id,
                        "app_secret": self.app_secret
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('code') == 0:
                        self.access_token = result['app_access_token']
                        # Token expires in 2 hours, refresh 5 minutes early
                        self.token_expires_at = datetime.now().timestamp() + (2 * 3600 - 300)
                        logger.info("Got new Feishu access token")
                        return self.access_token
                    else:
                        logger.error(f"Feishu auth failed: {result}")
                        return None
                else:
                    logger.error(f"Feishu auth request failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to get Feishu access token: {e}")
            return None


# Global instance
feishu_sync: Optional[FeishuSyncService] = None


def initialize_feishu_sync(
    webhook_url: Optional[str] = None,
    app_id: Optional[str] = None,
    app_secret: Optional[str] = None
) -> FeishuSyncService:
    """Initialize global Feishu sync service.
    
    Args:
        webhook_url: Feishu bot webhook URL
        app_id: Feishu app ID
        app_secret: Feishu app secret
        
    Returns:
        FeishuSyncService instance
    """
    global feishu_sync
    feishu_sync = FeishuSyncService(webhook_url, app_id, app_secret)
    return feishu_sync


async def sync_report_to_feishu(
    report: Dict[str, Any],
    webhook_url: Optional[str] = None
) -> bool:
    """Convenience function to sync report to Feishu.
    
    Args:
        report: Daily research report
        webhook_url: Feishu webhook URL
        
    Returns:
        True if successful
    """
    service = feishu_sync or FeishuSyncService(webhook_url)
    return await service.send_daily_report(report, webhook_url)
