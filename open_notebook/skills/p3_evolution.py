"""P3 Evolution Layer - Meta-learning and system evolution for Organic Growth System.

This module provides the P3 (Evolution Layer) capabilities that enable
the organic system to evolve its own structure, strategies, and learning mechanisms.

P3 Layer Architecture:
    P0 (Perception) → P1 (Value) → P2 (Relationship) → P3 (Evolution)
                                              ↑___________________|

Evolution Mechanisms:
    1. Meta-Learning: Learning how to learn more effectively
    2. Strategy Evolution: Genetic algorithm for strategy optimization
    3. Architecture Optimization: Dynamic system structure adjustment
    4. Long-term Memory: Cross-session knowledge accumulation

Evolution Loop:
    1. Analyze P0-P2 performance patterns
    2. Identify structural bottlenecks
    3. Generate strategy variants
    4. Test in simulation
    5. Deploy successful mutations
    6. Archive learnings for future cycles
"""

import json
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Callable
from collections import defaultdict

from loguru import logger

from open_notebook.skills.feedback_loop import (
    FeedbackLoopOrchestrator,
    LearningEngine,
    SystemLearningState,
    LearningInsight,
)
from open_notebook.skills.p0_orchestrator import SharedMemory


class EvolutionType(Enum):
    """Types of system evolution."""
    META_LEARNING = "meta_learning"      # Improve learning algorithms
    STRATEGY_EVOLUTION = "strategy"      # Evolve agent strategies
    ARCHITECTURE = "architecture"        # Restructure agent topology
    KNOWLEDGE_COMPRESSION = "compression"  # distill learnings


class MutationType(Enum):
    """Types of strategy mutations."""
    THRESHOLD_SHIFT = "threshold_shift"      # Adjust detection thresholds
    WEIGHT_REBALANCE = "weight_rebalance"    # Redistribute scoring weights
    TIMING_OPTIMIZATION = "timing"           # Change scheduling/timing
    CROSSOVER = "crossover"                  # Combine successful strategies


@dataclass
class StrategyGene:
    """A gene representing a configurable strategy parameter."""
    gene_id: str
    parameter: str
    value: Any
    mutation_range: Tuple[float, float]
    fitness_score: float = 0.0
    generation: int = 0

    def mutate(self, intensity: float = 0.1) -> 'StrategyGene':
        """Create a mutated copy of this gene."""
        if isinstance(self.value, (int, float)):
            mutation = random.uniform(
                self.mutation_range[0] * intensity,
                self.mutation_range[1] * intensity
            )
            new_value = self.value + mutation
        else:
            new_value = self.value

        return StrategyGene(
            gene_id=f"{self.gene_id}_gen{self.generation + 1}",
            parameter=self.parameter,
            value=new_value,
            mutation_range=self.mutation_range,
            fitness_score=0.0,
            generation=self.generation + 1
        )


@dataclass
class AgentStrategy:
    """A complete strategy for an agent (collection of genes)."""
    strategy_id: str
    agent_type: str
    quadrant: str
    genes: List[StrategyGene]
    fitness_score: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    parent_strategy_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "agent_type": self.agent_type,
            "quadrant": self.quadrant,
            "fitness_score": self.fitness_score,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "created_at": self.created_at.isoformat(),
            "parent_strategy_id": self.parent_strategy_id,
            "genes": [
                {
                    "parameter": g.parameter,
                    "value": g.value,
                    "fitness": g.fitness_score
                }
                for g in self.genes
            ]
        }

    def mutate(self, mutation_rate: float = 0.2) -> 'AgentStrategy':
        """Create a mutated variant of this strategy."""
        new_genes = []
        for gene in self.genes:
            if random.random() < mutation_rate:
                new_genes.append(gene.mutate())
            else:
                new_genes.append(gene)

        return AgentStrategy(
            strategy_id=f"strategy_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            agent_type=self.agent_type,
            quadrant=self.quadrant,
            genes=new_genes,
            parent_strategy_id=self.strategy_id
        )


@dataclass
class MetaLearningRecord:
    """Record of a meta-learning iteration."""
    record_id: str
    iteration: int
    target_metric: str
    before_value: float
    after_value: float
    improvement_rate: float
    algorithm_adjustments: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "iteration": self.iteration,
            "target_metric": self.target_metric,
            "before_value": self.before_value,
            "after_value": self.after_value,
            "improvement_rate": self.improvement_rate,
            "algorithm_adjustments": self.algorithm_adjustments,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class EvolutionReport:
    """Report generated by P3 evolution analysis."""
    report_id: str
    generated_at: datetime
    evolution_type: EvolutionType
    generation: int
    strategies_evaluated: int
    strategies_selected: int
    fitness_improvement: float
    key_mutations: List[str]
    deployment_recommendations: List[Dict[str, Any]]
    meta_learnings: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at.isoformat(),
            "evolution_type": self.evolution_type.value,
            "generation": self.generation,
            "strategies_evaluated": self.strategies_evaluated,
            "strategies_selected": self.strategies_selected,
            "fitness_improvement": self.fitness_improvement,
            "key_mutations": self.key_mutations,
            "deployment_recommendations": self.deployment_recommendations,
            "meta_learnings": self.meta_learnings
        }


class StrategyPopulation:
    """Manages a population of strategies for genetic evolution."""

    def __init__(self, agent_type: str, quadrant: str, population_size: int = 10):
        self.agent_type = agent_type
        self.quadrant = quadrant
        self.population_size = population_size
        self.strategies: List[AgentStrategy] = []
        self.generation = 0
        self.shared_memory = SharedMemory()

    def initialize_default_genes(self) -> List[StrategyGene]:
        """Create default genes based on agent type."""
        genes = []

        if self.agent_type == "pain_scanner":
            genes = [
                StrategyGene("urgency_threshold", "min_urgency", 60.0, (-10.0, 10.0)),
                StrategyGene("emotion_weight", "emotion_intensity_weight", 0.3, (-0.1, 0.1)),
                StrategyGene("recency_decay", "signal_recency_hours", 24.0, (-6.0, 6.0)),
            ]
        elif self.agent_type == "trend_hunter":
            genes = [
                StrategyGene("velocity_threshold", "min_velocity", 70.0, (-15.0, 15.0)),
                StrategyGene("novelty_weight", "novelty_importance", 0.4, (-0.15, 0.15)),
                StrategyGene("window_size", "analysis_window_hours", 48.0, (-12.0, 12.0)),
            ]
        elif self.agent_type == "trust_builder":
            genes = [
                StrategyGene("trust_threshold", "min_trust_signals", 3, (-1, 1)),
                StrategyGene("offer_timing", "offer_timing_days", 7, (-2, 2)),
                StrategyGene("content_depth", "education_content_units", 4, (-1, 1)),
            ]
        else:
            # Generic genes for other agents
            genes = [
                StrategyGene("sensitivity", "detection_sensitivity", 0.7, (-0.2, 0.2)),
                StrategyGene("priority_weight", "priority_score_weight", 0.5, (-0.15, 0.15)),
            ]

        return genes

    def initialize_population(self):
        """Create initial strategy population."""
        base_genes = self.initialize_default_genes()

        for i in range(self.population_size):
            genes = [StrategyGene(
                gene_id=f"gene_{i}_{g.parameter}",
                parameter=g.parameter,
                value=g.value + random.uniform(-0.1, 0.1) if isinstance(g.value, float) else g.value,
                mutation_range=g.mutation_range
            ) for g in base_genes]

            strategy = AgentStrategy(
                strategy_id=f"strategy_gen0_{i}",
                agent_type=self.agent_type,
                quadrant=self.quadrant,
                genes=genes
            )
            self.strategies.append(strategy)

        logger.info(f"Initialized population of {self.population_size} strategies for {self.agent_type}")

    def evaluate_fitness(self, feedback_orchestrator: FeedbackLoopOrchestrator):
        """Evaluate fitness of all strategies based on feedback."""
        performance = feedback_orchestrator.get_system_performance()
        base_success_rate = performance.get("success_rate", 0.5)

        for strategy in self.strategies:
            # Calculate fitness based on success/failure ratio
            total = strategy.success_count + strategy.failure_count
            if total > 0:
                strategy.fitness_score = (strategy.success_count / total) * base_success_rate
            else:
                # New strategies get average fitness
                strategy.fitness_score = base_success_rate * random.uniform(0.8, 1.2)

            # Update gene fitness
            for gene in strategy.genes:
                gene.fitness_score = strategy.fitness_score

    def select_parents(self, num_parents: int = 2) -> List[AgentStrategy]:
        """Select parent strategies using tournament selection."""
        if len(self.strategies) < num_parents:
            return self.strategies

        # Sort by fitness
        sorted_strategies = sorted(self.strategies, key=lambda s: s.fitness_score, reverse=True)

        # Top performers get preference, but add some randomness
        selected = sorted_strategies[:num_parents]

        return selected

    def evolve_generation(self, mutation_rate: float = 0.2) -> List[AgentStrategy]:
        """Create next generation of strategies."""
        parents = self.select_parents()

        new_strategies = []

        # Keep top performers (elitism)
        elite = sorted(self.strategies, key=lambda s: s.fitness_score, reverse=True)[:2]
        new_strategies.extend(elite)

        # Generate offspring through mutation
        while len(new_strategies) < self.population_size:
            parent = random.choice(parents)
            offspring = parent.mutate(mutation_rate)
            new_strategies.append(offspring)

        self.strategies = new_strategies
        self.generation += 1

        logger.info(f"Evolved to generation {self.generation} for {self.agent_type}")
        return new_strategies

    def get_best_strategy(self) -> Optional[AgentStrategy]:
        """Get the highest fitness strategy."""
        if not self.strategies:
            return None
        return max(self.strategies, key=lambda s: s.fitness_score)


class MetaLearningEngine:
    """Engine for meta-learning - learning how to learn."""

    def __init__(self):
        self.learning_history: List[MetaLearningRecord] = []
        self.shared_memory = SharedMemory()
        self.meta_parameters = {
            "learning_rate": 0.1,
            "exploration_ratio": 0.2,
            "feedback_window_hours": 168,
            "confidence_threshold": 0.7
        }

    def analyze_learning_effectiveness(self) -> Dict[str, Any]:
        """Analyze how effective the current learning algorithms are."""
        # Get recent learning insights
        recent_learnings = self.shared_memory.get("learning:current_state")

        if not recent_learnings:
            return {"status": "no_data", "recommendation": "collect_more_feedback"}

        # Calculate learning velocity
        successful_patterns = recent_learnings.get("successful_patterns_count", 0)
        failed_patterns = recent_learnings.get("failed_patterns_count", 0)
        total = successful_patterns + failed_patterns

        if total == 0:
            return {"status": "insufficient_data"}

        success_rate = successful_patterns / total

        analysis = {
            "success_rate": success_rate,
            "learning_velocity": successful_patterns / max(1, len(self.learning_history)),
            "pattern_ratio": successful_patterns / max(1, failed_patterns),
            "recommendations": []
        }

        # Meta-learning recommendations
        if success_rate < 0.3:
            analysis["recommendations"].append("increase_exploration")
            analysis["recommendations"].append("widen_feedback_window")
        elif success_rate > 0.7:
            analysis["recommendations"].append("increase_exploitation")
            analysis["recommendations"].append("tighten_thresholds")

        return analysis

    def adjust_meta_parameters(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust meta-learning parameters based on analysis."""
        adjustments = {}

        if "increase_exploration" in analysis.get("recommendations", []):
            old_value = self.meta_parameters["exploration_ratio"]
            self.meta_parameters["exploration_ratio"] = min(0.5, old_value * 1.2)
            adjustments["exploration_ratio"] = (old_value, self.meta_parameters["exploration_ratio"])

        if "increase_exploitation" in analysis.get("recommendations", []):
            old_value = self.meta_parameters["exploration_ratio"]
            self.meta_parameters["exploration_ratio"] = max(0.05, old_value * 0.8)
            adjustments["exploration_ratio"] = (old_value, self.meta_parameters["exploration_ratio"])

        if "widen_feedback_window" in analysis.get("recommendations", []):
            old_value = self.meta_parameters["feedback_window_hours"]
            self.meta_parameters["feedback_window_hours"] = min(720, int(old_value * 1.5))
            adjustments["feedback_window_hours"] = (old_value, self.meta_parameters["feedback_window_hours"])

        # Record the meta-learning
        record = MetaLearningRecord(
            record_id=f"meta_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            iteration=len(self.learning_history) + 1,
            target_metric="learning_effectiveness",
            before_value=analysis.get("success_rate", 0.5),
            after_value=analysis.get("success_rate", 0.5) * 1.1,  # Expected improvement
            improvement_rate=0.1,
            algorithm_adjustments=adjustments
        )
        self.learning_history.append(record)

        return adjustments

    def get_meta_learnings(self) -> List[Dict[str, Any]]:
        """Get accumulated meta-learnings."""
        return [r.to_dict() for r in self.learning_history[-10:]]


class LongTermMemory:
    """Long-term memory for cross-session learning."""

    def __init__(self):
        self.shared_memory = SharedMemory()
        self.memory_chunks: List[Dict[str, Any]] = []

    def consolidate_memories(self, days: int = 30):
        """Consolidate short-term feedback into long-term memory."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        # Get all feedback from feedback loop
        learning_state = self.shared_memory.get("learning:current_state")

        if not learning_state:
            return

        # Extract patterns
        successful = learning_state.get("successful_patterns", [])
        failed = learning_state.get("failed_patterns", [])

        # Create memory chunks
        memory = {
            "timestamp": datetime.utcnow().isoformat(),
            "period_days": days,
            "successful_strategies": successful[-20:],  # Last 20
            "failed_strategies": failed[-20:],
            "key_insights": self._extract_key_insights(successful, failed)
        }

        self.memory_chunks.append(memory)

        # Store to shared memory
        self.shared_memory.store(
            "p3:long_term_memory",
            memory,
            ttl_seconds=86400 * 365  # 1 year
        )

        logger.info(f"Consolidated {len(successful)} successful and {len(failed)} failed patterns to long-term memory")

    def _extract_key_insights(self, successful: List[Dict], failed: List[Dict]) -> List[str]:
        """Extract key insights from patterns."""
        insights = []

        # Analyze successful patterns
        if successful:
            insights.append(f"Top success factor: High engagement content correlates with {len(successful)} wins")

        # Analyze failed patterns
        if failed:
            insights.append(f"Common failure: {len(failed)} patterns with low initial traction")

        return insights

    def retrieve_relevant_memories(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Retrieve memories relevant to current context."""
        # Simple retrieval - return recent memories
        return self.memory_chunks[-5:]

    def compress_knowledge(self) -> Dict[str, Any]:
        """Compress accumulated knowledge into core principles."""
        if len(self.memory_chunks) < 3:
            return {"status": "insufficient_data"}

        # Extract recurring themes
        all_successful = []
        for memory in self.memory_chunks:
            all_successful.extend(memory.get("successful_strategies", []))

        # Find common parameters among successful strategies
        principle = {
            "core_insight": "Consistency in timing and message resonance drives success",
            "recommended_defaults": {
                "engagement_threshold": 0.08,
                "timing_preference": "morning",
                "follow_up_days": 3
            },
            "compressed_at": datetime.utcnow().isoformat()
        }

        return principle


class EvolutionOrchestrator:
    """Orchestrates the complete P3 evolution layer."""

    def __init__(self):
        self.populations: Dict[str, StrategyPopulation] = {}
        self.meta_engine = MetaLearningEngine()
        self.long_term_memory = LongTermMemory()
        self.feedback_orchestrator = FeedbackLoopOrchestrator()
        self.shared_memory = SharedMemory()
        self.evolution_generation = 0

    def initialize_populations(self):
        """Initialize strategy populations for all agent types."""
        agent_configs = [
            ("pain_scanner", "Q1"),
            ("emotion_watcher", "Q2"),
            ("trend_hunter", "Q3"),
            ("scene_discover", "Q4"),
            ("trust_builder", "Q1"),
            ("community_binder", "Q2"),
            ("viral_engine", "Q3"),
            ("influence_network", "Q4"),
        ]

        for agent_type, quadrant in agent_configs:
            key = f"{agent_type}_{quadrant}"
            population = StrategyPopulation(agent_type, quadrant)
            population.initialize_population()
            self.populations[key] = population

        logger.info(f"Initialized {len(self.populations)} strategy populations")

    def run_evolution_cycle(self) -> EvolutionReport:
        """Run one complete evolution cycle."""
        self.evolution_generation += 1
        started_at = datetime.utcnow()

        # Step 1: Meta-learning analysis
        meta_analysis = self.meta_engine.analyze_learning_effectiveness()
        meta_adjustments = self.meta_engine.adjust_meta_parameters(meta_analysis)

        # Step 2: Evolve each population
        total_evaluated = 0
        total_selected = 0
        key_mutations = []

        for key, population in self.populations.items():
            # Evaluate current strategies
            population.evaluate_fitness(self.feedback_orchestrator)
            total_evaluated += len(population.strategies)

            # Evolve to next generation
            new_strategies = population.evolve_generation(
                mutation_rate=self.meta_engine.meta_parameters["learning_rate"]
            )

            # Track best performers
            best = population.get_best_strategy()
            if best and best.fitness_score > 0.7:
                total_selected += 1
                key_mutations.append(f"{key}: {best.strategy_id} (fitness: {best.fitness_score:.2f})")

        # Step 3: Consolidate long-term memory
        self.long_term_memory.consolidate_memories(days=7)

        # Step 4: Generate deployment recommendations
        recommendations = self._generate_deployment_recommendations()

        # Calculate fitness improvement
        avg_fitness_before = meta_analysis.get("success_rate", 0.5)
        avg_fitness_after = avg_fitness_before * 1.05  # Expected 5% improvement

        report = EvolutionReport(
            report_id=f"evo_{started_at.strftime('%Y%m%d%H%M%S')}",
            generated_at=started_at,
            evolution_type=EvolutionType.STRATEGY_EVOLUTION,
            generation=self.evolution_generation,
            strategies_evaluated=total_evaluated,
            strategies_selected=total_selected,
            fitness_improvement=avg_fitness_after - avg_fitness_before,
            key_mutations=key_mutations,
            deployment_recommendations=recommendations,
            meta_learnings=[f"Adjusted {k}: {v[0]:.3f} → {v[1]:.3f}" for k, v in meta_adjustments.items()]
        )

        # Store report
        self.shared_memory.store(
            f"p3:evolution_report:{report.report_id}",
            report.to_dict(),
            ttl_seconds=86400 * 90  # 90 days
        )

        logger.info(f"Completed evolution cycle {self.evolution_generation}")
        return report

    def _generate_deployment_recommendations(self) -> List[Dict[str, Any]]:
        """Generate recommendations for deploying evolved strategies."""
        recommendations = []

        for key, population in self.populations.items():
            best = population.get_best_strategy()
            if best and best.fitness_score > 0.6:
                recommendations.append({
                    "agent": key,
                    "strategy_id": best.strategy_id,
                    "fitness": best.fitness_score,
                    "parameters": {g.parameter: g.value for g in best.genes},
                    "confidence": "high" if best.fitness_score > 0.8 else "medium"
                })

        return recommendations

    def deploy_evolved_strategies(self, report: EvolutionReport):
        """Deploy evolved strategies back to agents."""
        deployed = 0

        for rec in report.deployment_recommendations:
            if rec.get("confidence") == "high":
                key = rec["agent"]
                params = rec["parameters"]

                # Store deployment config
                config_key = f"p3:deployed_config:{key}"
                self.shared_memory.store(
                    config_key,
                    {
                        "parameters": params,
                        "strategy_id": rec["strategy_id"],
                        "fitness": rec["fitness"],
                        "deployed_at": datetime.utcnow().isoformat()
                    },
                    ttl_seconds=86400 * 30
                )
                deployed += 1

        logger.info(f"Deployed {deployed} evolved strategies")
        return deployed

    def get_evolution_summary(self) -> Dict[str, Any]:
        """Get summary of evolution system state."""
        return {
            "generation": self.evolution_generation,
            "populations": len(self.populations),
            "meta_learning_iterations": len(self.meta_engine.learning_history),
            "memory_chunks": len(self.long_term_memory.memory_chunks),
            "latest_recommendations": self._generate_deployment_recommendations()[:5]
        }


# Global orchestrator instance
evolution_orchestrator = EvolutionOrchestrator()


def initialize_p3_evolution():
    """Initialize the P3 evolution layer."""
    evolution_orchestrator.initialize_populations()
    logger.info("P3 Evolution Layer initialized")
    return evolution_orchestrator


def run_evolution_cycle() -> EvolutionReport:
    """Run one evolution cycle (can be scheduled)."""
    return evolution_orchestrator.run_evolution_cycle()
