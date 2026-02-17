"""Test Xiaohongshu Researcher Skill."""

import asyncio
from open_notebook.skills.xiaohongshu_researcher import research_xiaohongshu


async def main():
    """Run a test research."""
    print("🔍 开始测试小红书研究助手...")
    print("-" * 60)
    
    # Test with default keyword
    result = await research_xiaohongshu(
        keywords=["一人公司"],
        max_results=5,  # Small sample for testing
        save_to_notebook=False  # Don't save for standalone test
    )
    
    print("\n✅ 研究完成！")
    print(f"📊 收集笔记数：{result['total_notes']}")
    print(f"💡 洞察发现:")
    for i, insight in enumerate(result["insights"], 1):
        print(f"   {i}. {insight}")
    
    print("-" * 60)
    return result


if __name__ == "__main__":
    asyncio.run(main())
