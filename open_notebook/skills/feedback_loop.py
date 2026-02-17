"""Feedback Loop System - Closed-loop learning for Organic Growth System.

This module provides feedback collection, analysis, and learning mechanisms
that enable the organic system to improve itself based on execution results.

Feedback Loop Architecture:
    P0 → P1 → P2 → [Results] → Feedback Loop → [Learning] → P0 (Improved)

Feedback Types:
    1. Performance Feedback: Content metrics (views, engagement, conversion)
    2. Qualitative Feedback: User comments, sentiment, testimonials
    3. Outcome Feedback: Actual business results (leads, sales, retention)
    4. Meta Feedback: System performance, agent effectiveness

Learning Mechanisms:
    1. Signal Quality Scoring: Which P0 signals led to good outcomes?
    2. Pattern Recognition: What combinations predict success?
    3. Threshold Optimization: Adjust value judgment thresholds
    4. Strategy Evolution: Improve relationship building tactics
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from open_notebook.skills.p0_orchestrator import SharedMemory


class FeedbackType(Enum):
    """Types of feedback collected."""
    PERFORMANCE = "performance"    # Quantitative metrics
    QUALITATIVE = "qualitative"    # User comments, sentiment
    OUTCOME = "outcome"           # Business results
    META = "meta"                 # System performance


class LearningAction(Enum):
    """Actions that can be taken based on feedback."""
    ADJUST_THRESHOLD = "adjust_threshold"      # Change value thresholds
    UPDATE_WEIGHTS = "update_weights"          # Adjust scoring weights
    REFINE_SIGNALS = "refine_signals"          # Improve signal detection
    EVOLVE_STRATEGY = "evolve_strategy"        # Update relationship tactics


@dataclass
class FeedbackRecord:
    """A single feedback record from executed plans."""
    feedback_id: str
    source_plan_id: str           # Which P2 plan generated this
    source_quadrant: str          # Q1/Q2/Q3/Q4
    feedback_type: FeedbackType
    metrics: Dict[str, Any]       # Quantitative results
    qualitative_data: List[str]   # Comments, feedback text
    outcome_value: float          # Business value (revenue, leads, etc.)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feedback_id": self.feedback_id,
            "source_plan_id": self.source_plan_id,
            "source_quadrant": self.source_quadrant,
            "feedback_type": self.feedback_type.value,
            "metrics": self.metrics,
            "qualitative_data": self.qualitative_data,
            "outcome_value": self.outcome_value,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class LearningInsight:
    """An insight generated from analyzing feedback."""
    insight_id: str
    insight_type: str
    description: str
    confidence: float             # 0-1
    evidence: List[str]           # Supporting feedback IDs
    recommended_action: LearningAction
    action_parameters: Dict[str, Any]
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "insight_id": self.insight_id,
            "insight_type": self.insight_type,
            "description": self.description,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "recommended_action": self.recommended_action.value,
            "action_parameters": self.action_parameters,
            "generated_at": self.generated_at.isoformat()
        }


@dataclass
class SystemLearningState:
    """Current learning state of the organic system."""
    version: str
    last_updated: datetime
    p0_thresholds: Dict[str, float]       # Adjusted P0 detection thresholds
    p1_weights: Dict[str, Dict[str, float]]  # Adjusted P1 scoring weights
    p2_strategies: Dict[str, Any]         # Evolved P2 strategies
    successful_patterns: List[Dict[str, Any]]  # Patterns that worked
    failed_patterns: List[Dict[str, Any]]     # Patterns that didn't work

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "last_updated": self.last_updated.isoformat(),
            "p0_thresholds": self.p0_thresholds,
            "p1_weights": self.p1_weights,
            "p2_strategies": self.p2_strategies,
            "successful_patterns_count": len(self.successful_patterns),
            "failed_patterns_count": len(self.failed_patterns)
        }


class FeedbackCollector:
    """Collects and stores feedback from P2 plan executions."""

    def __init__(self):
        self.shared_memory = SharedMemory()
        self.feedback_history: List[FeedbackRecord] = []

    def collect_feedback(
        self,
        plan_id: str,
        quadrant: str,
        metrics: Dict[str, Any],
        qualitative_data: List[str] = None,
        outcome_value: float = 0.0
    ) -> FeedbackRecord:
        """Collect feedback from an executed plan."""
        feedback_id = f"fb_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{plan_id}"

        # Determine feedback type based on metrics
        if "conversion_rate" in metrics or "revenue" in metrics:
            feedback_type = FeedbackType.OUTCOME
        elif "sentiment" in metrics or "comments" in metrics:
            feedback_type = FeedbackType.QUALITATIVE
        else:
            feedback_type = FeedbackType.PERFORMANCE

        record = FeedbackRecord(
            feedback_id=feedback_id,
            source_plan_id=plan_id,
            source_quadrant=quadrant,
            feedback_type=feedback_type,
            metrics=metrics,
            qualitative_data=qualitative_data or [],
            outcome_value=outcome_value
        )

        # Store to SharedMemory
        key = f"feedback:{feedback_id}"
        self.shared_memory.store(key, record.to_dict(), ttl_seconds=2592000)  # 30 days

        self.feedback_history.append(record)

        logger.info(f"Collected {feedback_type.value} feedback for {plan_id}")
        return record

    def get_recent_feedback(
        self,
        hours: int = 168,  # 7 days default
        quadrant: Optional[str] = None
    ) -> List[FeedbackRecord]:
        """Get recent feedback records."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        records = []
        for record in self.feedback_history:
            if record.timestamp > cutoff:
                if quadrant is None or record.source_quadrant == quadrant:
                    records.append(record)

        return records

    def calculate_success_rate(self, plan_prefix: str = None) -> Dict[str, Any]:
        """Calculate success rate for plans."""
        relevant_feedback = self.feedback_history
        if plan_prefix:
            relevant_feedback = [
                f for f in relevant_feedback
                if f.source_plan_id.startswith(plan_prefix)
            ]

        if not relevant_feedback:
            return {"total": 0, "successful": 0, "rate": 0.0}

        # Define success criteria
        successful = sum(
            1 for f in relevant_feedback
            if f.outcome_value > 0 or f.metrics.get("engagement_rate", 0) > 0.05
        )

        return {
            "total": len(relevant_feedback),
            "successful": successful,
            "rate": successful / len(relevant_feedback) if relevant_feedback else 0.0
        }


class PatternAnalyzer:
    """Analyzes feedback to identify successful/failed patterns."""

    def __init__(self, feedback_collector: FeedbackCollector):
        self.feedback_collector = feedback_collector

    def analyze_signal_to_outcome(
        self,
        hours: int = 168
    ) -> Dict[str, Any]:
        """Analyze which P0 signals led to successful outcomes."""
        feedback_records = self.feedback_collector.get_recent_feedback(hours=hours)

        if not feedback_records:
            return {"patterns": [], "insights": "No feedback data available"}

        # Group by success/failure
        successful = [f for f in feedback_records if f.outcome_value > 100]
        failed = [f for f in feedback_records if f.outcome_value < 50]

        # Analyze patterns
        patterns = {
            "high_performers": self._extract_common_traits(successful),
            "low_performers": self._extract_common_traits(failed),
            "success_rate_by_quadrant": self._success_by_quadrant(feedback_records)
        }

        return patterns

    def _extract_common_traits(
        self,
        feedback_records: List[FeedbackRecord]
    ) -> List[str]:
        """Extract common traits from feedback records."""
        if not feedback_records:
            return []

        traits = []

        # Check engagement patterns
        avg_engagement = sum(
            f.metrics.get("engagement_rate", 0) for f in feedback_records
        ) / len(feedback_records)

        if avg_engagement > 0.08:
            traits.append("high_engagement")
        elif avg_engagement < 0.03:
            traits.append("low_engagement")

        # Check timing patterns
        hours = [f.timestamp.hour for f in feedback_records]
        if hours:
            avg_hour = sum(hours) / len(hours)
            if 8 <= avg_hour <= 10:
                traits.append("morning_posting")
            elif 19 <= avg_hour <= 21:
                traits.append("evening_posting")

        return traits

    def _success_by_quadrant(
        self,
        feedback_records: List[FeedbackRecord]
    ) -> Dict[str, float]:
        """Calculate success rate by quadrant."""
        quadrant_stats = {}

        for q in ["Q1", "Q2", "Q3", "Q4"]:
            q_feedback = [f for f in feedback_records if f.source_quadrant == q]
            if q_feedback:
                successful = sum(1 for f in q_feedback if f.outcome_value > 100)
                quadrant_stats[q] = successful / len(q_feedback)
            else:
                quadrant_stats[q] = 0.0

        return quadrant_stats

    def generate_insights(self) -> List[LearningInsight]:
        """Generate learning insights from feedback analysis."""
        insights = []
        patterns = self.analyze_signal_to_outcome()

        # Insight 1: Quadrant performance comparison
        success_by_q = patterns.get("success_rate_by_quadrant", {})
        best_quadrant = max(success_by_q.items(), key=lambda x: x[1]) if success_by_q else ("unknown", 0)
        worst_quadrant = min(success_by_q.items(), key=lambda x: x[1]) if success_by_q else ("unknown", 0)

        if best_quadrant[1] > 0.5:
            insights.append(LearningInsight(
                insight_id=f"insight_q_perf_{datetime.utcnow().strftime('%Y%m%d')}",
                insight_type="quadrant_optimization",
                description=f"{best_quadrant[0]} quadrant showing highest success rate ({best_quadrant[1]:.1%}). "
                           f"Consider increasing signal weight for {best_quadrant[0]}.",
                confidence=0.75,
                evidence=[],
                recommended_action=LearningAction.UPDATE_WEIGHTS,
                action_parameters={
                    "quadrant": best_quadrant[0],
                    "weight_adjustment": 1.2
                }
            ))

        # Insight 2: Engagement threshold
        recent_fb = self.feedback_collector.get_recent_feedback(hours=168)
        if recent_fb:
            high_engagement = [f for f in recent_fb if f.metrics.get("engagement_rate", 0) > 0.08]
            if len(high_engagement) > len(recent_fb) * 0.3:
                insights.append(LearningInsight(
                    insight_id=f"insight_engagement_{datetime.utcnow().strftime('%Y%m%d')}",
                    insight_type="engagement_pattern",
                    description="High-engagement content (>8%) correlates with better outcomes. "
                               "Recommend prioritizing high-engagement signal types.",
                    confidence=0.7,
                    evidence=[f.feedback_id for f in high_engagement[:5]],
                    recommended_action=LearningAction.ADJUST_THRESHOLD,
                    action_parameters={
                        "metric": "engagement_rate",
                        "new_threshold": 0.08
                    }
                ))

        return insights


class LearningEngine:
    """Applies insights to evolve the organic system."""

    def __init__(self):
        self.shared_memory = SharedMemory()
        self.current_state = self._load_learning_state()

    def _load_learning_state(self) -> SystemLearningState:
        """Load current learning state from SharedMemory."""
        state_data = self.shared_memory.get("learning:current_state")

        if state_data:
            return SystemLearningState(
                version=state_data.get("version", "1.0.0"),
                last_updated=datetime.fromisoformat(state_data.get("last_updated")),
                p0_thresholds=state_data.get("p0_thresholds", {}),
                p1_weights=state_data.get("p1_weights", {}),
                p2_strategies=state_data.get("p2_strategies", {}),
                successful_patterns=state_data.get("successful_patterns", []),
                failed_patterns=state_data.get("failed_patterns", [])
            )

        # Default initial state
        return SystemLearningState(
            version="1.0.0",
            last_updated=datetime.utcnow(),
            p0_thresholds={
                "min_urgency_score": 60,
                "min_emotion_intensity": 60
            },
            p1_weights={
                "Q1": {"commercial": 0.40, "audience": 0.25, "competition": 0.15, "alignment": 0.20},
                "Q2": {"authenticity": 0.30, "audience": 0.25, "shareability": 0.20, "brand": 0.15, "conversion": 0.10},
                "Q3": {"lifecycle": 0.30, "relevance": 0.25, "sustainability": 0.20, "cost": 0.15, "viral": 0.10},
                "Q4": {"readiness": 0.30, "fit": 0.25, "education": 0.20, "timing": 0.15, "gap": 0.10}
            },
            p2_strategies={},
            successful_patterns=[],
            failed_patterns=[]
        )

    def apply_insight(self, insight: LearningInsight) -> bool:
        """Apply a learning insight to evolve the system."""
        try:
            if insight.recommended_action == LearningAction.ADJUST_THRESHOLD:
                metric = insight.action_parameters.get("metric")
                new_threshold = insight.action_parameters.get("new_threshold")

                if metric and new_threshold:
                    self.current_state.p0_thresholds[metric] = new_threshold
                    logger.info(f"Adjusted threshold for {metric} to {new_threshold}")

            elif insight.recommended_action == LearningAction.UPDATE_WEIGHTS:
                quadrant = insight.action_parameters.get("quadrant")
                adjustment = insight.action_parameters.get("weight_adjustment", 1.1)

                if quadrant and quadrant in self.current_state.p1_weights:
                    weights = self.current_state.p1_weights[quadrant]
                    # Apply adjustment proportionally
                    for key in weights:
                        weights[key] = min(weights[key] * adjustment, 0.5)  # Cap at 50%
                    logger.info(f"Updated weights for {quadrant} with adjustment {adjustment}")

            # Update timestamp and save
            self.current_state.last_updated = datetime.utcnow()
            self._save_learning_state()

            return True

        except Exception as e:
            logger.error(f"Failed to apply insight: {e}")
            return False

    def _save_learning_state(self):
        """Save current learning state to SharedMemory."""
        self.shared_memory.store(
            "learning:current_state",
            self.current_state.to_dict(),
            ttl_seconds=86400 * 30  # 30 days
        )

    def get_improved_p0_config(self) -> Dict[str, Any]:
        """Get improved P0 configuration based on learning."""
        return {
            "min_urgency_score": self.current_state.p0_thresholds.get("min_urgency_score", 60),
            "min_emotion_intensity": self.current_state.p0_thresholds.get("min_emotion_intensity", 60)
        }

    def get_improved_p1_config(self, quadrant: str) -> Dict[str, float]:
        """Get improved P1 weights for a quadrant."""
        return self.current_state.p1_weights.get(quadrant, {})

    def record_pattern(
        self,
        pattern: Dict[str, Any],
        successful: bool
    ):
        """Record a pattern for future learning."""
        pattern_record = {
            "pattern": pattern,
            "timestamp": datetime.utcnow().isoformat(),
            "system_version": self.current_state.version
        }

        if successful:
            self.current_state.successful_patterns.append(pattern_record)
            # Keep only last 100 successful patterns
            self.current_state.successful_patterns = self.current_state.successful_patterns[-100:]
        else:
            self.current_state.failed_patterns.append(pattern_record)
            self.current_state.failed_patterns = self.current_state.failed_patterns[-100:]

        self._save_learning_state()


class FeedbackLoopOrchestrator:
    """Orchestrates the complete feedback loop."""

    def __init__(self):
        self.feedback_collector = FeedbackCollector()
        self.pattern_analyzer = PatternAnalyzer(self.feedback_collector)
        self.learning_engine = LearningEngine()

    def collect_and_learn(
        self,
        plan_id: str,
        quadrant: str,
        metrics: Dict[str, Any],
        qualitative_data: List[str] = None,
        outcome_value: float = 0.0
    ) -> Optional[LearningInsight]:
        """Collect feedback and generate learning in one step."""
        # Step 1: Collect feedback
        feedback = self.feedback_collector.collect_feedback(
            plan_id=plan_id,
            quadrant=quadrant,
            metrics=metrics,
            qualitative_data=qualitative_data,
            outcome_value=outcome_value
        )

        # Step 2: Record pattern
        pattern = {
            "quadrant": quadrant,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.learning_engine.record_pattern(
            pattern,
            successful=outcome_value > 100
        )

        # Step 3: Generate and apply insights (periodically)
        # Only apply learning every 10 feedback records to avoid overfitting
        if len(self.feedback_collector.feedback_history) % 10 == 0:
            insights = self.pattern_analyzer.generate_insights()

            for insight in insights:
                if insight.confidence > 0.7:
                    self.learning_engine.apply_insight(insight)
                    logger.info(f"Applied learning insight: {insight.description}")
                    return insight

        return None

    def get_system_performance(self) -> Dict[str, Any]:
        """Get overall system performance metrics."""
        success_rate = self.feedback_collector.calculate_success_rate()

        return {
            "total_feedback": success_rate["total"],
            "successful_executions": success_rate["successful"],
            "success_rate": success_rate["rate"],
            "learning_state": self.learning_engine.current_state.to_dict(),
            "recent_insights": len(self.pattern_analyzer.generate_insights())
        }
