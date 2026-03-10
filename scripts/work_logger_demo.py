"""Work Logger Skill Demo Script

演示如何使用 Work Logger Skill 进行工作记录和复盘。

Usage:
    uv run python scripts/work_logger_demo.py [action]

Actions:
    start       - 开始一个新的工作会话
    end         - 结束当前工作会话
    daily       - 获取今日工作摘要
    review      - 生成每日复盘提示
    weekly      - 获取本周工作统计
    check       - 检查待复盘事项
    mood        - 情绪检查
    mood-report - 生成情绪报告
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from open_notebook.skills.work_logger import (
    WorkLoggerSkill,
    MoodTracker,
    MoodLevel,
    EnergyLevel,
    FocusLevel,
)
from open_notebook.skills.base import SkillConfig, SkillContext


WORKSPACE_PATH = "~/.claude/work_logs"
PROJECT_PATHS = ["D:/Antigravity/opc/open-notebook"]


async def start_session():
    """开始工作会话"""
    config = SkillConfig(
        skill_type="work_logger",
        name="Daily Logger",
        description="Start a new work session",
        parameters={
            "workspace_path": WORKSPACE_PATH,
            "project_paths": PROJECT_PATHS,
            "current_action": "start_session",
            "session_title": f"开发工作 - {datetime.now().strftime('%H:%M')}",
            "session_type": "coding",
            "session_project": "open-notebook",
            "session_tags": ["skill-development", "python"]
        }
    )

    skill = WorkLoggerSkill(config)
    ctx = SkillContext(
        skill_id=f"demo_{datetime.now().timestamp()}",
        trigger_type="manual"
    )

    result = await skill.run(ctx)

    if result.success:
        print("=" * 50)
        print("工作会话已开始")
        print("=" * 50)
        print(result.output.get("message"))
        print(f"\n会话ID: {result.output.get('session_id')}")
    else:
        print(f"错误: {result.error_message}")


async def end_session():
    """结束工作会话"""
    config = SkillConfig(
        skill_type="work_logger",
        name="Daily Logger",
        description="End current work session",
        parameters={
            "workspace_path": WORKSPACE_PATH,
            "project_paths": PROJECT_PATHS,
            "current_action": "end_session"
        }
    )

    skill = WorkLoggerSkill(config)
    ctx = SkillContext(
        skill_id=f"demo_{datetime.now().timestamp()}",
        trigger_type="manual"
    )

    result = await skill.run(ctx)

    if result.success:
        print("=" * 50)
        print("工作会话已结束")
        print("=" * 50)
        print(result.output.get("message"))
    else:
        print(f"错误: {result.error_message}")


async def get_daily_summary():
    """获取今日工作摘要"""
    config = SkillConfig(
        skill_type="work_logger",
        name="Daily Summary",
        description="Get today's work summary",
        parameters={
            "workspace_path": WORKSPACE_PATH,
            "current_action": "get_daily"
        }
    )

    skill = WorkLoggerSkill(config)
    ctx = SkillContext(
        skill_id=f"demo_{datetime.now().timestamp()}",
        trigger_type="manual"
    )

    result = await skill.run(ctx)

    if result.success:
        print("=" * 50)
        print("今日工作摘要")
        print("=" * 50)
        print(result.output.get("formatted"))
    else:
        print(f"错误: {result.error_message}")


async def generate_daily_review():
    """生成每日复盘"""
    config = SkillConfig(
        skill_type="work_logger",
        name="Daily Review",
        description="Generate daily review prompt",
        parameters={
            "workspace_path": WORKSPACE_PATH,
            "current_action": "review_daily"
        }
    )

    skill = WorkLoggerSkill(config)
    ctx = SkillContext(
        skill_id=f"demo_{datetime.now().timestamp()}",
        trigger_type="manual"
    )

    result = await skill.run(ctx)

    if result.success:
        print("=" * 50)
        print("每日复盘")
        print("=" * 50)
        print(result.output.get("prompt"))
        print("\n" + "=" * 50)
        print("使用建议:")
        print("=" * 50)
        print("1. 复制上述问题到对话中")
        print("2. 逐条回答每个问题")
        print("3. 系统会自动整理成结构化日志")
    else:
        print(f"错误: {result.error_message}")


async def get_weekly_summary():
    """获取本周工作统计"""
    config = SkillConfig(
        skill_type="work_logger",
        name="Weekly Summary",
        description="Get weekly work summary",
        parameters={
            "workspace_path": WORKSPACE_PATH,
            "current_action": "get_weekly"
        }
    )

    skill = WorkLoggerSkill(config)
    ctx = SkillContext(
        skill_id=f"demo_{datetime.now().timestamp()}",
        trigger_type="manual"
    )

    result = await skill.run(ctx)

    if result.success:
        print("=" * 50)
        print("本周工作统计")
        print("=" * 50)
        print(result.output.get("message"))
        print(f"\n记录天数: {result.output.get('days_tracked')}")
        print(f"总会话数: {result.output.get('total_sessions')}")
        print(f"Git提交: {result.output.get('total_commits')}")
    else:
        print(f"错误: {result.error_message}")


async def check_pending_reviews():
    """检查待复盘事项"""
    config = SkillConfig(
        skill_type="work_logger",
        name="Review Checker",
        description="Check pending reviews",
        parameters={
            "workspace_path": WORKSPACE_PATH,
            "current_action": "check_reviews"
        }
    )

    skill = WorkLoggerSkill(config)
    ctx = SkillContext(
        skill_id=f"demo_{datetime.now().timestamp()}",
        trigger_type="manual"
    )

    result = await skill.run(ctx)

    if result.success:
        print("=" * 50)
        print("复盘状态检查")
        print("=" * 50)
        print(result.output.get("message"))

        review_info = result.output.get("review_info", {})
        print("\n详细状态:")
        for review_type, info in review_info.items():
            status = "待复盘" if info["due"] else "已完成"
            print(f"  {review_type}: {status}")
    else:
        print(f"错误: {result.error_message}")


async def mood_check():
    """情绪检查"""
    tracker = MoodTracker(WORKSPACE_PATH)
    check_in = tracker.quick_check_in()

    print("=" * 50)
    print("情绪检查")
    print("=" * 50)
    print(check_in["message"])
    print()

    for prompt in check_in["prompts"]:
        if "options" in prompt:
            print(f"\n{prompt['question']}")
            for i, opt in enumerate(prompt["options"], 1):
                print(f"  {i}. {opt}")
        else:
            print(f"\n{prompt['question']} ({prompt['min']}-{prompt['max']})")


async def mood_report():
    """生成情绪报告"""
    tracker = MoodTracker(WORKSPACE_PATH)
    report = tracker.generate_mood_report(days=7)

    print("=" * 50)
    print("情绪报告")
    print("=" * 50)
    print(report)


def show_help():
    """显示帮助信息"""
    print(__doc__)


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        show_help()
        return

    action = sys.argv[1].lower()

    actions = {
        "start": start_session,
        "end": end_session,
        "daily": get_daily_summary,
        "review": generate_daily_review,
        "weekly": get_weekly_summary,
        "check": check_pending_reviews,
        "mood": mood_check,
        "mood-report": mood_report,
        "help": show_help,
    }

    if action in actions:
        if asyncio.iscoroutinefunction(actions[action]):
            await actions[action]()
        else:
            actions[action]()
    else:
        print(f"未知操作: {action}")
        print(f"可用操作: {', '.join(actions.keys())}")


if __name__ == "__main__":
    asyncio.run(main())
