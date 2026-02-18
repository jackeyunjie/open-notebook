"""
Visual Knowledge Graph Generator - 可视化知识图谱生成器

功能:
1. 思维导图（Mermaid 格式）
2. 时间线（研究演进）
3. 网络图（概念关联）
4. 柱状图/饼图（主题分布）
5. 导出为 HTML 交互式图表
"""

import asyncio
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from loguru import logger

from open_notebook.domain.notebook import Notebook, Source


class VisualKnowledgeGraphGenerator:
    """可视化知识图谱生成器"""
    
    def __init__(self, notebook_id: str):
        self.notebook_id = notebook_id
        self.notebook: Optional[Notebook] = None
        
    async def initialize(self):
        """初始化"""
        logger.info(f"Initializing VisualKnowledgeGraphGenerator for notebook {self.notebook_id}")
        self.notebook = await Notebook.get(self.notebook_id)
        if not self.notebook:
            raise ValueError(f"Notebook {self.notebook_id} not found")
    
    async def generate_mind_map(
        self,
        source_ids: Optional[List[str]] = None,
        max_concepts: int = 20
    ) -> str:
        """生成思维导图（Mermaid 格式）
        
        Args:
            source_ids: 指定源列表
            max_concepts: 最大概念数量
            
        Returns:
            Mermaid 格式的思维导图
        """
        sources = await self._get_sources(source_ids)
        
        # 提取概念和关系
        concepts, relations = await self._extract_concepts_and_relations(sources)
        
        # 排序并限制数量
        sorted_concepts = sorted(concepts.items(), key=lambda x: x[1], reverse=True)[:max_concepts]
        
        # 生成 Mermaid 思维导图
        mind_map = self._generate_mermaid_mindmap(sorted_concepts, relations[:50])
        
        return mind_map
    
    async def generate_timeline(
        self,
        source_ids: Optional[List[str]] = None
    ) -> str:
        """生成时间线（研究演进）
        
        Args:
            source_ids: 指定源列表
            
        Returns:
            Mermaid 格式的时间线
        """
        sources = await self._get_sources(source_ids)
        
        # 按时间排序（假设有 created 字段）
        # TODO: 实际需要从数据库获取真实时间
        timeline_data = []
        for i, source in enumerate(sources, 1):
            title = getattr(source, 'title', f'Untitled {i}')
            topics = getattr(source, 'topics', []) or []
            timeline_data.append({
                'order': i,
                'title': title,
                'topics': topics[:3],
                'date': f'Day {i}'  # 简化处理
            })
        
        # 生成 Mermaid 时间线
        timeline = self._generate_mermaid_timeline(timeline_data)
        
        return timeline
    
    async def generate_network_graph(
        self,
        source_ids: Optional[List[str]] = None,
        min_connections: int = 2
    ) -> str:
        """生成网络图（概念关联）
        
        Args:
            source_ids: 指定源列表
            min_connections: 最小连接数
            
        Returns:
            Mermaid 网络图或 JSON 格式（用于 D3.js）
        """
        sources = await self._get_sources(source_ids)
        
        # 提取概念共现关系
        concept_cooccurrence = defaultdict(lambda: defaultdict(int))
        
        for source in sources:
            concepts = getattr(source, 'topics', []) or []
            for i, c1 in enumerate(concepts):
                for c2 in concepts[i+1:]:
                    concept_cooccurrence[c1][c2] += 1
                    concept_cooccurrence[c2][c1] += 1
        
        # 筛选强关联
        links = []
        processed = set()
        for c1, related in concept_cooccurrence.items():
            for c2, count in related.items():
                if count >= min_connections and (c1, c2) not in processed:
                    links.append((c1, c2, count))
                    processed.add((c1, c2))
                    processed.add((c2, c1))
        
        # 生成 Mermaid 网络图
        network_graph = self._generate_mermaid_network(links[:30])
        
        return network_graph
    
    async def generate_topic_distribution(
        self,
        source_ids: Optional[List[str]] = None,
        top_n: int = 10,
        chart_type: str = "bar"
    ) -> str:
        """生成主题分布图
        
        Args:
            source_ids: 指定源列表
            top_n: 显示前 N 个主题
            chart_type: 图表类型 (bar, pie)
            
        Returns:
            HTML + Chart.js 代码
        """
        sources = await self._get_sources(source_ids)
        
        # 统计主题频率
        all_topics = []
        for source in sources:
            topics = getattr(source, 'topics', []) or []
            all_topics.extend(topics)
        
        topic_counts = Counter(all_topics)
        top_topics = topic_counts.most_common(top_n)
        
        # 生成 HTML 图表
        if chart_type == "bar":
            html_chart = self._generate_bar_chart_html(top_topics)
        elif chart_type == "pie":
            html_chart = self._generate_pie_chart_html(top_topics)
        else:
            html_chart = self._generate_bar_chart_html(top_topics)
        
        return html_chart
    
    def _generate_mermaid_mindmap(
        self,
        concepts: List[Tuple[str, int]],
        relations: List[Tuple[str, str, int]]
    ) -> str:
        """生成 Mermaid 思维导图"""
        
        if not concepts:
            return "```mermaid\nmindmap\n  root((No Data))\n```"
        
        # 构建层级结构（简化版：基于频率分组）
        high_freq = [c for c, count in concepts if count >= 5][:5]
        medium_freq = [c for c, count in concepts if 2 <= count < 5][:8]
        low_freq = [c for c, count in concepts if count < 2][:7]
        
        mindmap = "```mermaid\nmindmap\n  root((核心主题))\n"
        
        # 高频概念作为主分支
        if high_freq:
            mindmap += "    高频概念\n"
            for concept in high_freq:
                mindmap += f"      {concept}\n"
        
        # 中频概念作为次级分支
        if medium_freq:
            mindmap += "    中频概念\n"
            for concept in medium_freq:
                mindmap += f"      {concept}\n"
        
        # 低频概念作为第三级分支
        if low_freq:
            mindmap += "    其他概念\n"
            for concept in low_freq:
                mindmap += f"      {concept}\n"
        
        mindmap += "```"
        
        return mindmap
    
    def _generate_mermaid_timeline(self, data: List[Dict[str, Any]]) -> str:
        """生成 Mermaid 时间线"""
        
        if not data:
            return "```mermaid\ntimeline\n  No Data\n```"
        
        timeline = "```mermaid\ntimeline\n  研究演进\n    section 早期\n"
        
        # 分组展示
        early = data[:len(data)//3]
        middle = data[len(data)//3:2*len(data)//3]
        recent = data[2*len(data)//3:]
        
        for item in early:
            timeline += f"      {item['date']} : {item['title'][:30]}\n"
            if item['topics']:
                timeline += f"        : {', '.join(item['topics'])}\n"
        
        timeline += "    section 中期\n"
        for item in middle:
            timeline += f"      {item['date']} : {item['title'][:30]}\n"
            if item['topics']:
                timeline += f"        : {', '.join(item['topics'])}\n"
        
        timeline += "    section 近期\n"
        for item in recent:
            timeline += f"      {item['date']} : {item['title'][:30]}\n"
            if item['topics']:
                timeline += f"        : {', '.join(item['topics'])}\n"
        
        timeline += "```"
        
        return timeline
    
    def _generate_mermaid_network(self, links: List[Tuple[str, str, int]]) -> str:
        """生成 Mermaid 网络图"""
        
        if not links:
            return "```mermaid\ngraph TD\n  No connections found\n```"
        
        graph = "```mermaid\ngraph TD\n"
        
        # 添加节点和边
        nodes = set()
        for c1, c2, strength in links:
            if c1 not in nodes:
                graph += f"  {c1.replace(' ', '_')}[{c1}]\n"
                nodes.add(c1)
            if c2 not in nodes:
                graph += f"  {c2.replace(' ', '_')}[{c2}]\n"
                nodes.add(c2)
            
            # 根据强度设置边的样式
            line_style = "---"
            if strength >= 5:
                line_style = "===="  # 粗线
            elif strength >= 3:
                line_style = "--"  # 中等
            
            graph += f"  {c1.replace(' ', '_')} {line_style}|{strength}| {c2.replace(' ', '_')}\n"
        
        graph += "```"
        
        return graph
    
    def _generate_bar_chart_html(self, top_topics: List[Tuple[str, int]]) -> str:
        """生成柱状图 HTML（Chart.js）"""
        
        labels = [topic for topic, _ in top_topics]
        data = [count for topic, _ in top_topics]
        
        html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>主题分布 - 柱状图</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    body {{ font-family: Arial; padding: 20px; }}
    .chart-container {{ width: 800px; margin: 0 auto; }}
  </style>
</head>
<body>
  <h2 style="text-align: center;">📊 主题分布（TOP {len(top_topics)}）</h2>
  <div class="chart-container">
    <canvas id="myChart"></canvas>
  </div>
  <script>
    const ctx = document.getElementById('myChart');
    new Chart(ctx, {{
      type: 'bar',
      data: {{
        labels: {labels},
        datasets: [{{
          label: '提及次数',
          data: {data},
          backgroundColor: 'rgba(102, 126, 234, 0.6)',
          borderColor: 'rgba(102, 126, 234, 1)',
          borderWidth: 1
        }}]
      }},
      options: {{
        responsive: true,
        scales: {{
          y: {{
            beginAtZero: true,
            ticks: {{ stepSize: 1 }}
          }}
        }}
      }}
    }});
  </script>
</body>
</html>
"""
        
        return html
    
    def _generate_pie_chart_html(self, top_topics: List[Tuple[str, int]]) -> str:
        """生成饼图 HTML（Chart.js）"""
        
        labels = [topic for topic, _ in top_topics]
        data = [count for topic, _ in top_topics]
        
        html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>主题分布 - 饼图</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    body {{ font-family: Arial; padding: 20px; }}
    .chart-container {{ width: 600px; margin: 0 auto; }}
  </style>
</head>
<body>
  <h2 style="text-align: center;">🥧 主题分布（TOP {len(top_topics)}）</h2>
  <div class="chart-container">
    <canvas id="myChart"></canvas>
  </div>
  <script>
    const ctx = document.getElementById('myChart');
    new Chart(ctx, {{
      type: 'pie',
      data: {{
        labels: {labels},
        datasets: [{{
          data: {data},
          backgroundColor: [
            '#667eea', '#764ba2', '#f093fb', '#f5576c',
            '#4facfe', '#43e97b', '#fa709a', '#fee140',
            '#30cfd0', '#a8edea'
          ]
        }}]
      }},
      options: {{
        responsive: true,
        plugins: {{
          legend: {{
            position: 'bottom'
          }}
        }}
      }}
    }});
  </script>
</body>
</html>
"""
        
        return html
    
    async def _extract_concepts_and_relations(
        self,
        sources: List[Source]
    ) -> Tuple[Dict[str, int], List[Tuple[str, str, int]]]:
        """提取概念和关系"""
        
        concepts = Counter()
        concept_cooccurrence = defaultdict(lambda: defaultdict(int))
        
        for source in sources:
            topics = getattr(source, 'topics', []) or []
            for topic in topics:
                concepts[topic] += 1
            
            # 记录共现关系
            for i, c1 in enumerate(topics):
                for c2 in topics[i+1:]:
                    concept_cooccurrence[c1][c2] += 1
                    concept_cooccurrence[c2][c1] += 1
        
        # 转换为关系列表
        relations = []
        processed = set()
        for c1, related in concept_cooccurrence.items():
            for c2, count in related.items():
                if (c1, c2) not in processed:
                    relations.append((c1, c2, count))
                    processed.add((c1, c2))
                    processed.add((c2, c1))
        
        # 按强度排序
        relations.sort(key=lambda x: x[2], reverse=True)
        
        return dict(concepts), relations
    
    async def export_all_visualizations(
        self,
        output_dir: str = "exports/visualizations",
        source_ids: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """导出所有可视化图表
        
        Args:
            output_dir: 输出目录
            source_ids: 指定源列表
            
        Returns:
            导出的文件路径字典
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        results = {}
        
        # 1. 思维导图
        mindmap = await self.generate_mind_map(source_ids)
        mindmap_path = output_path / f"mindmap_{timestamp}.md"
        with open(mindmap_path, 'w', encoding='utf-8') as f:
            f.write(mindmap)
        results['mindmap'] = str(mindmap_path)
        
        # 2. 时间线
        timeline = await self.generate_timeline(source_ids)
        timeline_path = output_path / f"timeline_{timestamp}.md"
        with open(timeline_path, 'w', encoding='utf-8') as f:
            f.write(timeline)
        results['timeline'] = str(timeline_path)
        
        # 3. 网络图
        network = await self.generate_network_graph(source_ids)
        network_path = output_path / f"network_{timestamp}.md"
        with open(network_path, 'w', encoding='utf-8') as f:
            f.write(network)
        results['network'] = str(network_path)
        
        # 4. 柱状图
        bar_chart = await self.generate_topic_distribution(source_ids, chart_type="bar")
        bar_chart_path = output_path / f"bar_chart_{timestamp}.html"
        with open(bar_chart_path, 'w', encoding='utf-8') as f:
            f.write(bar_chart)
        results['bar_chart'] = str(bar_chart_path)
        
        # 5. 饼图
        pie_chart = await self.generate_topic_distribution(source_ids, chart_type="pie")
        pie_chart_path = output_path / f"pie_chart_{timestamp}.html"
        with open(pie_chart_path, 'w', encoding='utf-8') as f:
            f.write(pie_chart)
        results['pie_chart'] = str(pie_chart_path)
        
        logger.info(f"All visualizations exported to {output_path}")
        
        return results
    
    async def _get_sources(self, source_ids: Optional[List[str]] = None) -> List[Source]:
        """获取源列表"""
        if source_ids:
            sources = []
            for sid in source_ids:
                source = await Source.get(sid)
                if source:
                    sources.append(source)
            return sources
        else:
            return await self.notebook.get_sources()
    
    async def close(self):
        """关闭"""
        logger.info("Closing VisualKnowledgeGraphGenerator")


# ============================================================================
# Convenience Functions
# ============================================================================

async def create_mind_map(notebook_id: str, source_ids: Optional[List[str]] = None) -> str:
    """便捷函数：创建思维导图"""
    generator = VisualKnowledgeGraphGenerator(notebook_id)
    await generator.initialize()
    try:
        return await generator.generate_mind_map(source_ids)
    finally:
        await generator.close()


async def create_timeline(notebook_id: str, source_ids: Optional[List[str]] = None) -> str:
    """便捷函数：创建时间线"""
    generator = VisualKnowledgeGraphGenerator(notebook_id)
    await generator.initialize()
    try:
        return await generator.generate_timeline(source_ids)
    finally:
        await generator.close()


async def create_network_graph(notebook_id: str, source_ids: Optional[List[str]] = None) -> str:
    """便捷函数：创建网络图"""
    generator = VisualKnowledgeGraphGenerator(notebook_id)
    await generator.initialize()
    try:
        return await generator.generate_network_graph(source_ids)
    finally:
        await generator.close()


async def create_topic_chart(
    notebook_id: str,
    source_ids: Optional[List[str]] = None,
    chart_type: str = "bar"
) -> str:
    """便捷函数：创建主题分布图"""
    generator = VisualKnowledgeGraphGenerator(notebook_id)
    await generator.initialize()
    try:
        return await generator.generate_topic_distribution(source_ids, chart_type=chart_type)
    finally:
        await generator.close()
