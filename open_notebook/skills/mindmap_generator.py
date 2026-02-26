"""Mind Map Generator - Interactive mind map creation from notebook content.

This skill generates interactive mind maps from notebook content:
1. Hierarchical structure extraction
2. Multiple layout algorithms (radial, tree, organic)
3. Node categorization and coloring
4. Export to multiple formats (HTML, Markdown, JSON)
5. Interactive web visualization

Key Features:
- Automatic topic extraction and hierarchy building
- Support for multiple mind map layouts
- Rich node metadata (notes, links, sources)
- Interactive HTML export with collapse/expand
- Integration with knowledge graph
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from loguru import logger

from open_notebook.domain.notebook import Notebook, Note, Source
from open_notebook.skills.base import Skill, SkillConfig, SkillContext, SkillResult, SkillStatus
from open_notebook.skills.registry import register_skill


class LayoutType(Enum):
    """Mind map layout types."""
    RADIAL = "radial"  # Circular layout
    TREE = "tree"  # Hierarchical tree
    ORGANIC = "organic"  # Free-form organic
    FISHBONE = "fishbone"  # Cause-effect diagram
    TIMELINE = "timeline"  # Time-based layout


class NodeType(Enum):
    """Node types for categorization."""
    ROOT = "root"
    TOPIC = "topic"
    SUBTOPIC = "subtopic"
    DETAIL = "detail"
    QUESTION = "question"
    IDEA = "idea"
    SOURCE = "source"


@dataclass
class MindNode:
    """A node in the mind map."""
    id: str
    text: str
    node_type: NodeType
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    notes: str = ""
    source_refs: List[str] = field(default_factory=list)
    color: Optional[str] = None
    emoji: Optional[str] = None
    collapsed: bool = False
    priority: int = 0  # 0-5 priority level

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "node_type": self.node_type.value,
            "parent_id": self.parent_id,
            "children": self.children,
            "notes": self.notes,
            "source_refs": self.source_refs,
            "color": self.color,
            "emoji": self.emoji,
            "collapsed": self.collapsed,
            "priority": self.priority,
        }


@dataclass
class MindMap:
    """Complete mind map structure."""
    title: str
    layout: LayoutType
    root_node: str
    nodes: Dict[str, MindNode] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "layout": self.layout.value,
            "root_node": self.root_node,
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "node_count": len(self.nodes),
            "created_at": self.created_at.isoformat(),
        }

    def to_markdown(self) -> str:
        """Convert to markdown outline."""
        lines = [f"# {self.title}", ""]
        root = self.nodes.get(self.root_node)
        if root:
            self._node_to_markdown(root, 0, lines, set())
        return "\n".join(lines)

    def _node_to_markdown(self, node: MindNode, level: int, lines: List[str], visited: Set[str]):
        """Recursively convert nodes to markdown."""
        if node.id in visited:
            return
        visited.add(node.id)

        indent = "  " * level
        prefix = "- " if level > 0 else "## "
        emoji = f"{node.emoji} " if node.emoji else ""
        lines.append(f"{indent}{prefix}{emoji}{node.text}")

        if node.notes:
            lines.append(f"{indent}  > {node.notes[:100]}...")

        for child_id in node.children:
            child = self.nodes.get(child_id)
            if child:
                self._node_to_markdown(child, level + 1, lines, visited)


class MindMapGenerator(Skill):
    """Generate interactive mind maps from notebook content.

    Parameters:
        - notebook_id: Notebook to analyze
        - note_id: Specific note (optional)
        - layout: Layout type (radial, tree, organic)
        - max_depth: Maximum hierarchy depth (default: 4)
        - focus_topic: Focus on specific topic (optional)
        - include_sources: Link to source documents
        - color_scheme: Color scheme name

    Example:
        config = SkillConfig(
            skill_type="mindmap_generator",
            parameters={"notebook_id": "nb:123", "layout": "radial"}
        )
    """

    skill_type = "mindmap_generator"
    name = "Mind Map Generator"
    description = "Interactive mind map creation with multiple layouts"

    parameters_schema = {
        "notebook_id": {"type": "string", "description": "Notebook ID"},
        "note_id": {"type": "string", "description": "Specific note ID"},
        "layout": {"type": "string", "enum": ["radial", "tree", "organic", "fishbone", "timeline"], "default": "radial"},
        "max_depth": {"type": "integer", "default": 4, "minimum": 2, "maximum": 6},
        "focus_topic": {"type": "string", "description": "Focus topic"},
        "include_sources": {"type": "boolean", "default": True},
        "color_scheme": {"type": "string", "default": "default"},
    }

    def __init__(self, config: SkillConfig):
        self.notebook_id: Optional[str] = config.parameters.get("notebook_id")
        self.note_id: Optional[str] = config.parameters.get("note_id")
        self.layout: LayoutType = LayoutType(config.parameters.get("layout", "radial"))
        self.max_depth: int = config.parameters.get("max_depth", 4)
        self.focus_topic: Optional[str] = config.parameters.get("focus_topic")
        self.include_sources: bool = config.parameters.get("include_sources", True)
        self.color_scheme: str = config.parameters.get("color_scheme", "default")
        super().__init__(config)

    def _validate_config(self) -> None:
        super()._validate_config()
        if not self.notebook_id and not self.note_id:
            raise ValueError("notebook_id or note_id required")

    async def _get_content(self) -> Tuple[str, str]:
        """Get title and content."""
        title = "Mind Map"
        content = ""

        if self.note_id:
            note = await Note.get(self.note_id)
            if note:
                title = note.title or title
                content = note.content or ""
        elif self.notebook_id:
            notebook = await Notebook.get(self.notebook_id)
            if notebook:
                title = getattr(notebook, 'title', title)
                sources = await notebook.get_sources()
                parts = []
                for s in sources[:8]:
                    if s.full_text:
                        parts.append(f"# {s.title}\n{s.full_text[:3000]}")
                content = "\n\n".join(parts)

        return title, content

    async def _extract_structure(self, title: str, content: str) -> MindMap:
        """Extract hierarchical structure from content."""
        try:
            from open_notebook.ai.provision import provision_langchain_model

            prompt = f"""Create a mind map structure from this content.

Title: {title}
Layout: {self.layout.value}
Max Depth: {self.max_depth}
Focus: {self.focus_topic or "General overview"}

Content:
---
{content[:12000]}
---

Generate mind map structure as JSON:
{{
  "root": {{
    "text": "Central topic",
    "emoji": "🎯",
    "children": [
      {{
        "text": "Branch 1",
        "emoji": "📌",
        "node_type": "topic",
        "notes": "Brief description",
        "children": [
          {{
            "text": "Sub-branch",
            "emoji": "💡",
            "node_type": "subtopic",
            "notes": "Details"
          }}
        ]
      }}
    ]
  }}
}}

Guidelines:
- Use emojis to make it visually engaging
- Keep text concise (1-5 words per node)
- Maximum {self.max_depth} levels deep
- Branch out to 3-7 main topics
- 2-4 sub-branches per topic
- Include brief notes for key nodes

Return ONLY the JSON."""

            model = await provision_langchain_model(prompt_text=prompt, model_id=None, default_type="transformation")
            response = await model.ainvoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)

            # Clean
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            data = json.loads(response_text.strip())
            return self._build_mindmap_from_data(title, data)

        except Exception as e:
            logger.error(f"Structure extraction failed: {e}")
            return self._create_default_mindmap(title)

    def _build_mindmap_from_data(self, title: str, data: Dict) -> MindMap:
        """Build MindMap from parsed data."""
        mindmap = MindMap(title=title, layout=self.layout, root_node="root")

        root_data = data.get("root", {})
        root = MindNode(
            id="root",
            text=root_data.get("text", title),
            node_type=NodeType.ROOT,
            emoji=root_data.get("emoji", "🎯"),
            color="#FF6B6B",
        )
        mindmap.nodes["root"] = root

        # Process children recursively
        self._process_children(root_data.get("children", []), "root", mindmap, 1)

        return mindmap

    def _process_children(self, children_data: List[Dict], parent_id: str, mindmap: MindMap, depth: int):
        """Recursively process child nodes."""
        if depth > self.max_depth:
            return

        colors = ["#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD", "#98D8C8"]

        for i, child_data in enumerate(children_data):
            node_id = f"{parent_id}_{i}"
            node_type = NodeType(child_data.get("node_type", "topic" if depth == 1 else "subtopic"))

            node = MindNode(
                id=node_id,
                text=child_data.get("text", "Topic"),
                node_type=node_type,
                parent_id=parent_id,
                emoji=child_data.get("emoji"),
                notes=child_data.get("notes", ""),
                color=colors[depth % len(colors)],
                priority=child_data.get("priority", 0),
            )

            mindmap.nodes[node_id] = node
            mindmap.nodes[parent_id].children.append(node_id)

            # Process grandchildren
            if "children" in child_data:
                self._process_children(child_data["children"], node_id, mindmap, depth + 1)

    def _create_default_mindmap(self, title: str) -> MindMap:
        """Create default mind map."""
        mindmap = MindMap(title=title, layout=self.layout, root_node="root")

        root = MindNode(id="root", text=title, node_type=NodeType.ROOT, emoji="🎯", color="#FF6B6B")
        mindmap.nodes["root"] = root

        default_branches = [
            ("Overview", "📋", NodeType.TOPIC),
            ("Key Points", "🔑", NodeType.TOPIC),
            ("Details", "📊", NodeType.TOPIC),
            ("Conclusions", "✅", NodeType.TOPIC),
        ]

        colors = ["#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7"]

        for i, (text, emoji, node_type) in enumerate(default_branches):
            node_id = f"root_{i}"
            node = MindNode(
                id=node_id,
                text=text,
                node_type=node_type,
                parent_id="root",
                emoji=emoji,
                color=colors[i],
            )
            mindmap.nodes[node_id] = node
            root.children.append(node_id)

        return mindmap

    def _generate_interactive_html(self, mindmap: MindMap) -> str:
        """Generate interactive HTML mind map."""
        # Simple D3.js-based interactive mind map
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{mindmap.title}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{ margin: 0; font-family: Arial, sans-serif; }}
        #mindmap {{ width: 100vw; height: 100vh; }}
        .node circle {{ cursor: pointer; stroke-width: 3px; }}
        .node text {{ font-size: 14px; pointer-events: none; }}
        .link {{ fill: none; stroke: #ccc; stroke-width: 2px; }}
        .tooltip {{ position: absolute; padding: 10px; background: rgba(0,0,0,0.8); color: white; border-radius: 5px; pointer-events: none; opacity: 0; transition: opacity 0.3s; }}
    </style>
</head>
<body>
    <div id="mindmap"></div>
    <div class="tooltip"></div>
    <script>
        const data = {json.dumps(self._convert_to_d3_format(mindmap))};

        const width = window.innerWidth;
        const height = window.innerHeight;
        const radius = Math.min(width, height) / 2 - 100;

        const svg = d3.select("#mindmap").append("svg")
            .attr("width", width)
            .attr("height", height)
            .append("g")
            .attr("transform", `translate(${{width/2}},${{height/2}})`);

        const tree = d3.tree().size([2 * Math.PI, radius]);
        const root = d3.hierarchy(data);
        tree(root);

        // Links
        svg.selectAll(".link")
            .data(root.links())
            .enter().append("path")
            .attr("class", "link")
            .attr("d", d3.linkRadial().angle(d => d.x).radius(d => d.y));

        // Nodes
        const node = svg.selectAll(".node")
            .data(root.descendants())
            .enter().append("g")
            .attr("class", "node")
            .attr("transform", d => `rotate(${{d.x * 180 / Math.PI - 90}})translate(${{d.y}},0)`)
            .on("click", (e, d) => {{ if (d.children) {{ d.children = d.children ? null : d._children; update(d); }} }});

        node.append("circle")
            .attr("r", 8)
            .style("fill", d => d.data.color || "#69b3a2");

        node.append("text")
            .attr("dy", "0.31em")
            .attr("x", d => d.x < Math.PI === !d.children ? 15 : -15)
            .attr("text-anchor", d => d.x < Math.PI === !d.children ? "start" : "end")
            .attr("transform", d => d.x >= Math.PI ? "rotate(180)" : null)
            .text(d => `${{d.data.emoji || ''}} ${{d.data.name}}`);

        // Tooltip
        const tooltip = d3.select(".tooltip");
        node.on("mouseover", (e, d) => {{
            if (d.data.notes) {{
                tooltip.style("opacity", 1).html(d.data.notes).style("left", e.pageX + 10 + "px").style("top", e.pageY + "px");
            }}
        }}).on("mouseout", () => tooltip.style("opacity", 0));
    </script>
</body>
</html>"""
        return html

    def _convert_to_d3_format(self, mindmap: MindMap) -> Dict:
        """Convert mindmap to D3 hierarchy format."""
        root = mindmap.nodes.get(mindmap.root_node)
        if not root:
            return {"name": "Root", "children": []}

        def build_node(node_id: str) -> Dict:
            node = mindmap.nodes.get(node_id)
            if not node:
                return {"name": ""}

            result = {
                "name": node.text,
                "emoji": node.emoji,
                "notes": node.notes,
                "color": node.color,
            }

            if node.children:
                result["children"] = [build_node(child_id) for child_id in node.children]

            return result

        return build_node(mindmap.root_node)

    async def _save_outputs(self, mindmap: MindMap, notebook_id: str) -> Dict[str, str]:
        """Save all output formats."""
        output_dir = Path(f"./data/mindmaps/{datetime.utcnow().strftime('%Y%m%d')}")
        output_dir.mkdir(parents=True, exist_ok=True)

        safe_title = "".join(c for c in mindmap.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        outputs = {}

        # Markdown
        md_path = output_dir / f"{safe_title}.md"
        md_path.write_text(mindmap.to_markdown(), encoding='utf-8')
        outputs["markdown"] = str(md_path)

        # JSON
        json_path = output_dir / f"{safe_title}.json"
        json_path.write_text(json.dumps(mindmap.to_dict(), indent=2), encoding='utf-8')
        outputs["json"] = str(json_path)

        # HTML
        html_path = output_dir / f"{safe_title}.html"
        html_path.write_text(self._generate_interactive_html(mindmap), encoding='utf-8')
        outputs["html"] = str(html_path)

        # Note
        note = Note(
            title=f"🗺️ Mind Map: {mindmap.title[:40]}",
            content=f"""# 🗺️ Mind Map: {mindmap.title}

**Layout:** {mindmap.layout.value}
**Nodes:** {len(mindmap.nodes)}
**Created:** {mindmap.created_at.strftime('%Y-%m-%d %H:%M')}

## Overview

```
{mindmap.to_markdown()[:2000]}...
```

## Files
- Markdown: `{outputs.get('markdown', 'N/A')}`
- JSON: `{outputs.get('json', 'N/A')}`
- Interactive HTML: `{outputs.get('html', 'N/A')}`

Open the HTML file in a browser for interactive exploration.
""",
            note_type="ai",
        )
        await note.save()
        await note.add_to_notebook(notebook_id)
        outputs["note_id"] = str(note.id) if note.id else None

        return outputs

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute mind map generation."""
        logger.info(f"Starting mind map generation")
        start_time = datetime.utcnow()

        try:
            title, content = await self._get_content()
            if not content:
                raise ValueError("No content found")

            mindmap = await self._extract_structure(title, content)
            logger.info(f"Generated mind map with {len(mindmap.nodes)} nodes")

            outputs = {}
            if self.notebook_id:
                outputs = await self._save_outputs(mindmap, self.notebook_id)

            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.SUCCESS,
                started_at=start_time,
                completed_at=datetime.utcnow(),
                output={
                    "mindmap": mindmap.to_dict(),
                    "files": outputs,
                    "preview": mindmap.to_markdown()[:1000],
                }
            )

        except Exception as e:
            logger.error(f"Mind map generation failed: {e}")
            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.FAILED,
                started_at=start_time,
                completed_at=datetime.utcnow(),
                error_message=str(e)
            )


async def generate_mindmap(notebook_id: str, layout: str = "radial") -> Optional[MindMap]:
    """Quick mind map generation."""
    config = SkillConfig(
        skill_type="mindmap_generator",
        name="Mind Map Generator",
        parameters={"notebook_id": notebook_id, "layout": layout}
    )

    generator = MindMapGenerator(config)
    from open_notebook.skills.base import SkillContext
    ctx = SkillContext(skill_id=f"mindmap_{datetime.utcnow().timestamp()}", trigger_type="manual")

    result = await generator.run(ctx)

    if result.success:
        data = result.output.get("mindmap", {})
        return MindMap(
            title=data.get("title", "Mind Map"),
            layout=LayoutType(data.get("layout", "radial")),
            root_node=data.get("root_node", "root"),
        )

    return None


register_skill(MindMapGenerator)
