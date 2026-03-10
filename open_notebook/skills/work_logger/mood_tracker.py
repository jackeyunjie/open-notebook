"""Mood Tracker - Emotional state tracking for work sessions.

Provides mood logging, energy level tracking, and correlation
analysis with productivity metrics.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any

from loguru import logger


class MoodLevel(str, Enum):
    """Mood levels."""
    EXCELLENT = "excellent"  # Very positive, energetic
    GOOD = "good"           # Positive, satisfied
    NEUTRAL = "neutral"     # Balanced, okay
    TIRED = "tired"         # Low energy, struggling
    STRESSED = "stressed"   # Anxious, overwhelmed


class EnergyLevel(int, Enum):
    """Energy levels (1-5)."""
    VERY_LOW = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    VERY_HIGH = 5


class FocusLevel(int, Enum):
    """Focus/concentration levels (1-5)."""
    DISTRACTED = 1
    UNFOCUSED = 2
    MODERATE = 3
    FOCUSED = 4
    DEEP_FOCUS = 5


@dataclass
class MoodEntry:
    """A mood tracking entry."""
    entry_id: str
    timestamp: datetime
    mood: MoodLevel
    energy: EnergyLevel
    focus: FocusLevel
    stress: int  # 1-10 scale
    satisfaction: int  # 1-10 scale
    notes: str = ""
    session_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "mood": self.mood.value,
            "energy": self.energy.value,
            "focus": self.focus.value,
            "stress": self.stress,
            "satisfaction": self.satisfaction,
            "notes": self.notes,
            "session_id": self.session_id,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "MoodEntry":
        return cls(
            entry_id=data["entry_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            mood=MoodLevel(data["mood"]),
            energy=EnergyLevel(data["energy"]),
            focus=FocusLevel(data["focus"]),
            stress=data["stress"],
            satisfaction=data["satisfaction"],
            notes=data.get("notes", ""),
            session_id=data.get("session_id"),
            tags=data.get("tags", []),
        )


@dataclass
class MoodInsights:
    """Insights from mood tracking data."""
    period: str
    avg_mood: float
    avg_energy: float
    avg_focus: float
    avg_stress: float
    avg_satisfaction: float
    mood_distribution: Dict[str, int]
    best_time_of_day: Optional[str]
    productivity_correlation: float
    recommendations: List[str]


class MoodTracker:
    """Mood tracking system for work sessions.

    Tracks emotional state, energy, focus, and stress levels.
    Provides insights and correlations with productivity.

    Usage:
        tracker = MoodTracker(workspace_path="~/.work_logs")

        # Log mood
        tracker.log_mood(
            mood=MoodLevel.GOOD,
            energy=EnergyLevel.HIGH,
            focus=FocusLevel.FOCUSED,
            stress=3,
            satisfaction=8,
            notes="Feeling productive today"
        )

        # Get insights
        insights = tracker.get_weekly_insights()
    """

    def __init__(self, workspace_path: str):
        """Initialize mood tracker.

        Args:
            workspace_path: Path to work logger workspace
        """
        self.workspace_path = Path(workspace_path).expanduser()
        self.mood_dir = self.workspace_path / "mood"
        self.mood_dir.mkdir(parents=True, exist_ok=True)

    def _get_mood_file(self, date: datetime) -> Path:
        """Get mood file for a specific date."""
        return self.mood_dir / f"{date.strftime('%Y-%m')}.json"

    def log_mood(
        self,
        mood: MoodLevel,
        energy: EnergyLevel,
        focus: FocusLevel,
        stress: int,
        satisfaction: int,
        notes: str = "",
        session_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> MoodEntry:
        """Log a mood entry.

        Args:
            mood: Overall mood level
            energy: Energy level
            focus: Focus level
            stress: Stress level (1-10)
            satisfaction: Satisfaction level (1-10)
            notes: Optional notes
            session_id: Associated work session
            tags: Optional tags

        Returns:
            Created mood entry
        """
        entry = MoodEntry(
            entry_id=f"mood_{datetime.now().timestamp()}",
            timestamp=datetime.now(),
            mood=mood,
            energy=energy,
            focus=focus,
            stress=max(1, min(10, stress)),
            satisfaction=max(1, min(10, satisfaction)),
            notes=notes,
            session_id=session_id,
            tags=tags or [],
        )

        # Load existing entries for this month
        mood_file = self._get_mood_file(entry.timestamp)
        entries = []
        if mood_file.exists():
            try:
                with open(mood_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    entries = [MoodEntry.from_dict(e) for e in data.get("entries", [])]
            except Exception as e:
                logger.error(f"Failed to load mood data: {e}")

        # Add new entry
        entries.append(entry)

        # Save
        try:
            with open(mood_file, "w", encoding="utf-8") as f:
                json.dump(
                    {"entries": [e.to_dict() for e in entries]},
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
            logger.info(f"Logged mood entry: {entry.mood.value}")
        except Exception as e:
            logger.error(f"Failed to save mood entry: {e}")

        return entry

    def get_entries(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        days: Optional[int] = None,
    ) -> List[MoodEntry]:
        """Get mood entries within a date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            limit: Maximum entries to return
            days: Alternative to start_date - get entries from last N days

        Returns:
            List of mood entries
        """
        entries = []

        # Determine which files to load
        now = datetime.now()
        if days is not None:
            start = now - timedelta(days=days)
            end = now
        else:
            start = start_date or (now - timedelta(days=30))
            end = end_date or now

        current = start.replace(day=1)
        while current <= end:
            mood_file = self._get_mood_file(current)
            if mood_file.exists():
                try:
                    with open(mood_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        for entry_data in data.get("entries", []):
                            entry = MoodEntry.from_dict(entry_data)
                            if start <= entry.timestamp <= end:
                                entries.append(entry)
                except Exception as e:
                    logger.error(f"Failed to load mood file {mood_file}: {e}")

            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

        # Sort by timestamp and limit
        entries.sort(key=lambda e: e.timestamp, reverse=True)
        return entries[:limit]

    def get_today_entries(self) -> List[MoodEntry]:
        """Get today's mood entries."""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        return self.get_entries(today, tomorrow)

    def get_weekly_insights(self) -> MoodInsights:
        """Get insights from the past week."""
        end = datetime.now()
        start = end - timedelta(days=7)
        entries = self.get_entries(start, end)

        if not entries:
            return MoodInsights(
                period="last_7_days",
                avg_mood=0,
                avg_energy=0,
                avg_focus=0,
                avg_stress=0,
                avg_satisfaction=0,
                mood_distribution={},
                best_time_of_day=None,
                productivity_correlation=0,
                recommendations=["Start tracking your mood to get insights!"],
            )

        # Calculate averages
        mood_scores = {m: i for i, m in enumerate(MoodLevel)}
        mood_values = [mood_scores[e.mood] for e in entries]
        avg_mood = sum(mood_values) / len(mood_values)

        avg_energy = sum(e.energy.value for e in entries) / len(entries)
        avg_focus = sum(e.focus.value for e in entries) / len(entries)
        avg_stress = sum(e.stress for e in entries) / len(entries)
        avg_satisfaction = sum(e.satisfaction for e in entries) / len(entries)

        # Mood distribution
        mood_distribution = {}
        for e in entries:
            mood_distribution[e.mood.value] = mood_distribution.get(e.mood.value, 0) + 1

        # Best time of day
        time_periods = {"morning": [], "afternoon": [], "evening": []}
        for e in entries:
            hour = e.timestamp.hour
            if 6 <= hour < 12:
                time_periods["morning"].append(mood_scores[e.mood])
            elif 12 <= hour < 18:
                time_periods["afternoon"].append(mood_scores[e.mood])
            else:
                time_periods["evening"].append(mood_scores[e.mood])

        avg_by_time = {
            period: sum(scores) / len(scores) if scores else 0
            for period, scores in time_periods.items()
        }
        best_time = max(avg_by_time, key=avg_by_time.get) if avg_by_time else None

        # Generate recommendations
        recommendations = []
        if avg_stress > 6:
            recommendations.append("High stress detected. Consider taking breaks or reducing workload.")
        if avg_energy < 3:
            recommendations.append("Low energy levels. Check sleep and exercise habits.")
        if avg_focus < 3:
            recommendations.append("Focus issues detected. Try the Pomodoro technique or reduce distractions.")
        if avg_satisfaction > 7 and avg_energy > 3:
            recommendations.append("Great week! You're in a productive flow state.")

        return MoodInsights(
            period="last_7_days",
            avg_mood=avg_mood,
            avg_energy=avg_energy,
            avg_focus=avg_focus,
            avg_stress=avg_stress,
            avg_satisfaction=avg_satisfaction,
            mood_distribution=mood_distribution,
            best_time_of_day=best_time,
            productivity_correlation=self._calculate_productivity_correlation(entries),
            recommendations=recommendations,
        )

    def _calculate_productivity_correlation(self, entries: List[MoodEntry]) -> float:
        """Calculate correlation between mood and perceived productivity."""
        if len(entries) < 3:
            return 0.0

        # Simple correlation: energy * focus vs satisfaction
        import statistics

        productivity_scores = [e.energy.value * e.focus.value for e in entries]
        satisfaction_scores = [e.satisfaction for e in entries]

        try:
            # Calculate correlation coefficient
            mean_p = statistics.mean(productivity_scores)
            mean_s = statistics.mean(satisfaction_scores)

            numerator = sum(
                (p - mean_p) * (s - mean_s)
                for p, s in zip(productivity_scores, satisfaction_scores)
            )
            denom_p = sum((p - mean_p) ** 2 for p in productivity_scores) ** 0.5
            denom_s = sum((s - mean_s) ** 2 for s in satisfaction_scores) ** 0.5

            if denom_p == 0 or denom_s == 0:
                return 0.0

            return numerator / (denom_p * denom_s)
        except Exception:
            return 0.0

    def generate_mood_report(self, days: int = 7) -> str:
        """Generate a mood report for the specified period.

        Args:
            days: Number of days to include

        Returns:
            Markdown formatted report
        """
        end = datetime.now()
        start = end - timedelta(days=days)
        entries = self.get_entries(start, end)
        insights = self.get_weekly_insights()

        report = f"""# Mood Report - Last {days} Days

## Overview
- **Entries Logged**: {len(entries)}
- **Average Mood**: {insights.avg_mood:.1f}/4
- **Average Energy**: {insights.avg_energy:.1f}/5
- **Average Focus**: {insights.avg_focus:.1f}/5
- **Average Stress**: {insights.avg_stress:.1f}/10
- **Average Satisfaction**: {insights.avg_satisfaction:.1f}/10

## Mood Distribution
"""

        for mood, count in sorted(insights.mood_distribution.items()):
            percentage = (count / len(entries)) * 100 if entries else 0
            report += f"- **{mood}**: {count} ({percentage:.0f}%)\n"

        if insights.best_time_of_day:
            report += f"\n## Best Time of Day\n{insights.best_time_of_day.title()}"

        if insights.recommendations:
            report += "\n\n## Recommendations\n"
            for rec in insights.recommendations:
                report += f"- {rec}\n"

        if entries:
            report += "\n## Recent Entries\n"
            for entry in entries[:5]:
                report += f"\n**{entry.timestamp.strftime('%Y-%m-%d %H:%M')}**\n"
                report += f"- Mood: {entry.mood.value}\n"
                report += f"- Energy: {entry.energy.value}/5\n"
                report += f"- Focus: {entry.focus.value}/5\n"
                if entry.notes:
                    report += f"- Notes: {entry.notes}\n"

        return report

    def quick_check_in(self) -> Dict[str, Any]:
        """Quick check-in helper with prompts.

        Returns:
            Dictionary with check-in prompts
        """
        return {
            "prompts": [
                {
                    "question": "How are you feeling right now?",
                    "options": ["excellent", "good", "neutral", "tired", "stressed"],
                    "key": "mood",
                },
                {
                    "question": "What's your energy level?",
                    "options": ["1 (very low)", "2 (low)", "3 (moderate)", "4 (high)", "5 (very high)"],
                    "key": "energy",
                },
                {
                    "question": "How focused do you feel?",
                    "options": ["1 (distracted)", "2 (unfocused)", "3 (moderate)", "4 (focused)", "5 (deep focus)"],
                    "key": "focus",
                },
                {
                    "question": "Stress level (1-10)?",
                    "type": "scale",
                    "min": 1,
                    "max": 10,
                    "key": "stress",
                },
                {
                    "question": "Satisfaction with current work (1-10)?",
                    "type": "scale",
                    "min": 1,
                    "max": 10,
                    "key": "satisfaction",
                },
            ],
            "message": "Take a moment to check in with yourself. Your well-being matters!",
        }
