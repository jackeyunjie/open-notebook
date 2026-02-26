"""Knowledge Connector - AI-powered knowledge graph construction and cross-document analysis.

This skill enhances Open Notebook with advanced knowledge management capabilities:
1. Automatic entity extraction from sources
2. Relationship discovery between entities
3. Cross-document association and linking
4. Knowledge graph visualization
5. Cross-document question answering

Key Features:
- AI-driven entity extraction (not just existing topics)
- Semantic relationship discovery
- Implicit connection detection
- Interactive knowledge graph export
- Cross-source synthesis
"""

import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from loguru import logger

from open_notebook.domain.notebook import Notebook, Source, Note
from open_notebook.skills.base import Skill, SkillConfig, SkillContext, SkillResult, SkillStatus
from open_notebook.skills.registry import register_skill
from open_notebook.skills.visual_knowledge_graph import VisualKnowledgeGraphGenerator


@dataclass
class Entity:
    """A knowledge entity extracted from content."""
    id: str
    name: str
    entity_type: str  # person, organization, concept, technology, etc.
    mentions: List[Dict[str, Any]] = field(default_factory=list)  # Where it appears
    attributes: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


@dataclass
class Relationship:
    """A relationship between two entities."""
    source_id: str
    target_id: str
    relation_type: str  # relates_to, part_of, uses, contradicts, supports, etc.
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 1.0
    bidirectional: bool = False


@dataclass
class KnowledgeGraph:
    """Complete knowledge graph for a notebook."""
    entities: Dict[str, Entity] = field(default_factory=dict)
    relationships: List[Relationship] = field(default_factory=list)
    sources_analyzed: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "entities": {
                k: {
                    "id": v.id,
                    "name": v.name,
                    "entity_type": v.entity_type,
                    "mentions_count": len(v.mentions),
                    "attributes": v.attributes,
                    "confidence": v.confidence
                }
                for k, v in self.entities.items()
            },
            "relationships": [
                {
                    "source": r.source_id,
                    "target": r.target_id,
                    "type": r.relation_type,
                    "evidence_count": len(r.evidence),
                    "confidence": r.confidence
                }
                for r in self.relationships
            ],
            "sources_analyzed": self.sources_analyzed,
            "stats": {
                "total_entities": len(self.entities),
                "total_relationships": len(self.relationships),
                "entity_types": list(set(e.entity_type for e in self.entities.values()))
            }
        }


class KnowledgeConnector(Skill):
    """Build and manage knowledge graphs from notebook sources.

    This skill performs:
    1. Entity extraction from source content using AI
    2. Relationship discovery between entities
    3. Cross-document connection detection
    4. Knowledge graph construction and visualization
    5. Cross-source synthesis for comprehensive answers

    Parameters:
        - notebook_id: Notebook to analyze
        - source_ids: Specific sources to include (optional, all if not provided)
        - extract_entities: Whether to extract entities with AI (default: true)
        - discover_relationships: Whether to discover relationships (default: true)
        - min_confidence: Minimum confidence threshold (default: 0.7)
        - generate_visualization: Whether to generate visual outputs (default: true)

    Example:
        config = SkillConfig(
            skill_type="knowledge_connector",
            name="Knowledge Connector",
            parameters={
                "notebook_id": "notebook:abc123",
                "extract_entities": True,
                "discover_relationships": True,
                "min_confidence": 0.7
            }
        )
    """

    skill_type = "knowledge_connector"
    name = "Knowledge Connector"
    description = "Build AI-powered knowledge graphs and discover cross-document connections"

    parameters_schema = {
        "notebook_id": {
            "type": "string",
            "description": "Notebook ID to analyze"
        },
        "source_ids": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Specific source IDs to include (optional)"
        },
        "extract_entities": {
            "type": "boolean",
            "default": True,
            "description": "Extract entities using AI"
        },
        "discover_relationships": {
            "type": "boolean",
            "default": True,
            "description": "Discover relationships between entities"
        },
        "min_confidence": {
            "type": "number",
            "default": 0.7,
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "Minimum confidence threshold"
        },
        "generate_visualization": {
            "type": "boolean",
            "default": True,
            "description": "Generate visualization outputs"
        }
    }

    def __init__(self, config: SkillConfig):
        self.notebook_id: str = config.parameters.get("notebook_id", "")
        self.source_ids: Optional[List[str]] = config.parameters.get("source_ids")
        self.extract_entities: bool = config.parameters.get("extract_entities", True)
        self.discover_relationships: bool = config.parameters.get("discover_relationships", True)
        self.min_confidence: float = config.parameters.get("min_confidence", 0.7)
        self.generate_visualization: bool = config.parameters.get("generate_visualization", True)
        super().__init__(config)

    def _validate_config(self) -> None:
        """Validate configuration."""
        super()._validate_config()

        if not self.notebook_id:
            raise ValueError("notebook_id is required")

    async def _extract_entities_with_ai(self, source: Source) -> List[Entity]:
        """Extract entities from source content using AI.

        Args:
            source: Source to analyze

        Returns:
            List of extracted entities
        """
        if not source.full_text:
            return []

        try:
            from open_notebook.ai.provision import provision_langchain_model

            # Prepare extraction prompt
            content_sample = source.full_text[:8000]  # Limit for performance

            prompt = f"""Analyze the following content and extract key entities.

Content Title: {source.title or "Untitled"}
Content Type: {getattr(source, 'content_type', 'unknown')}

Content:
---
{content_sample}
---

Extract entities in this JSON format:
{{
  "entities": [
    {{
      "name": "Entity Name",
      "entity_type": "person|organization|concept|technology|location|product|event",
      "attributes": {{"key": "value"}},
      "confidence": 0.95
    }}
  ]
}}

Focus on:
- People (researchers, authors, key figures)
- Organizations (companies, institutions)
- Concepts (theories, methodologies)
- Technologies (tools, frameworks, algorithms)
- Locations (countries, cities if relevant)
- Products (software, services)
- Events (conferences, milestones)

Return ONLY the JSON, no other text."""

            model = await provision_langchain_model(
                prompt_text=prompt,
                model_id=None,
                default_type="transformation"
            )

            response = await model.ainvoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)

            # Clean and parse JSON
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            data = json.loads(response_text)

            entities = []
            for item in data.get("entities", []):
                entity = Entity(
                    id=f"entity:{source.id.split(':')[1]}:{item['name'].lower().replace(' ', '_')}",
                    name=item["name"],
                    entity_type=item.get("entity_type", "concept"),
                    mentions=[{"source_id": str(source.id), "context": ""}],
                    attributes=item.get("attributes", {}),
                    confidence=item.get("confidence", 0.8)
                )
                if entity.confidence >= self.min_confidence:
                    entities.append(entity)

            logger.info(f"Extracted {len(entities)} entities from {source.id}")
            return entities

        except Exception as e:
            logger.error(f"Entity extraction failed for {source.id}: {e}")
            return []

    async def _discover_relationships(
        self,
        entities: Dict[str, Entity],
        sources: List[Source]
    ) -> List[Relationship]:
        """Discover relationships between entities.

        Args:
            entities: Dictionary of entities
            sources: List of sources

        Returns:
            List of discovered relationships
        """
        relationships = []

        # 1. Co-occurrence relationships (entities appearing in same source)
        source_entities = defaultdict(list)
        for entity_id, entity in entities.items():
            for mention in entity.mentions:
                source_entities[mention["source_id"]].append(entity_id)

        for source_id, entity_ids in source_entities.items():
            if len(entity_ids) > 1:
                for i, e1 in enumerate(entity_ids):
                    for e2 in entity_ids[i+1:]:
                        # Check if relationship already exists
                        exists = any(
                            (r.source_id == e1 and r.target_id == e2) or
                            (r.source_id == e2 and r.target_id == e1)
                            for r in relationships
                        )
                        if not exists:
                            rel = Relationship(
                                source_id=e1,
                                target_id=e2,
                                relation_type="co_occurs_with",
                                evidence=[{"source_id": source_id, "type": "co_occurrence"}],
                                confidence=0.6,
                                bidirectional=True
                            )
                            relationships.append(rel)

        # 2. Semantic relationships using AI (if we have enough entities)
        if len(entities) >= 3 and self.discover_relationships:
            try:
                semantic_rels = await self._extract_semantic_relationships(entities)
                relationships.extend(semantic_rels)
            except Exception as e:
                logger.warning(f"Semantic relationship extraction failed: {e}")

        logger.info(f"Discovered {len(relationships)} relationships")
        return relationships

    async def _extract_semantic_relationships(
        self,
        entities: Dict[str, Entity]
    ) -> List[Relationship]:
        """Extract semantic relationships using AI.

        Args:
            entities: Dictionary of entities

        Returns:
            List of semantic relationships
        """
        try:
            from open_notebook.ai.provision import provision_langchain_model

            # Select top entities for analysis
            top_entities = sorted(
                entities.values(),
                key=lambda e: len(e.mentions),
                reverse=True
            )[:15]  # Limit to top 15

            entity_list = [
                f"{e.name} ({e.entity_type})"
                for e in top_entities
            ]

            prompt = f"""Analyze the following entities and identify meaningful relationships between them.

Entities:
{chr(10).join(f"- {name}" for name in entity_list)}

Identify relationships in this format:
{{
  "relationships": [
    {{
      "source": "Entity Name 1",
      "target": "Entity Name 2",
      "relation_type": "uses|part_of|contradicts|supports|developed_by|related_to",
      "confidence": 0.85
    }}
  ]
}}

Consider:
- Organizational relationships (part of, developed by)
- Conceptual relationships (supports, contradicts, extends)
- Functional relationships (uses, enables, requires)

Return ONLY the JSON, no other text."""

            model = await provision_langchain_model(
                prompt_text=prompt,
                model_id=None,
                default_type="transformation"
            )

            response = await model.ainvoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)

            # Clean and parse
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            data = json.loads(response_text)

            relationships = []
            name_to_id = {e.name: e.id for e in top_entities}

            for item in data.get("relationships", []):
                source_name = item.get("source", "")
                target_name = item.get("target", "")

                if source_name in name_to_id and target_name in name_to_id:
                    rel = Relationship(
                        source_id=name_to_id[source_name],
                        target_id=name_to_id[target_name],
                        relation_type=item.get("relation_type", "related_to"),
                        evidence=[{"type": "semantic_inference"}],
                        confidence=item.get("confidence", 0.7),
                        bidirectional=item.get("relation_type") in ["related_to", "co_occurs_with"]
                    )
                    if rel.confidence >= self.min_confidence:
                        relationships.append(rel)

            return relationships

        except Exception as e:
            logger.error(f"Semantic relationship extraction failed: {e}")
            return []

    def _generate_cytoscape_graph(self, kg: KnowledgeGraph) -> Dict[str, Any]:
        """Generate Cytoscape.js compatible graph data.

        Args:
            kg: Knowledge graph

        Returns:
            Cytoscape elements dictionary
        """
        nodes = []
        edges = []

        # Color scheme for entity types
        type_colors = {
            "person": "#4a90d9",
            "organization": "#d94a90",
            "concept": "#90d94a",
            "technology": "#d9904a",
            "location": "#904ad9",
            "product": "#4ad990",
            "event": "#d9d94a",
            "default": "#999999"
        }

        for entity_id, entity in kg.entities.items():
            nodes.append({
                "data": {
                    "id": entity_id,
                    "label": entity.name,
                    "type": entity.entity_type,
                    "confidence": entity.confidence,
                    "mentions": len(entity.mentions),
                    "color": type_colors.get(entity.entity_type, type_colors["default"])
                }
            })

        for i, rel in enumerate(kg.relationships):
            edges.append({
                "data": {
                    "id": f"edge_{i}",
                    "source": rel.source_id,
                    "target": rel.target_id,
                    "label": rel.relation_type,
                    "confidence": rel.confidence
                }
            })

        return {"nodes": nodes, "edges": edges}

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute knowledge graph construction."""
        logger.info(f"Building knowledge graph for notebook {self.notebook_id}")

        start_time = datetime.utcnow()

        try:
            # 1. Get notebook and sources
            notebook = await Notebook.get(self.notebook_id)
            if not notebook:
                raise ValueError(f"Notebook {self.notebook_id} not found")

            if self.source_ids:
                sources = []
                for sid in self.source_ids:
                    source = await Source.get(sid)
                    if source:
                        sources.append(source)
            else:
                sources = await notebook.get_sources()

            if not sources:
                return SkillResult(
                    skill_id=context.skill_id,
                    status=SkillStatus.SUCCESS,
                    started_at=start_time,
                    output={
                        "message": "No sources found in notebook",
                        "knowledge_graph": None,
                        "stats": {"sources_analyzed": 0}
                    }
                )

            logger.info(f"Analyzing {len(sources)} sources")

            # 2. Extract entities
            all_entities: Dict[str, Entity] = {}

            if self.extract_entities:
                for source in sources:
                    entities = await self._extract_entities_with_ai(source)
                    for entity in entities:
                        if entity.id in all_entities:
                            # Merge mentions
                            all_entities[entity.id].mentions.extend(entity.mentions)
                            all_entities[entity.id].confidence = max(
                                all_entities[entity.id].confidence,
                                entity.confidence
                            )
                        else:
                            all_entities[entity.id] = entity

            # 3. Add existing topics as entities if no AI extraction
            if not all_entities:
                for source in sources:
                    topics = getattr(source, 'topics', []) or []
                    for topic in topics:
                        entity_id = f"entity:topic:{topic.lower().replace(' ', '_')}"
                        if entity_id not in all_entities:
                            all_entities[entity_id] = Entity(
                                id=entity_id,
                                name=topic,
                                entity_type="concept",
                                mentions=[{"source_id": str(source.id)}],
                                confidence=0.8
                            )
                        else:
                            all_entities[entity_id].mentions.append({"source_id": str(source.id)})

            logger.info(f"Total entities: {len(all_entities)}")

            # 4. Discover relationships
            relationships = []
            if self.discover_relationships:
                relationships = await self._discover_relationships(all_entities, sources)

            # 5. Build knowledge graph
            kg = KnowledgeGraph(
                entities=all_entities,
                relationships=relationships,
                sources_analyzed=[str(s.id) for s in sources]
            )

            # 6. Generate visualizations
            visualizations = {}
            if self.generate_visualization:
                # Use existing visualizer for basic charts
                viz_gen = VisualKnowledgeGraphGenerator(self.notebook_id)
                await viz_gen.initialize()

                # Generate topic distribution
                visualizations["topic_bar_chart"] = await viz_gen.generate_topic_distribution(
                    [str(s.id) for s in sources],
                    chart_type="bar"
                )

                # Generate network graph
                visualizations["network_graph"] = await viz_gen.generate_network_graph(
                    [str(s.id) for s in sources]
                )

                # Generate Cytoscape graph data
                visualizations["cytoscape_data"] = self._generate_cytoscape_graph(kg)

                await viz_gen.close()

            logger.info("Knowledge graph construction complete")

            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.SUCCESS,
                started_at=start_time,
                completed_at=datetime.utcnow(),
                output={
                    "knowledge_graph": kg.to_dict(),
                    "visualizations": visualizations,
                    "stats": {
                        "sources_analyzed": len(sources),
                        "entities_extracted": len(all_entities),
                        "relationships_discovered": len(relationships),
                        "entity_types": list(set(e.entity_type for e in all_entities.values()))
                    }
                }
            )

        except Exception as e:
            logger.error(f"Knowledge graph construction failed: {e}")
            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.FAILED,
                started_at=start_time,
                completed_at=datetime.utcnow(),
                error_message=str(e)
            )


# Convenience functions
async def build_knowledge_graph(
    notebook_id: str,
    source_ids: Optional[List[str]] = None
) -> Optional[KnowledgeGraph]:
    """Build knowledge graph for a notebook.

    Args:
        notebook_id: Notebook ID
        source_ids: Specific sources (optional)

    Returns:
        KnowledgeGraph or None if failed
    """
    config = SkillConfig(
        skill_type="knowledge_connector",
        name="Build Knowledge Graph",
        parameters={
            "notebook_id": notebook_id,
            "source_ids": source_ids,
            "extract_entities": True,
            "discover_relationships": True
        }
    )

    connector = KnowledgeConnector(config)

    from open_notebook.skills.base import SkillContext
    ctx = SkillContext(
        skill_id=f"kg_build_{datetime.utcnow().timestamp()}",
        trigger_type="manual"
    )

    result = await connector.run(ctx)

    if result.success and result.output.get("knowledge_graph"):
        kg_data = result.output["knowledge_graph"]
        return KnowledgeGraph(
            entities={
                k: Entity(**v) if isinstance(v, dict) else v
                for k, v in kg_data.get("entities", {}).items()
            },
            relationships=[
                Relationship(**r) if isinstance(r, dict) else r
                for r in kg_data.get("relationships", [])
            ],
            sources_analyzed=kg_data.get("sources_analyzed", [])
        )

    return None


async def find_cross_document_connections(
    notebook_id: str,
    entity_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Find connections across documents.

    Args:
        notebook_id: Notebook ID
        entity_name: Specific entity to find connections for (optional)

    Returns:
        List of connection dictionaries
    """
    kg = await build_knowledge_graph(notebook_id)

    if not kg:
        return []

    connections = []

    # Group entities by mention sources
    entity_sources = defaultdict(list)
    for entity_id, entity in kg.entities.items():
        sources = set(m["source_id"] for m in entity.mentions)
        for source_id in sources:
            entity_sources[source_id].append(entity)

    # Find cross-document entities (appearing in multiple sources)
    for entity_id, entity in kg.entities.items():
        sources = set(m["source_id"] for m in entity.mentions)
        if len(sources) > 1:
            connections.append({
                "type": "cross_document_entity",
                "entity": entity.name,
                "entity_type": entity.entity_type,
                "sources": list(sources),
                "connection_strength": len(sources)
            })

    # Sort by connection strength
    connections.sort(key=lambda x: x["connection_strength"], reverse=True)

    return connections


# Register the skill
register_skill(KnowledgeConnector)
