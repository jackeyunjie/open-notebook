"""
One-Click Report Generator - 一键报告生成器

对标 Google NotebookLM 的 "Create Study Guide" 功能

功能:
1. 一键生成结构化报告（Study Guide, Literature Review, Research Digest）
2. 基于 Workflow Template 快速套用模板
3. 支持多种报告类型
4. 自动生成目录和摘要
5. 导出 Markdown/PDF/HTML 格式
"""

import asyncio
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from open_notebook.domain.notebook import Notebook, Note, Source


class ReportType(str, Enum):
    """报告类型"""
    STUDY_GUIDE = "study_guide"  # 学习指南
    LITERATURE_REVIEW = "literature_review"  # 文献综述
    RESEARCH_DIGEST = "research_digest"  # 研究简报
    WEEKLY_TRENDS = "weekly_trends"  # 周度趋势
    CONCEPT_MAP = "concept_map"  # 概念图谱


class OneClickReportGenerator:
    """一键报告生成器"""
    
    def __init__(self, notebook_id: str):
        self.notebook_id = notebook_id
        self.notebook: Optional[Notebook] = None
        
    async def initialize(self):
        """初始化"""
        logger.info(f"Initializing OneClickReportGenerator for notebook {self.notebook_id}")
        self.notebook = await Notebook.get(self.notebook_id)
        if not self.notebook:
            raise ValueError(f"Notebook {self.notebook_id} not found")
        
    async def generate_report(
        self,
        report_type: ReportType,
        title: Optional[str] = None,
        source_ids: Optional[List[str]] = None,
        output_format: str = "markdown"
    ) -> Dict[str, Any]:
        """生成报告
        
        Args:
            report_type: 报告类型
            title: 报告标题（可选，自动生成如果未提供）
            source_ids: 指定源列表（可选，默认使用所有源）
            output_format: 输出格式 (markdown, html, pdf)
            
        Returns:
            生成的报告数据
        """
        logger.info(f"Generating {report_type.value} report...")
        
        # Step 1: 获取源数据
        if source_ids:
            sources = []
            for sid in source_ids:
                source = await Source.get(sid)
                if source:
                    sources.append(source)
        else:
            sources = await self.notebook.get_sources()
        
        if not sources:
            raise ValueError("No sources available in notebook")
        
        # Step 2: 根据报告类型生成内容
        if report_type == ReportType.STUDY_GUIDE:
            content = await self._generate_study_guide(sources)
        elif report_type == ReportType.LITERATURE_REVIEW:
            content = await self._generate_literature_review(sources)
        elif report_type == ReportType.RESEARCH_DIGEST:
            content = await self._generate_research_digest(sources)
        elif report_type == ReportType.WEEKLY_TRENDS:
            content = await self._generate_weekly_trends(sources)
        elif report_type == ReportType.CONCEPT_MAP:
            content = await self._generate_concept_map(sources)
        else:
            raise ValueError(f"Unknown report type: {report_type}")
        
        # Step 3: 生成标题
        if not title:
            title = await self._auto_generate_title(content, report_type)
        
        # Step 4: 保存为 Note
        note = Note(
            title=title,
            content=content,
            note_type="ai"
        )
        await note.save()
        await note.add_to_notebook(self.notebook_id)
        
        # Step 5: 导出（如果需要）
        output_path = None
        if output_format != "markdown":
            output_path = await self._export_report(note, output_format)
        
        logger.info(f"Report generated successfully: {title}")
        
        return {
            "note_id": note.id,
            "title": title,
            "content": content,
            "report_type": report_type.value,
            "output_format": output_format,
            "output_path": output_path,
            "sources_count": len(sources),
            "created_at": datetime.now().isoformat()
        }
    
    async def _generate_study_guide(self, sources: List[Source]) -> str:
        """生成学习指南"""
        logger.info(f"Generating study guide from {len(sources)} sources")
        
        # 提取关键概念
        concepts = []
        for source in sources:
            if hasattr(source, 'topics') and source.topics:
                concepts.extend(source.topics[:5])
        
        # 去重
        unique_concepts = list(set(concepts))[:20]
        
        content = f"""# 📚 学习指南

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**资料来源**: {len(sources)} 个文档  
**核心概念**: {len(unique_concepts)} 个

---

## 📖 概述

本学习指南基于 {len(sources)} 个核心资料整理而成，涵盖以下关键领域：

{chr(10).join(['- ' + concept for concept in unique_concepts[:10]])}

---

## 🎯 核心概念详解

"""
        
        # 为每个概念生成详细说明
        for i, concept in enumerate(unique_concepts[:10], 1):
            content += f"""### {i}. {concept}

**定义**: [待补充]

**相关资料**: 
{chr(10).join([f"- {source.title}" for source in sources if hasattr(source, 'title') and source.title][:3])}

**关键要点**:
- 要点 1
- 要点 2
- 要点 3

**思考题**:
1. 如何理解{concept}在实际应用中的作用？
2. {concept}与其他概念有什么联系？

---

"""
        
        content += f"""
## 📝 复习建议

1. **第一遍**: 快速浏览所有核心概念，建立整体框架
2. **第二遍**: 深入理解每个概念的定义和应用
3. **第三遍**: 完成思考题，检验理解程度
4. **实践**: 将所学知识应用到实际项目中

## 🔗 延伸阅读

- 相关资料链接
- 推荐的学习资源
- 进一步阅读的建议

---

*本指南由 Open Notebook 一键生成*
"""
        
        return content
    
    async def _generate_literature_review(self, sources: List[Source]) -> str:
        """生成文献综述"""
        logger.info(f"Generating literature review from {len(sources)} sources")
        
        content = f"""# 📖 文献综述

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**纳入文献**: {len(sources)} 篇  
**分析维度**: 主题、方法、发现、趋势

---

## 📊 文献概览

本次综述共纳入 {len(sources)} 篇文献，以下是详细列表：

"""
        
        for i, source in enumerate(sources, 1):
            if hasattr(source, 'title') and source.title:
                content += f"{i}. **{source.title}**\n"
                if hasattr(source, 'topics') and source.topics:
                    content += f"   - 关键词：{', '.join(source.topics[:5])}\n"
                content += "\n"
        
        content += f"""
---

## 🔍 主题聚类

基于文献内容，识别出以下主要研究主题：

### 主题 1: [待分析]
- 相关文献：[自动归类]
- 核心发现：[待提取]
- 研究方法：[待总结]

### 主题 2: [待分析]
- 相关文献：[自动归类]
- 核心发现：[待提取]
- 研究方法：[待总结]

---

## 💡 研究趋势

### 时间演变
- 早期研究重点：[待分析]
- 近期研究热点：[待分析]
- 未来研究方向：[待预测]

### 方法论演进
- 主流研究方法：[待总结]
- 新兴技术趋势：[待识别]

---

## ⚠️ 研究空白

通过对比分析，发现以下研究空白：

1. [空白 1]
2. [空白 2]
3. [空白 3]

---

## 📌 结论与建议

### 主要发现
1. [核心发现 1]
2. [核心发现 2]
3. [核心发现 3]

### 对未来研究的建议
- 建议 1
- 建议 2
- 建议 3

---

*本综述由 Open Notebook 一键生成*
"""
        
        return content
    
    async def _generate_research_digest(self, sources: List[Source]) -> str:
        """生成研究简报"""
        logger.info(f"Generating research digest from {len(sources)} sources")
        
        content = f"""# 📰 研究简报

**期号**: {datetime.now().strftime('%Y年第%W周')}  
**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**覆盖文献**: {len(sources)} 篇

---

## 🎯 本周焦点

**主题**: [待确定]

**一句话总结**: [用一句话概括本周最重要的发现]

---

## 📋 重要发现速览

"""
        
        # 列出最重要的 3-5 个发现
        for i, source in enumerate(sources[:5], 1):
            if hasattr(source, 'title') and source.title:
                content += f"""### {i}. {source.title}

**重要性**: ⭐⭐⭐⭐⭐

**核心发现**: 
- [待提取关键点 1]
- [待提取关键点 2]
- [待提取关键点 3]

**实际应用**: [如何将此发现应用到实际工作中]

**原文链接**: [如有]

---

"""
        
        content += f"""
## 🔍 深度解读

### 背景说明
[为什么这些发现很重要]

### 影响分析
- 短期影响：[待分析]
- 长期影响：[待预测]

### 行动建议
基于本周研究，建议采取以下行动：
1. [行动 1]
2. [行动 2]
3. [行动 3]

---

## 📅 下周展望

**值得关注的方向**:
- [方向 1]
- [方向 2]
- [方向 3]

**预期发布**: [下周可能发布的重要研究]

---

*本简报由 Open Notebook 一键生成*
"""
        
        return content
    
    async def _generate_weekly_trends(self, sources: List[Source]) -> str:
        """生成周度趋势报告"""
        logger.info(f"Generating weekly trends from {len(sources)} sources")
        
        # 提取所有主题
        all_topics = []
        for source in sources:
            if hasattr(source, 'topics'):
                all_topics.extend(source.topics or [])
        
        # 统计主题频率
        from collections import Counter
        topic_counts = Counter(all_topics)
        top_topics = topic_counts.most_common(10)
        
        content = f"""# 📈 周度研究趋势

**周期**: {datetime.now().strftime('%Y-%m-%d')}  
**分析文献**: {len(sources)} 篇  
**识别主题**: {len(all_topics)} 个

---

## 🔥 热门主题 TOP 10

"""
        
        for i, (topic, count) in enumerate(top_topics, 1):
            percentage = (count / len(sources) * 100) if sources else 0
            stars = "⭐" * min(5, int(percentage / 20) + 1)
            content += f"{i}. **{topic}** {stars} ({count}次提及，{percentage:.1f}%)\n\n"
        
        content += f"""
---

## 📊 趋势分析

### 上升最快的主题
1. [主题名称] - 本周新增 {X} 篇文献
2. [主题名称] - 环比增长 {X}%
3. [主题名称] - 首次成为热点

### 持续热门的主题
1. [主题名称] - 连续 {X} 周上榜
2. [主题名称] - 稳定性高

### 新兴主题（潜力股）
1. [主题名称] - 首次出现，增长迅速
2. [主题名称] - 跨领域应用增多

---

## 🔍 主题关联分析

### 主题聚类
基于共现分析，识别出以下主题簇：

**簇 1: [簇名称]**
- 包含主题：[主题 1, 主题 2, 主题 3]
- 核心联系：[描述关联性]

**簇 2: [簇名称]**
- 包含主题：[主题 1, 主题 2, 主题 3]
- 核心联系：[描述关联性]

---

## 💡 洞察与建议

### 关键洞察
1. [洞察 1：描述某个重要趋势]
2. [洞察 2：发现某个模式]
3. [洞察 3：预测某个方向]

### 行动建议
基于趋势分析，建议：
- ✅ 重点关注：[应该投入精力的方向]
- ⚠️ 保持观察：[需要继续跟踪的方向]
- ❌ 谨慎投入：[可能过时的方向]

---

## 📅 下周预测

**可能成为热点的主题**:
1. [预测 1]
2. [预测 2]
3. [预测 3]

**理由**: [预测依据]

---

*本报告由 Open Notebook 一键生成*
"""
        
        return content
    
    async def _generate_concept_map(self, sources: List[Source]) -> str:
        """生成概念图谱（Markdown 版本）"""
        logger.info(f"Generating concept map from {len(sources)} sources")
        
        # 提取概念和关系
        concepts = {}
        relations = []
        
        for source in sources:
            if hasattr(source, 'topics'):
                for topic in (source.topics or []):
                    if topic not in concepts:
                        concepts[topic] = {
                            'count': 0,
                            'sources': [],
                            'related_concepts': set()
                        }
                    concepts[topic]['count'] += 1
                    if hasattr(source, 'title'):
                        concepts[topic]['sources'].append(source.title)
        
        # 简化版：只列出概念和来源
        sorted_concepts = sorted(concepts.items(), key=lambda x: x[1]['count'], reverse=True)
        
        content = f"""# 🗺️ 概念图谱

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**覆盖文献**: {len(sources)} 篇  
**识别概念**: {len(concepts)} 个

---

## 📊 概念层级结构

```
核心概念
├── {sorted_concepts[0][0] if sorted_concepts else 'N/A'} ({sorted_concepts[0][1]['count']}次提及)
│   ├── 子概念 1
│   ├── 子概念 2
│   └── 子概念 3
├── {sorted_concepts[1][0] if len(sorted_concepts) > 1 else 'N/A'} ({sorted_concepts[1][1]['count']}次提及)
│   ├── 子概念 1
│   └── 子概念 2
└── {sorted_concepts[2][0] if len(sorted_concepts) > 2 else 'N/A'} ({sorted_concepts[2][1]['count']}次提及)
```

---

## 🔑 核心概念详解

"""
        
        for i, (concept, data) in enumerate(sorted_concepts[:10], 1):
            sources_list = list(set(data['sources']))[:5]
            content += f"""### {i}. {concept}

**提及次数**: {data['count']} 次

**相关文献**:
{chr(10).join(['- ' + s for s in sources_list])}

**定义**: [待补充]

**应用场景**: [待补充]

**相关概念**: 
- [相关概念 1]
- [相关概念 2]
- [相关概念 3]

---

"""
        
        content += f"""
## 🔗 概念关系网络

基于共现分析，识别出以下概念关联：

### 强关联（经常同时出现）
- {sorted_concepts[0][0] if sorted_concepts else 'A'} ↔ {sorted_concepts[1][0] if len(sorted_concepts) > 1 else 'B'}
- {sorted_concepts[1][0] if len(sorted_concepts) > 1 else 'B'} ↔ {sorted_concepts[2][0] if len(sorted_concepts) > 2 else 'C'}
- {sorted_concepts[0][0] if sorted_concepts else 'A'} ↔ {sorted_concepts[2][0] if len(sorted_concepts) > 2 else 'C'}

### 中等关联
- [概念对 1]
- [概念对 2]
- [概念对 3]

---

## 💡 知识框架建议

基于概念分布，建议采用以下框架组织知识：

```
{sorted_concepts[0][0] if sorted_concepts else '核心主题'}
│
├─ 理论基础
│  ├─ {sorted_concepts[1][0] if len(sorted_concepts) > 1 else '基础概念 1'}
│  └─ {sorted_concepts[2][0] if len(sorted_concepts) > 2 else '基础概念 2'}
│
├─ 核心技术
│  ├─ [技术 1]
│  └─ [技术 2]
│
└─ 应用领域
   ├─ [领域 1]
   └─ [领域 2]
```

---

*本图谱由 Open Notebook 一键生成*
"""
        
        return content
    
    async def _auto_generate_title(self, content: str, report_type: ReportType) -> str:
        """自动生成标题"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        titles = {
            ReportType.STUDY_GUIDE: f"📚 学习指南 - {self.notebook.name} ({date_str})",
            ReportType.LITERATURE_REVIEW: f"📖 文献综述 - {self.notebook.name}",
            ReportType.RESEARCH_DIGEST: f"📰 研究简报 - {datetime.now().strftime('%Y年第%W周')}",
            ReportType.WEEKLY_TRENDS: f"📈 周度趋势 - {date_str}",
            ReportType.CONCEPT_MAP: f"🗺️ 概念图谱 - {self.notebook.name}"
        }
        
        return titles.get(report_type, f"研究报告 - {date_str}")
    
    async def _export_report(self, note: Note, format: str) -> str:
        """导出报告"""
        output_dir = Path("exports/reports")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "html":
            # TODO: 转换为 HTML
            output_path = output_dir / f"{note.id}_{timestamp}.html"
        elif format == "pdf":
            # TODO: 转换为 PDF
            output_path = output_dir / f"{note.id}_{timestamp}.pdf"
        else:
            output_path = output_dir / f"{note.id}_{timestamp}.md"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"# {note.title}\n\n{note.content}")
        
        logger.info(f"Report exported to {output_path}")
        return str(output_path)
    
    async def close(self):
        """关闭"""
        logger.info("Closing OneClickReportGenerator")


# ============================================================================
# Convenience Functions
# ============================================================================

async def create_study_guide(notebook_id: str, source_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """便捷函数：创建学习指南"""
    generator = OneClickReportGenerator(notebook_id)
    await generator.initialize()
    try:
        return await generator.generate_report(
            ReportType.STUDY_GUIDE,
            source_ids=source_ids
        )
    finally:
        await generator.close()


async def create_literature_review(notebook_id: str, source_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """便捷函数：创建文献综述"""
    generator = OneClickReportGenerator(notebook_id)
    await generator.initialize()
    try:
        return await generator.generate_report(
            ReportType.LITERATURE_REVIEW,
            source_ids=source_ids
        )
    finally:
        await generator.close()


async def create_research_digest(notebook_id: str, source_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """便捷函数：创建研究简报"""
    generator = OneClickReportGenerator(notebook_id)
    await generator.initialize()
    try:
        return await generator.generate_report(
            ReportType.RESEARCH_DIGEST,
            source_ids=source_ids
        )
    finally:
        await generator.close()


async def create_weekly_trends(notebook_id: str, source_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """便捷函数：创建周度趋势报告"""
    generator = OneClickReportGenerator(notebook_id)
    await generator.initialize()
    try:
        return await generator.generate_report(
            ReportType.WEEKLY_TRENDS,
            source_ids=source_ids
        )
    finally:
        await generator.close()


async def create_concept_map(notebook_id: str, source_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """便捷函数：创建概念图谱"""
    generator = OneClickReportGenerator(notebook_id)
    await generator.initialize()
    try:
        return await generator.generate_report(
            ReportType.CONCEPT_MAP,
            source_ids=source_ids
        )
    finally:
        await generator.close()
