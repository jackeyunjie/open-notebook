"""Test Scheduler Trigger - 模拟任务触发

通过临时修改任务时间为当前时间来测试触发机制。
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path

from open_notebook.skills.work_logger.task_scheduler import WorkLoggerScheduler, ScheduleType


async def test_trigger():
    """测试任务触发"""
    workspace = Path("~/.claude/work_logs").expanduser()
    scheduler = WorkLoggerScheduler(str(workspace))

    print("=" * 60)
    print("Scheduler Trigger Test")
    print("=" * 60)

    # 创建一个即将触发的任务（1秒后）
    now = datetime.now()
    test_task_id = "test_immediate_task"

    # 手动添加测试任务
    from open_notebook.skills.work_logger.task_scheduler import ScheduledTask

    # 创建一个将在2秒后触发的任务
    future_time = now + timedelta(seconds=2)
    test_task = ScheduledTask(
        task_id=test_task_id,
        task_type=ScheduleType.MOOD_CHECK,
        schedule=f"{future_time.hour}:{future_time.minute:02d}",
        enabled=True,
        last_run=None,
        next_run=future_time,  # 2秒后触发
    )
    scheduler.tasks[test_task_id] = test_task

    triggered = []

    def on_trigger():
        triggered.append({
            'time': datetime.now().isoformat(),
            'task': test_task_id
        })
        print(f">>> [CALLBACK TRIGGERED] at {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
        print(f"    Task: {test_task_id}")

    scheduler.on_mood_check(on_trigger)

    print(f"\n[Setup]")
    print(f"Test task scheduled: {test_task.schedule}")
    print(f"Next run: {test_task.next_run}")
    print(f"Current time: {now}")

    # 等待任务过期
    wait_seconds = 3
    print(f"\n[Waiting {wait_seconds}s for task to become due...]")
    await asyncio.sleep(wait_seconds)

    # 手动检查触发
    print(f"\n[Triggering check...]")
    scheduler._check_and_trigger()

    # 检查结果
    print(f"\n[Result]")
    if triggered:
        print(f"Triggered: {len(triggered)} times")
        for t in triggered:
            print(f"  - {t['task']} @ {t['time']}")
    else:
        print("No triggers (task may have been run before)")

    # 显示更新后的配置
    print(f"\n[Updated Config]")
    print(f"Last run: {scheduler.tasks[test_task_id].last_run}")
    print(f"Next run: {scheduler.tasks[test_task_id].next_run}")

    # 清理测试任务
    del scheduler.tasks[test_task_id]
    scheduler._save_config()

    print("\n" + "=" * 60)
    print("Test completed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_trigger())
