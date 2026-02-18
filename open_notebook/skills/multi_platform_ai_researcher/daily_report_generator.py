"""Daily AI Tools Report Generator.

Automatically generates structured daily reports from collected
AI tools information across multiple platforms.
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger


class DailyReportGenerator:
    """Generates daily AI tools research reports."""

    def __init__(self):
        self.report_template = {
            'title': '',
            'date': '',
            'summary': {},
            'platform_breakdown': {},
            'trending_tools': [],
            'hot_topics': [],
            'insights': [],
            'raw_data': []
        }

    def generate(
        self,
        collected_items: List[Dict[str, Any]],
        date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate a comprehensive daily report.
        
        Args:
            collected_items: List of collected content items
            date: Report date (default: today)
            
        Returns:
            Structured report dictionary
        """
        if date is None:
            date = datetime.now()
        
        # Filter items for the specified date
        date_str = date.strftime("%Y-%m-%d")
        today_items = [
            item for item in collected_items
            if self._is_from_date(item, date)
        ]
        
        logger.info(f"Generating report for {date_str} with {len(today_items)} items")
        
        # Build report sections
        report = {
            'title': f'AI 工具集信息日报 - {date_str}',
            'date': date_str,
            'generated_at': datetime.now().isoformat(),
            'summary': self._generate_summary(today_items),
            'platform_breakdown': self._analyze_by_platform(today_items),
            'trending_tools': self._extract_trending_tools(today_items),
            'hot_topics': self._identify_hot_topics(today_items),
            'insights': self._generate_insights(today_items),
            'recommendations': self._generate_recommendations(today_items),
            'raw_data': today_items
        }
        
        return report

    def _is_from_date(self, item: Dict[str, Any], date: datetime) -> bool:
        """Check if item is from the specified date."""
        collected_at = item.get('collected_at', '')
        date_str = date.strftime("%Y-%m-%d")
        return collected_at.startswith(date_str)

    def _generate_summary(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate executive summary."""
        if not items:
            return {'total_items': 0}
        
        total_engagement = sum(
            item.get('like_count', 0) + 
            item.get('collect_count', 0) +
            item.get('comment_count', 0)
            for item in items
        )
        
        avg_engagement = total_engagement / len(items) if items else 0
        
        platforms = set(item.get('platform', 'unknown') for item in items)
        
        return {
            'total_items': len(items),
            'platforms_covered': len(platforms),
            'total_engagement': total_engagement,
            'average_engagement_per_item': round(avg_engagement, 2),
            'data_collection_period': '24h'
        }

    def _analyze_by_platform(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze data distribution by platform."""
        platform_stats = {}
        
        for item in items:
            platform = item.get('platform', 'unknown')
            if platform not in platform_stats:
                platform_stats[platform] = {
                    'count': 0,
                    'total_likes': 0,
                    'total_collects': 0,
                    'items': []
                }
            
            platform_stats[platform]['count'] += 1
            platform_stats[platform]['total_likes'] += item.get('like_count', 0)
            platform_stats[platform]['total_collects'] += item.get('collect_count', 0)
            platform_stats[platform]['items'].append({
                'title': item.get('title', ''),
                'engagement': item.get('like_count', 0) + item.get('collect_count', 0)
            })
        
        # Sort platforms by activity
        sorted_platforms = sorted(
            platform_stats.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        
        return {
            platform: {
                'item_count': stats['count'],
                'total_engagement': stats['total_likes'] + stats['total_collects'],
                'top_items': sorted(
                    stats['items'],
                    key=lambda x: x['engagement'],
                    reverse=True
                )[:5]  # Top 5 items per platform
            }
            for platform, stats in sorted_platforms
        }

    def _extract_trending_tools(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract trending AI tools from content."""
        tool_keywords = [
            'ChatGPT', 'Midjourney', 'Stable Diffusion', 'Notion AI',
            'Jasper', 'Copy.ai', 'Runway', 'Descript', 'Otter.ai',
            'Grammarly', 'Canva AI', 'Firefly', 'Leonardo.ai',
            '通义千问', '文心一言', '讯飞星火', 'Kimi', '智谱 AI'
        ]
        
        tool_mentions = {}
        
        for item in items:
            title = item.get('title', '').lower()
            content = item.get('content', '').lower()
            text = f"{title} {content}"
            
            for tool in tool_keywords:
                if tool.lower() in text:
                    tool_mentions[tool] = tool_mentions.get(tool, 0) + 1
        
        # Sort by mentions
        sorted_tools = sorted(
            tool_mentions.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {'tool_name': tool, 'mention_count': count, 'trend': 'rising'}
            for tool, count in sorted_tools[:15]
        ]

    def _identify_hot_topics(self, items: List[Dict[str, Any]]) -> List[str]:
        """Identify hot topics and themes."""
        topic_keywords = {
            '效率提升': ['效率', '提效', '自动化', '节省时间'],
            '内容创作': ['写作', '绘画', '视频', '设计', '创作'],
            '办公应用': ['办公', '文档', '表格', 'PPT', '邮件'],
            '营销推广': ['营销', '推广', 'SEO', '社交媒体'],
            '数据分析': ['数据', '分析', '报表', '可视化'],
            '客户服务': ['客服', '聊天机器人', '自动回复'],
            '编程开发': ['编程', '代码', '开发', 'debug'],
            '学习成长': ['学习', '知识管理', '笔记', '阅读']
        }
        
        topic_scores = {topic: 0 for topic in topic_keywords.keys()}
        
        for item in items:
            title = item.get('title', '').lower()
            content = item.get('content', '').lower()
            text = f"{title} {content}"
            
            for topic, keywords in topic_keywords.items():
                if any(keyword in text for keyword in keywords):
                    topic_scores[topic] += 1
        
        # Filter and sort topics
        hot_topics = [
            topic for topic, score in topic_scores.items()
            if score > 0
        ]
        
        return sorted(hot_topics, key=lambda t: topic_scores[t], reverse=True)[:8]

    def _generate_insights(self, items: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable insights."""
        insights = []
        
        if not items:
            return ["今日无数据，建议检查采集器运行状态"]
        
        # Engagement analysis
        high_engagement = [
            item for item in items
            if item.get('like_count', 0) + item.get('collect_count', 0) > 100
        ]
        
        if high_engagement:
            insights.append(
                f"发现 {len(high_engagement)} 篇高互动内容（点赞 + 收藏>100），"
                "建议深入分析其内容特征"
            )
        
        # Platform activity
        platform_counts = {}
        for item in items:
            platform = item.get('platform', 'unknown')
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        if platform_counts:
            most_active = max(platform_counts.items(), key=lambda x: x[1])
            insights.append(
                f"{most_active[0]} 是最活跃平台（{most_active[1]}条内容），"
                "建议重点关注该平台动态"
            )
        
        # Content freshness
        recent_items = [
            item for item in items
            if 'collected_at' in item
        ]
        
        if len(recent_items) < 5:
            insights.append("今日采集内容较少，建议扩展关键词范围或增加采集频率")
        
        return insights

    def _generate_recommendations(self, items: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for next actions."""
        recommendations = []
        
        # Based on trending tools
        trending = self._extract_trending_tools(items)
        if trending:
            top_tool = trending[0]['tool_name']
            recommendations.append(
                f"重点关注热门工具「{top_tool}」的最新使用技巧和案例"
            )
        
        # Based on hot topics
        topics = self._identify_hot_topics(items)
        if topics:
            recommendations.append(
                f"围绕热门话题「{topics[0]}」创作相关内容"
            )
        
        # General recommendations
        recommendations.append("定期回顾和整理采集的 AI 工具信息，形成结构化知识库")
        recommendations.append("关注高互动内容的创作者，建立行业人脉网络")
        
        return recommendations[:4]

    def export_markdown(self, report: Dict[str, Any], output_path: str) -> str:
        """Export report to Markdown format.
        
        Args:
            report: Report dictionary
            output_path: Path to save markdown file
            
        Returns:
            Path to saved file
        """
        md_content = f"""# {report['title']}

**生成时间**: {report['generated_at']}

---

## 📊 今日概览

- **内容总数**: {report['summary'].get('total_items', 0)} 条
- **覆盖平台**: {report['summary'].get('platforms_covered', 0)} 个
- **总互动量**: {report['summary'].get('total_engagement', 0)}
- **平均互动**: {report['summary'].get('average_engagement_per_item', 0)}

---

## 🔥 热门 AI 工具

"""
        
        for i, tool in enumerate(report['trending_tools'][:10], 1):
            md_content += f"{i}. **{tool['tool_name']}** ({tool['mention_count']}次提及)\n"
        
        md_content += "\n## 💡 热门话题\n\n"
        for topic in report['hot_topics']:
            md_content += f"- {topic}\n"
        
        md_content += "\n## 📱 平台分布\n\n"
        for platform, stats in report['platform_breakdown'].items():
            md_content += f"**{platform}**: {stats['item_count']}条内容\n"
        
        md_content += "\n## 🎯 核心洞察\n\n"
        for insight in report['insights']:
            md_content += f"- {insight}\n"
        
        md_content += "\n## 📋 行动建议\n\n"
        for rec in report['recommendations']:
            md_content += f"- {rec}\n"
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        logger.info(f"Report exported to {output_path}")
        return output_path


# ============================================================================
# Convenience Function
# ============================================================================

def generate_daily_report(
    collected_items: List[Dict[str, Any]],
    date: Optional[datetime] = None
) -> Dict[str, Any]:
    """Convenience function to generate daily report.
    
    Args:
        collected_items: List of collected content items
        date: Report date (default: today)
        
    Returns:
        Structured report dictionary
    """
    generator = DailyReportGenerator()
    return generator.generate(collected_items, date)
