"""Multi-Platform AI Tools Researcher Skill.

Automatically collects information about "AI tools for solopreneurs" from
multiple Chinese social media platforms (Xiaohongshu, Zhihu, Weibo, Video
Account, Official Account, Douyin) and generates daily research reports.
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from open_notebook.database.repository import repo_create, repo_query


class MultiPlatformAIResearcher:
    """Cross-platform researcher for AI tools information."""

    def __init__(self):
        self.platforms = {
            'xiaohongshu': '小红书',
            'zhihu': '知乎',
            'weibo': '微博',
            'video_account': '视频号',
            'official_account': '公众号',
            'douyin': '抖音'
        }
        
        self.ai_tools_keywords = [
            "AI 工具",
            "人工智能工具",
            "AIGC",
            "AI 效率工具",
            "AI 办公工具",
            "AI 创作工具",
            "ChatGPT",
            "Midjourney",
            "Stable Diffusion",
            "Notion AI",
            "一人公司 AI",
            "solo 创业 AI",
            "独立开发者 AI 工具"
        ]
        
        self.collected_data = []

    async def collect_from_platform(
        self, 
        platform: str, 
        keywords: List[str],
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """Collect data from a specific platform.
        
        Args:
            platform: Platform name (xiaohongshu, zhihu, weibo, etc.)
            keywords: List of keywords to search
            max_results: Maximum results per keyword
            
        Returns:
            List of collected items
        """
        logger.info(f"Collecting from {self.platforms.get(platform, platform)}: {keywords}")
        
        # Delegate to platform-specific collectors
        if platform == 'xiaohongshu':
            return await self._collect_xiaohongshu(keywords, max_results)
        elif platform == 'zhihu':
            return await self._collect_zhihu(keywords, max_results)
        elif platform == 'weibo':
            return await self._collect_weibo(keywords, max_results)
        # Add more platform collectors as needed
        
        return []

    async def _collect_xiaohongshu(
        self, 
        keywords: List[str],
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """Collect from Xiaohongshu using existing skill."""
        try:
            from open_notebook.skills.xiaohongshu_researcher.skill import (
                XiaohongshuResearcherSkill
            )
            
            skill = XiaohongshuResearcherSkill()
            await skill.initialize()  # Initialize browser first!
            all_notes = []
            
            for keyword in keywords[:3]:  # Limit to top 3 keywords
                try:
                    notes = await skill.search_keyword(keyword, max_results // 3)
                    all_notes.extend(notes)
                except Exception as e:
                    logger.error(f"Failed to search '{keyword}': {e}")
                    continue
            
            await skill.close()  # Clean up browser
            return all_notes
            
        except Exception as e:
            logger.error(f"Xiaohongshu collection failed: {e}")
            return []

    async def _collect_zhihu(
        self,
        keywords: List[str],
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """Collect from Zhihu using web scraping.
        
        Args:
            keywords: List of keywords to search
            max_results: Maximum results per keyword
            
        Returns:
            List of collected items
        """
        try:
            from playwright.async_api import async_playwright
            
            all_items = []
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                for keyword in keywords[:5]:  # Limit keywords for Zhihu
                    logger.info(f"Searching Zhihu for: {keyword}")
                    
                    try:
                        # Navigate to Zhihu search
                        search_url = f"https://www.zhihu.com/search?q={keyword}&type=content"
                        await page.goto(search_url, wait_until="networkidle")
                        await asyncio.sleep(3)
                        
                        # Scroll to load more content
                        for _ in range(3):
                            await page.evaluate("window.scrollBy(0, window.innerHeight)")
                            await asyncio.sleep(2)
                        
                        # Extract search results - use flexible selectors
                        result_selectors = [
                            ".ContentItem-title",
                            "[data-zop-question]",
                            "h2.ContentItem-title",
                            ".SearchResult-Card h2"
                        ]
                        
                        items = []
                        for selector in result_selectors:
                            elements = await page.query_selector_all(selector)
                            if elements:
                                items = elements
                                logger.info(f"Found {len(items)} results using selector: {selector}")
                                break
                        
                        for i, item in enumerate(items[:max_results//2]):
                            try:
                                title_elem = await item.query_selector("a, h2, .ContentItem-title")
                                title = await title_elem.inner_text() if title_elem else ""
                                
                                # Try to get author
                                author_elem = await item.query_selector(".UserLink-link, .AuthorInfo-name")
                                author = await author_elem.inner_text() if author_elem else ""
                                
                                # Try to get engagement metrics
                                vote_elem = await item.query_selector(".VoteButton--up, .ContentItem-action")
                                votes = await vote_elem.inner_text() if vote_elem else "0"
                                
                                # Clean up data
                                title = title.strip()
                                if title and len(title) > 10:  # Filter very short titles
                                    all_items.append({
                                        'title': title,
                                        'author': author.strip(),
                                        'platform': 'zhihu',
                                        'url': await item.evaluate("el => { const a = el.closest('a'); return a ? a.href : ''; }"),
                                        'like_count': int(votes.replace(",", "").replace("K", "000").replace("万", "0000")) if votes else 0,
                                        'collect_count': 0,  # Hard to extract from search results
                                        'collected_at': datetime.now().isoformat(),
                                        'content_type': 'answer' if '回答' in title.lower() else 'article'
                                    })
                            except Exception as e:
                                logger.debug(f"Failed to extract Zhihu item: {e}")
                                continue
                        
                    except Exception as e:
                        logger.error(f"Failed to search '{keyword}' on Zhihu: {e}")
                        continue
                
                await browser.close()
            
            logger.info(f"Collected {len(all_items)} items from Zhihu")
            return all_items
            
        except Exception as e:
            logger.error(f"Zhihu collection failed: {e}")
            return []

    async def _collect_weibo(
        self,
        keywords: List[str],
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """Collect from Weibo using web scraping.
        
        Args:
            keywords: List of keywords to search
            max_results: Maximum results per keyword
            
        Returns:
            List of collected items
        """
        try:
            from playwright.async_api import async_playwright
            
            all_items = []
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                for keyword in keywords[:5]:
                    logger.info(f"Searching Weibo for: {keyword}")
                    
                    try:
                        # Navigate to Weibo search
                        search_url = f"https://s.weibo.com/weibo/{keyword}"
                        await page.goto(search_url, wait_until="networkidle")
                        await asyncio.sleep(3)
                        
                        # Extract weibos
                        weibo_cards = await page.query_selector_all(".card-wrap")
                        
                        for card in weibo_cards[:max_results//2]:
                            try:
                                # Get content
                                content_elem = await card.query_selector(".txt")
                                content = await content_elem.get_attribute('title') if content_elem else ""
                                
                                # Get author
                                author_elem = await card.query_selector(".name")
                                author = await author_elem.inner_text() if author_elem else ""
                                
                                # Get engagement metrics
                                actions = []
                                action_elems = await card.query_selector_all(".line-list li")
                                for action_elem in action_elems:
                                    text = await action_elem.inner_text()
                                    actions.append(text.strip())
                                
                                # Parse numbers from actions (likes, reposts, comments)
                                like_count = 0
                                collect_count = 0
                                comment_count = 0
                                
                                for action in actions:
                                    import re
                                    numbers = re.findall(r'\d+', action)
                                    if numbers:
                                        num = int(numbers[0])
                                        if '赞' in action or 'like' in action.lower():
                                            like_count = num
                                        elif '收藏' in action or 'collect' in action.lower():
                                            collect_count = num
                                        elif '评论' in action or 'comment' in action.lower():
                                            comment_count = num
                                
                                # Get link
                                link_elem = await card.query_selector("a[href*='/status/']")
                                url = await link_elem.get_attribute('href') if link_elem else ""
                                
                                if content and len(content) > 10:
                                    all_items.append({
                                        'title': content[:100] + "..." if len(content) > 100 else content,
                                        'content': content,
                                        'author': author.strip(),
                                        'platform': 'weibo',
                                        'url': f"https://weibo.com{url}" if url and url.startswith("/") else url,
                                        'like_count': like_count,
                                        'collect_count': collect_count,
                                        'comment_count': comment_count,
                                        'collected_at': datetime.now().isoformat(),
                                        'content_type': 'weibo'
                                    })
                                    
                            except Exception as e:
                                logger.debug(f"Failed to extract Weibo item: {e}")
                                continue
                                
                    except Exception as e:
                        logger.error(f"Failed to search '{keyword}' on Weibo: {e}")
                        continue
                
                await browser.close()
            
            logger.info(f"Collected {len(all_items)} items from Weibo")
            return all_items
            
        except Exception as e:
            logger.error(f"Weibo collection failed: {e}")
            return []

    def identify_ai_tools(self, content_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter and identify AI tools related content.
        
        Args:
            content_items: Raw content items from platforms
            
        Returns:
            Filtered list of AI tools related items
        """
        ai_tools_content = []
        
        for item in content_items:
            title = item.get('title', '').lower()
            content = item.get('content', '').lower()
            
            # Check if any AI tools keyword appears
            is_related = any(
                keyword.lower() in title or keyword.lower() in content
                for keyword in self.ai_tools_keywords
            )
            
            if is_related:
                # Enrich with metadata
                item['is_ai_tools'] = True
                item['matched_keywords'] = [
                    kw for kw in self.ai_tools_keywords
                    if kw.lower() in title or kw.lower() in content
                ]
                ai_tools_content.append(item)
        
        logger.info(f"Identified {len(ai_tools_content)} AI tools related items")
        return ai_tools_content

    def generate_daily_report(
        self,
        date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate daily research report.
        
        Args:
            date: Report date (default: today)
            
        Returns:
            Report dictionary with structured insights
        """
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime("%Y-%m-%d")
        
        # Filter today's data
        today_items = [
            item for item in self.collected_data
            if item.get('collected_at', '').startswith(date_str)
        ]
        
        # Group by platform
        by_platform = {}
        for item in today_items:
            platform = item.get('platform', 'unknown')
            if platform not in by_platform:
                by_platform[platform] = []
            by_platform[platform].append(item)
        
        # Extract top AI tools mentioned
        tool_mentions = {}
        for item in today_items:
            for tool in item.get('matched_keywords', []):
                tool_mentions[tool] = tool_mentions.get(tool, 0) + 1
        
        top_tools = sorted(
            tool_mentions.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        # Generate insights
        insights = []
        if top_tools:
            insights.append(f"今日热门 AI 工具：{', '.join([t[0] for t in top_tools[:5]])}")
        
        total_engagement = sum(
            item.get('like_count', 0) + item.get('collect_count', 0)
            for item in today_items
        )
        insights.append(f"总互动量：{total_engagement}")
        
        if by_platform:
            most_active = max(by_platform.items(), key=lambda x: len(x[1]))
            insights.append(f"最活跃平台：{self.platforms.get(most_active[0], most_active[0])} ({len(most_active[1])}条)")
        
        report = {
            'report_date': date_str,
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_items': len(today_items),
                'platforms_covered': list(by_platform.keys()),
                'total_engagement': total_engagement
            },
            'by_platform': {
                self.platforms.get(k, k): len(v) 
                for k, v in by_platform.items()
            },
            'top_ai_tools': [
                {'tool': tool, 'mentions': count}
                for tool, count in top_tools
            ],
            'insights': insights,
            'items': today_items
        }
        
        return report

    async def execute(
        self,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the multi-platform research.
        
        Args:
            params: Execution parameters
                - platforms: List of platforms to search (default: all)
                - keywords: Additional keywords (default: AI tools keywords)
                - max_results_per_platform: Max results per platform (default: 20)
                - generate_report: Whether to generate daily report (default: True)
                - save_to_notebook: Whether to save to notebook (default: True)
                - sync_to_feishu: Whether to sync to Feishu (default: False)
                - feishu_webhook: Feishu webhook URL (optional)
                - feishu_app_id: Feishu app ID (optional)
                - feishu_app_secret: Feishu app secret (optional)
                
        Returns:
            Execution results
        """
        platforms = params.get('platforms', list(self.platforms.keys()))
        keywords = params.get('keywords', self.ai_tools_keywords)
        max_results = params.get('max_results_per_platform', 20)
        generate_report = params.get('generate_report', True)
        save_to_notebook = params.get('save_to_notebook', True)
        sync_to_feishu = params.get('sync_to_feishu', False)
        feishu_webhook = params.get('feishu_webhook')
        feishu_app_id = params.get('feishu_app_id')
        feishu_app_secret = params.get('feishu_app_secret')
        
        logger.info(f"Starting multi-platform AI tools research...")
        logger.info(f"Platforms: {[self.platforms.get(p, p) for p in platforms]}")
        logger.info(f"Keywords: {keywords[:5]}...")
        
        # Collect from all platforms
        all_content = []
        for platform in platforms:
            try:
                items = await self.collect_from_platform(
                    platform, 
                    keywords,
                    max_results
                )
                
                # Add platform metadata
                for item in items:
                    item['platform'] = platform
                
                all_content.extend(items)
                logger.info(f"Collected {len(items)} items from {self.platforms.get(platform, platform)}")
                
            except Exception as e:
                logger.error(f"Failed to collect from {platform}: {e}")
        
        # Identify AI tools content
        ai_tools_content = self.identify_ai_tools(all_content)
        self.collected_data = ai_tools_content
        
        # Generate report
        report = None
        if generate_report and ai_tools_content:
            report = self.generate_daily_report()
            
            # Save to notebook
            if save_to_notebook:
                await self.save_report_to_notebook(report)
            
            # Sync to Feishu
            if sync_to_feishu:
                await self.sync_to_feishu(
                    report,
                    webhook_url=feishu_webhook,
                    app_id=feishu_app_id,
                    app_secret=feishu_app_secret
                )
        
        return {
            'total_collected': len(all_content),
            'ai_tools_related': len(ai_tools_content),
            'platforms_searched': [self.platforms.get(p, p) for p in platforms],
            'report_generated': report is not None,
            'report': report
        }

    async def sync_to_feishu(
        self,
        report: Dict[str, Any],
        webhook_url: Optional[str] = None,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None
    ) -> bool:
        """Sync report to Feishu.
        
        Args:
            report: Daily report
            webhook_url: Feishu webhook URL
            app_id: Feishu app ID
            app_secret: Feishu app secret
            
        Returns:
            True if successful
        """
        try:
            from .feishu_sync import FeishuSyncService
            
            service = FeishuSyncService(
                webhook_url=webhook_url,
                app_id=app_id,
                app_secret=app_secret
            )
            
            success = await service.send_daily_report(report)
            
            if success:
                logger.info("Successfully synced report to Feishu")
                return True
            else:
                logger.warning("Failed to sync report to Feishu")
                return False
                
        except Exception as e:
            logger.error(f"Feishu sync failed: {e}")
            return False

    async def save_report_to_notebook(self, report: Dict[str, Any]) -> int:
        """Save daily report to Notebook.
        
        Args:
            report: Daily report dictionary
            
        Returns:
            Number of sources created
        """
        today = datetime.now().strftime("%Y-%m-%d")
        notebook_name = f"AI 工具集研究 - {today}"
        
        # Find or create notebook
        existing = await repo_query(
            f"SELECT * FROM notebook WHERE name = '{notebook_name}'"
        )
        
        if existing:
            notebook_id = existing[0]["id"]
        else:
            notebook_data = {
                "name": notebook_name,
                "description": "跨平台 AI 工具集信息追踪与研究",
                "created_at": datetime.now()
            }
            result = await repo_create("notebook", notebook_data)
            notebook_id = result["id"]
        
        # Create source with report
        source_data = {
            "notebook_id": notebook_id,
            "title": f"AI 工具集日报 - {today}",
            "source_type": "ai_tools_daily_report",
            "content": json.dumps(report, ensure_ascii=False, indent=2),
            "metadata": {
                'report_type': 'daily',
                'report_date': report['report_date'],
                'total_items': report['summary']['total_items'],
                'platforms': report['summary']['platforms_covered']
            }
        }
        
        result = await repo_create("source", source_data)
        logger.info(f"Saved daily report to source: {result['id']}")
        
        return 1


# Convenience function
async def research_ai_tools(
    platforms: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
    max_results: int = 20,
    generate_report: bool = True,
    save_to_notebook: bool = True
) -> Dict[str, Any]:
    """Convenience function to run multi-platform AI tools research.
    
    Args:
        platforms: Platforms to search (default: all supported)
        keywords: Keywords to search (default: AI tools keywords)
        max_results: Max results per platform
        generate_report: Whether to generate daily report
        save_to_notebook: Whether to save to notebook
        
    Returns:
        Research results
    """
    researcher = MultiPlatformAIResearcher()
    return await researcher.execute({
        'platforms': platforms,
        'keywords': keywords,
        'max_results_per_platform': max_results,
        'generate_report': generate_report,
        'save_to_notebook': save_to_notebook
    })
