"""P2 Relationship Layer - Knowledge graph construction and pattern discovery.

This layer builds relationships between knowledge nodes:
- Entity Linker: Extracts and links entities
- Semantic Cluster: Groups related content
- Temporal Weaver: Discovers time-based relationships
- Cross-Reference Mapper: Builds citation and reference networks
"""

import asyncio
import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from loguru import logger

from open_notebook.skills.living.agent_tissue import AgentTissue, AgentCoordination, CoordinationPattern
from open_notebook.skills.living.skill_cell import LivingSkill, SkillState


class RelationshipType(Enum):
    """Types of relationships between knowledge nodes."""
    SIMILAR = "similar"           # 语义相似
    RELATED = "related"           # 相关关联
    DERIVED = "derived"           # 派生关系
    CONTRADICTS = "contradicts"   # 矛盾关系
    SUPPORTS = "supports"         # 支持关系
    TEMPORAL = "temporal"         # 时序关系
    CAUSAL = "causal"             # 因果关系
    PART_OF = "part_of"           # 组成部分


@dataclass
class KnowledgeNode:
    """A node in the knowledge graph."""
    node_id: str
    node_type: str  # note, source, insight, concept
    title: str
    content_hash: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    p1_score: float = 0.5  # From P1 judgment layer


@dataclass
class KnowledgeEdge:
    """An edge connecting two knowledge nodes."""
    edge_id: str
    source_id: str
    target_id: str
    relation_type: RelationshipType
    weight: float  # 0.0 to 1.0
    evidence: str = ""  # Why this relationship exists
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class KnowledgeGraph:
    """A subgraph of related knowledge."""
    graph_id: str
    name: str
    nodes: Dict[str, KnowledgeNode] = field(default_factory=dict)
    edges: List[KnowledgeEdge] = field(default_factory=list)
    clusters: List[List[str]] = field(default_factory=list)  # Node ID clusters
    insights: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class RelationshipAnalysis:
    """Result of relationship analysis for a piece of content."""
    content_id: str
    related_nodes: List[Tuple[str, RelationshipType, float]] = field(default_factory=list)
    suggested_connections: List[Tuple[str, str, str]] = field(default_factory=list)  # (source, target, reason)
    cluster_id: Optional[str] = None
    graph_insights: List[str] = field(default_factory=list)
    analyzed_at: datetime = field(default_factory=datetime.now)


class EntityLinkerSkill(LivingSkill):
    """
    P2.1 Entity Linker - 实体链接器

    Extracts key entities from content and links them to existing knowledge:
    - Named entities (people, organizations, concepts)
    - Key terms and phrases
    - Core concepts
    """

    def __init__(self):
        super().__init__(
            skill_id="p2.entity_linker",
            name="Entity Linker",
            description="提取和链接知识实体",
            version="1.0.0"
        )
        self.entity_patterns = {
            "concept": r"(?:什么是|定义为|指的是)[""']?([^""'。，]+)",
            "person": r"(?:[^。，\n]{2,20})(?:提到|指出|认为|建议)",
            "organization": r"(?:公司|机构|团队|组织)[""']?([^""'。，]{2,30})",
        }

    async def _execute(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract and link entities."""
        content = context.get("content", "")
        content_id = context.get("content_id", "unknown")

        # Extract entities using simple patterns
        entities = self._extract_entities(content)

        # Find links to existing knowledge
        links = await self._find_entity_links(entities, context.get("existing_nodes", []))

        return {
            "content_id": content_id,
            "entities": entities,
            "links": links,
            "entity_count": len(entities)
        }

    def _extract_entities(self, content: str) -> List[Dict[str, Any]]:
        """Extract entities from content."""
        entities = []

        # Simple extraction based on patterns and heuristics
        lines = content.split('\n')

        for line in lines:
            # Look for concept definitions
            if match := re.search(self.entity_patterns["concept"], line):
                entities.append({
                    "type": "concept",
                    "name": match.group(1).strip(),
                    "context": line[:100]
                })

            # Look for emphasized terms (quotes or brackets)
            if matches := re.findall(r'["\']([^"\']{2,20})["\']', line):
                for m in matches:
                    entities.append({
                        "type": "term",
                        "name": m,
                        "context": line[:100]
                    })

            # Look for capitalized phrases (potential proper nouns)
            if matches := re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}', line):
                for m in matches:
                    if len(m) > 3:
                        entities.append({
                            "type": "proper_noun",
                            "name": m,
                            "context": line[:100]
                        })

        # Deduplicate by name
        seen = set()
        unique = []
        for e in entities:
            if e["name"] not in seen:
                seen.add(e["name"])
                unique.append(e)

        return unique[:20]  # Limit to top 20

    async def _find_entity_links(self, entities: List[Dict], existing_nodes: List[Dict]) -> List[Dict]:
        """Find links between extracted entities and existing knowledge."""
        links = []

        for entity in entities:
            entity_name = entity["name"].lower()

            for node in existing_nodes:
                node_text = f"{node.get('title', '')} {node.get('content', '')}".lower()

                # Simple string matching for links
                if entity_name in node_text:
                    links.append({
                        "entity": entity["name"],
                        "node_id": node.get("id"),
                        "match_type": "exact" if entity_name == node_text else "partial",
                        "confidence": 0.8 if entity_name in node.get("title", "").lower() else 0.5
                    })

        return links[:10]


class SemanticClusterSkill(LivingSkill):
    """
    P2.2 Semantic Cluster - 语义聚类器

    Groups related knowledge nodes based on:
    - Semantic similarity (embeddings)
    - Shared entities
    - Topic overlap
    """

    def __init__(self):
        super().__init__(
            skill_id="p2.semantic_cluster",
            name="Semantic Cluster",
            description="基于语义相似度聚类知识",
            version="1.0.0"
        )
        self.similarity_threshold = 0.7

    async def _execute(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Cluster knowledge nodes."""
        nodes = context.get("nodes", [])
        content_id = context.get("content_id", "unknown")

        if len(nodes) < 2:
            return {
                "content_id": content_id,
                "clusters": [],
                "message": "Not enough nodes to cluster"
            }

        # Build similarity matrix
        similarities = self._calculate_similarities(nodes)

        # Perform clustering
        clusters = self._cluster_nodes(nodes, similarities)

        # Find cluster for current content
        my_cluster = None
        for i, cluster in enumerate(clusters):
            if content_id in cluster:
                my_cluster = i
                break

        return {
            "content_id": content_id,
            "clusters": clusters,
            "my_cluster": my_cluster,
            "cluster_count": len(clusters),
            "avg_cluster_size": sum(len(c) for c in clusters) / len(clusters) if clusters else 0
        }

    def _calculate_similarities(self, nodes: List[Dict]) -> Dict[Tuple[str, str], float]:
        """Calculate pairwise similarities between nodes."""
        similarities = {}

        for i, node1 in enumerate(nodes):
            for node2 in nodes[i+1:]:
                sim = self._calculate_similarity(node1, node2)
                if sim > 0.3:  # Only store meaningful similarities
                    similarities[(node1["id"], node2["id"])] = sim
                    similarities[(node2["id"], node1["id"])] = sim

        return similarities

    def _calculate_similarity(self, node1: Dict, node2: Dict) -> float:
        """Calculate similarity between two nodes."""
        scores = []

        # Title similarity
        title1 = node1.get("title", "").lower()
        title2 = node2.get("title", "").lower()
        title_sim = self._text_similarity(title1, title2)
        scores.append(("title", title_sim, 0.3))

        # Content similarity (using word overlap)
        content1 = node1.get("content", "")[:500].lower()
        content2 = node2.get("content", "")[:500].lower()
        content_sim = self._text_similarity(content1, content2)
        scores.append(("content", content_sim, 0.4))

        # Tag overlap
        tags1 = set(node1.get("tags", []))
        tags2 = set(node2.get("tags", []))
        if tags1 and tags2:
            tag_sim = len(tags1 & tags2) / len(tags1 | tags2)
            scores.append(("tags", tag_sim, 0.3))

        # Weighted average
        total_weight = sum(w for _, _, w in scores)
        weighted_sum = sum(s * w for _, s, w in scores)

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple word overlap similarity."""
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _cluster_nodes(self, nodes: List[Dict], similarities: Dict[Tuple[str, str], float]) -> List[List[str]]:
        """Simple hierarchical clustering."""
        node_ids = [n["id"] for n in nodes]

        # Start with each node as its own cluster
        clusters = [[nid] for nid in node_ids]

        # Merge clusters based on similarity
        merged = True
        while merged and len(clusters) > 1:
            merged = False

            for i in range(len(clusters)):
                for j in range(i + 1, len(clusters)):
                    # Calculate average inter-cluster similarity
                    sim_sum = 0
                    count = 0
                    for nid1 in clusters[i]:
                        for nid2 in clusters[j]:
                            sim = similarities.get((nid1, nid2), 0)
                            sim_sum += sim
                            count += 1

                    avg_sim = sim_sum / count if count > 0 else 0

                    if avg_sim > self.similarity_threshold:
                        # Merge clusters
                        clusters[i] = clusters[i] + clusters[j]
                        clusters.pop(j)
                        merged = True
                        break
                if merged:
                    break

        return clusters


class TemporalWeaverSkill(LivingSkill):
    """
    P2.3 Temporal Weaver - 时序编织器

    Discovers time-based relationships:
    - Sequence (before/after)
    - Evolution (version changes)
    - Trends over time
    """

    def __init__(self):
        super().__init__(
            skill_id="p2.temporal_weaver",
            name="Temporal Weaver",
            description="发现知识的时间关系",
            version="1.0.0"
        )

    async def _execute(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Discover temporal relationships."""
        content = context.get("content", "")
        content_id = context.get("content_id", "unknown")
        metadata = context.get("metadata", {})
        created_at = metadata.get("created_at")

        # Find temporal references in content
        temporal_refs = self._extract_temporal_refs(content)

        # Find related content by time proximity
        time_neighbors = await self._find_time_neighbors(
            content_id,
            created_at,
            context.get("all_nodes", [])
        )

        # Detect sequences
        sequences = self._detect_sequences(content_id, time_neighbors)

        return {
            "content_id": content_id,
            "temporal_refs": temporal_refs,
            "time_neighbors": time_neighbors,
            "sequences": sequences,
            "temporal_insights": self._generate_temporal_insights(temporal_refs, sequences)
        }

    def _extract_temporal_refs(self, content: str) -> List[Dict[str, Any]]:
        """Extract temporal references from content."""
        refs = []

        # Date patterns
        date_patterns = [
            (r'(\d{4})年', 'year'),
            (r'(\d{4})-(\d{2})-(\d{2})', 'date'),
            (r'(\d{2})/(\d{2})/(\d{4})', 'date'),
            (r'(一|二|三|四|五|六|七|八|九|十)月', 'month'),
        ]

        for pattern, ptype in date_patterns:
            for match in re.finditer(pattern, content):
                refs.append({
                    "type": ptype,
                    "value": match.group(0),
                    "position": match.start()
                })

        # Relative time patterns
        relative_patterns = [
            (r'(?:之前|以前|此前)', 'before'),
            (r'(?:之后|以后|此后)', 'after'),
            (r'(?:当时|那时)', 'during'),
            (r'(?:现在|目前|当前)', 'now'),
        ]

        for pattern, ptype in relative_patterns:
            for match in re.finditer(pattern, content):
                refs.append({
                    "type": "relative",
                    "value": ptype,
                    "context": content[max(0, match.start()-10):min(len(content), match.end()+10)]
                })

        return refs

    async def _find_time_neighbors(self, content_id: str, created_at: Any, all_nodes: List[Dict]) -> List[Dict]:
        """Find nodes created near the same time."""
        if not created_at:
            return []

        try:
            if isinstance(created_at, str):
                created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                created_dt = created_at
        except:
            return []

        neighbors = []
        window = timedelta(days=7)  # 1 week window

        for node in all_nodes:
            if node.get("id") == content_id:
                continue

            node_time = node.get("created_at")
            if not node_time:
                continue

            try:
                if isinstance(node_time, str):
                    node_dt = datetime.fromisoformat(node_time.replace('Z', '+00:00'))
                else:
                    node_dt = node_time

                diff = abs((node_dt - created_dt).total_seconds())
                if diff <= window.total_seconds():
                    neighbors.append({
                        "node_id": node["id"],
                        "time_diff_hours": diff / 3600,
                        "relation": "temporal_proximity"
                    })
            except:
                continue

        return sorted(neighbors, key=lambda x: x["time_diff_hours"])[:10]

    def _detect_sequences(self, content_id: str, neighbors: List[Dict]) -> List[Dict]:
        """Detect sequential relationships."""
        sequences = []

        # Group neighbors by time direction
        before = [n for n in neighbors if n.get("time_diff_hours", 0) > 0]
        after = [n for n in neighbors if n.get("time_diff_hours", 0) < 0]

        if before:
            sequences.append({
                "type": "follows",
                "predecessors": [n["node_id"] for n in before[:3]],
                "current": content_id
            })

        if after:
            sequences.append({
                "type": "precedes",
                "current": content_id,
                "successors": [n["node_id"] for n in after[:3]]
            })

        return sequences

    def _generate_temporal_insights(self, refs: List[Dict], sequences: List[Dict]) -> List[str]:
        """Generate insights about temporal patterns."""
        insights = []

        if len(refs) > 3:
            insights.append(f"内容包含 {len(refs)} 个时间引用，可能是时序性分析")

        if sequences:
            seq_count = sum(len(s.get("predecessors", [])) + len(s.get("successors", [])) for s in sequences)
            insights.append(f"发现 {seq_count} 个时间序列关联")

        return insights


class CrossReferenceSkill(LivingSkill):
    """
    P2.4 Cross-Reference Mapper - 交叉引用映射器

    Builds citation and reference networks:
    - Direct citations
    - Conceptual references
    - Related work suggestions
    """

    def __init__(self):
        super().__init__(
            skill_id="p2.cross_reference",
            name="Cross-Reference Mapper",
            description="构建知识引用和参考网络",
            version="1.0.0"
        )

    async def _execute(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build cross-reference network."""
        content = context.get("content", "")
        content_id = context.get("content_id", "unknown")
        metadata = context.get("metadata", {})

        # Find explicit references
        explicit_refs = self._find_explicit_refs(content)

        # Find implicit references based on content overlap
        implicit_refs = await self._find_implicit_refs(
            content,
            content_id,
            context.get("all_nodes", [])
        )

        # Suggest related reading
        suggestions = self._suggest_related(content, metadata, context.get("all_nodes", []))

        return {
            "content_id": content_id,
            "explicit_refs": explicit_refs,
            "implicit_refs": implicit_refs,
            "suggestions": suggestions,
            "reference_count": len(explicit_refs) + len(implicit_refs)
        }

    def _find_explicit_refs(self, content: str) -> List[Dict]:
        """Find explicit citations in content."""
        refs = []

        # Reference patterns
        patterns = [
            (r'(?:参见|参考|引用|出自)[《"\']([^《"\']+)[》"\']', "cite"),
            (r'(?:根据|依据|基于)([^，。]{2,20})的', "source"),
            (r'(?:[^。，\n]{2,30})(?:等?人?)(?:提出|指出|发现|认为)', "author"),
        ]

        for pattern, reftype in patterns:
            for match in re.finditer(pattern, content):
                refs.append({
                    "type": reftype,
                    "reference": match.group(1).strip(),
                    "context": content[max(0, match.start()-20):min(len(content), match.end()+20)]
                })

        # URL references
        urls = re.findall(r'https?://[^\s\)]+', content)
        for url in urls:
            refs.append({
                "type": "url",
                "reference": url,
                "context": "external_link"
            })

        return refs[:15]

    async def _find_implicit_refs(self, content: str, content_id: str, all_nodes: List[Dict]) -> List[Dict]:
        """Find implicit references through content similarity."""
        implicit = []

        content_words = set(content.lower().split())

        for node in all_nodes:
            if node.get("id") == content_id:
                continue

            node_content = f"{node.get('title', '')} {node.get('content', '')}".lower()
            node_words = set(node_content.split())

            # Calculate overlap
            if content_words and node_words:
                overlap = len(content_words & node_words)
                total = len(content_words | node_words)
                similarity = overlap / total if total > 0 else 0

                if similarity > 0.3:  # Significant overlap
                    implicit.append({
                        "node_id": node["id"],
                        "similarity": round(similarity, 3),
                        "shared_terms": list(content_words & node_words)[:10],
                        "type": "content_similarity"
                    })

        return sorted(implicit, key=lambda x: x["similarity"], reverse=True)[:10]

    def _suggest_related(self, content: str, metadata: Dict, all_nodes: List[Dict]) -> List[Dict]:
        """Suggest related content to explore."""
        suggestions = []

        # Get tags from metadata
        my_tags = set(metadata.get("tags", []))

        for node in all_nodes:
            node_tags = set(node.get("tags", []))

            if my_tags and node_tags:
                overlap = len(my_tags & node_tags)
                if overlap > 0:
                    suggestions.append({
                        "node_id": node["id"],
                        "title": node.get("title", "Untitled"),
                        "shared_tags": list(my_tags & node_tags),
                        "relevance_score": overlap / len(my_tags | node_tags)
                    })

        return sorted(suggestions, key=lambda x: x["relevance_score"], reverse=True)[:5]


class P2RelationshipOrgan(AgentTissue):
    """
    P2 Relationship Organ - 关系构建器官

    Coordinates four relationship skills to build
    comprehensive knowledge graphs from incoming content.
    """

    def __init__(self):
        super().__init__(
            agent_id="p2.relationship_organ",
            name="P2 Relationship Organ",
            description="四维度关系构建器官",
            purpose="构建知识图谱、发现关联、建立引用网络",
            coordination=AgentCoordination(pattern=CoordinationPattern.PARALLEL)
        )

        # Create skills
        entity_skill = EntityLinkerSkill()
        cluster_skill = SemanticClusterSkill()
        temporal_skill = TemporalWeaverSkill()
        xref_skill = CrossReferenceSkill()

        # Add to organ
        self.add_skill(entity_skill.skill_id)
        self.add_skill(cluster_skill.skill_id)
        self.add_skill(temporal_skill.skill_id)
        self.add_skill(xref_skill.skill_id)

        # Store references
        self._entity_skill = entity_skill
        self._cluster_skill = cluster_skill
        self._temporal_skill = temporal_skill
        self._xref_skill = xref_skill

        # Knowledge graph storage
        self._nodes: Dict[str, KnowledgeNode] = {}
        self._edges: List[KnowledgeEdge] = []

        logger.info("P2 Relationship Organ initialized with 4 relationship skills")

    async def analyze_relationships(self, content: str, metadata: Dict[str, Any],
                                   existing_nodes: Optional[List[Dict]] = None) -> RelationshipAnalysis:
        """
        Perform comprehensive relationship analysis.

        Args:
            content: Content to analyze
            metadata: Associated metadata
            existing_nodes: Optional list of existing knowledge nodes

        Returns:
            RelationshipAnalysis with all discovered relationships
        """
        content_id = metadata.get("id", hashlib.md5(content.encode()).hexdigest()[:12])

        # Prepare context
        context = {
            "content": content,
            "content_id": content_id,
            "metadata": metadata,
            "nodes": existing_nodes or [],
            "all_nodes": existing_nodes or []
        }

        # Execute all skills in parallel
        execution_result = await self.execute(context)

        # Parse results
        entity_result = {}
        cluster_result = {}
        temporal_result = {}
        xref_result = {}

        if execution_result.get("success") and "result" in execution_result:
            for item in execution_result["result"]:
                if isinstance(item, dict) and "result" in item:
                    skill_result = item["result"]
                    skill_id = item.get("skill_id", "")

                    if "entity" in skill_id:
                        entity_result = skill_result
                    elif "cluster" in skill_id:
                        cluster_result = skill_result
                    elif "temporal" in skill_id:
                        temporal_result = skill_result
                    elif "cross" in skill_id or "xref" in skill_id:
                        xref_result = skill_result

        # Build relationship analysis
        related_nodes = []
        suggested_connections = []
        insights = []

        # From entity linking
        for link in entity_result.get("links", []):
            related_nodes.append((link["node_id"], RelationshipType.RELATED, link["confidence"]))

        # From cross-reference
        for ref in xref_result.get("implicit_refs", []):
            related_nodes.append((ref["node_id"], RelationshipType.RELATED, ref["similarity"]))
            suggested_connections.append((
                content_id,
                ref["node_id"],
                f"内容相似度 {ref['similarity']}"
            ))

        # From temporal
        for seq in temporal_result.get("sequences", []):
            for pred in seq.get("predecessors", []):
                related_nodes.append((pred, RelationshipType.TEMPORAL, 0.8))
                suggested_connections.append((pred, content_id, "时序前驱"))

        # From suggestions
        for sugg in xref_result.get("suggestions", []):
            insights.append(f"建议阅读: {sugg['title']} (共享标签: {', '.join(sugg['shared_tags'])})")

        # Temporal insights
        insights.extend(temporal_result.get("temporal_insights", []))

        # Deduplicate related nodes
        seen = set()
        unique_related = []
        for nid, rtype, weight in related_nodes:
            key = (nid, rtype)
            if key not in seen:
                seen.add(key)
                unique_related.append((nid, rtype, weight))

        return RelationshipAnalysis(
            content_id=content_id,
            related_nodes=unique_related,
            suggested_connections=suggested_connections,
            cluster_id=str(cluster_result.get("my_cluster")) if cluster_result.get("my_cluster") is not None else None,
            graph_insights=insights
        )

    def add_to_graph(self, content_id: str, content: str, metadata: Dict,
                    analysis: RelationshipAnalysis, p1_score: float = 0.5) -> KnowledgeNode:
        """Add a node to the knowledge graph."""
        # Create node
        node = KnowledgeNode(
            node_id=content_id,
            node_type=metadata.get("type", "note"),
            title=metadata.get("title", "Untitled"),
            content_hash=hashlib.md5(content.encode()).hexdigest()[:16],
            metadata=metadata,
            p1_score=p1_score
        )

        self._nodes[content_id] = node

        # Create edges from analysis
        for target_id, rel_type, weight in analysis.related_nodes:
            if target_id in self._nodes:
                edge = KnowledgeEdge(
                    edge_id=f"{content_id}_{target_id}_{rel_type.value}",
                    source_id=content_id,
                    target_id=target_id,
                    relation_type=rel_type,
                    weight=weight
                )
                self._edges.append(edge)

        return node

    def get_graph(self, node_ids: Optional[List[str]] = None) -> KnowledgeGraph:
        """Get a subgraph containing specified nodes."""
        if node_ids is None:
            node_ids = list(self._nodes.keys())

        nodes = {nid: self._nodes[nid] for nid in node_ids if nid in self._nodes}

        # Get edges between these nodes
        edges = [
            e for e in self._edges
            if e.source_id in node_ids and e.target_id in node_ids
        ]

        return KnowledgeGraph(
            graph_id=f"subgraph_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name="Knowledge Subgraph",
            nodes=nodes,
            edges=edges
        )


# ============================================================================
# Factory Functions
# ============================================================================

def create_p2_relationship_organ() -> P2RelationshipOrgan:
    """Factory function to create P2 Relationship Organ."""
    return P2RelationshipOrgan()


async def demo_relationship_analysis():
    """Demo function to show P2 in action."""
    organ = create_p2_relationship_organ()

    # Sample content
    content = """
    AI Agent 正在从工具向协作者转变

    2024年以来，这个趋势越来越明显。根据 OpenAI 的研究，
    多 Agent 协作框架正在快速成熟。此前的研究主要集中在单 Agent 能力上。

    这个转变有三个关键信号：
    1. 多 Agent 协作框架的成熟（参见《Multi-Agent Systems Survey》）
    2. 长期记忆和上下文理解能力的提升
    3. 从被动响应到主动建议的演进

    这与2023年的技术路线有显著不同。建议立即关注这个领域。
    https://openai.com/research
    """

    # Sample existing nodes
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
        },
        {
            "id": "node_003",
            "title": "多 Agent 系统研究",
            "content": "Multi-Agent Systems 是 AI 的重要方向",
            "tags": ["AI", "Agent", "多Agent"],
            "created_at": (datetime.now() - timedelta(days=5)).isoformat()
        }
    ]

    metadata = {
        "id": "demo_p2_001",
        "type": "insight",
        "title": "AI Agent 趋势分析",
        "created_at": datetime.now().isoformat(),
        "tags": ["AI", "Agent", "趋势", "2024"]
    }

    # Analyze relationships
    analysis = await organ.analyze_relationships(content, metadata, existing_nodes)

    # Add to graph
    node = organ.add_to_graph(
        analysis.content_id,
        content,
        metadata,
        analysis,
        p1_score=0.75
    )

    # Get subgraph
    graph = organ.get_graph()

    # Print results
    print("=" * 60)
    print("P2 Relationship Analysis Demo")
    print("=" * 60)
    print(f"Content ID: {analysis.content_id}")
    print(f"Cluster ID: {analysis.cluster_id}")
    print(f"Related Nodes: {len(analysis.related_nodes)}")
    print()

    print("Discovered Relationships:")
    for nid, rtype, weight in analysis.related_nodes:
        print(f"  -> {nid} [{rtype.value}] weight={weight:.2f}")

    print()
    print("Suggested Connections:")
    for source, target, reason in analysis.suggested_connections:
        print(f"  {source} → {target}: {reason}")

    print()
    print("Graph Insights:")
    for insight in analysis.graph_insights:
        print(f"  - {insight}")

    print()
    print(f"Graph Stats: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
    print("=" * 60)

    return analysis, graph


if __name__ == "__main__":
    asyncio.run(demo_relationship_analysis())
