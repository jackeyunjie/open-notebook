"""P1 Judgment Layer - Value assessment and prioritization.

Four judgment agents working together to evaluate information quality:
- ValueAssessor: Intrinsic worth evaluation
- HeatAssessor: Trending and timeliness
- CredibilityAssessor: Source reliability
- UtilityAssessor: Practical applicability
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from open_notebook.skills.living.agent_tissue import AgentTissue, AgentCoordination, CoordinationPattern
from open_notebook.skills.living.skill_cell import LivingSkill, SkillState


class JudgmentDimension(Enum):
    """Dimensions of judgment."""
    VALUE = "value"           # 价值维度
    HEAT = "heat"             # 热度维度
    CREDIBILITY = "credibility"  # 可信度维度
    UTILITY = "utility"       # 效用维度


@dataclass
class JudgmentResult:
    """Result of a judgment assessment."""
    dimension: JudgmentDimension
    score: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    reasoning: str
    factors: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ValueAssessment:
    """Comprehensive value assessment of information."""
    content_id: str
    content_type: str  # note, source, insight, etc.
    overall_score: float  # Weighted composite
    judgments: Dict[JudgmentDimension, JudgmentResult] = field(default_factory=dict)
    priority: str = "normal"  # low, normal, high, critical
    recommended_action: str = ""
    assessed_at: datetime = field(default_factory=datetime.now)


class ValueAssessorSkill(LivingSkill):
    """
    P1.1 Value Assessor - 价值评估师
    
    Evaluates intrinsic worth of information based on:
    - Novelty (newness of information)
    - Depth (substantial content)
    - Relevance (alignment with goals)
    - Uniqueness (distinctiveness)
    """
    
    def __init__(self):
        super().__init__(
            skill_id="p1.value_assessor",
            name="Value Assessor",
            description="评估信息的内在价值",
            version="1.0.0"
        )
        self.dimension = JudgmentDimension.VALUE
    
    async def _execute(self, context: Optional[Dict[str, Any]]) -> JudgmentResult:
        """Execute value assessment."""
        content = context.get("content", "")
        metadata = context.get("metadata", {})
        
        # Calculate factors
        factors = {
            "novelty": self._assess_novelty(content, metadata),
            "depth": self._assess_depth(content),
            "relevance": self._assess_relevance(content, metadata),
            "uniqueness": self._assess_uniqueness(content),
        }
        
        # Weighted score
        weights = {"novelty": 0.25, "depth": 0.35, "relevance": 0.25, "uniqueness": 0.15}
        score = sum(factors[k] * weights[k] for k in factors)
        
        # Confidence based on available data
        confidence = 0.7 if len(content) > 100 else 0.5
        
        reasoning = self._generate_reasoning(factors, score)
        
        return JudgmentResult(
            dimension=self.dimension,
            score=score,
            confidence=confidence,
            reasoning=reasoning,
            factors=factors
        )
    
    def _assess_novelty(self, content: str, metadata: Dict) -> float:
        """Assess how new/unique the information is."""
        # Check if has timestamp
        created_at = metadata.get("created_at")
        if created_at:
            age = datetime.now() - datetime.fromisoformat(created_at)
            if age < timedelta(hours=24):
                return 0.9
            elif age < timedelta(days=7):
                return 0.7
            elif age < timedelta(days=30):
                return 0.5
        return 0.3
    
    def _assess_depth(self, content: str) -> float:
        """Assess content depth/substance."""
        length = len(content)
        if length > 5000:
            return 0.9
        elif length > 2000:
            return 0.7
        elif length > 500:
            return 0.5
        elif length > 100:
            return 0.3
        return 0.1
    
    def _assess_relevance(self, content: str, metadata: Dict) -> float:
        """Assess relevance to current goals/topics."""
        # Get user's current focus areas
        focus_areas = metadata.get("focus_areas", [])
        tags = metadata.get("tags", [])
        
        if not focus_areas:
            return 0.5  # Neutral if no focus defined
        
        # Check overlap
        matches = sum(1 for area in focus_areas if area.lower() in content.lower())
        relevance = min(matches / len(focus_areas), 1.0)
        
        return max(relevance, 0.3)
    
    def _assess_uniqueness(self, content: str) -> float:
        """Assess distinctiveness of perspective."""
        # Simple heuristic: presence of unique insights/opinions
        indicators = ["我认为", "我发现", "独特的", "不同于", "创新", "突破"]
        matches = sum(1 for ind in indicators if ind in content)
        return min(0.3 + matches * 0.15, 0.9)
    
    def _generate_reasoning(self, factors: Dict[str, float], score: float) -> str:
        """Generate human-readable reasoning."""
        top_factor = max(factors, key=factors.get)
        factor_names = {
            "novelty": "新颖性",
            "depth": "深度",
            "relevance": "相关性",
            "uniqueness": "独特性"
        }
        return f"价值评分{score:.2f}，主要由{factor_names[top_factor]}({factors[top_factor]:.2f})贡献"


class HeatAssessorSkill(LivingSkill):
    """
    P1.2 Heat Assessor - 热度评估师
    
    Evaluates trending and timeliness:
    - Recency (how recent)
    - Momentum (growth trajectory)
    - Engagement (social signals)
    - Seasonality (temporal relevance)
    """
    
    def __init__(self):
        super().__init__(
            skill_id="p1.heat_assessor",
            name="Heat Assessor",
            description="评估信息的热度和时效性",
            version="1.0.0"
        )
        self.dimension = JudgmentDimension.HEAT
    
    async def _execute(self, context: Optional[Dict[str, Any]]) -> JudgmentResult:
        """Execute heat assessment."""
        metadata = context.get("metadata", {})
        
        factors = {
            "recency": self._assess_recency(metadata),
            "momentum": self._assess_momentum(metadata),
            "engagement": self._assess_engagement(metadata),
            "seasonality": self._assess_seasonality(metadata),
        }
        
        weights = {"recency": 0.4, "momentum": 0.3, "engagement": 0.2, "seasonality": 0.1}
        score = sum(factors[k] * weights[k] for k in factors)
        
        confidence = 0.6  # Heat assessment has inherent uncertainty
        
        reasoning = f"热度评分{score:.2f}，时效性{factors['recency']:.2f}"
        
        return JudgmentResult(
            dimension=self.dimension,
            score=score,
            confidence=confidence,
            reasoning=reasoning,
            factors=factors
        )
    
    def _assess_recency(self, metadata: Dict) -> float:
        """Assess how recent the information is."""
        created_at = metadata.get("created_at")
        if not created_at:
            return 0.5
        
        age = datetime.now() - datetime.fromisoformat(created_at)
        hours = age.total_seconds() / 3600
        
        if hours < 1:
            return 1.0
        elif hours < 24:
            return 0.9
        elif hours < 72:
            return 0.7
        elif hours < 168:  # 1 week
            return 0.5
        elif hours < 720:  # 1 month
            return 0.3
        return 0.1
    
    def _assess_momentum(self, metadata: Dict) -> float:
        """Assess growth trajectory."""
        # Check for velocity indicators
        views = metadata.get("views", 0)
        view_velocity = metadata.get("view_velocity", 0)  # views per hour
        
        if view_velocity > 1000:
            return 0.9
        elif view_velocity > 100:
            return 0.7
        elif view_velocity > 10:
            return 0.5
        elif views > 10000:
            return 0.4
        return 0.2
    
    def _assess_engagement(self, metadata: Dict) -> float:
        """Assess social engagement."""
        likes = metadata.get("likes", 0)
        comments = metadata.get("comments", 0)
        shares = metadata.get("shares", 0)
        
        engagement_score = min((likes + comments * 2 + shares * 3) / 1000, 1.0)
        return max(engagement_score, 0.1)
    
    def _assess_seasonality(self, metadata: Dict) -> float:
        """Assess temporal relevance to current time."""
        # Check if content is seasonally relevant
        tags = metadata.get("tags", [])
        seasonal_keywords = ["春节", "年终", "季度", "2026", "新年", "规划"]
        
        matches = sum(1 for kw in seasonal_keywords if kw in str(tags))
        return min(0.5 + matches * 0.15, 0.9)


class CredibilityAssessorSkill(LivingSkill):
    """
    P1.3 Credibility Assessor - 可信度评估师
    
    Evaluates source reliability:
    - Source authority (expertise/reputation)
    - Consistency (alignment with known facts)
    - Verifiability (can claims be checked)
    - Bias indicator (potential skew)
    """
    
    def __init__(self):
        super().__init__(
            skill_id="p1.credibility_assessor",
            name="Credibility Assessor",
            description="评估信息的可信度",
            version="1.0.0"
        )
        self.dimension = JudgmentDimension.CREDIBILITY
        
        # Source reputation database (simplified)
        self.source_tiers = {
            "academic": 0.9,
            "official": 0.85,
            "expert": 0.8,
            "media": 0.6,
            "social": 0.4,
            "unknown": 0.3,
        }
    
    async def _execute(self, context: Optional[Dict[str, Any]]) -> JudgmentResult:
        """Execute credibility assessment."""
        metadata = context.get("metadata", {})
        
        factors = {
            "authority": self._assess_authority(metadata),
            "consistency": self._assess_consistency(metadata),
            "verifiability": self._assess_verifiability(metadata),
            "bias": self._assess_bias(metadata),
        }
        
        weights = {"authority": 0.35, "consistency": 0.3, "verifiability": 0.25, "bias": 0.1}
        score = sum(factors[k] * weights[k] for k in factors)
        
        # Higher confidence with more metadata
        confidence = min(0.5 + len(metadata) * 0.05, 0.9)
        
        reasoning = f"可信度{score:.2f}，来源权威性{factors['authority']:.2f}"
        
        return JudgmentResult(
            dimension=self.dimension,
            score=score,
            confidence=confidence,
            reasoning=reasoning,
            factors=factors
        )
    
    def _assess_authority(self, metadata: Dict) -> float:
        """Assess source authority."""
        source_type = metadata.get("source_type", "unknown")
        author = metadata.get("author", "")
        
        base_score = self.source_tiers.get(source_type, 0.3)
        
        # Boost for known experts
        expert_indicators = ["博士", "教授", "专家", "研究员", "分析师"]
        if any(ind in author for ind in expert_indicators):
            base_score = min(base_score + 0.1, 1.0)
        
        return base_score
    
    def _assess_consistency(self, metadata: Dict) -> float:
        """Assess alignment with known facts."""
        # Placeholder: would cross-reference with knowledge base
        verified = metadata.get("verified", False)
        contradictions = metadata.get("contradictions", 0)
        
        if verified:
            return 0.9
        if contradictions > 0:
            return max(0.9 - contradictions * 0.2, 0.2)
        return 0.6  # Neutral if unknown
    
    def _assess_verifiability(self, metadata: Dict) -> float:
        """Assess if claims can be verified."""
        has_sources = metadata.get("has_sources", False)
        citations = metadata.get("citations", 0)
        data_points = metadata.get("data_points", 0)
        
        if has_sources and citations > 3:
            return 0.9
        elif has_sources:
            return 0.7
        elif data_points > 5:
            return 0.6
        return 0.3
    
    def _assess_bias(self, metadata: Dict) -> float:
        """Assess potential bias (inverse score)."""
        # Lower bias = higher score
        emotional_language = metadata.get("emotional_language_score", 0.5)
        sponsored = metadata.get("sponsored", False)
        
        bias_score = emotional_language
        if sponsored:
            bias_score += 0.2
        
        # Return inverse (low bias = high credibility)
        return max(1.0 - bias_score, 0.1)


class UtilityAssessorSkill(LivingSkill):
    """
    P1.4 Utility Assessor - 效用评估师
    
    Evaluates practical applicability:
    - Actionability (can be acted upon)
    - Transferability (applicable to other contexts)
    - Combinability (can combine with other knowledge)
    - Retrievability (easy to find when needed)
    """
    
    def __init__(self):
        super().__init__(
            skill_id="p1.utility_assessor",
            name="Utility Assessor",
            description="评估信息的实用性和可操作性",
            version="1.0.0"
        )
        self.dimension = JudgmentDimension.UTILITY
    
    async def _execute(self, context: Optional[Dict[str, Any]]) -> JudgmentResult:
        """Execute utility assessment."""
        content = context.get("content", "")
        metadata = context.get("metadata", {})
        
        factors = {
            "actionability": self._assess_actionability(content),
            "transferability": self._assess_transferability(content, metadata),
            "combinability": self._assess_combinability(content, metadata),
            "retrievability": self._assess_retrievability(metadata),
        }
        
        weights = {"actionability": 0.35, "transferability": 0.25, "combinability": 0.25, "retrievability": 0.15}
        score = sum(factors[k] * weights[k] for k in factors)
        
        confidence = 0.65
        
        reasoning = f"效用评分{score:.2f}，可操作性{factors['actionability']:.2f}"
        
        return JudgmentResult(
            dimension=self.dimension,
            score=score,
            confidence=confidence,
            reasoning=reasoning,
            factors=factors
        )
    
    def _assess_actionability(self, content: str) -> float:
        """Assess if content can be acted upon."""
        action_indicators = [
            "步骤", "方法", "建议", "策略", "技巧", "指南",
            "如何", "怎么做", "应该", "可以", "推荐"
        ]
        
        matches = sum(1 for ind in action_indicators if ind in content)
        return min(0.3 + matches * 0.1, 0.9)
    
    def _assess_transferability(self, content: str, metadata: Dict) -> float:
        """Assess applicability to other contexts."""
        # Check for general principles vs specific cases
        general_indicators = ["通用", "普遍", "原理", "框架", "模型", "理论"]
        specific_indicators = ["具体", "特定", "案例", "实例", "某"]
        
        general_score = sum(1 for ind in general_indicators if ind in content)
        specific_score = sum(1 for ind in specific_indicators if ind in content)
        
        if general_score > specific_score:
            return 0.8
        elif general_score > 0:
            return 0.6
        return 0.4
    
    def _assess_combinability(self, content: str, metadata: Dict) -> float:
        """Assess if can combine with other knowledge."""
        # Check for connections to other concepts
        tags = metadata.get("tags", [])
        related_concepts = metadata.get("related_concepts", [])
        
        connectivity = len(tags) + len(related_concepts)
        return min(0.3 + connectivity * 0.1, 0.9)
    
    def _assess_retrievability(self, metadata: Dict) -> float:
        """Assess how easy to find when needed."""
        # Check organization
        has_tags = len(metadata.get("tags", [])) > 0
        has_category = metadata.get("category") is not None
        has_title = metadata.get("title") is not None
        
        score = 0.3
        if has_tags:
            score += 0.2
        if has_category:
            score += 0.2
        if has_title:
            score += 0.2
        
        return min(score, 0.9)


class P1JudgmentOrgan(AgentTissue):
    """
    P1 Judgment Organ - 价值判断器官
    
    Coordinates four assessor skills to provide comprehensive
    value assessment of information entering the system.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="p1.judgment_organ",
            name="P1 Judgment Organ",
            description="四维度价值判断器官",
            purpose="评估信息的价值、热度、可信度和效用",
            coordination=AgentCoordination(pattern=CoordinationPattern.PARALLEL)
        )
        
        # Create and register four assessor skills
        value_skill = ValueAssessorSkill()
        heat_skill = HeatAssessorSkill()
        cred_skill = CredibilityAssessorSkill()
        util_skill = UtilityAssessorSkill()
        
        # Add skill IDs (skills auto-register themselves)
        self.add_skill(value_skill.skill_id)
        self.add_skill(heat_skill.skill_id)
        self.add_skill(cred_skill.skill_id)
        self.add_skill(util_skill.skill_id)
        
        # Store references
        self._value_skill = value_skill
        self._heat_skill = heat_skill
        self._cred_skill = cred_skill
        self._util_skill = util_skill
        
        logger.info("P1 Judgment Organ initialized with 4 assessor skills")
    
    async def assess(self, content: str, metadata: Dict[str, Any]) -> ValueAssessment:
        """
        Perform comprehensive value assessment.
        
        Args:
            content: The content to assess
            metadata: Associated metadata
            
        Returns:
            ValueAssessment with scores from all dimensions
        """
        context = {
            "content": content,
            "metadata": metadata,
            "timestamp": datetime.now().isoformat()
        }
        
        # Execute all skills in parallel
        execution_result = await self.execute(context)
        
        # Collect judgments from execution result
        judgments = {}
        if execution_result.get("success") and "result" in execution_result:
            for item in execution_result["result"]:
                if isinstance(item, dict) and "result" in item:
                    judgment = item["result"]
                    if isinstance(judgment, JudgmentResult):
                        judgments[judgment.dimension] = judgment
        
        # Calculate overall score (weighted)
        dimension_weights = {
            JudgmentDimension.VALUE: 0.30,
            JudgmentDimension.HEAT: 0.20,
            JudgmentDimension.CREDIBILITY: 0.30,
            JudgmentDimension.UTILITY: 0.20,
        }
        
        overall_score = sum(
            judgments[dim].score * weight
            for dim, weight in dimension_weights.items()
            if dim in judgments
        )
        
        # Determine priority
        priority = self._determine_priority(overall_score, judgments)
        
        # Generate recommendation
        recommended_action = self._generate_recommendation(overall_score, judgments)
        
        # Create assessment
        assessment = ValueAssessment(
            content_id=metadata.get("id", "unknown"),
            content_type=metadata.get("type", "unknown"),
            overall_score=overall_score,
            judgments=judgments,
            priority=priority,
            recommended_action=recommended_action
        )
        
        logger.info(f"Assessment complete for {assessment.content_id}: "
                   f"score={overall_score:.2f}, priority={priority}")
        
        return assessment
    
    def _determine_priority(self, overall_score: float, 
                           judgments: Dict[JudgmentDimension, JudgmentResult]) -> str:
        """Determine priority level based on scores."""
        if overall_score >= 0.8:
            return "critical"
        elif overall_score >= 0.6:
            return "high"
        elif overall_score >= 0.4:
            return "normal"
        return "low"
    
    def _generate_recommendation(self, overall_score: float,
                                  judgments: Dict[JudgmentDimension, JudgmentResult]) -> str:
        """Generate action recommendation."""
        if overall_score >= 0.8:
            return "立即处理并深度整合"
        elif overall_score >= 0.6:
            return "优先处理并建立关联"
        elif overall_score >= 0.4:
            return "常规处理并监控"
        
        # Check if any dimension is particularly low
        low_dimensions = [
            dim.value for dim, result in judgments.items()
            if result.score < 0.3
        ]
        
        if low_dimensions:
            return f"质量不足，建议补充{', '.join(low_dimensions)}"
        
        return "暂存观察"


# ============================================================================
# Factory Functions
# ============================================================================

def create_p1_judgment_organ() -> P1JudgmentOrgan:
    """Factory function to create P1 Judgment Organ."""
    return P1JudgmentOrgan()


async def demo_assessment():
    """Demo function to show P1 in action."""
    organ = create_p1_judgment_organ()
    
    # Sample content
    content = """
    我发现了一个重要的趋势：AI Agent 正在从工具向协作者转变。
    这个转变有三个关键信号：
    1. 多 Agent 协作框架的成熟
    2. 长期记忆和上下文理解能力的提升
    3. 从被动响应到主动建议的演进
    
    建议立即关注这个领域，建立系统性的跟踪机制。
    """
    
    metadata = {
        "id": "demo_001",
        "type": "insight",
        "created_at": datetime.now().isoformat(),
        "author": "AI研究员",
        "tags": ["AI", "Agent", "趋势"],
        "focus_areas": ["AI", "技术趋势"],
        "source_type": "expert"
    }
    
    assessment = await organ.assess(content, metadata)
    
    print("=" * 60)
    print("P1 Judgment Assessment Demo")
    print("=" * 60)
    print(f"Content ID: {assessment.content_id}")
    print(f"Overall Score: {assessment.overall_score:.2f}")
    print(f"Priority: {assessment.priority}")
    print(f"Recommendation: {assessment.recommended_action}")
    print()
    print("Dimension Scores:")
    for dim, result in assessment.judgments.items():
        print(f"  {dim.value}: {result.score:.2f} ({result.reasoning})")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(demo_assessment())
