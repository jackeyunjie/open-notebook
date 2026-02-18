#!/usr/bin/env python3
"""Test script for Weekly Evolution Scheduler."""

import asyncio
from open_notebook.skills.weekly_evolution_scheduler import run_weekly_evolution


async def main():
    print("=" * 60)
    print("🚀 Testing Weekly Evolution Scheduler")
    print("=" * 60)
    
    # Mock data for testing
    mock_data = {
        'period': '2024-02-12 to 2024-02-18',
        'total_views': 15000,
        'total_followers': 230,
        'total_engagement': 890,
        'content_count': 7,
        'platforms': {
            'xiaohongshu': {'views': 8000, 'engagement': 450},
            'zhihu': {'views': 5000, 'engagement': 320},
            'weibo': {'views': 2000, 'engagement': 120}
        }
    }
    
    print("\n📊 Running weekly evolution with mock data...")
    result = await run_weekly_evolution()
    
    print("\n" + "=" * 60)
    print("📈 WEEKLY EVOLUTION SUMMARY")
    print("=" * 60)
    print(f"✅ Period: {result.get('period', 'N/A')}")
    print(f"🎯 Evolution Score: {result.get('evolution_score', 0)}/100")
    print(f"💡 Key Insights: {len(result.get('key_insights', []))} items")
    print(f"📝 Action Items: {len(result.get('action_items', []))} items")
    
    print("\n🔍 Top 3 Insights:")
    for i, insight in enumerate(result.get('key_insights', [])[:3], 1):
        print(f"  {i}. {insight}")
    
    print("\n✅ Priority Actions:")
    for i, item in enumerate(result.get('action_items', [])[:3], 1):
        print(f"  {i}. {item}")
    
    print("\n" + "=" * 60)
    print("✅ Test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
