"""P0-P4 Full Integration Pipeline - End-to-end Living Knowledge System workflow.

This demonstrates the complete five-layer architecture working together:
1. P0 Perception: Detect information from various sources
2. P1 Judgment: Assess value and quality
3. P2 Relationship: Build knowledge graph connections
4. P3 Evolution: Learn and optimize strategies
5. P4 DataAgent: Manage data lifecycle

Usage:
    python -m open_notebook.skills.living.p0_p4_integration
"""

import asyncio
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from open_notebook.skills.living.database.memory import InMemoryDatabase
from open_notebook.skills.living.p4_data_agent import P4DataAgent, DataGenerationRule

# P0 Skills
from open_notebook.skills.living.skill_cell import LivingSkill, SkillState


class PainScannerSkill(LivingSkill):
    """P0.1 Detect friction points."""

    def __init__(self):
        super().__init__(
            skill_id="p0.pain_scanner",
            name="Pain Scanner",
            description="Detect user friction points",
            version="1.0.0"
        )

    async def _execute(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        user_input = context.get("user_input", "")

        pain_indicators = [
            "困难", "问题", "错误", "失败", "慢", "卡", "崩溃",
            "找不到", "不懂", "困惑", "麻烦", "痛苦"
        ]

        detected = []
        for indicator in pain_indicators:
            if indicator in user_input:
                detected.append({
                    "type": "pain_point",
                    "indicator": indicator,
                    "severity": 0.8 if indicator in ["崩溃", "错误", "失败"] else 0.5
                })

        return {
            "pain_points": detected,
            "pain_count": len(detected),
            "has_pain": len(detected) > 0
        }


class TrendHunterSkill(LivingSkill):
    """P0.3 Detect trends and patterns."""

    def __init__(self):
        super().__init__(
            skill_id="p0.trend_hunter",
            name="Trend Hunter",
            description="Identify emerging trends",
            version="1.0.0"
        )

    async def _execute(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        content = context.get("content", "")

        trend_indicators = [
            "趋势", "增长", "上升", "热门", "流行", "新",
            "发现", "突破", "创新", "变革"
        ]

        signals = []
        for indicator in trend_indicators:
            if indicator in content:
                signals.append({
                    "signal": indicator,
                    "strength": 0.7
                })

        return {
            "trend_signals": signals,
            "trend_strength": min(len(signals) * 0.2, 1.0),
            "is_trending": len(signals) >= 2
        }


# P1 Skills (simplified versions)
class ValueAssessorSkill(LivingSkill):
    """P1.1 Assess intrinsic value."""

    def __init__(self):
        super().__init__(
            skill_id="p1.value_assessor",
            name="Value Assessor",
            description="评估信息价值",
            version="1.0.0"
        )

    async def _execute(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        content = context.get("content", "")
        p0_result = context.get("p0_result", {})

        # Value based on content length + trend signals
        length_score = min(len(content) / 1000, 1.0)
        trend_bonus = 0.2 if p0_result.get("is_trending") else 0

        return {
            "value_score": min(length_score + trend_bonus, 1.0),
            "dimensions": {
                "depth": length_score,
                "novelty": 0.7 if trend_bonus > 0 else 0.4
            }
        }


class CredibilityAssessorSkill(LivingSkill):
    """P1.3 Assess credibility."""

    def __init__(self):
        super().__init__(
            skill_id="p1.credibility_assessor",
            name="Credibility Assessor",
            description="评估可信度",
            version="1.0.0"
        )

    async def _execute(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        metadata = context.get("metadata", {})

        source_scores = {
            "expert": 0.9, "official": 0.85, "media": 0.6,
            "social": 0.4, "unknown": 0.3
        }

        source_type = metadata.get("source_type", "unknown")
        score = source_scores.get(source_type, 0.3)

        return {
            "credibility_score": score,
            "source_tier": source_type
        }


# P2 Skills (simplified)
class EntityLinkerSkill(LivingSkill):
    """P2.1 Extract and link entities."""

    def __init__(self):
        super().__init__(
            skill_id="p2.entity_linker",
            name="Entity Linker",
            description="提取知识实体",
            version="1.0.0"
        )

    async def _execute(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        content = context.get("content", "")

        # Simple entity extraction
        import re
        entities = []

        # Capitalized terms
        for match in re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}', content):
            if len(match) > 3:
                entities.append({"name": match, "type": "concept"})

        # Quoted terms
        for match in re.findall(r'["\']([^"\']{3,20})["\']', content):
            entities.append({"name": match, "type": "term"})

        return {
            "entities": entities[:10],
            "entity_count": len(entities)
        }


class SemanticClusterSkill(LivingSkill):
    """P2.2 Cluster related content."""

    def __init__(self):
        super().__init__(
            skill_id="p2.semantic_cluster",
            name="Semantic Cluster",
            description="语义聚类",
            version="1.0.0"
        )

    async def _execute(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        entities = context.get("entities", [])
        existing_nodes = context.get("existing_nodes", [])

        # Find similar nodes
        related = []
        for node in existing_nodes:
            node_tags = set(node.get("tags", []))
            for entity in entities:
                if entity["name"].lower() in str(node).lower():
                    related.append(node["id"])

        return {
            "cluster_id": f"cluster_{hash(str(entities)) % 1000}",
            "related_nodes": list(set(related))[:5],
            "cluster_size": len(related) + 1
        }


# P3 Skills (simplified)
class StrategyEvolverSkill(LivingSkill):
    """P3.1 Evolve strategies."""

    def __init__(self):
        super().__init__(
            skill_id="p3.strategy_evolver",
            name="Strategy Evolver",
            description="策略进化",
            version="1.0.0"
        )
        self._performance_history: List[Dict] = []

    async def _execute(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        p1_result = context.get("p1_result", {})
        current_strategy = context.get("strategy", "default")

        value_score = p1_result.get("value_score", 0.5)

        # Record performance
        self._performance_history.append({
            "strategy": current_strategy,
            "value_score": value_score,
            "timestamp": datetime.now()
        })

        # Evolution logic
        if len(self._performance_history) >= 3:
            recent = self._performance_history[-3:]
            avg_score = sum(r["value_score"] for r in recent) / 3

            if avg_score > 0.7:
                recommendation = "当前策略有效，继续"
            elif avg_score < 0.4:
                recommendation = "建议切换策略"
            else:
                recommendation = "观察中"
        else:
            recommendation = "数据不足"

        return {
            "recommendation": recommendation,
            "sample_count": len(self._performance_history),
            "best_strategy": current_strategy if value_score > 0.6 else "explore"
        }


class FeedbackLoopSkill(LivingSkill):
    """P3.2 Feedback collection."""

    def __init__(self):
        super().__init__(
            skill_id="p3.feedback_loop",
            name="Feedback Loop",
            description="反馈收集",
            version="1.0.0"
        )
        self._feedback_count = 0

    async def _execute(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        pipeline_result = context.get("pipeline_result", {})

        self._feedback_count += 1

        return {
            "feedback_id": f"fb_{self._feedback_count:04d}",
            "processed": True,
            "total_feedback": self._feedback_count
        }


@dataclass
class IntegrationResult:
    """Complete result from P0-P4 integration."""
    content_id: str
    timestamp: datetime

    # P0 Results
    pain_points: List[Dict] = field(default_factory=list)
    trend_signals: List[Dict] = field(default_factory=list)

    # P1 Results
    value_score: float = 0.0
    credibility_score: float = 0.0
    overall_judgment: str = ""

    # P2 Results
    entities: List[Dict] = field(default_factory=list)
    related_nodes: List[str] = field(default_factory=list)
    cluster_id: Optional[str] = None

    # P3 Results
    strategy_recommendation: str = ""
    feedback_id: str = ""

    # P4 Results
    data_lineage_id: str = ""
    data_tier: str = "hot"
    quality_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content_id": self.content_id,
            "timestamp": self.timestamp.isoformat(),
            "p0_perception": {
                "pain_points": len(self.pain_points),
                "trend_signals": len(self.trend_signals)
            },
            "p1_judgment": {
                "value_score": round(self.value_score, 2),
                "credibility_score": round(self.credibility_score, 2),
                "overall": self.overall_judgment
            },
            "p2_relationship": {
                "entities": len(self.entities),
                "related_nodes": len(self.related_nodes),
                "cluster": self.cluster_id
            },
            "p3_evolution": {
                "recommendation": self.strategy_recommendation,
                "feedback": self.feedback_id
            },
            "p4_data": {
                "lineage_id": self.data_lineage_id,
                "tier": self.data_tier,
                "quality": round(self.quality_score, 2)
            }
        }


class LivingKnowledgePipeline:
    """
    P0-P4 Full Integration Pipeline.

    Orchestrates all five layers for complete knowledge processing.
    """

    def __init__(self):
        # Initialize database
        self.db = InMemoryDatabase()

        # Initialize P4 Data Agent
        self.p4 = P4DataAgent(self.db)

        # Initialize skills (P0-P3)
        self.p0_pain = PainScannerSkill()
        self.p0_trend = TrendHunterSkill()
        self.p1_value = ValueAssessorSkill()
        self.p1_credibility = CredibilityAssessorSkill()
        self.p2_entity = EntityLinkerSkill()
        self.p2_cluster = SemanticClusterSkill()
        self.p3_strategy = StrategyEvolverSkill()
        self.p3_feedback = FeedbackLoopSkill()

        # Register data sources with P4
        self._setup_data_sources()

        logger.info("Living Knowledge Pipeline initialized")

    def _setup_data_sources(self):
        """Setup data sources in P4."""
        self.p4.register_data_source(DataGenerationRule(
            source_id="user_content",
            source_type="manual",
            retention_hot=timedelta(days=7),
            retention_warm=timedelta(days=30),
            retention_cold=timedelta(days=365)
        ))

        self.p4.register_data_source(DataGenerationRule(
            source_id="system_insights",
            source_type="processor",
            retention_hot=timedelta(days=1),
            retention_warm=timedelta(days=7),
            retention_cold=timedelta(days=90)
        ))

    async def process(self, content: str, metadata: Optional[Dict] = None,
                     existing_nodes: Optional[List[Dict]] = None) -> IntegrationResult:
        """
        Process content through all five layers.

        Args:
            content: The content to process
            metadata: Associated metadata
            existing_nodes: Existing knowledge nodes for relationship building

        Returns:
            IntegrationResult with outputs from all layers
        """
        metadata = metadata or {}
        existing_nodes = existing_nodes or []
        content_id = metadata.get("id", f"content_{hashlib.md5(content.encode()).hexdigest()[:8]}")

        logger.info(f"Processing content {content_id} through P0-P4 pipeline")

        result = IntegrationResult(
            content_id=content_id,
            timestamp=datetime.now()
        )

        # ======================================================================
        # LAYER P0: PERCEPTION
        # ======================================================================
        logger.debug("P0: Running perception layer")

        pain_result = await self.p0_pain.invoke({
            "user_input": content
        })
        result.pain_points = pain_result.get("pain_points", [])

        trend_result = await self.p0_trend.invoke({
            "content": content
        })
        result.trend_signals = trend_result.get("trend_signals", [])

        p0_summary = {
            "has_pain": pain_result.get("has_pain", False),
            "is_trending": trend_result.get("is_trending", False)
        }

        # ======================================================================
        # LAYER P1: JUDGMENT
        # ======================================================================
        logger.debug("P1: Running judgment layer")

        value_result = await self.p1_value.invoke({
            "content": content,
            "p0_result": trend_result
        })
        result.value_score = value_result.get("value_score", 0.5)

        credibility_result = await self.p1_credibility.invoke({
            "metadata": metadata
        })
        result.credibility_score = credibility_result.get("credibility_score", 0.5)

        # Overall judgment
        overall = (result.value_score * 0.6 + result.credibility_score * 0.4)
        if overall >= 0.8:
            result.overall_judgment = "high_value"
        elif overall >= 0.5:
            result.overall_judgment = "medium_value"
        else:
            result.overall_judgment = "low_value"

        p1_result = {
            "value_score": result.value_score,
            "credibility_score": result.credibility_score
        }

        # ======================================================================
        # LAYER P2: RELATIONSHIP
        # ======================================================================
        logger.debug("P2: Running relationship layer")

        entity_result = await self.p2_entity.invoke({
            "content": content
        })
        result.entities = entity_result.get("entities", [])

        cluster_result = await self.p2_cluster.invoke({
            "entities": result.entities,
            "existing_nodes": existing_nodes
        })
        result.cluster_id = cluster_result.get("cluster_id")
        result.related_nodes = cluster_result.get("related_nodes", [])

        # ======================================================================
        # LAYER P3: EVOLUTION
        # ======================================================================
        logger.debug("P3: Running evolution layer")

        strategy_result = await self.p3_strategy.invoke({
            "p1_result": p1_result,
            "strategy": "default"
        })
        result.strategy_recommendation = strategy_result.get("recommendation", "")

        feedback_result = await self.p3_feedback.invoke({
            "pipeline_result": result.to_dict()
        })
        result.feedback_id = feedback_result.get("feedback_id", "")

        # ======================================================================
        # LAYER P4: DATA MANAGEMENT
        # ======================================================================
        logger.debug("P4: Running data management layer")

        # Record data lineage
        lineage = await self.p4.record_data_generation(
            source_id="user_content",
            data_id=content_id,
            metadata={
                **metadata,
                "p1_value_score": result.value_score,
                "entity_count": len(result.entities)
            }
        )
        result.data_lineage_id = lineage.data_id
        result.data_tier = lineage.current_tier.value

        # Check quality
        quality_report = await self.p4.quality_agent.check_quality(content_id)
        result.quality_score = quality_report.overall_score

        logger.info(f"Pipeline complete for {content_id}: judgment={result.overall_judgment}, "
                   f"entities={len(result.entities)}, quality={result.quality_score:.2f}")

        return result

    async def get_system_status(self) -> Dict[str, Any]:
        """Get full system status across all layers."""
        p4_health = await self.p4.get_system_health()

        return {
            "pipeline_status": "healthy",
            "p0_skills": 2,
            "p1_skills": 2,
            "p2_skills": 2,
            "p3_skills": 2,
            "p4_components": 4,
            "database": p4_health,
            "timestamp": datetime.now().isoformat()
        }


# =============================================================================
# Demo
# =============================================================================

async def demo_full_pipeline():
    """Demonstrate the complete P0-P4 pipeline."""

    print("=" * 70)
    print("Living Knowledge System - P0-P4 Full Integration Demo")
    print("=" * 70)

    # Create pipeline
    pipeline = LivingKnowledgePipeline()

    # Sample content
    test_contents = [
        {
            "content": """
            AI Agent 正在从工具向协作者转变，这是一个重要的趋势突破。
            我们发现多 Agent 协作框架正在快速成熟，用户对这个功能有强烈需求。
            但目前的系统在处理复杂任务时经常出现问题，响应速度很慢。
            """,
            "metadata": {
                "id": "demo_001",
                "source_type": "expert",
                "author": "AI研究员",
                "tags": ["AI", "Agent", "趋势"]
            }
        },
        {
            "content": """
            2024年知识管理工具的新方向是智能化整合。
            用户希望系统能自动发现知识之间的关联，而不是手动整理。
            这个需求在快速发展的技术团队中越来越普遍。
            """,
            "metadata": {
                "id": "demo_002",
                "source_type": "media",
                "author": "科技博主",
                "tags": ["知识管理", "工具", "2024"]
            }
        }
    ]

    # Existing nodes for relationship building
    existing_nodes = [
        {
            "id": "existing_001",
            "title": "AI Agent 基础",
            "tags": ["AI", "Agent"],
            "content": "Agent是能够自主行动的AI系统"
        },
        {
            "id": "existing_002",
            "title": "知识管理方法",
            "tags": ["知识管理"],
            "content": "如何有效管理和组织知识"
        }
    ]

    print("\n[Processing] Processing 2 sample contents through P0-P4 pipeline...\n")

    results = []
    for i, test in enumerate(test_contents, 1):
        print(f"\n{'─' * 70}")
        print(f"Content {i}/{len(test_contents)}: {test['metadata']['id']}")
        print(f"{'─' * 70}")

        result = await pipeline.process(
            content=test["content"],
            metadata=test["metadata"],
            existing_nodes=existing_nodes
        )
        results.append(result)

        # Display results
        print(f"\n[P0] Perception Layer:")
        print(f"   Pain points detected: {len(result.pain_points)}")
        print(f"   Trend signals: {len(result.trend_signals)}")

        print(f"\n[P1] Judgment Layer:")
        print(f"   Value score: {result.value_score:.2f}")
        print(f"   Credibility: {result.credibility_score:.2f}")
        print(f"   Overall: {result.overall_judgment}")

        print(f"\n[P2] Relationship Layer:")
        print(f"   Entities extracted: {len(result.entities)}")
        print(f"   Related nodes: {len(result.related_nodes)}")
        print(f"   Cluster: {result.cluster_id}")

        print(f"\n[P3] Evolution Layer:")
        print(f"   Strategy: {result.strategy_recommendation}")
        print(f"   Feedback: {result.feedback_id}")

        print(f"\n[P4] Data Layer:")
        print(f"   Lineage ID: {result.data_lineage_id}")
        print(f"   Data tier: {result.data_tier}")
        print(f"   Quality: {result.quality_score:.2f}")

    # Summary
    print(f"\n{'=' * 70}")
    print("Integration Summary")
    print(f"{'=' * 70}")

    status = await pipeline.get_system_status()
    print(f"\nSystem Status: {status['pipeline_status']}")
    print(f"Layers Active:")
    print(f"  P0 Perception: {status['p0_skills']} skills")
    print(f"  P1 Judgment: {status['p1_skills']} skills")
    print(f"  P2 Relationship: {status['p2_skills']} skills")
    print(f"  P3 Evolution: {status['p3_skills']} skills")
    print(f"  P4 DataAgent: {status['p4_components']} components")

    print(f"\nProcessed {len(results)} contents:")
    high_value = sum(1 for r in results if r.overall_judgment == "high_value")
    medium_value = sum(1 for r in results if r.overall_judgment == "medium_value")
    print(f"  High value: {high_value}")
    print(f"  Medium value: {medium_value}")
    print(f"  Low value: {len(results) - high_value - medium_value}")

    total_entities = sum(len(r.entities) for r in results)
    print(f"\nTotal entities extracted: {total_entities}")

    print(f"\n{'=' * 70}")
    print("[Done] P0-P4 Full Integration Demo Complete!")
    print(f"{'=' * 70}")

    return results


if __name__ == "__main__":
    asyncio.run(demo_full_pipeline())
