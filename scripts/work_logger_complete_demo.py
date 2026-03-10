"""Complete Work Logger Demo - 完整功能演示

展示 Work Logger Skill 的全部功能：
- A: 工作记录和复盘
- B: 定时任务调度
- C: 情绪追踪

Usage:
    uv run python scripts/work_logger_complete_demo.py
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from open_notebook.skills.work_logger import (
    WorkLoggerSkill,
    WorkLoggerScheduler,
    MoodTracker,
    MoodLevel,
    EnergyLevel,
    FocusLevel,
    ScheduleType,
)
from open_notebook.skills.base import SkillConfig, SkillContext


WORKSPACE = "~/.claude/work_logs"
PROJECT = "D:/Antigravity/opc/open-notebook"


async def demo_work_session():
    """演示工作会话记录"""
    print("\n" + "=" * 60)
    print("[A] 工作会话记录")
    print("=" * 60)

    # 开始会话
    config = SkillConfig(
        skill_type="work_logger",
        name="Demo Session",
        description="Demo work session",
        parameters={
            "workspace_path": WORKSPACE,
            "project_paths": [PROJECT],
            "current_action": "start_session",
            "session_title": f"Work Logger Complete Demo - {datetime.now().strftime('%H:%M')}",
            "session_type": "coding",
            "session_project": "open-notebook",
            "session_tags": ["demo", "work-logger"]
        }
    )

    skill = WorkLoggerSkill(config)
    result = await skill.run(SkillContext(
        skill_id=f"demo_{datetime.now().timestamp()}",
        trigger_type="manual"
    ))

    if result.success:
        print(f"[OK] Session started: {result.output.get('title')}")
        print(f"  Message: {result.output.get('message')}")
        return result.output.get("session_id")
    else:
        print(f"[ERR] Error: {result.error_message}")
        return None


async def demo_mood_tracking():
    """演示情绪追踪"""
    print("\n" + "=" * 60)
    print("[C] 情绪追踪")
    print("=" * 60)

    tracker = MoodTracker(WORKSPACE)

    # 记录情绪
    print("\nLogging mood entries...")

    moods = [
        (MoodLevel.GOOD, EnergyLevel.HIGH, FocusLevel.FOCUSED, 3, 8, "Starting the demo"),
        (MoodLevel.EXCELLENT, EnergyLevel.VERY_HIGH, FocusLevel.DEEP_FOCUS, 2, 9, "Everything working well!"),
    ]

    for mood, energy, focus, stress, sat, note in moods:
        entry = tracker.log_mood(
            mood=mood,
            energy=energy,
            focus=focus,
            stress=stress,
            satisfaction=sat,
            notes=note
        )
        print(f"  [OK] {entry.mood.value} | Energy: {entry.energy.value}/5 | Focus: {entry.focus.value}/5")

    # 获取洞察
    print("\nGenerating insights...")
    insights = tracker.get_weekly_insights()

    print(f"  Total entries: {len(tracker.get_entries(limit=10))}")
    print(f"  Avg Mood: {insights.avg_mood:.1f}/4")
    print(f"  Avg Energy: {insights.avg_energy:.1f}/5")
    print(f"  Avg Focus: {insights.avg_focus:.1f}/5")
    print(f"  Avg Stress: {insights.avg_stress:.1f}/10")

    if insights.recommendations:
        print(f"\n  Recommendations:")
        for rec in insights.recommendations:
            print(f"    - {rec}")


async def demo_scheduler():
    """演示定时任务调度"""
    print("\n" + "=" * 60)
    print("[B] 定时任务调度")
    print("=" * 60)

    scheduler = WorkLoggerScheduler(WORKSPACE)

    print("\nScheduled Tasks:")
    info = scheduler.get_schedule_info()

    for task in info["tasks"]:
        status = "[待触发]" if task["due"] else "[等待中]"
        next_run = task.get("next_run", "N/A")
        if next_run and next_run != "N/A":
            next_run = next_run[:16].replace("T", " ")
        print(f"  {status} {task['task_id']}")
        print(f"         Type: {task['task_type']}")
        print(f"         Schedule: {task['schedule']}")
        print(f"         Next: {next_run}")
        print()

    # 注册回调演示
    print("Registering callbacks...")

    def on_daily():
        print("  [CALLBACK] Daily review time!")

    def on_mood():
        print("  [CALLBACK] Mood check time!")

    scheduler.on_daily_review(on_daily)
    scheduler.on_mood_check(on_mood)

    print(f"  Daily callbacks: {len(scheduler._callbacks[ScheduleType.DAILY_REVIEW])}")
    print(f"  Mood callbacks: {len(scheduler._callbacks[ScheduleType.MOOD_CHECK])}")
    print(f"\nScheduler ready to run (use --run to start daemon)")


async def demo_daily_summary():
    """演示日报"""
    print("\n" + "=" * 60)
    print("[A] 工作日报")
    print("=" * 60)

    config = SkillConfig(
        skill_type="work_logger",
        name="Daily Summary",
        description="Get daily summary",
        parameters={
            "workspace_path": WORKSPACE,
            "current_action": "get_daily"
        }
    )

    skill = WorkLoggerSkill(config)
    result = await skill.run(SkillContext(
        skill_id=f"daily_{datetime.now().timestamp()}",
        trigger_type="manual"
    ))

    if result.success:
        print(result.output.get("formatted"))


async def main():
    """主函数"""
    print("=" * 60)
    print("Work Logger Skill - Complete Demo")
    print("=" * 60)
    print(f"Workspace: {WORKSPACE}")
    print(f"Project: {PROJECT}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 运行所有演示
    session_id = await demo_work_session()
    await demo_mood_tracking()
    await demo_scheduler()
    await demo_daily_summary()

    # 结束会话
    if session_id:
        print("\n" + "=" * 60)
        print("Ending session...")
        print("=" * 60)

        config = SkillConfig(
            skill_type="work_logger",
            name="End Session",
            description="End demo session",
            parameters={
                "workspace_path": WORKSPACE,
                "project_paths": [PROJECT],
                "current_action": "end_session"
            }
        )

        skill = WorkLoggerSkill(config)
        result = await skill.run(SkillContext(
            skill_id=f"end_{datetime.now().timestamp()}",
            trigger_type="manual"
        ))

        if result.success:
            print(f"[OK] {result.output.get('message')}")

    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)
    print("\nFiles saved to:")
    print(f"  {Path(WORKSPACE).expanduser()}")
    print("\nNext steps:")
    print("  1. Start scheduler daemon: --run")
    print("  2. Check mood report: mood-report")
    print("  3. Export daily: export_daily")


if __name__ == "__main__":
    asyncio.run(main())
