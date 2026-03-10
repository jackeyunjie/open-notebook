"""Test Work Logger Scheduler

测试定时任务调度器，验证任务触发和记录保存。
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from open_notebook.skills.work_logger import WorkLoggerScheduler, ScheduleType


async def test_scheduler():
    """测试调度器"""
    scheduler = WorkLoggerScheduler("~/.claude/work_logs")

    print("=" * 60)
    print("Work Logger Scheduler 测试")
    print("=" * 60)

    # 初始状态
    info = scheduler.get_schedule_info()
    print(f"\n[初始状态]")
    print(f"运行中: {info['running']}")
    print(f"任务数: {len(info['tasks'])}")

    # 注册测试回调
    triggered_tasks = []

    def on_task_trigger(task_type):
        def callback():
            triggered_tasks.append({
                'type': task_type,
                'time': datetime.now().isoformat()
            })
            print(f"\n[触发] {task_type} at {datetime.now().strftime('%H:%M:%S')}")
        return callback

    scheduler.on(ScheduleType.DAILY_REVIEW, on_task_trigger("daily_review"))
    scheduler.on(ScheduleType.MOOD_CHECK, on_task_trigger("mood_check"))
    scheduler.on(ScheduleType.WEEKLY_REVIEW, on_task_trigger("weekly_review"))

    print("\n[回调注册]")
    for st in ScheduleType:
        count = len(scheduler._callbacks.get(st, []))
        print(f"  {st.value}: {count} 个回调")

    # 模拟调度检查（不启动后台循环，手动检查）
    print("\n[手动触发检查]")
    scheduler._check_and_trigger()

    # 保存配置
    scheduler._save_config()
    print("\n[配置已保存]")
    print(f"配置文件: {scheduler.scheduler_file}")

    # 检查是否有任务被触发
    if triggered_tasks:
        print(f"\n[本次触发任务] {len(triggered_tasks)} 个")
        for task in triggered_tasks:
            print(f"  - {task['type']} @ {task['time']}")
    else:
        print("\n[本次无任务触发] (未到预定时间)")

    # 显示下次运行时间
    print("\n[下次运行时间]")
    for task in scheduler.tasks.values():
        if task.next_run:
            print(f"  {task.task_id}: {task.next_run.strftime('%Y-%m-%d %H:%M')}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

    return scheduler


async def start_scheduler_for(seconds: int = 10):
    """启动调度器运行指定秒数"""
    scheduler = WorkLoggerScheduler("~/.claude/work_logs")

    # 注册回调
    def make_callback(name):
        def callback():
            print(f"\n>>> [触发] {name} @ {datetime.now().strftime('%H:%M:%S')}")
            # 保存触发记录
            log_file = Path("~/.claude/work_logs/scheduler_log.txt").expanduser()
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()} - {name}\n")
        return callback

    scheduler.on_daily_review(make_callback("daily_review"))
    scheduler.on_mood_check(make_callback("mood_check"))
    scheduler.on_weekly_review(make_callback("weekly_review"))
    scheduler.on_monthly_review(make_callback("monthly_review"))

    print(f"\n启动调度器，运行 {seconds} 秒...")
    print("按 Ctrl+C 提前停止\n")

    # 启动调度器
    task = asyncio.create_task(scheduler.start())

    try:
        await asyncio.sleep(seconds)
    except asyncio.CancelledError:
        pass
    finally:
        await scheduler.stop()
        print("\n调度器已停止")

    # 检查日志
    log_file = Path("~/.claude/work_logs/scheduler_log.txt").expanduser()
    if log_file.exists():
        print(f"\n调度日志 ({log_file}):")
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if lines:
                for line in lines[-10:]:  # 显示最近10条
                    print(f"  {line.strip()}")
            else:
                print("  (暂无记录)")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test Work Logger Scheduler")
    parser.add_argument("--run", type=int, metavar="SECONDS",
                        help="启动调度器运行指定秒数")

    args = parser.parse_args()

    if args.run:
        asyncio.run(start_scheduler_for(args.run))
    else:
        asyncio.run(test_scheduler())
