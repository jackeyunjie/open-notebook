"""Test G, F, H Features - Goal Management, AI Insights, Export

Tests:
- G: Goal tracking, OKR, Weekly planning
- F: AI insights, Pattern analysis, Recommendations
- H: Export to Markdown, JSON, Email preparation
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from open_notebook.skills.work_logger import (
    GoalTracker,
    GoalType,
    GoalStatus,
    AIInsightsEngine,
    ExportManager,
)


WORKSPACE = "~/.claude/work_logs"


async def test_goal_management():
    """测试目标管理 (G)"""
    print("\n" + "=" * 60)
    print("[G] Goal Management Test")
    print("=" * 60)

    tracker = GoalTracker(WORKSPACE)

    # 创建周目标
    print("\nCreating weekly goals...")
    goal1 = tracker.create_weekly_goal(
        title="Implement Work Logger Features",
        description="Complete G, F, H modules for work logger",
        week_id="2026-10"
    )
    print(f"  Created: {goal1.title} ({goal1.goal_id[:8]})")

    goal2 = tracker.create_weekly_goal(
        title="Test All Modules",
        description="Write tests for goal, insights, export",
        week_id="2026-10"
    )
    print(f"  Created: {goal2.title} ({goal2.goal_id[:8]})")

    # 更新进度
    print("\nUpdating progress...")
    tracker.update_progress(goal1.goal_id, 75)
    tracker.update_progress(goal2.goal_id, 100)
    print(f"  Goal 1: 75%")
    print(f"  Goal 2: 100%")

    # 创建OKR
    print("\nCreating OKR...")
    okr_goals = tracker.create_okr(
        objective="Build Complete Work Logger System",
        key_results=[
            "Implement core features (A, B, C)",
            "Add goal management (G)",
            "Add AI insights (F)",
            "Add export capabilities (H)",
        ],
        quarter="2026-Q1"
    )
    print(f"  Objective: {okr_goals[0].title}")
    print(f"  Key Results: {len(okr_goals) - 1}")

    # 获取进度报告
    print("\nGenerating progress report...")
    progress = tracker.get_goal_progress()
    print(f"  Total Goals: {progress.total_goals}")
    print(f"  Completed: {progress.completed_goals}")
    print(f"  In Progress: {progress.in_progress_goals}")
    print(f"  Overall Progress: {progress.overall_progress:.1f}%")
    print(f"  Trend: {progress.trend}")

    # 生成周报
    print("\nWeekly Report Preview:")
    report = tracker.get_weekly_report("2026-10")
    print(report[:500] + "...")


async def test_ai_insights():
    """测试AI洞察 (F)"""
    print("\n" + "=" * 60)
    print("[F] AI Insights Test")
    print("=" * 60)

    engine = AIInsightsEngine(WORKSPACE)

    # 分析工作模式
    print("\nAnalyzing work patterns...")
    patterns = engine.analyze_work_patterns(days=7)
    print(f"  Found {len(patterns)} patterns:")
    for pattern in patterns:
        print(f"    - {pattern.pattern_type}: {pattern.description[:60]}...")

    # 获取效率洞察
    print("\nGetting efficiency insights...")
    insights = engine.get_efficiency_insights(days=7)
    for insight in insights:
        print(f"  {insight.category}: {insight.score}/100")
        if insight.bottlenecks:
            print(f"    Bottleneck: {insight.bottlenecks[0]}")

    # 生成建议
    print("\nGenerating recommendations...")
    recommendations = engine.generate_recommendations()
    for rec in recommendations[:3]:
        print(f"  [{rec['priority'].upper()}] {rec['title']}")
        print(f"    Action: {rec['action'][:50]}...")

    # 获取生产力指标
    print("\nProductivity Metrics:")
    metrics = engine.get_productivity_metrics(days=7)
    print(f"  Sessions: {metrics.total_sessions}")
    print(f"  Total Time: {metrics.total_duration_hours:.1f} hours")
    print(f"  Best Day: {metrics.most_productive_day or 'N/A'}")
    print(f"  Best Hour: {metrics.most_productive_hour or 'N/A'}")
    print(f"  Consistency: {metrics.consistency_score:.0f}%")
    print(f"  Trend: {metrics.velocity_trend}")


async def test_export():
    """测试导出功能 (H)"""
    print("\n" + "=" * 60)
    print("[H] Export Test")
    print("=" * 60)

    manager = ExportManager(WORKSPACE)

    # 导出Markdown日报
    print("\nExporting daily markdown...")
    md_report = manager.export_daily_markdown()
    print(f"  Exported {len(md_report)} characters")

    # 导出Markdown周报
    print("\nExporting weekly markdown...")
    weekly_md = manager.export_weekly_markdown()
    print(f"  Exported {len(weekly_md)} characters")

    # 导出JSON
    print("\nExporting JSON data...")
    json_data = manager.export_json(days=7)
    print(f"  Sessions: {json_data['summary']['total_sessions']}")
    print(f"  Mood Entries: {json_data['summary']['mood_entries']}")

    # 准备第三方平台导出
    print("\nPreparing third-party exports...")
    notion_data = manager.prepare_notion_export(days=7)
    print(f"  Notion: {len(notion_data['children'])} blocks prepared")

    feishu_data = manager.prepare_feishu_export(days=7)
    print(f"  Feishu: Content prepared")

    # 列出导出文件
    exports_dir = Path(WORKSPACE).expanduser() / "exports"
    if exports_dir.exists():
        files = list(exports_dir.glob("*"))
        print(f"\nExported files ({len(files)}):")
        for f in files[-5:]:
            print(f"  - {f.name} ({f.stat().st_size} bytes)")


async def main():
    """主函数"""
    print("=" * 60)
    print("Work Logger - G/F/H Features Test")
    print("=" * 60)
    print(f"Workspace: {WORKSPACE}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        await test_goal_management()
    except Exception as e:
        print(f"\n[G] Error: {e}")

    try:
        await test_ai_insights()
    except Exception as e:
        print(f"\n[F] Error: {e}")

    try:
        await test_export()
    except Exception as e:
        print(f"\n[H] Error: {e}")

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
