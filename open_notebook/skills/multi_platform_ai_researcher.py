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
        """Collect from Zhihu using web scraping."""
        # TODO: Implement Zhihu collector
        # For now, return placeholder
        logger.info("Zhihu collector - to be implemented")
        return []

    async def _collect_weibo(
        self,
        keywords: List[str],
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """Collect from Weibo using API or scraping."""
        # TODO: Implement Weibo collector
        logger.info("Weibo collector - to be implemented")
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
                
        Returns:
            Execution results
        """
        platforms = params.get('platforms', list(self.platforms.keys()))
        keywords = params.get('keywords', self.ai_tools_keywords)
        max_results = params.get('max_results_per_platform', 20)
        generate_report = params.get('generate_report', True)
        save_to_notebook = params.get('save_to_notebook', True)
        
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
        
        return {
            'total_collected': len(all_content),
            'ai_tools_related': len(ai_tools_content),
            'platforms_searched': [self.platforms.get(p, p) for p in platforms],
            'report_generated': report is not None,
            'report': report
        }

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
