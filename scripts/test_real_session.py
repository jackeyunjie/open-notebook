"""Test Work Logger with Real Session

Complete workflow test for Work Logger Skill v2.0
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from open_notebook.skills.work_logger import (
    WorkLoggerSkill,
    MoodTracker,
    MoodLevel,
    EnergyLevel,
    FocusLevel,
    GoalTracker,
    GoalType,
    AIInsightsEngine,
    ExportManager,
)
from open_notebook.skills.base import SkillConfig, SkillContext


WORKSPACE = "~/.claude/work_logs"
PROJECT = "D:/Antigravity/opc/open-notebook"


async def start_session():
    """Step 1: Start a work session"""
    print("\n[Step 1] Starting Work Session")
    print("-" * 50)

    config = SkillConfig(
        skill_type="work_logger",
        name="Real Session Test",
        description="Real work session for testing",
        parameters={
            "workspace_path": WORKSPACE,
            "project_paths": [PROJECT],
            "current_action": "start_session",
            "session_title": "Implementing Work Logger Features",
            "session_type": "coding",
            "session_project": "open-notebook",
            "session_tags": ["testing", "work-logger", "v2"]
        }
    )

    skill = WorkLoggerSkill(config)
    result = await skill.run(SkillContext(
        skill_id=f"real_{datetime.now().timestamp()}",
        trigger_type="manual"
    ))

    if result.success:
        print(f"Session started: {result.output.get('session_id', 'N/A')[:25]}...")
        print(f"Recent commits: {result.output.get('recent_commits', 0)}")
        print(f"Recent files: {result.output.get('recent_files', 0)}")
        return result.output.get("session_id")
    else:
        print(f"Error: {result.error_message}")
        return None


async def log_mood():
    """Step 2: Log current mood"""
    print("\n[Step 2] Logging Mood")
    print("-" * 50)

    tracker = MoodTracker(WORKSPACE)
    entry = tracker.log_mood(
        mood=MoodLevel.GOOD,
        energy=EnergyLevel.HIGH,
        focus=FocusLevel.FOCUSED,
        stress=3,
        satisfaction=8,
        notes="Feeling productive, ready to test the work logger"
    )

    print(f"Mood: {entry.mood.value}")
    print(f"Energy: {entry.energy.value}/5")
    print(f"Focus: {entry.focus.value}/5")
    print(f"Stress: {entry.stress}/10")
    print(f"Satisfaction: {entry.satisfaction}/10")


async def create_goal():
    """Step 3: Create a goal"""
    print("\n[Step 3] Creating Goal")
    print("-" * 50)

    tracker = GoalTracker(WORKSPACE)

    # Create weekly goal
    goal = tracker.create_weekly_goal(
        title="Complete Work Logger Testing",
        description="Test all features of Work Logger Skill v2.0",
        week_id=datetime.now().strftime("%Y-%W")
    )

    print(f"Goal created: {goal.title}")
    print(f"Goal ID: {goal.goal_id[:30]}...")

    # Update progress
    tracker.update_progress(goal.goal_id, 50)
    print("Progress updated to 50%")

    return goal.goal_id


async def get_ai_insights():
    """Step 4: Get AI insights"""
    print("\n[Step 4] AI Insights")
    print("-" * 50)

    engine = AIInsightsEngine(WORKSPACE)

    # Get productivity metrics
    metrics = engine.get_productivity_metrics(days=7)
    print(f"Total Sessions (7 days): {metrics.total_sessions}")
    print(f"Total Time: {metrics.total_duration_hours:.1f} hours")
    print(f"Best Day: {metrics.most_productive_day or 'N/A'}")
    print(f"Best Hour: {f'{metrics.most_productive_hour:02d}:00' if metrics.most_productive_hour is not None else 'N/A'}")
    print(f"Consistency: {metrics.consistency_score:.0f}%")
    print(f"Trend: {metrics.velocity_trend}")

    # Get patterns
    patterns = engine.analyze_work_patterns(days=7)
    print(f"\nIdentified Patterns: {len(patterns)}")
    for p in patterns:
        print(f"  - {p.pattern_type}: {p.description[:50]}...")


async def export_data():
    """Step 5: Export data"""
    print("\n[Step 5] Export Data")
    print("-" * 50)

    manager = ExportManager(WORKSPACE)

    # Export daily markdown
    md_content = manager.export_daily_markdown()
    print(f"Daily Markdown: {len(md_content)} characters")

    # Export JSON
    json_data = manager.export_json(days=7)
    print(f"JSON Export: {json_data['summary']['total_sessions']} sessions, {json_data['summary']['mood_entries']} mood entries")

    # List exported files
    exports_dir = Path(WORKSPACE).expanduser() / "exports"
    if exports_dir.exists():
        files = list(exports_dir.glob("*"))
        print(f"\nExported files ({len(files)}):")
        for f in files[-5:]:
            print(f"  - {f.name}")


async def end_session():
    """Step 6: End the session"""
    print("\n[Step 6] Ending Session")
    print("-" * 50)

    config = SkillConfig(
        skill_type="work_logger",
        name="End Session",
        description="End the test session",
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
        print(f"Session ended")
        print(f"Duration: {result.output.get('duration_minutes', 0):.0f} minutes")
        print(f"Total commits: {result.output.get('total_commits', 0)}")
    else:
        print(f"Error: {result.error_message}")


async def show_summary():
    """Show final summary"""
    print("\n[Final Summary]")
    print("=" * 50)

    # Check workspace
    workspace = Path(WORKSPACE).expanduser()

    stats = {
        "sessions": len(list((workspace / "sessions").rglob("*.json"))),
        "mood_entries": len(json.loads((workspace / "mood" / "2026-03.json").read_text()).get("entries", [])),
        "goals": sum(len(json.loads(f.read_text()).get("goals", [])) for f in (workspace / "goals").glob("*.json") if f.exists()),
        "exports": len(list((workspace / "exports").glob("*"))),
    }

    print(f"Total Sessions: {stats['sessions']}")
    print(f"Mood Entries: {stats['mood_entries']}")
    print(f"Goals: {stats['goals']}")
    print(f"Exported Files: {stats['exports']}")

    print("\nData saved to:", WORKSPACE)


async def main():
    """Main test flow"""
    print("=" * 50)
    print("Work Logger v2.0 - Real Session Test")
    print("=" * 50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Run all steps
    await start_session()
    await log_mood()
    await create_goal()
    await get_ai_insights()
    await export_data()
    await end_session()
    await show_summary()

    print("\n" + "=" * 50)
    print("Test completed successfully!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
