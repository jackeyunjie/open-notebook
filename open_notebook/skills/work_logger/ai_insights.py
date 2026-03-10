"""AI Insights - Work pattern analysis and productivity intelligence.

Provides AI-powered analysis of work patterns, efficiency bottlenecks,
and personalized recommendations based on historical data.
"""

import json
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from loguru import logger

from open_notebook.skills.work_logger.models import WorkSession
from open_notebook.skills.work_logger.mood_tracker import MoodTracker, MoodLevel


@dataclass
class WorkPattern:
    """Identified work pattern."""
    pattern_type: str  # focus_time, productivity_peak, interruption_prone
    description: str
    confidence: float  # 0-1
    supporting_data: Dict[str, Any]
    recommendation: str


@dataclass
class EfficiencyInsight:
    """Efficiency analysis insight."""
    category: str  # time_management, focus_quality, energy_management
    score: float  # 0-100
    findings: List[str]
    bottlenecks: List[str]
    recommendations: List[str]


@dataclass
class ProductivityMetrics:
    """Comprehensive productivity metrics."""
    period: str
    total_sessions: int
    total_duration_hours: float
    avg_session_duration: float
    most_productive_day: Optional[str]
    most_productive_hour: Optional[int]
    consistency_score: float  # 0-100
    deep_work_ratio: float  # % of time in deep focus
    interruption_rate: float  # interruptions per hour
    completion_rate: float  # % of goals completed
    velocity_trend: str  # accelerating, steady, declining


class AIInsightsEngine:
    """AI-powered insights engine for work analysis.

    Analyzes work sessions, mood data, and goals to provide
    intelligent insights and recommendations.

    Usage:
        engine = AIInsightsEngine("~/.claude/work_logs")

        # Analyze work patterns
        patterns = engine.analyze_work_patterns(days=30)

        # Get efficiency insights
        insights = engine.get_efficiency_insights()

        # Generate personalized recommendations
        recommendations = engine.generate_recommendations()
    """

    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path).expanduser()
        self.mood_tracker = MoodTracker(workspace_path)

    def analyze_work_patterns(self, days: int = 30) -> List[WorkPattern]:
        """Analyze work patterns from historical data."""
        patterns = []

        # Load sessions
        sessions = self._load_sessions(days)
        if len(sessions) < 3:
            return [WorkPattern(
                pattern_type="insufficient_data",
                description="Not enough data to identify patterns",
                confidence=0.0,
                supporting_data={},
                recommendation="Continue logging work sessions for at least a week"
            )]

        # Pattern 1: Peak productivity hours
        hour_productivity = self._analyze_hourly_patterns(sessions)
        if hour_productivity:
            peak_hours = [h for h, score in hour_productivity.items() if score > 70]
            if peak_hours:
                patterns.append(WorkPattern(
                    pattern_type="productivity_peak",
                    description=f"Peak productivity hours: {', '.join(f'{h:02d}:00' for h in peak_hours[:3])}",
                    confidence=0.8,
                    supporting_data={"peak_hours": peak_hours, "hourly_scores": hour_productivity},
                    recommendation=f"Schedule important tasks during {peak_hours[0]:02d}:00-{peak_hours[0]+1:02d}:00"
                ))

        # Pattern 2: Focus duration patterns
        focus_pattern = self._analyze_focus_patterns(sessions)
        if focus_pattern:
            patterns.append(WorkPattern(
                pattern_type="focus_time",
                description=focus_pattern["description"],
                confidence=focus_pattern["confidence"],
                supporting_data=focus_pattern["data"],
                recommendation=focus_pattern["recommendation"]
            ))

        # Pattern 3: Mood-productivity correlation
        mood_correlation = self._analyze_mood_productivity_correlation(days)
        if mood_correlation:
            patterns.append(WorkPattern(
                pattern_type="mood_productivity_correlation",
                description=mood_correlation["description"],
                confidence=mood_correlation["confidence"],
                supporting_data=mood_correlation["data"],
                recommendation=mood_correlation["recommendation"]
            ))

        # Pattern 4: Session consistency
        consistency = self._analyze_consistency(sessions)
        if consistency:
            patterns.append(WorkPattern(
                pattern_type="consistency",
                description=consistency["description"],
                confidence=consistency["confidence"],
                supporting_data=consistency["data"],
                recommendation=consistency["recommendation"]
            ))

        return patterns

    def get_efficiency_insights(self, days: int = 14) -> List[EfficiencyInsight]:
        """Get efficiency analysis insights."""
        insights = []

        sessions = self._load_sessions(days)
        if len(sessions) < 3:
            return []

        # Time Management
        time_insight = self._analyze_time_management(sessions)
        insights.append(time_insight)

        # Focus Quality
        focus_insight = self._analyze_focus_quality(sessions)
        insights.append(focus_insight)

        # Energy Management
        energy_insight = self._analyze_energy_management(days)
        insights.append(energy_insight)

        return insights

    def generate_recommendations(self) -> List[Dict[str, str]]:
        """Generate personalized recommendations."""
        recommendations = []

        # Analyze patterns
        patterns = self.analyze_work_patterns(days=14)
        insights = self.get_efficiency_insights(days=14)

        # Pattern-based recommendations
        for pattern in patterns:
            if pattern.pattern_type == "productivity_peak":
                peak_hours = pattern.supporting_data.get("peak_hours", [])
                if peak_hours:
                    recommendations.append({
                        "category": "scheduling",
                        "priority": "high",
                        "title": "Optimize your peak hours",
                        "description": f"Your most productive time is {peak_hours[0]:02d}:00. Schedule deep work then.",
                        "action": f"Block {peak_hours[0]:02d}:00-{peak_hours[0]+2:02d}:00 daily for focused work"
                    })

            elif pattern.pattern_type == "mood_productivity_correlation":
                corr = pattern.supporting_data.get("correlation", 0)
                if corr > 0.5:
                    recommendations.append({
                        "category": "wellbeing",
                        "priority": "high",
                        "title": "Prioritize emotional well-being",
                        "description": "Your mood strongly correlates with productivity.",
                        "action": "Start each day with mood check-in; take breaks when energy drops"
                    })

        # Efficiency-based recommendations
        for insight in insights:
            if insight.category == "focus_quality" and insight.score < 60:
                recommendations.append({
                    "category": "focus",
                    "priority": "medium",
                    "title": "Improve focus sessions",
                    "description": f"Focus score is {insight.score:.0f}/100. {insight.bottlenecks[0] if insight.bottlenecks else 'Consider using Pomodoro technique.'}",
                    "action": "Use 25/5 Pomodoro cycles; eliminate notifications during focus time"
                })

            elif insight.category == "time_management" and insight.score < 50:
                recommendations.append({
                    "category": "planning",
                    "priority": "high",
                    "title": "Improve time planning",
                    "description": "Session planning needs improvement.",
                    "action": "Set clear goals before each session; use time-blocking"
                })

        # Default recommendations if few found
        if len(recommendations) < 2:
            recommendations.append({
                "category": "general",
                "priority": "low",
                "title": "Continue tracking",
                "description": "Keep logging sessions to get more personalized insights.",
                "action": "Log at least 5 more sessions for better analysis"
            })

        return recommendations

    def get_productivity_metrics(self, days: int = 7) -> ProductivityMetrics:
        """Calculate comprehensive productivity metrics."""
        sessions = self._load_sessions(days)

        if not sessions:
            return ProductivityMetrics(
                period=f"last_{days}_days",
                total_sessions=0,
                total_duration_hours=0,
                avg_session_duration=0,
                most_productive_day=None,
                most_productive_hour=None,
                consistency_score=0,
                deep_work_ratio=0,
                interruption_rate=0,
                completion_rate=0,
                velocity_trend="stable"
            )

        # Calculate basic metrics
        total_duration = sum(
            s.duration_minutes or 0 for s in sessions
        )
        avg_duration = total_duration / len(sessions) if sessions else 0

        # Most productive day/hour
        day_scores = {}
        hour_scores = {}
        for s in sessions:
            day = s.start_time.strftime("%A")
            hour = s.start_time.hour
            duration = s.duration_minutes or 0

            day_scores[day] = day_scores.get(day, 0) + duration
            hour_scores[hour] = hour_scores.get(hour, 0) + duration

        most_productive_day = max(day_scores, key=day_scores.get) if day_scores else None
        most_productive_hour = max(hour_scores, key=hour_scores.get) if hour_scores else None

        # Consistency score (days with sessions / total days)
        days_with_sessions = len(set(s.start_time.date() for s in sessions))
        consistency = (days_with_sessions / days) * 100

        # Deep work ratio (sessions > 60 min)
        deep_sessions = sum(1 for s in sessions if (s.duration_minutes or 0) > 60)
        deep_work_ratio = (deep_sessions / len(sessions)) * 100 if sessions else 0

        # Velocity trend (compare first half vs second half)
        mid = len(sessions) // 2
        first_half = sum(s.duration_minutes or 0 for s in sessions[:mid])
        second_half = sum(s.duration_minutes or 0 for s in sessions[mid:])

        if second_half > first_half * 1.2:
            trend = "accelerating"
        elif second_half < first_half * 0.8:
            trend = "declining"
        else:
            trend = "steady"

        return ProductivityMetrics(
            period=f"last_{days}_days",
            total_sessions=len(sessions),
            total_duration_hours=total_duration / 60,
            avg_session_duration=avg_duration,
            most_productive_day=most_productive_day,
            most_productive_hour=most_productive_hour,
            consistency_score=consistency,
            deep_work_ratio=deep_work_ratio,
            interruption_rate=0,
            completion_rate=0,
            velocity_trend=trend
        )

    def generate_weekly_ai_report(self) -> str:
        """Generate AI-powered weekly report."""
        metrics = self.get_productivity_metrics(days=7)
        patterns = self.analyze_work_patterns(days=14)
        insights = self.get_efficiency_insights(days=7)
        recommendations = self.generate_recommendations()

        report = f"""# AI-Powered Weekly Report

## Productivity Metrics (Last 7 Days)
- **Total Sessions**: {metrics.total_sessions}
- **Total Time**: {metrics.total_duration_hours:.1f} hours
- **Avg Session**: {metrics.avg_session_duration:.0f} minutes
- **Best Day**: {metrics.most_productive_day or 'N/A'}
- **Best Hour**: {f"{metrics.most_productive_hour:02d}:00" if metrics.most_productive_hour is not None else 'N/A'}
- **Consistency**: {metrics.consistency_score:.0f}%
- **Deep Work Ratio**: {metrics.deep_work_ratio:.0f}%
- **Trend**: {metrics.velocity_trend}

## Identified Patterns
"""

        for i, pattern in enumerate(patterns, 1):
            report += f"\n### {i}. {pattern.pattern_type.replace('_', ' ').title()}\n"
            report += f"**Confidence**: {pattern.confidence*100:.0f}%\n\n"
            report += f"{pattern.description}\n\n"
            report += f"**Recommendation**: {pattern.recommendation}\n"

        report += "\n## Efficiency Analysis\n"
        for insight in insights:
            report += f"\n### {insight.category.replace('_', ' ').title()}\n"
            report += f"**Score**: {insight.score:.0f}/100\n\n"
            if insight.findings:
                report += "**Findings**:\n"
                for finding in insight.findings[:3]:
                    report += f"- {finding}\n"
            if insight.bottlenecks:
                report += "\n**Bottlenecks**:\n"
                for bottleneck in insight.bottlenecks[:2]:
                    report += f"- {bottleneck}\n"

        report += "\n## Top Recommendations\n"
        high_priority = [r for r in recommendations if r["priority"] == "high"]
        for rec in high_priority[:3]:
            report += f"\n### {rec['title']}\n"
            report += f"**{rec['description']}**\n\n"
            report += f"**Action**: {rec['action']}\n"

        return report

    def _load_sessions(self, days: int) -> List[WorkSession]:
        """Load work sessions from the past N days."""
        sessions = []
        cutoff = datetime.now() - timedelta(days=days)

        sessions_dir = self.workspace_path / "sessions"
        if not sessions_dir.exists():
            return sessions

        for year_dir in sessions_dir.iterdir():
            if not year_dir.is_dir():
                continue
            for month_dir in year_dir.iterdir():
                if not month_dir.is_dir():
                    continue
                for day_dir in month_dir.iterdir():
                    if not day_dir.is_dir():
                        continue
                    for session_file in day_dir.glob("*.json"):
                        try:
                            with open(session_file, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            from open_notebook.skills.work_logger.models import SessionType, SessionStatus
                            session = WorkSession(
                                session_id=data["session_id"],
                                start_time=datetime.fromisoformat(data["start_time"]),
                                session_type=SessionType(data.get("session_type", "other")),
                                title=data["title"],
                                description=data.get("description", ""),
                                project=data.get("project"),
                                tags=data.get("tags", []),
                                status=SessionStatus(data.get("status", "completed")),
                                end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
                                related_files=data.get("related_files", []),
                                context_notes=data.get("context_notes", ""),
                            )
                            if session.start_time >= cutoff:
                                sessions.append(session)
                        except Exception:
                            continue

        return sorted(sessions, key=lambda s: s.start_time)

    def _analyze_hourly_patterns(self, sessions: List[WorkSession]) -> Dict[int, float]:
        """Analyze productivity by hour."""
        hour_durations = {}
        hour_counts = {}

        for s in sessions:
            hour = s.start_time.hour
            duration = s.duration_minutes or 0

            hour_durations[hour] = hour_durations.get(hour, 0) + duration
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

        # Calculate average productivity score per hour
        hour_scores = {}
        max_avg = 0
        for hour in hour_durations:
            avg = hour_durations[hour] / hour_counts[hour]
            hour_scores[hour] = avg
            max_avg = max(max_avg, avg)

        # Normalize to 0-100
        if max_avg > 0:
            hour_scores = {h: (s / max_avg) * 100 for h, s in hour_scores.items()}

        return hour_scores

    def _analyze_focus_patterns(self, sessions: List[WorkSession]) -> Optional[Dict]:
        """Analyze focus duration patterns."""
        durations = [s.duration_minutes or 0 for s in sessions if s.duration_minutes]

        if len(durations) < 3:
            return None

        avg_duration = statistics.mean(durations)
        long_sessions = [d for d in durations if d > 60]

        if len(long_sessions) > len(durations) * 0.5:
            return {
                "description": f"You have strong focus capability. Average session: {avg_duration:.0f} min",
                "confidence": 0.75,
                "data": {"avg_duration": avg_duration, "long_sessions": len(long_sessions)},
                "recommendation": "Great focus! Try extending deep work blocks to 90 minutes"
            }
        else:
            return {
                "description": f"Sessions are relatively short ({avg_duration:.0f} min avg). May indicate interruptions.",
                "confidence": 0.65,
                "data": {"avg_duration": avg_duration, "long_sessions": len(long_sessions)},
                "recommendation": "Try Pomodoro technique: 25 min focus + 5 min break"
            }

    def _analyze_mood_productivity_correlation(self, days: int) -> Optional[Dict]:
        """Analyze correlation between mood and productivity."""
        mood_entries = self.mood_tracker.get_entries(days=days)

        if len(mood_entries) < 3:
            return None

        # Simple correlation: mood vs energy * focus
        mood_scores = {"excellent": 4, "good": 3, "neutral": 2, "tired": 1, "stressed": 0}

        x = [mood_scores.get(e.mood.value, 2) for e in mood_entries]
        y = [(e.energy.value * e.focus.value) for e in mood_entries]

        if len(x) < 2:
            return None

        # Calculate correlation
        try:
            mean_x, mean_y = statistics.mean(x), statistics.mean(y)
            numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
            denom_x = sum((xi - mean_x) ** 2 for xi in x) ** 0.5
            denom_y = sum((yi - mean_y) ** 2 for yi in y) ** 0.5

            correlation = numerator / (denom_x * denom_y) if denom_x and denom_y else 0
        except Exception:
            correlation = 0

        if abs(correlation) > 0.3:
            return {
                "description": f"Strong mood-productivity correlation detected (r={correlation:.2f})",
                "confidence": abs(correlation),
                "data": {"correlation": correlation, "sample_size": len(mood_entries)},
                "recommendation": "Prioritize activities that boost mood before important work"
            }

        return None

    def _analyze_consistency(self, sessions: List[WorkSession]) -> Optional[Dict]:
        """Analyze work consistency."""
        if len(sessions) < 5:
            return None

        days = [s.start_time.date() for s in sessions]
        unique_days = len(set(days))
        total_span = (max(days) - min(days)).days + 1

        consistency = unique_days / total_span if total_span > 0 else 1.0

        if consistency > 0.8:
            return {
                "description": f"Excellent consistency! Working {unique_days} out of {total_span} days",
                "confidence": 0.85,
                "data": {"consistency_ratio": consistency, "days_worked": unique_days},
                "recommendation": "Maintain this rhythm. Consider adding rest days to prevent burnout"
            }
        elif consistency < 0.4:
            return {
                "description": f"Inconsistent work pattern. Only {unique_days} active days in {total_span} days",
                "confidence": 0.7,
                "data": {"consistency_ratio": consistency, "days_worked": unique_days},
                "recommendation": "Try to establish a daily work routine, even if short"
            }

        return None

    def _analyze_time_management(self, sessions: List[WorkSession]) -> EfficiencyInsight:
        """Analyze time management efficiency."""
        if len(sessions) < 3:
            return EfficiencyInsight(
                category="time_management",
                score=50,
                findings=["Insufficient data for analysis"],
                bottlenecks=[],
                recommendations=["Continue logging sessions"]
            )

        findings = []
        bottlenecks = []
        recommendations = []

        # Check session planning
        well_planned = sum(1 for s in sessions if len(s.title) > 10 or s.description)
        planning_rate = well_planned / len(sessions)

        if planning_rate < 0.5:
            score = 40
            bottlenecks.append("Many sessions lack clear goals")
            recommendations.append("Write specific session objectives before starting")
        else:
            score = 75
            findings.append("Good session planning habits")

        # Check session length consistency
        durations = [s.duration_minutes or 0 for s in sessions]
        if durations:
            std_dev = statistics.stdev(durations) if len(durations) > 1 else 0
            avg = statistics.mean(durations)
            cv = std_dev / avg if avg > 0 else 0

            if cv > 0.5:
                score -= 10
                bottlenecks.append("High variability in session length")
                recommendations.append("Try to maintain consistent work blocks")

        return EfficiencyInsight(
            category="time_management",
            score=max(0, min(100, score)),
            findings=findings,
            bottlenecks=bottlenecks,
            recommendations=recommendations
        )

    def _analyze_focus_quality(self, sessions: List[WorkSession]) -> EfficiencyInsight:
        """Analyze focus quality."""
        if len(sessions) < 3:
            return EfficiencyInsight(
                category="focus_quality",
                score=50,
                findings=["Insufficient data"],
                bottlenecks=[],
                recommendations=["Continue tracking sessions"]
            )

        findings = []
        bottlenecks = []
        recommendations = []

        durations = [s.duration_minutes or 0 for s in sessions]
        long_sessions = [d for d in durations if d >= 45]

        if len(long_sessions) >= len(sessions) * 0.6:
            score = 80
            findings.append("Strong ability to maintain long focus sessions")
        elif len(long_sessions) >= len(sessions) * 0.3:
            score = 60
            findings.append("Moderate focus duration")
            recommendations.append("Try extending sessions by 10-15 minutes gradually")
        else:
            score = 40
            bottlenecks.append("Most sessions are short (under 45 min)")
            recommendations.append("Use Pomodoro technique to build focus stamina")

        return EfficiencyInsight(
            category="focus_quality",
            score=score,
            findings=findings,
            bottlenecks=bottlenecks,
            recommendations=recommendations
        )

    def _analyze_energy_management(self, days: int) -> EfficiencyInsight:
        """Analyze energy management from mood data."""
        entries = self.mood_tracker.get_entries(days=days)

        if len(entries) < 3:
            return EfficiencyInsight(
                category="energy_management",
                score=50,
                findings=["No mood data available"],
                bottlenecks=[],
                recommendations=["Start logging mood to get energy insights"]
            )

        avg_energy = statistics.mean(e.energy.value for e in entries)
        avg_stress = statistics.mean(e.stress for e in entries)

        findings = []
        bottlenecks = []
        recommendations = []

        score = int((avg_energy / 5) * 100)

        if avg_energy >= 4:
            findings.append(f"High average energy level ({avg_energy:.1f}/5)")
        elif avg_energy <= 2.5:
            score -= 20
            bottlenecks.append(f"Low energy levels detected ({avg_energy:.1f}/5)")
            recommendations.append("Check sleep, exercise, and nutrition")

        if avg_stress > 6:
            score -= 15
            bottlenecks.append(f"High stress levels ({avg_stress:.1f}/10)")
            recommendations.append("Practice stress management techniques")

        return EfficiencyInsight(
            category="energy_management",
            score=max(0, min(100, score)),
            findings=findings,
            bottlenecks=bottlenecks,
            recommendations=recommendations
        )
