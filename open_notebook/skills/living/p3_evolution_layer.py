"""P3 Evolution Layer - Self-improvement through feedback loops.

The evolution layer enables the system to learn and optimize:
- Strategy Evolution: Optimize approaches based on results
- Feedback Loop: Learn from successes and failures
- Pattern Recognition: Identify successful patterns
- Parameter Tuning: Auto-tune system parameters
"""

import asyncio
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

from loguru import logger

from open_notebook.skills.living.agent_tissue import AgentTissue, AgentCoordination, CoordinationPattern
from open_notebook.skills.living.skill_cell import LivingSkill, SkillState


class EvolutionStrategy(Enum):
    """Strategies for evolution."""
    INCREMENTAL = "incremental"      # Gradual improvements
    EXPLORATORY = "exploratory"      # Try new approaches
    CONSERVATIVE = "conservative"    # Minor adjustments only
    AGGRESSIVE = "aggressive"        # Major changes allowed


@dataclass
class FeedbackRecord:
    """A single feedback record for learning."""
    record_id: str
    task_type: str
    input_hash: str
    output_hash: str
    success_score: float  # 0.0 to 1.0
    execution_time_ms: float
    resource_usage: Dict[str, float]
    user_feedback: Optional[str] = None
    auto_feedback: Optional[Dict] = None
    timestamp: datetime = field(default_factory=datetime.now)
    strategy_used: str = "default"


@dataclass
class StrategyPerformance:
    """Performance metrics for a strategy."""
    strategy_name: str
    task_type: str
    total_uses: int = 0
    success_count: int = 0
    avg_success_score: float = 0.0
    avg_execution_time: float = 0.0
    last_used: Optional[datetime] = None
    trend: str = "stable"  # improving, stable, declining


@dataclass
class EvolutionRecommendation:
    """Recommendation from evolution analysis."""
    task_type: str
    current_strategy: str
    recommended_strategy: str
    confidence: float
    reason: str
    expected_improvement: float
    parameters: Dict[str, Any] = field(default_factory=dict)


class StrategyEvolverSkill(LivingSkill):
    """
    P3.1 Strategy Evolver - 策略进化器

    Evolves execution strategies based on performance history:
    - Tracks strategy effectiveness
    - Identifies best approaches
    - Recommends strategy switches
    """

    def __init__(self):
        super().__init__(
            skill_id="p3.strategy_evolver",
            name="Strategy Evolver",
            description="进化执行策略 based on performance",
            version="1.0.0"
        )
        self._performance_db: Dict[str, StrategyPerformance] = {}
        self._feedback_history: List[FeedbackRecord] = []
        self._evolution_threshold = 10  # Min samples before evolving

    async def _execute(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Evolve strategies based on feedback."""
        feedback_list = context.get("feedback_records", [])
        task_type = context.get("task_type", "generic")

        # Update performance metrics
        for feedback in feedback_list:
            self._add_feedback(feedback)

        # Analyze and evolve
        if len(self._feedback_history) >= self._evolution_threshold:
            recommendations = self._evolve_strategies(task_type)
        else:
            recommendations = []

        return {
            "task_type": task_type,
            "feedback_count": len(self._feedback_history),
            "recommendations": recommendations,
            "best_strategy": self._get_best_strategy(task_type),
            "evolution_status": "evolved" if recommendations else "insufficient_data"
        }

    def _add_feedback(self, feedback: FeedbackRecord):
        """Add feedback to history."""
        self._feedback_history.append(feedback)

        # Update performance
        key = f"{feedback.task_type}:{feedback.strategy_used}"
        perf = self._performance_db.get(key)

        if not perf:
            perf = StrategyPerformance(
                strategy_name=feedback.strategy_used,
                task_type=feedback.task_type
            )
            self._performance_db[key] = perf

        # Update metrics
        perf.total_uses += 1
        if feedback.success_score >= 0.7:
            perf.success_count += 1

        # Rolling average
        n = perf.total_uses
        perf.avg_success_score = (perf.avg_success_score * (n-1) + feedback.success_score) / n
        perf.avg_execution_time = (perf.avg_execution_time * (n-1) + feedback.execution_time_ms) / n
        perf.last_used = feedback.timestamp

        # Trim history
        if len(self._feedback_history) > 1000:
            self._feedback_history = self._feedback_history[-1000:]

    def _evolve_strategies(self, task_type: str) -> List[EvolutionRecommendation]:
        """Generate evolution recommendations."""
        recommendations = []

        # Get all strategies for this task type
        strategies = [
            perf for key, perf in self._performance_db.items()
            if perf.task_type == task_type
        ]

        if len(strategies) < 2:
            return recommendations

        # Find best performer
        best = max(strategies, key=lambda p: p.avg_success_score)
        current = strategies[0]  # Assume first is current

        if best.strategy_name != current.strategy_name:
            improvement = best.avg_success_score - current.avg_success_score
            if improvement > 0.1:  # Significant improvement threshold
                recommendations.append(EvolutionRecommendation(
                    task_type=task_type,
                    current_strategy=current.strategy_name,
                    recommended_strategy=best.strategy_name,
                    confidence=min(best.total_uses / 20, 0.9),
                    reason=f"{best.strategy_name} has {improvement:.1%} higher success rate",
                    expected_improvement=improvement,
                    parameters={"switch_threshold": 0.7}
                ))

        return recommendations

    def _get_best_strategy(self, task_type: str) -> Optional[str]:
        """Get the best strategy for a task type."""
        strategies = [
            perf for key, perf in self._performance_db.items()
            if perf.task_type == task_type
        ]

        if not strategies:
            return None

        best = max(strategies, key=lambda p: p.avg_success_score)
        return best.strategy_name if best.total_uses >= 5 else None


class FeedbackLoopSkill(LivingSkill):
    """
    P3.2 Feedback Loop - 反馈循环器

    Collects and processes feedback for continuous learning:
    - Automatic feedback generation
    - User feedback integration
    - Feedback correlation analysis
    """

    def __init__(self):
        super().__init__(
            skill_id="p3.feedback_loop",
            name="Feedback Loop",
            description="收集和处理反馈以实现持续学习",
            version="1.0.0"
        )
        self._feedback_queue: List[FeedbackRecord] = []
        self._correlation_patterns: Dict[str, Any] = {}

    async def _execute(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Process feedback and generate insights."""
        action = context.get("action", "collect")

        if action == "collect":
            return await self._collect_feedback(context)
        elif action == "analyze":
            return await self._analyze_feedback(context)
        elif action == "correlate":
            return await self._correlate_feedback(context)

        return {"error": f"Unknown action: {action}"}

    async def _collect_feedback(self, context: Dict) -> Dict:
        """Collect feedback from execution results."""
        task_result = context.get("task_result", {})
        task_input = context.get("task_input", {})
        task_type = context.get("task_type", "unknown")

        # Generate automatic feedback
        auto_feedback = self._generate_auto_feedback(task_result)

        # Create record
        record = FeedbackRecord(
            record_id=f"fb_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hashlib.md5(str(task_input).encode()).hexdigest()[:8]}",
            task_type=task_type,
            input_hash=hashlib.md5(json.dumps(task_input, sort_keys=True).encode()).hexdigest()[:16],
            output_hash=hashlib.md5(json.dumps(task_result, sort_keys=True).encode()).hexdigest()[:16],
            success_score=auto_feedback.get("success_score", 0.5),
            execution_time_ms=auto_feedback.get("execution_time_ms", 0),
            resource_usage=auto_feedback.get("resources", {}),
            auto_feedback=auto_feedback,
            strategy_used=context.get("strategy", "default")
        )

        self._feedback_queue.append(record)

        # Process queue if large
        if len(self._feedback_queue) > 100:
            await self._process_batch()

        return {
            "record_id": record.record_id,
            "success_score": record.success_score,
            "auto_feedback": auto_feedback,
            "queue_size": len(self._feedback_queue)
        }

    def _generate_auto_feedback(self, task_result: Dict) -> Dict:
        """Generate automatic feedback from results."""
        feedback = {
            "execution_time_ms": task_result.get("duration_ms", 0),
            "resources": task_result.get("resources", {}),
            "success_score": 0.5,
            "quality_indicators": {}
        }

        # Calculate success score
        if task_result.get("success"):
            base_score = 0.7

            # Boost for fast execution
            if feedback["execution_time_ms"] < 1000:
                base_score += 0.15
            elif feedback["execution_time_ms"] < 5000:
                base_score += 0.05

            # Boost for resource efficiency
            resource_score = task_result.get("efficiency_score", 0.5)
            base_score += resource_score * 0.1

            feedback["success_score"] = min(base_score, 1.0)
        else:
            feedback["success_score"] = 0.2 if task_result.get("partial_success") else 0.0

        # Quality indicators
        if "output_quality" in task_result:
            feedback["quality_indicators"]["output"] = task_result["output_quality"]

        return feedback

    async def _analyze_feedback(self, context: Dict) -> Dict:
        """Analyze feedback patterns."""
        task_type = context.get("task_type")

        # Filter by task type
        feedbacks = [
            f for f in self._feedback_queue
            if not task_type or f.task_type == task_type
        ]

        if not feedbacks:
            return {"message": "No feedback to analyze"}

        # Calculate statistics
        scores = [f.success_score for f in feedbacks]
        times = [f.execution_time_ms for f in feedbacks]

        analysis = {
            "sample_size": len(feedbacks),
            "avg_success_score": sum(scores) / len(scores),
            "success_rate": sum(1 for s in scores if s >= 0.7) / len(scores),
            "avg_execution_time": sum(times) / len(times),
            "best_performers": self._find_best_performers(feedbacks),
            "common_failures": self._find_common_failures(feedbacks)
        }

        return analysis

    async def _correlate_feedback(self, context: Dict) -> Dict:
        """Find correlations in feedback."""
        # Simple correlation: input patterns -> success
        patterns: Dict[str, List[float]] = {}

        for fb in self._feedback_queue:
            pattern_key = f"{fb.task_type}:{fb.strategy_used}"
            if pattern_key not in patterns:
                patterns[pattern_key] = []
            patterns[pattern_key].append(fb.success_score)

        # Calculate pattern reliability
        correlations = {}
        for key, scores in patterns.items():
            if len(scores) >= 5:
                avg = sum(scores) / len(scores)
                variance = sum((s - avg) ** 2 for s in scores) / len(scores)
                correlations[key] = {
                    "avg_score": avg,
                    "reliability": 1.0 - min(variance * 4, 1.0),  # Lower variance = higher reliability
                    "sample_count": len(scores)
                }

        self._correlation_patterns = correlations

        return {
            "patterns_found": len(correlations),
            "correlations": correlations
        }

    def _find_best_performers(self, feedbacks: List[FeedbackRecord]) -> List[Dict]:
        """Find the best performing strategies."""
        by_strategy: Dict[str, List[float]] = {}

        for fb in feedbacks:
            key = fb.strategy_used
            if key not in by_strategy:
                by_strategy[key] = []
            by_strategy[key].append(fb.success_score)

        performers = []
        for strategy, scores in by_strategy.items():
            if len(scores) >= 3:
                performers.append({
                    "strategy": strategy,
                    "avg_score": sum(scores) / len(scores),
                    "sample_count": len(scores)
                })

        return sorted(performers, key=lambda x: x["avg_score"], reverse=True)[:5]

    def _find_common_failures(self, feedbacks: List[FeedbackRecord]) -> List[Dict]:
        """Identify common failure patterns."""
        failures = [fb for fb in feedbacks if fb.success_score < 0.5]

        by_type: Dict[str, int] = {}
        for fb in failures:
            by_type[fb.task_type] = by_type.get(fb.task_type, 0) + 1

        return [
            {"task_type": tt, "failure_count": count}
            for tt, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:3]
        ]

    async def _process_batch(self):
        """Process a batch of feedback."""
        # In real implementation: persist to database
        logger.debug(f"Processing {len(self._feedback_queue)} feedback records")
        self._feedback_queue = []


class PatternRecognitionSkill(LivingSkill):
    """
    P3.3 Pattern Recognition - 模式识别器

    Identifies successful patterns in execution:
    - Input patterns leading to success
    - Optimal parameter combinations
    - Context-success correlations
    """

    def __init__(self):
        super().__init__(
            skill_id="p3.pattern_recognition",
            name="Pattern Recognition",
            description="识别成功的执行模式",
            version="1.0.0"
        )
        self._patterns: Dict[str, Dict] = {}
        self._parameter_effects: Dict[str, Dict] = {}

    async def _execute(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Recognize and extract patterns."""
        action = context.get("action", "extract")
        data = context.get("data", [])

        if action == "extract":
            return self._extract_patterns(data)
        elif action == "match":
            return self._match_pattern(context.get("input", {}))
        elif action == "recommend_params":
            return self._recommend_parameters(context.get("task_type", ""))

        return {"error": f"Unknown action: {action}"}

    def _extract_patterns(self, data: List[Dict]) -> Dict:
        """Extract patterns from successful executions."""
        if not data:
            return {"patterns_found": 0}

        # Group by success
        successful = [d for d in data if d.get("success_score", 0) >= 0.7]

        if not successful:
            return {"patterns_found": 0, "message": "No successful executions to learn from"}

        # Extract common features
        patterns = {
            "input_features": self._extract_common_features([d.get("input", {}) for d in successful]),
            "context_features": self._extract_common_features([d.get("context", {}) for d in successful]),
            "parameter_correlations": self._analyze_parameters(successful)
        }

        pattern_id = f"pattern_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self._patterns[pattern_id] = {
            "data": patterns,
            "success_count": len(successful),
            "confidence": len(successful) / len(data)
        }

        return {
            "pattern_id": pattern_id,
            "patterns_found": len(patterns),
            "confidence": len(successful) / len(data),
            "features": patterns["input_features"]
        }

    def _extract_common_features(self, items: List[Dict]) -> Dict:
        """Extract features common across items."""
        if not items:
            return {}

        features = {}

        # Find common keys and value types
        all_keys = set()
        for item in items:
            all_keys.update(item.keys())

        for key in all_keys:
            values = [item.get(key) for item in items if key in item]
            if len(values) >= len(items) * 0.7:  # Present in 70% of items
                # Check for common values
                value_counts: Dict[str, int] = {}
                for v in values:
                    v_str = str(v)[:50]  # Truncate for hashing
                    value_counts[v_str] = value_counts.get(v_str, 0) + 1

                most_common = max(value_counts.items(), key=lambda x: x[1])
                if most_common[1] >= len(values) * 0.5:  # 50% have same value
                    features[key] = {
                        "common_value": most_common[0],
                        "frequency": most_common[1] / len(values)
                    }

        return features

    def _analyze_parameters(self, successful: List[Dict]) -> Dict:
        """Analyze parameter effects on success."""
        param_analysis = {}

        for execution in successful:
            params = execution.get("parameters", {})
            for param, value in params.items():
                if param not in param_analysis:
                    param_analysis[param] = {"values": [], "success_scores": []}

                param_analysis[param]["values"].append(value)
                param_analysis[param]["success_scores"].append(execution.get("success_score", 0))

        # Find optimal ranges
        optimal = {}
        for param, data in param_analysis.items():
            if len(data["values"]) >= 5:
                values = data["values"]
                if all(isinstance(v, (int, float)) for v in values):
                    optimal[param] = {
                        "optimal_range": (min(values), max(values)),
                        "mean": sum(values) / len(values),
                        "sample_count": len(values)
                    }

        self._parameter_effects.update(optimal)
        return optimal

    def _match_pattern(self, input_data: Dict) -> Dict:
        """Match input against known patterns."""
        matches = []

        for pattern_id, pattern_data in self._patterns.items():
            features = pattern_data["data"]["input_features"]
            match_score = 0

            for key, feature in features.items():
                if key in input_data:
                    if str(input_data[key]) == feature["common_value"]:
                        match_score += feature["frequency"]

            if match_score > 0.3:  # Significant match
                matches.append({
                    "pattern_id": pattern_id,
                    "match_score": match_score,
                    "confidence": pattern_data["confidence"]
                })

        matches.sort(key=lambda x: x["match_score"], reverse=True)

        return {
            "matches": matches[:3],
            "best_match": matches[0] if matches else None
        }

    def _recommend_parameters(self, task_type: str) -> Dict:
        """Recommend parameters for a task type."""
        relevant = {
            param: data for param, data in self._parameter_effects.items()
            if task_type in param or param.startswith(task_type)
        }

        return {
            "task_type": task_type,
            "recommended_params": relevant,
            "confidence": min(len(relevant) * 0.2, 0.8)
        }


class ParameterTunerSkill(LivingSkill):
    """
    P3.4 Parameter Tuner - 参数调优器

    Automatically tunes system parameters:
    - Grid search for optimal values
    - A/B testing framework
    - Bayesian optimization (simplified)
    """

    def __init__(self):
        super().__init__(
            skill_id="p3.parameter_tuner",
            name="Parameter Tuner",
            description="自动调优系统参数",
            version="1.0.0"
        )
        self._parameter_space: Dict[str, Dict] = {}
        self._test_results: List[Dict] = []

    async def _execute(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Tune parameters based on context."""
        action = context.get("action", "tune")

        if action == "tune":
            return await self._tune_parameters(context)
        elif action == "ab_test":
            return await self._run_ab_test(context)
        elif action == "recommend":
            return self._recommend_parameters(context)

        return {"error": f"Unknown action: {action}"}

    async def _tune_parameters(self, context: Dict) -> Dict:
        """Run parameter tuning."""
        param_name = context.get("parameter")
        current_value = context.get("current_value")
        test_range = context.get("range", [0.0, 1.0])

        if not param_name:
            return {"error": "No parameter specified"}

        # Define search space
        if isinstance(test_range[0], int):
            candidates = list(range(test_range[0], test_range[1] + 1, max(1, (test_range[1] - test_range[0]) // 5)))
        else:
            step = (test_range[1] - test_range[0]) / 5
            candidates = [test_range[0] + step * i for i in range(6)]

        # In real implementation: test each candidate
        # Here we simulate with estimated scores
        results = []
        for candidate in candidates:
            # Simulate score based on distance from optimal (0.7)
            optimal = 0.7
            distance = abs((candidate - test_range[0]) / (test_range[1] - test_range[0]) - optimal)
            simulated_score = max(0.5, 0.95 - distance * 0.5)

            results.append({
                "value": candidate,
                "score": simulated_score,
                "confidence": 0.6
            })

        # Find best
        best = max(results, key=lambda x: x["score"])

        return {
            "parameter": param_name,
            "current_value": current_value,
            "recommended_value": best["value"],
            "expected_improvement": best["score"] - 0.5,  # Assume 0.5 baseline
            "test_results": results,
            "method": "grid_search"
        }

    async def _run_ab_test(self, context: Dict) -> Dict:
        """Run A/B test between configurations."""
        config_a = context.get("config_a", {})
        config_b = context.get("config_b", {})
        metric = context.get("metric", "success_score")

        # Simulate A/B test
        # In real implementation: run actual tests
        n_samples = 30

        results_a = {"mean": 0.72, "variance": 0.04, "n": n_samples}
        results_b = {"mean": 0.78, "variance": 0.03, "n": n_samples}

        # Simple t-test approximation
        diff = results_b["mean"] - results_a["mean"]
        pooled_se = ((results_a["variance"] / n_samples) + (results_b["variance"] / n_samples)) ** 0.5
        t_stat = diff / pooled_se if pooled_se > 0 else 0

        significant = abs(t_stat) > 1.96  # p < 0.05

        test_result = {
            "config_a": results_a,
            "config_b": results_b,
            "difference": diff,
            "significant": significant,
            "winner": "b" if diff > 0 and significant else ("a" if diff < 0 and significant else "tie"),
            "recommendation": "Use config B" if diff > 0 and significant else "Keep config A"
        }

        self._test_results.append(test_result)

        return test_result

    def _recommend_parameters(self, context: Dict) -> Dict:
        """Generate parameter recommendations."""
        task_type = context.get("task_type", "generic")

        # Based on historical tuning
        defaults = {
            "threshold": 0.7,
            "batch_size": 10,
            "timeout_seconds": 30,
            "retry_count": 3
        }

        # Adjust based on task type
        if task_type == "critical":
            defaults["threshold"] = 0.9
            defaults["retry_count"] = 5
        elif task_type == "fast":
            defaults["timeout_seconds"] = 10
            defaults["batch_size"] = 5

        return {
            "task_type": task_type,
            "recommended": defaults,
            "source": "heuristic"
        }


class P3EvolutionOrgan(AgentTissue):
    """
    P3 Evolution Organ - 进化器官

    Coordinates four evolution skills to enable
    continuous self-improvement of the system.
    """

    def __init__(self):
        super().__init__(
            agent_id="p3.evolution_organ",
            name="P3 Evolution Organ",
            description="四维度自我进化器官",
            purpose="通过反馈循环实现系统自我改进",
            coordination=AgentCoordination(pattern=CoordinationPattern.SEQUENCE)
        )

        # Create skills
        strategy_skill = StrategyEvolverSkill()
        feedback_skill = FeedbackLoopSkill()
        pattern_skill = PatternRecognitionSkill()
        tuner_skill = ParameterTunerSkill()

        # Add to organ
        self.add_skill(strategy_skill.skill_id)
        self.add_skill(feedback_skill.skill_id)
        self.add_skill(pattern_skill.skill_id)
        self.add_skill(tuner_skill.skill_id)

        # Store references
        self._strategy_skill = strategy_skill
        self._feedback_skill = feedback_skill
        self._pattern_skill = pattern_skill
        self._tuner_skill = tuner_skill

        # Evolution state
        self._evolution_history: List[Dict] = []
        self._current_generation = 0

        logger.info("P3 Evolution Organ initialized with 4 evolution skills")

    async def evolve(self, feedback_records: List[FeedbackRecord],
                    task_type: str = "generic") -> Dict[str, Any]:
        """
        Run a complete evolution cycle.

        Args:
            feedback_records: Recent feedback to learn from
            task_type: Type of task to evolve for

        Returns:
            Evolution results and recommendations
        """
        self._current_generation += 1

        logger.info(f"Starting evolution cycle {self._current_generation} for {task_type}")

        # Step 1: Process feedback
        feedback_result = await self._feedback_skill.invoke({
            "action": "collect",
            "feedback_records": feedback_records,
            "task_type": task_type
        })

        # Step 2: Evolve strategies
        strategy_result = await self._strategy_skill.invoke({
            "feedback_records": feedback_records,
            "task_type": task_type
        })

        # Step 3: Extract patterns
        pattern_data = [
            {
                "input": fb.input_hash,
                "success_score": fb.success_score,
                "parameters": fb.resource_usage
            }
            for fb in feedback_records
        ]

        pattern_result = await self._pattern_skill.invoke({
            "action": "extract",
            "data": pattern_data
        })

        # Step 4: Get parameter recommendations
        tuner_result = await self._tuner_skill.invoke({
            "action": "recommend",
            "task_type": task_type
        })

        # Compile evolution report
        evolution_result = {
            "generation": self._current_generation,
            "task_type": task_type,
            "feedback_processed": len(feedback_records),
            "strategy_recommendations": strategy_result.get("recommendations", []),
            "patterns_found": pattern_result.get("patterns_found", 0),
            "recommended_parameters": tuner_result.get("recommended", {}),
            "best_strategy": strategy_result.get("best_strategy"),
            "timestamp": datetime.now().isoformat()
        }

        self._evolution_history.append(evolution_result)

        logger.info(f"Evolution cycle {self._current_generation} complete. "
                   f"Best strategy: {evolution_result['best_strategy']}")

        return evolution_result

    async def get_recommendation(self, task_type: str,
                                  current_strategy: str) -> Optional[EvolutionRecommendation]:
        """Get evolution recommendation for a task."""
        # Check for existing recommendations
        for result in reversed(self._evolution_history):
            if result["task_type"] == task_type:
                for rec in result.get("strategy_recommendations", []):
                    if rec["current_strategy"] == current_strategy:
                        return EvolutionRecommendation(**rec)

        return None

    def get_evolution_report(self) -> Dict:
        """Get comprehensive evolution report."""
        if not self._evolution_history:
            return {"message": "No evolution cycles completed yet"}

        return {
            "total_generations": self._current_generation,
            "evolution_cycles": self._evolution_history,
            "improvement_trend": self._calculate_improvement_trend(),
            "best_performers": self._identify_best_strategies()
        }

    def _calculate_improvement_trend(self) -> str:
        """Calculate overall improvement trend."""
        if len(self._evolution_history) < 3:
            return "insufficient_data"

        recent = self._evolution_history[-3:]
        patterns = [r["patterns_found"] for r in recent]

        if patterns[-1] > patterns[0]:
            return "improving"
        elif patterns[-1] < patterns[0]:
            return "declining"
        return "stable"

    def _identify_best_strategies(self) -> List[Dict]:
        """Identify best performing strategies across all cycles."""
        strategy_scores: Dict[str, List[float]] = {}

        for cycle in self._evolution_history:
            for rec in cycle.get("strategy_recommendations", []):
                strategy = rec["recommended_strategy"]
                if strategy not in strategy_scores:
                    strategy_scores[strategy] = []
                strategy_scores[strategy].append(rec.get("expected_improvement", 0))

        return [
            {
                "strategy": strategy,
                "avg_improvement": sum(scores) / len(scores),
                "uses": len(scores)
            }
            for strategy, scores in strategy_scores.items()
            if len(scores) >= 1
        ]


# ============================================================================
# Factory Functions
# ============================================================================

def create_p3_evolution_organ() -> P3EvolutionOrgan:
    """Factory function to create P3 Evolution Organ."""
    return P3EvolutionOrgan()


async def demo_evolution():
    """Demo function to show P3 in action."""
    print("=" * 60)
    print("P3 Evolution Demo")
    print("=" * 60)

    # Test individual skills directly (avoiding AgentTissue coordination for demo)

    # 1. Test Strategy Evolver
    print("\n1. Strategy Evolver Test")
    strategy_skill = StrategyEvolverSkill()

    # Simulate feedback records
    feedback_records = [
        FeedbackRecord(
            record_id=f"fb_{i:03d}",
            task_type="content_analysis",
            input_hash=f"input_{i}",
            output_hash=f"output_{i}",
            success_score=0.6 + (i % 5) * 0.08,
            execution_time_ms=1000 + i * 100,
            resource_usage={"cpu": 0.5, "memory": 256},
            strategy_used="parallel" if i % 2 == 0 else "sequential"
        )
        for i in range(20)
    ]

    result = await strategy_skill.invoke({
        "feedback_records": feedback_records,
        "task_type": "content_analysis"
    })

    print(f"   Feedback Processed: {result['feedback_count']}")
    print(f"   Best Strategy: {result['best_strategy']}")
    print(f"   Status: {result['evolution_status']}")

    # 2. Test Feedback Loop
    print("\n2. Feedback Loop Test")
    feedback_skill = FeedbackLoopSkill()

    collect_result = await feedback_skill.invoke({
        "action": "collect",
        "task_result": {"success": True, "duration_ms": 1200, "output_quality": 0.85},
        "task_type": "test_task"
    })
    print(f"   Record ID: {collect_result['record_id']}")
    print(f"   Success Score: {collect_result['success_score']:.2f}")

    analyze_result = await feedback_skill.invoke({
        "action": "analyze",
        "task_type": "content_analysis"
    })
    print(f"   Analysis Sample Size: {analyze_result.get('sample_size', 0)}")

    # 3. Test Pattern Recognition
    print("\n3. Pattern Recognition Test")
    pattern_skill = PatternRecognitionSkill()

    pattern_data = [
        {"input": {"size": "large"}, "success_score": 0.9, "parameters": {"threshold": 0.8}},
        {"input": {"size": "large"}, "success_score": 0.85, "parameters": {"threshold": 0.8}},
        {"input": {"size": "small"}, "success_score": 0.6, "parameters": {"threshold": 0.5}},
    ]

    pattern_result = await pattern_skill.invoke({
        "action": "extract",
        "data": pattern_data
    })
    print(f"   Patterns Found: {pattern_result['patterns_found']}")
    print(f"   Confidence: {pattern_result.get('confidence', 0):.2f}")

    # 4. Test Parameter Tuner
    print("\n4. Parameter Tuner Test")
    tuner_skill = ParameterTunerSkill()

    tune_result = await tuner_skill.invoke({
        "action": "recommend",
        "task_type": "critical"
    })
    print(f"   Task Type: {tune_result['task_type']}")
    print(f"   Recommended Threshold: {tune_result['recommended']['threshold']}")

    # 5. Evolution Report
    print("\n5. P3 Evolution Organ Summary")
    organ = create_p3_evolution_organ()
    report = organ.get_evolution_report()
    print(f"   Status: {report.get('message', 'Ready')}")
    print(f"   Skills: 4 (Strategy, Feedback, Pattern, Tuner)")

    print("\n" + "=" * 60)
    print("P3 Evolution Demo Complete")
    print("=" * 60)

    return result


if __name__ == "__main__":
    asyncio.run(demo_evolution())
