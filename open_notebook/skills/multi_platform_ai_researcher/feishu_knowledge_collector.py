"""Feishu Knowledge Base Collector.

Automatically collect AI tools information from Feishu docs and meetings.
支持飞书知识库、文档、会议纪要的自动化采集。
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger


class FeishuKnowledgeCollector:
    """飞书知识库采集器"""

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        tenant_key: Optional[str] = None
    ):
        """初始化飞书采集器
        
        Args:
            app_id: 飞书应用 App ID
            app_secret: 飞书应用 App Secret
            tenant_key: 企业标识（可选）
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.tenant_key = tenant_key
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

    async def _get_access_token(self) -> Optional[str]:
        """获取飞书访问令牌"""
        # 检查缓存的 token
        if self.access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at:
                return self.access_token
        
        # 请求新 token
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
                        # Token 有效期 2 小时，提前 5 分钟刷新
                        self.token_expires_at = datetime.now().timestamp() + (2 * 3600 - 300)
                        logger.info("获取到新的飞书访问令牌")
                        return self.access_token
                    else:
                        logger.error(f"飞书认证失败：{result}")
                        return None
                else:
                    logger.error(f"飞书认证请求失败：{response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"获取飞书令牌失败：{e}")
            return None

    async def list_docs(
        self,
        folder_token: Optional[str] = None,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """列出知识库中的文档
        
        Args:
            folder_token: 指定文件夹 token（可选）
            max_results: 最大结果数
            
        Returns:
            文档列表
        """
        await self._get_access_token()
        
        if not self.access_token:
            logger.error("缺少有效的访问令牌")
            return []
        
        all_docs = []
        page_token = None
        
        try:
            while len(all_docs) < max_results:
                params = {
                    "page_size": min(50, max_results - len(all_docs))
                }
                
                if page_token:
                    params["page_token"] = page_token
                
                if folder_token:
                    params["folder_token"] = folder_token
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        "https://open.feishu.cn/open-apis/drive/v1/files/search",
                        params=params,
                        headers={
                            "Authorization": f"Bearer {self.access_token}",
                            "Content-Type": "application/json"
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('code') == 0:
                            files = result.get('data', {}).get('files', [])
                            
                            # 过滤出文档类型
                            for file in files:
                                if file.get('file_type') == 'doc':
                                    all_docs.append({
                                        'obj_token': file.get('obj_token'),
                                        'name': file.get('name'),
                                        'file_type': file.get('file_type'),
                                        'parent_folder': file.get('parent_folder'),
                                        'created_time': file.get('created_time'),
                                        'modified_time': file.get('modified_time')
                                    })
                            
                            # 检查是否有下一页
                            has_more = result.get('data', {}).get('has_more', False)
                            if not has_more:
                                break
                            
                            page_token = result.get('data', {}).get('page_token')
                            if not page_token:
                                break
                        else:
                            logger.error(f"飞书文档列表获取失败：{result}")
                            break
                    else:
                        logger.error(f"飞书文档列表请求失败：{response.status_code}")
                        break
                
                await asyncio.sleep(0.5)  # 避免速率限制
            
            logger.info(f"成功获取 {len(all_docs)} 个飞书文档")
            return all_docs
            
        except Exception as e:
            logger.error(f"获取飞书文档列表失败：{e}")
            return []

    async def get_doc_content(self, obj_token: str) -> Optional[str]:
        """获取文档内容
        
        Args:
            obj_token: 文档对象 token
            
        Returns:
            文档内容（Markdown 格式）
        """
        await self._get_access_token()
        
        if not self.access_token:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://open.feishu.cn/open-apis/docx/v1/documents/{obj_token}/raw_content",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('code') == 0:
                        content = result.get('data', {}).get('content', '')
                        logger.info(f"成功获取文档内容：{obj_token[:10]}...")
                        return content
                    else:
                        logger.error(f"飞书文档内容获取失败：{result}")
                        return None
                else:
                    logger.error(f"飞书文档内容请求失败：{response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"获取飞书文档内容失败：{e}")
            return None

    async def list_meetings(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """列出会议记录
        
        Args:
            start_time: 开始时间（ISO 格式）
            end_time: 结束时间（ISO 格式）
            max_results: 最大结果数
            
        Returns:
            会议列表
        """
        await self._get_access_token()
        
        if not self.access_token:
            return []
        
        # 默认查询最近 7 天的会议
        if not start_time:
            from datetime import timedelta
            start_time = (datetime.now() - timedelta(days=7)).isoformat()
        
        if not end_time:
            end_time = datetime.now().isoformat()
        
        all_meetings = []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://open.feishu.cn/open-apis/meetingroom/v1/meetings/list",
                    json={
                        "start_time": start_time,
                        "end_time": end_time,
                        "limit": max_results
                    },
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('code') == 0:
                        meetings = result.get('data', {}).get('meetings', [])
                        
                        for meeting in meetings:
                            all_meetings.append({
                                'meeting_id': meeting.get('meeting_id'),
                                'title': meeting.get('title'),
                                'start_time': meeting.get('start_time'),
                                'end_time': meeting.get('end_time'),
                                'organizer': meeting.get('organizer'),
                                'participants': meeting.get('participants', []),
                                'meeting_url': meeting.get('meeting_url')
                            })
                        
                        logger.info(f"成功获取 {len(all_meetings)} 个会议记录")
                        return all_meetings
                    else:
                        logger.error(f"飞书会议列表获取失败：{result}")
                        return []
                else:
                    logger.error(f"飞书会议列表请求失败：{response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"获取飞书会议列表失败：{e}")
            return []

    async def get_meeting_minutes(self, meeting_id: str) -> Optional[str]:
        """获取会议纪要
        
        Args:
            meeting_id: 会议 ID
            
        Returns:
            会议纪要内容
        """
        await self._get_access_token()
        
        if not self.access_token:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://open.feishu.cn/open-apis/meetingroom/v1/meetings/{meeting_id}/minutes",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('code') == 0:
                        minutes = result.get('data', {}).get('minutes', '')
                        logger.info(f"成功获取会议纪要：{meeting_id[:10]}...")
                        return minutes
                    else:
                        logger.error(f"飞书会议纪要获取失败：{result}")
                        return None
                else:
                    logger.error(f"飞书会议纪要请求失败：{response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"获取飞书会议纪要失败：{e}")
            return None

    async def collect_ai_tools_knowledge(
        self,
        keywords: List[str] = None,
        max_docs: int = 50,
        max_meetings: int = 20
    ) -> Dict[str, Any]:
        """采集 AI 工具相关知识
        
        Args:
            keywords: AI 工具相关关键词列表
            max_docs: 最大文档数
            max_meetings: 最大会议数
            
        Returns:
            采集结果汇总
        """
        if keywords is None:
            keywords = [
                'AI 工具', '人工智能', 'ChatGPT', 'Kimi',
                'Midjourney', 'Stable Diffusion', 'Notion AI',
                'AIGC', '大模型', 'LLM'
            ]
        
        logger.info("开始采集飞书知识库中的 AI 工具信息...")
        
        # 采集文档
        docs = await self.list_docs(max_results=max_docs)
        ai_docs = []
        
        for doc in docs:
            # 简单关键词匹配
            is_relevant = any(
                kw.lower() in doc.get('name', '').lower()
                for kw in keywords
            )
            
            if is_relevant:
                content = await self.get_doc_content(doc['obj_token'])
                if content:
                    ai_docs.append({
                        'title': doc.get('name'),
                        'content': content,
                        'created_time': doc.get('created_time'),
                        'url': f"https://your-company.feishu.cn/docs/{doc['obj_token']}"
                    })
        
        logger.info(f"筛选出 {len(ai_docs)} 篇 AI 工具相关文档")
        
        # 采集会议
        meetings = await self.list_meetings(max_results=max_meetings)
        ai_meetings = []
        
        for meeting in meetings:
            # 检查会议标题是否包含 AI 相关关键词
            is_relevant = any(
                kw.lower() in meeting.get('title', '').lower()
                for kw in keywords
            )
            
            if is_relevant:
                minutes = await self.get_meeting_minutes(meeting['meeting_id'])
                ai_meetings.append({
                    'title': meeting.get('title'),
                    'start_time': meeting.get('start_time'),
                    'participants': meeting.get('participants', []),
                    'minutes': minutes,
                    'url': meeting.get('meeting_url')
                })
        
        logger.info(f"筛选出 {len(ai_meetings)} 场 AI 工具相关会议")
        
        return {
            'total_docs': len(docs),
            'ai_docs': len(ai_docs),
            'total_meetings': len(meetings),
            'ai_meetings': len(ai_meetings),
            'docs': ai_docs,
            'meetings': ai_meetings,
            'collected_at': datetime.now().isoformat()
        }


# 全局实例
feishu_collector: Optional[FeishuKnowledgeCollector] = None


def initialize_feishu_collector(
    app_id: str,
    app_secret: str,
    tenant_key: Optional[str] = None
) -> FeishuKnowledgeCollector:
    """初始化全局飞书采集器"""
    global feishu_collector
    feishu_collector = FeishuKnowledgeCollector(app_id, app_secret, tenant_key)
    return feishu_collector


async def collect_from_feishu(
    app_id: str,
    app_secret: str,
    keywords: List[str] = None,
    max_docs: int = 50,
    max_meetings: int = 20
) -> Dict[str, Any]:
    """便捷函数：从飞书采集 AI 工具知识
    
    Args:
        app_id: 飞书应用 ID
        app_secret: 飞书应用密钥
        keywords: 关键词列表
        max_docs: 最大文档数
        max_meetings: 最大会议数
        
    Returns:
        采集结果
    """
    collector = FeishuKnowledgeCollector(app_id, app_secret)
    return await collector.collect_ai_tools_knowledge(
        keywords=keywords,
        max_docs=max_docs,
        max_meetings=max_meetings
    )
