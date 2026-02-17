"""Test Multi-Platform AI Tools Researcher."""

import asyncio
from open_notebook.skills.multi_platform_ai_researcher import research_ai_tools


async def main():
    """Run test research."""
    print("=" * 60)
    print("🤖 跨平台 AI 工具集研究助手 - 测试")
    print("=" * 60)
    
    # Run research
    result = await research_ai_tools(
        platforms=['xiaohongshu'],  # Start with Xiaohongshu only
        keywords=[
            '一人公司 AI 工具',
            'solo 创业 AI',
            'AI 效率工具'
        ],
        max_results=5,  # Small sample for testing
        generate_report=True,
        save_to_notebook=False  # Don't save for test
    )
    
    print("\n✅ 研究完成！")
    print(f"📊 采集总数：{result['total_collected']} 条")
    print(f"🎯 AI 工具相关：{result['ai_tools_related']} 条")
    print(f"📱 覆盖平台：{', '.join(result['platforms_searched'])}")
    print(f"📝 报告生成：{'是' if result['report_generated'] else '否'}")
    
    if result.get('report'):
        report = result['report']
        print("\n📋 今日概览:")
        summary = report['summary']
        print(f"   - 内容总数：{summary.get('total_items', 0)} 条")
        print(f"   - 总互动量：{summary.get('total_engagement', 0)}")
        
        print("\n🔥 热门 AI 工具:")
        for i, tool in enumerate(report['trending_tools'][:5], 1):
            print(f"   {i}. {tool['tool_name']} ({tool['mention_count']}次)")
        
        print("\n💡 核心洞察:")
        for insight in report['insights'][:3]:
            print(f"   • {insight}")
    
    print("\n" + "=" * 60)
    return result


if __name__ == "__main__":
    asyncio.run(main())
