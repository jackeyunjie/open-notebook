"""P0-P2 Integration Test - 感知层到关系层集成测试

测试活体知识系统中 P0(感知层) -> P1(判断层) -> P2(关系层) 的完整数据流
"""

import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pytest
from loguru import logger

# P0 组件
from open_notebook.skills.living.examples.p0_perception_organ import (
    create_pain_scanner_skill,
    create_emotion_watcher_skill,
    create_trend_hunter_skill,
    create_scene_discover_skill,
    create_p0_perception_agent,
)

# P1 组件
from open_notebook.skills.living.p1_judgment_layer import (
    create_p1_judgment_organ,
    ValueAssessment,
    JudgmentDimension,
)

# P2 组件
from open_notebook.skills.living.p2_relationship_layer import (
    create_p2_relationship_organ,
    RelationshipAnalysis,
    KnowledgeGraph,
    RelationshipType,
)


class TestP0PerceptionLayer:
    """测试 P0 感知层"""

    @pytest.mark.asyncio
    async def test_pain_scanner_skill(self):
        """测试痛点扫描技能"""
        skill = create_pain_scanner_skill()

        context = {
            "platform_data": {
                "comments": [
                    {"text": "I have a problem with login", "platform": "weibo", "timestamp": "2024-01-01"},
                    {"text": "This feature is frustrating", "platform": "xiaohongshu", "timestamp": "2024-01-01"},
                    {"text": "Love this!", "platform": "douyin", "timestamp": "2024-01-01"},
                ]
            }
        }

        result = await skill.invoke(context)

        assert result is not None
        assert "pain_points" in result
        assert result["count"] >= 2  # 至少检测到2个痛点
        print(f"✅ Pain Scanner: 检测到 {result['count']} 个痛点")

    @pytest.mark.asyncio
    async def test_emotion_watcher_skill(self):
        """测试情感监控技能"""
        skill = create_emotion_watcher_skill()

        context = {
            "content": [
                {"text": "I'm so happy with this product!", "timestamp": "2024-01-01"},
                {"text": "This makes me angry", "timestamp": "2024-01-01"},
                {"text": "Love it!", "timestamp": "2024-01-01"},
            ]
        }

        result = await skill.invoke(context)

        assert result is not None
        assert "emotions" in result
        assert "dominant_emotion" in result
        print(f"✅ Emotion Watcher: 主导情感 = {result['dominant_emotion']}")

    @pytest.mark.asyncio
    async def test_trend_hunter_skill(self):
        """测试趋势发现技能"""
        skill = create_trend_hunter_skill()

        context = {
            "hashtags": [
                {"name": "AI", "volume": 10000, "growth": 15.5},
                {"name": "MachineLearning", "volume": 5000, "growth": 8.2},
                {"name": "startup", "volume": 3000, "growth": 20.0},
            ]
        }

        result = await skill.invoke(context)

        assert result is not None
        assert "trends" in result
        assert len(result["trends"]) > 0
        print(f"✅ Trend Hunter: 发现 {len(result['trends'])} 个趋势")

    @pytest.mark.asyncio
    async def test_scene_discover_skill(self):
        """测试场景发现技能"""
        skill = create_scene_discover_skill()

        context = {
            "locations": [
                {"name": "Tech Conference", "audience": 5000, "engagement": 0.8, "competition": 2},
                {"name": "Online Forum", "audience": 10000, "engagement": 0.6, "competition": 5},
            ]
        }

        result = await skill.invoke(context)

        assert result is not None
        assert "scenes" in result
        assert "total_addressable_audience" in result
        print(f"✅ Scene Discover: 发现 {len(result['scenes'])} 个场景")


class TestP1JudgmentLayer:
    """测试 P1 判断层"""

    @pytest.mark.asyncio
    async def test_value_assessment(self):
        """测试价值评估"""
        organ = create_p1_judgment_organ()

        content = """
        我发现了一个重要的趋势：AI Agent 正在从工具向协作者转变。
        这个转变有三个关键信号：
        1. 多 Agent 协作框架的成熟
        2. 长期记忆和上下文理解能力的提升
        3. 从被动响应到主动建议的演进
        """

        metadata = {
            "id": "test_001",
            "type": "insight",
            "created_at": datetime.now().isoformat(),
            "author": "AI研究员",
            "tags": ["AI", "Agent", "趋势"],
            "source_type": "expert"
        }

        assessment = await organ.assess(content, metadata)

        assert assessment is not None
        assert isinstance(assessment, ValueAssessment)
        assert 0 <= assessment.overall_score <= 1
        assert assessment.priority in ["low", "normal", "high", "critical"]
        assert len(assessment.judgments) == 4  # 四个维度

        print(f"✅ P1 Judgment: 总分={assessment.overall_score:.2f}, 优先级={assessment.priority}")

    @pytest.mark.asyncio
    async def test_all_dimensions(self):
        """测试所有判断维度"""
        organ = create_p1_judgment_organ()

        content = "测试内容"
        metadata = {
            "id": "test_002",
            "type": "note",
            "created_at": datetime.now().isoformat(),
        }

        assessment = await organ.assess(content, metadata)

        dimensions = [d for d in JudgmentDimension]
        for dim in dimensions:
            assert dim in assessment.judgments
            result = assessment.judgments[dim]
            assert 0 <= result.score <= 1
            assert 0 <= result.confidence <= 1
            assert len(result.reasoning) > 0

        print(f"✅ P1 Judgment: 所有 {len(dimensions)} 个维度评估完成")


class TestP2RelationshipLayer:
    """测试 P2 关系层"""

    @pytest.mark.asyncio
    async def test_relationship_analysis(self):
        """测试关系分析"""
        organ = create_p2_relationship_organ()

        content = """
        AI Agent 正在从工具向协作者转变

        2024年以来，这个趋势越来越明显。根据 OpenAI 的研究，
        多 Agent 协作框架正在快速成熟。

        建议立即关注这个领域。
        https://openai.com/research
        """

        metadata = {
            "id": "test_p2_001",
            "type": "insight",
            "title": "AI Agent 趋势分析",
            "created_at": datetime.now().isoformat(),
            "tags": ["AI", "Agent", "趋势"]
        }

        existing_nodes = [
            {
                "id": "node_001",
                "title": "AI Agent 基础概念",
                "content": "Agent 是能够自主行动的 AI 系统",
                "tags": ["AI", "Agent"],
                "created_at": (datetime.now() - timedelta(days=30)).isoformat()
            },
            {
                "id": "node_002",
                "title": "2023 AI 技术回顾",
                "content": "2023年是大语言模型爆发的一年",
                "tags": ["AI", "2023", "回顾"],
                "created_at": (datetime.now() - timedelta(days=15)).isoformat()
            }
        ]

        analysis = await organ.analyze_relationships(content, metadata, existing_nodes)

        assert analysis is not None
        assert isinstance(analysis, RelationshipAnalysis)
        assert analysis.content_id == "test_p2_001"

        print(f"✅ P2 Relationship: 发现 {len(analysis.related_nodes)} 个关联节点")

    @pytest.mark.asyncio
    async def test_knowledge_graph_construction(self):
        """测试知识图谱构建"""
        organ = create_p2_relationship_organ()

        content = "测试内容"
        metadata = {
            "id": "graph_test_001",
            "type": "note",
            "title": "测试笔记"
        }

        analysis = await organ.analyze_relationships(content, metadata)
        node = organ.add_to_graph("graph_test_001", content, metadata, analysis, p1_score=0.75)

        graph = organ.get_graph()

        assert graph is not None
        assert isinstance(graph, KnowledgeGraph)
        assert len(graph.nodes) >= 1

        print(f"✅ P2 Graph: 图谱包含 {len(graph.nodes)} 个节点, {len(graph.edges)} 条边")


class TestP0ToP2Integration:
    """测试 P0 -> P1 -> P2 完整集成流"""

    @pytest.mark.asyncio
    async def test_perception_to_judgment_flow(self):
        """测试 P0 -> P1 数据流"""
        # P0: 感知数据
        pain_scanner = create_pain_scanner_skill()
        context = {
            "platform_data": {
                "comments": [
                    {"text": "AI tools are difficult to use", "platform": "twitter", "timestamp": "2024-01-01"},
                    {"text": "Need better AI interfaces", "platform": "reddit", "timestamp": "2024-01-01"},
                ]
            }
        }
        p0_result = await pain_scanner.invoke(context)

        # 将 P0 输出转换为 P1 输入
        content = f"""
        用户痛点分析:
        {p0_result['count']} 个痛点被发现
        最高严重度: {p0_result.get('top_severity', 0)}
        
        主要反馈:
        """
        for point in p0_result.get('pain_points', [])[:3]:
            content += f"- {point.get('text', '')}\n"

        metadata = {
            "id": "p0_p1_flow_001",
            "type": "perception_insight",
            "created_at": datetime.now().isoformat(),
            "tags": ["痛点", "用户反馈", "AI"],
            "source_type": "social"
        }

        # P1: 价值判断
        p1_organ = create_p1_judgment_organ()
        assessment = await p1_organ.assess(content, metadata)

        assert assessment.overall_score > 0
        print(f"✅ P0->P1 Flow: 感知数据评分 = {assessment.overall_score:.2f}")

    @pytest.mark.asyncio
    async def test_judgment_to_relationship_flow(self):
        """测试 P1 -> P2 数据流"""
        # P1: 生成高质量洞察
        content = """
        AI Agent 正在从工具向协作者转变
        
        关键发现:
        1. 多 Agent 协作框架成熟
        2. 长期记忆能力提升
        3. 从被动到主动建议
        
        建议: 立即关注此领域
        """

        metadata = {
            "id": "p1_p2_flow_001",
            "type": "insight",
            "title": "AI Agent 趋势洞察",
            "created_at": datetime.now().isoformat(),
            "author": "研究员",
            "tags": ["AI", "Agent", "趋势"],
            "source_type": "expert"
        }

        p1_organ = create_p1_judgment_organ()
        assessment = await p1_organ.assess(content, metadata)

        # 只有通过判断的内容才进入 P2
        if assessment.overall_score >= 0.4:
            p2_organ = create_p2_relationship_organ()

            existing_nodes = [
                {
                    "id": "existing_001",
                    "title": "Multi-Agent Systems",
                    "content": "Multi-agent collaboration frameworks",
                    "tags": ["AI", "Agent"],
                    "created_at": (datetime.now() - timedelta(days=7)).isoformat()
                }
            ]

            analysis = await p2_organ.analyze_relationships(content, metadata, existing_nodes)
            node = p2_organ.add_to_graph(
                metadata["id"],
                content,
                metadata,
                analysis,
                p1_score=assessment.overall_score
            )

            assert node is not None
            assert node.p1_score == assessment.overall_score
            print(f"✅ P1->P2 Flow: 高分内容({assessment.overall_score:.2f})进入知识图谱")

    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        """测试完整 P0 -> P1 -> P2 管道"""
        print("\n" + "="*60)
        print("开始完整管道测试: P0 -> P1 -> P2")
        print("="*60)

        # ========== P0: 感知层 ==========
        print("\n[1/3] P0 感知层 - 收集市场情报...")

        # 模拟多个感知技能并行执行
        pain_scanner = create_pain_scanner_skill()
        emotion_watcher = create_emotion_watcher_skill()
        trend_hunter = create_trend_hunter_skill()

        p0_contexts = {
            "pain": {
                "platform_data": {
                    "comments": [
                        {"text": "I have a problem with AI collaboration", "platform": "twitter", "timestamp": "2024-01-01"},
                        {"text": "This feature is frustrating and difficult to use", "platform": "reddit", "timestamp": "2024-01-01"},
                        {"text": "I'm struggling with multi-agent systems", "platform": "hackernews", "timestamp": "2024-01-01"},
                    ]
                }
            },
            "emotion": {
                "content": [
                    {"text": "Excited about AI agents!", "timestamp": "2024-01-01"},
                    {"text": "Worried about complexity", "timestamp": "2024-01-01"},
                    {"text": "Hopeful for the future", "timestamp": "2024-01-01"},
                ]
            },
            "trend": {
                "hashtags": [
                    {"name": "AIAgent", "volume": 50000, "growth": 25.5},
                    {"name": "MultiAgent", "volume": 20000, "growth": 35.0},
                    {"name": "AgentFramework", "volume": 15000, "growth": 40.2},
                ]
            }
        }

        # 并行执行 P0 技能
        p0_results = await asyncio.gather(
            pain_scanner.invoke(p0_contexts["pain"]),
            emotion_watcher.invoke(p0_contexts["emotion"]),
            trend_hunter.invoke(p0_contexts["trend"]),
        )

        pain_result, emotion_result, trend_result = p0_results

        print(f"  ✅ Pain Scanner: {pain_result['count']} 痛点")
        print(f"  ✅ Emotion Watcher: 主导情感={emotion_result['dominant_emotion']}")
        print(f"  ✅ Trend Hunter: {len(trend_result['trends'])} 趋势")

        # 整合 P0 输出为结构化内容
        integrated_content = f"""
# 市场情报综合分析

## 用户痛点 ({pain_result['count']}个)
"""
        for point in pain_result.get('pain_points', [])[:3]:
            integrated_content += f"- [{point.get('source', '')}] {point.get('text', '')}\n"

        integrated_content += f"""
## 情感趋势
- 主导情感: {emotion_result['dominant_emotion']}
- 情感分布: {emotion_result['emotions']}

## 热门趋势
"""
        for trend in trend_result.get('trends', [])[:3]:
            integrated_content += f"- #{trend['name']}: 增长率 {trend['growth_rate']}%\n"

        # ========== P1: 判断层 ==========
        print("\n[2/3] P1 判断层 - 评估内容价值...")

        p1_metadata = {
            "id": f"integrated_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "type": "market_intelligence",
            "title": "AI Agent 市场情报",
            "created_at": datetime.now().isoformat(),
            "tags": ["AI", "Agent", "市场情报", "用户痛点", "趋势"],
            "source_type": "social",
            "focus_areas": ["AI", "Agent", "市场趋势"]
        }

        p1_organ = create_p1_judgment_organ()
        assessment = await p1_organ.assess(integrated_content, p1_metadata)

        print(f"  ✅ 综合评分: {assessment.overall_score:.2f}")
        print(f"  ✅ 优先级: {assessment.priority}")
        print(f"  ✅ 建议: {assessment.recommended_action}")

        for dim, result in assessment.judgments.items():
            print(f"    - {dim.value}: {result.score:.2f}")

        # ========== P2: 关系层 ==========
        print("\n[3/3] P2 关系层 - 构建知识关联...")

        p2_organ = create_p2_relationship_organ()

        # 模拟已有知识节点
        existing_nodes = [
            {
                "id": "knowledge_001",
                "title": "AI Agent 基础概念",
                "content": "Agent 是能够自主行动的 AI 系统，具有感知、决策和执行能力",
                "tags": ["AI", "Agent", "基础"],
                "created_at": (datetime.now() - timedelta(days=30)).isoformat()
            },
            {
                "id": "knowledge_002",
                "title": "Multi-Agent Systems 综述",
                "content": "多智能体系统的协作机制和通信协议",
                "tags": ["AI", "Agent", "Multi-Agent"],
                "created_at": (datetime.now() - timedelta(days=15)).isoformat()
            },
            {
                "id": "knowledge_003",
                "title": "2024 AI 趋势预测",
                "content": "2024年 AI 发展的主要方向和趋势",
                "tags": ["AI", "趋势", "2024"],
                "created_at": (datetime.now() - timedelta(days=7)).isoformat()
            }
        ]

        analysis = await p2_organ.analyze_relationships(
            integrated_content,
            p1_metadata,
            existing_nodes
        )

        # 将内容加入知识图谱
        node = p2_organ.add_to_graph(
            p1_metadata["id"],
            integrated_content,
            p1_metadata,
            analysis,
            p1_score=assessment.overall_score
        )

        # 获取子图
        graph = p2_organ.get_graph()

        print(f"  ✅ 发现 {len(analysis.related_nodes)} 个关联节点")
        print(f"  ✅ 建议 {len(analysis.suggested_connections)} 个连接")
        print(f"  ✅ 图谱洞察:")
        for insight in analysis.graph_insights[:3]:
            print(f"    - {insight}")

        print(f"\n  📊 知识图谱统计:")
        print(f"    - 节点数: {len(graph.nodes)}")
        print(f"    - 边数: {len(graph.edges)}")

        # ========== 验证 ==========
        print("\n" + "="*60)
        print("管道验证")
        print("="*60)

        # 验证数据流完整性
        assert pain_result["count"] > 0, "P0 应该收集到痛点数据"
        assert assessment.overall_score > 0, "P1 应该产生有效评分"
        assert node.p1_score == assessment.overall_score, "P2 应该继承 P1 评分"
        assert len(graph.nodes) > 0, "P2 应该构建知识图谱"

        print("✅ 完整管道测试通过!")
        print(f"   数据流: P0({pain_result['count']}痛点) -> P1({assessment.overall_score:.2f}分) -> P2({len(graph.nodes)}节点)")

        return {
            "p0": {
                "pain_count": pain_result["count"],
                "dominant_emotion": emotion_result["dominant_emotion"],
                "trend_count": len(trend_result["trends"])
            },
            "p1": {
                "score": assessment.overall_score,
                "priority": assessment.priority,
                "dimensions": {dim.value: result.score for dim, result in assessment.judgments.items()}
            },
            "p2": {
                "related_nodes": len(analysis.related_nodes),
                "suggestions": len(analysis.suggested_connections),
                "graph_nodes": len(graph.nodes),
                "graph_edges": len(graph.edges)
            }
        }


class TestEdgeCases:
    """测试边界情况"""

    @pytest.mark.asyncio
    async def test_low_quality_content_filtering(self):
        """测试低质量内容过滤"""
        p1_organ = create_p1_judgment_organ()

        # 低质量内容
        low_quality_content = "ok"
        metadata = {
            "id": "low_quality_001",
            "type": "note",
            "created_at": datetime.now().isoformat(),
        }

        assessment = await p1_organ.assess(low_quality_content, metadata)

        # 低质量内容应该得到低分
        assert assessment.overall_score < 0.5
        assert assessment.priority in ["low", "normal"]

        print(f"✅ 低质量内容过滤: 评分={assessment.overall_score:.2f}, 优先级={assessment.priority}")

    @pytest.mark.asyncio
    async def test_empty_content_handling(self):
        """测试空内容处理"""
        p1_organ = create_p1_judgment_organ()
        p2_organ = create_p2_relationship_organ()

        # 空内容
        empty_content = ""
        metadata = {
            "id": "empty_001",
            "type": "note",
            "title": "Empty Note"
        }

        # P1 应该能处理空内容
        assessment = await p1_organ.assess(empty_content, metadata)
        assert assessment is not None

        # P2 应该能处理空内容
        analysis = await p2_organ.analyze_relationships(empty_content, metadata)
        assert analysis is not None

        print(f"✅ 空内容处理: P1评分={assessment.overall_score:.2f}, P2关联={len(analysis.related_nodes)}")


async def run_integration_demo():
    """运行集成演示"""
    print("\n" + "="*70)
    print("活体知识系统 - P0-P2 集成演示")
    print("="*70)

    integration_test = TestP0ToP2Integration()
    result = await integration_test.test_full_pipeline()

    print("\n" + "="*70)
    print("演示完成!")
    print("="*70)
    print(f"\n结果摘要:")
    print(f"  P0 感知: {result['p0']}")
    print(f"  P1 判断: {result['p1']}")
    print(f"  P2 关系: {result['p2']}")

    return result


if __name__ == "__main__":
    # 运行演示
    asyncio.run(run_integration_demo())
