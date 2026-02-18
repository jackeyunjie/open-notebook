#!/usr/bin/env python3
"""
集成测试 - 数据追踪 + 可视化报告生成

演示完整工作流程:
1. 记录多条内容数据
2. 获取平台统计
3. 执行周度进化分析
4. 生成可视化 HTML 报告
"""

import asyncio
from datetime import datetime, timedelta
from open_notebook.skills.performance_tracker import PerformanceTracker, track_content_performance
from open_notebook.skills.weekly_evolution_scheduler import run_weekly_evolution
from open_notebook.skills.report_generator import generate_visualized_report


async def main():
    print("=" * 60)
    print("🚀 集成测试：数据追踪 + 可视化报告")
    print("=" * 60)
    
    # Step 1: 模拟记录一周的内容数据
    print("\n📊 Step 1: 记录内容数据...")
    
    sample_contents = [
        # 周一
        {
            'platform': 'xiaohongshu',
            'content_id': 'note_001',
            'title': 'AI 工具提升效率的 5 个技巧',
            'views': 2500,
            'likes': 180,
            'favorites': 95,
            'comments': 42,
            'shares': 28,
            'new_followers': 28
        },
        # 周二
        {
            'platform': 'xiaohongshu',
            'content_id': 'note_002',
            'title': '一人公司如何用 AI 自动化运营',
            'views': 3200,
            'likes': 256,
            'favorites': 142,
            'comments': 68,
            'shares': 45,
            'new_followers': 42
        },
        # 周三
        {
            'platform': 'zhihu',
            'content_id': 'article_001',
            'title': '深度解析：AI 时代的内容创作变革',
            'views': 5800,
            'likes': 420,
            'favorites': 285,
            'comments': 156,
            'shares': 98,
            'new_followers': 85
        },
        # 周四
        {
            'platform': 'weibo',
            'content_id': 'post_001',
            'title': 'AI 绘画工具对比测评',
            'views': 1800,
            'likes': 125,
            'favorites': 48,
            'comments': 32,
            'shares': 15,
            'new_followers': 12
        },
        # 周五
        {
            'platform': 'xiaohongshu',
            'content_id': 'note_003',
            'title': '我的 AI 工作流大公开',
            'views': 4200,
            'likes': 358,
            'favorites': 195,
            'comments': 92,
            'shares': 67,
            'new_followers': 58
        },
        # 周六
        {
            'platform': 'zhihu',
            'content_id': 'article_002',
            'title': '从 0 到 1：构建你的 AI 知识体系',
            'views': 6500,
            'likes': 512,
            'favorites': 368,
            'comments': 185,
            'shares': 125,
            'new_followers': 102
        },
        # 周日
        {
            'platform': 'xiaohongshu',
            'content_id': 'note_004',
            'title': '周末复盘：本周 AI 工具学习心得',
            'views': 2800,
            'likes': 198,
            'favorites': 88,
            'comments': 45,
            'shares': 32,
            'new_followers': 35
        }
    ]
    
    tracker = PerformanceTracker()
    await tracker.initialize()
    
    total_views = 0
    total_followers = 0
    total_engagement = 0
    
    for content in sample_contents:
        result = await track_content_performance(
            platform=content['platform'],
            content_id=content['content_id'],
            title=content['title'],
            views=content['views'],
            likes=content['likes'],
            favorites=content['favorites'],
            comments=content['comments'],
            shares=content['shares'],
            new_followers=content['new_followers']
        )
        
        total_views += content['views']
        total_followers += content['new_followers']
        total_engagement += content['likes'] + content['favorites'] + content['comments'] + content['shares']
        
        print(f"  ✓ {content['platform']}/{content['content_id']}: "
              f"{content['views']} views, "
              f"{result['metrics']['engagement_rate']}% engagement")
    
    await tracker.close()
    
    # Step 2: 执行周度进化分析
    print("\n📈 Step 2: 执行周度进化分析...")
    
    # 使用真实数据
    mock_data = {
        'period': f"{(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}",
        'total_views': total_views,
        'total_followers': total_followers,
        'total_engagement': total_engagement,
        'content_count': len(sample_contents),
        'platforms': {
            'xiaohongshu': {'views': 12700, 'engagement': 1856},
            'zhihu': {'views': 12300, 'engagement': 2649},
            'weibo': {'views': 1800, 'engagement': 220}
        }
    }
    
    evolution_result = await run_weekly_evolution()
    
    # Step 3: 生成可视化 HTML 报告
    print("\n🎨 Step 3: 生成可视化 HTML 报告...")
    
    html_path = generate_visualized_report(
        evolution_result,
        output_path=f"weekly_report_{datetime.now().strftime('%Y%m%d')}.html"
    )
    
    print(f"\n✅ HTML 报告已生成：{html_path}")
    print(f"   可用浏览器打开查看完整可视化效果")
    
    # Step 4: 打印摘要
    print("\n" + "=" * 60)
    print("📊 WEEKLY EVOLUTION SUMMARY")
    print("=" * 60)
    print(f"Period: {evolution_result.get('period')}")
    print(f"Evolution Score: {evolution_result.get('evolution_score')}/100")
    print(f"Total Contents: {len(sample_contents)}")
    print(f"Total Views: {total_views:,}")
    print(f"Total New Followers: {total_followers:,}")
    print(f"Total Engagement: {total_engagement:,}")
    
    print("\n🔍 Top 3 Insights:")
    for i, insight in enumerate(evolution_result.get('key_insights', [])[:3], 1):
        print(f"  {i}. {insight}")
    
    print("\n✅ Priority Actions:")
    for i, item in enumerate(evolution_result.get('action_items', [])[:3], 1):
        print(f"  {i}. {item}")
    
    print("\n" + "=" * 60)
    print("✅ 集成测试完成！")
    print("=" * 60)
    
    return {
        'tracked_contents': len(sample_contents),
        'total_views': total_views,
        'total_followers': total_followers,
        'evolution_score': evolution_result.get('evolution_score', 0),
        'report_path': html_path
    }


if __name__ == "__main__":
    result = asyncio.run(main())
    
    print("\n\n🎯 测试结果:")
    print(f"  - 追踪内容数：{result['tracked_contents']}")
    print(f"  - 总阅读量：{result['total_views']:,}")
    print(f"  - 总涨粉数：{result['total_followers']:,}")
    print(f"  - 进化得分：{result['evolution_score']}/100")
    print(f"  - 报告路径：{result['report_path']}")
