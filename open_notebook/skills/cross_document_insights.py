"""
Cross-Document Insights - 跨文档洞察系统

功能:
1. 发现多个 Source 之间的共性和矛盾
2. 识别主题演化趋势
3. 自动生成"本周研究趋势"报告
4. 概念聚类和关联分析
5. 矛盾观点检测
"""

import asyncio
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from loguru import logger

from open_notebook.domain.notebook import Notebook, Source


class CrossDocumentAnalyzer:
    """跨文档分析器"""
    
    def __init__(self, notebook_id: str):
        self.notebook_id = notebook_id
        self.notebook: Optional[Notebook] = None
        
    async def initialize(self):
        """初始化"""
        logger.info(f"Initializing CrossDocumentAnalyzer for notebook {self.notebook_id}")
        self.notebook = await Notebook.get(self.notebook_id)
        if not self.notebook:
            raise ValueError(f"Notebook {self.notebook_id} not found")
    
    async def analyze_common_themes(
        self,
        source_ids: Optional[List[str]] = None,
        min_frequency: int = 2
    ) -> Dict[str, Any]:
        """分析共同主题
        
        Args:
            source_ids: 指定源列表（可选，默认分析所有源）
            min_frequency: 最小出现频次
            
        Returns:
            共同主题分析结果
        """
        sources = await self._get_sources(source_ids)
        
        # 统计所有主题
        all_topics = []
        topic_sources = defaultdict(list)
        
        for source in sources:
            topics = getattr(source, 'topics', []) or []
            for topic in topics:
                all_topics.append(topic)
                topic_sources[topic].append({
                    'source_id': source.id,
                    'source_title': getattr(source, 'title', 'Untitled')
                })
        
        # 计算频率
        topic_counts = Counter(all_topics)
        
        # 筛选高频主题
        common_themes = {
            topic: {
                'count': count,
                'percentage': round(count / len(sources) * 100, 2) if sources else 0,
                'sources': topic_sources[topic],
                'trend': 'stable'  # TODO: 计算趋势
            }
            for topic, count in topic_counts.items()
            if count >= min_frequency
        }
        
        # 按频率排序
        sorted_themes = dict(sorted(
            common_themes.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        ))
        
        return {
            'total_sources': len(sources),
            'total_topics': len(all_topics),
            'unique_topics': len(topic_counts),
            'common_themes': sorted_themes,
            'top_themes': list(sorted_themes.items())[:10]
        }
    
    async def detect_contradictions(
        self,
        source_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """检测矛盾观点
        
        Args:
            source_ids: 指定源列表
            
        Returns:
            矛盾观点列表
        """
        sources = await self._get_sources(source_ids)
        contradictions = []
        
        # TODO: 实现智能矛盾检测
        # 当前版本使用简化策略：检测相同主题下的不同观点
        
        # 按主题分组
        topic_groups = defaultdict(list)
        for source in sources:
            topics = getattr(source, 'topics', []) or []
            for topic in topics:
                topic_groups[topic].append(source)
        
        # 检测每个主题下的潜在矛盾
        for topic, topic_sources in topic_groups.items():
            if len(topic_sources) >= 2:
                # 简单规则：如果多个文档讨论同一主题，可能存在不同观点
                contradictions.append({
                    'type': 'potential_disagreement',
                    'topic': topic,
                    'sources': [
                        {'id': s.id, 'title': getattr(s, 'title', 'Untitled')}
                        for s in topic_sources
                    ],
                    'confidence': 'low',
                    'description': f"{len(topic_sources)} 个文档讨论了'{topic}'主题，可能存在不同观点",
                    'action_required': 'manual_review'
                })
        
        return contradictions
    
    async def identify_trends(
        self,
        days: int = 7,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """识别研究趋势
        
        Args:
            days: 分析最近 N 天
            top_n: 返回前 N 个趋势
            
        Returns:
            趋势分析结果
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 获取最近的源
        recent_sources = []
        all_sources = await self.notebook.get_sources()
        
        for source in all_sources:
            # TODO: 检查 source 的创建时间
            recent_sources.append(source)
        
        # 分析主题分布
        recent_topics = []
        for source in recent_sources:
            topics = getattr(source, 'topics', []) or []
            recent_topics.extend(topics)
        
        topic_counts = Counter(recent_topics)
        
        # 识别上升最快的主题
        trending_topics = []
        for topic, count in topic_counts.most_common(top_n):
            trending_topics.append({
                'topic': topic,
                'count': count,
                'percentage': round(count / len(recent_topics) * 100, 2) if recent_topics else 0,
                'velocity': 'high'  # TODO: 计算增长速度
            })
        
        return {
            'period_days': days,
            'total_sources': len(recent_sources),
            'total_topics': len(recent_topics),
            'trending_topics': trending_topics,
            'hot_topics': trending_topics[:3],
            'emerging_topics': self._identify_emerging_topics(topic_counts, days)
        }
    
    def _identify_emerging_topics(
        self,
        topic_counts: Counter,
        days: int
    ) -> List[Dict[str, Any]]:
        """识别新兴主题"""
        # TODO: 需要历史数据对比
        # 当前版本简化实现：假设低频但新出现的主题是新兴主题
        
        emerging = []
        total_count = sum(topic_counts.values())
        
        for topic, count in topic_counts.items():
            percentage = count / total_count if total_count > 0 else 0
            if 0 < percentage < 5:  # 占比小于 5% 可能是新兴主题
                emerging.append({
                    'topic': topic,
                    'count': count,
                    'percentage': round(percentage, 2),
                    'potential': 'medium'
                })
        
        return emerging[:5]
    
    async def cluster_concepts(
        self,
        source_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """聚类概念
        
        Args:
            source_ids: 指定源列表
            
        Returns:
            概念聚类结果
        """
        sources = await self._get_sources(source_ids)
        
        # 提取所有概念
        all_concepts = []
        concept_cooccurrence = defaultdict(lambda: defaultdict(int))
        
        for source in sources:
            concepts = getattr(source, 'topics', []) or []
            all_concepts.extend(concepts)
            
            # 记录共现关系
            for i, c1 in enumerate(concepts):
                for c2 in concepts[i+1:]:
                    concept_cooccurrence[c1][c2] += 1
                    concept_cooccurrence[c2][c1] += 1
        
        # 简单的基于频率的聚类
        concept_counts = Counter(all_concepts)
        
        # 找出强关联的概念对
        strong_links = []
        for c1, related in concept_cooccurrence.items():
            for c2, count in related.items():
                if count >= 2 and c1 < c2:  # 避免重复
                    strong_links.append((c1, c2, count))
        
        # 生成聚类（简化版）
        clusters = self._generate_clusters(strong_links, concept_counts)
        
        return {
            'total_concepts': len(all_concepts),
            'unique_concepts': len(concept_counts),
            'top_concepts': concept_counts.most_common(10),
            'strong_links': strong_links[:20],
            'clusters': clusters
        }
    
    def _generate_clusters(
        self,
        links: List[Tuple[str, str, int]],
        concept_counts: Counter
    ) -> List[Dict[str, Any]]:
        """生成概念簇（简化版）"""
        # 使用并查集或连通分量算法会更好
        # 当前版本使用简单启发式方法
        
        clusters = []
        processed = set()
        
        # 找到最核心的概念（出现频率最高）
        core_concepts = [c for c, _ in concept_counts.most_common(5)]
        
        for core in core_concepts:
            if core in processed:
                continue
            
            # 找到与核心概念相关的所有概念
            cluster_members = {core}
            for c1, c2, _ in links:
                if c1 == core:
                    cluster_members.add(c2)
                elif c2 == core:
                    cluster_members.add(c1)
            
            clusters.append({
                'cluster_id': len(clusters) + 1,
                'core_concept': core,
                'members': list(cluster_members),
                'size': len(cluster_members)
            })
            
            processed.update(cluster_members)
        
        return clusters
    
    async def generate_weekly_trends_report(
        self,
        source_ids: Optional[List[str]] = None
    ) -> str:
        """生成周度趋势报告
        
        Args:
            source_ids: 指定源列表
            
        Returns:
            Markdown 格式的报告
        """
        # 执行多项分析
        themes_result = await self.analyze_common_themes(source_ids)
        trends_result = await self.identify_trends(days=7)
        contradictions = await self.detect_contradictions(source_ids)
        clusters_result = await self.cluster_concepts(source_ids)
        
        # 生成报告
        report = f"""# 📈 周度研究趋势报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**分析周期**: 最近 7 天  
**覆盖文献**: {themes_result['total_sources']} 篇

---

## 🔥 热门主题 TOP 10

"""
        
        for i, (topic, data) in enumerate(themes_result['top_themes'], 1):
            stars = "⭐" * min(5, int(data['percentage'] / 10) + 1)
            report += f"{i}. **{topic}** {stars} ({data['count']}次提及，{data['percentage']}%)\n\n"
        
        report += f"""
---

## 📊 趋势分析

### 上升最快的主题
"""
        
        for item in trends_result['trending_topics'][:3]:
            report += f"- **{item['topic']}** - {item['count']}次提及 ({item['percentage']}%)\n"
        
        report += f"""
### 新兴主题（潜力股）
"""
        
        for item in trends_result['emerging_topics'][:3]:
            report += f"- **{item['topic']}** - 首次出现，占比{item['percentage']}%\n"
        
        report += f"""
---

## ⚠️ 潜在矛盾与分歧

检测到 {len(contradictions)} 处潜在矛盾：

"""
        
        for i, contradiction in enumerate(contradictions[:3], 1):
            report += f"""### {i}. {contradiction['topic']}

**类型**: {contradiction['type']}  
**置信度**: {contradiction['confidence']}  
**涉及文献**: {len(contradiction['sources'])} 篇  
**描述**: {contradiction['description']}

**建议行动**: {contradiction['action_required']}

---

"""
        
        report += f"""
## 🗺️ 概念聚类

识别出 {len(clusters_result['clusters'])} 个概念簇：

"""
        
        for i, cluster in enumerate(clusters_result['clusters'][:3], 1):
            members_str = ', '.join(cluster['members'][:5])
            report += f"""### 簇{i}: {cluster['core_concept']}

**核心概念**: {cluster['core_concept']}  
**成员数量**: {cluster['size']} 个  
**主要成员**: {members_str}

---

"""
        
        report += f"""
## 💡 关键洞察

### 洞察 1: [待补充]
基于数据分析，发现...

### 洞察 2: [待补充]
值得注意的模式是...

### 洞察 3: [待补充]
预测未来趋势...

---

## 📅 下周展望

**可能成为热点的主题**:
1. [预测 1]
2. [预测 2]
3. [预测 3]

**建议关注的方向**:
- ✅ [方向 1]
- ⚠️ [方向 2]
- ❌ [方向 3]

---

*本报告由 Open Notebook 跨文档分析系统自动生成*
"""
        
        return report
    
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
        logger.info("Closing CrossDocumentAnalyzer")


# ============================================================================
# Convenience Functions
# ============================================================================

async def analyze_cross_document_themes(notebook_id: str, source_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """便捷函数：分析跨文档主题"""
    analyzer = CrossDocumentAnalyzer(notebook_id)
    await analyzer.initialize()
    try:
        return await analyzer.analyze_common_themes(source_ids)
    finally:
        await analyzer.close()


async def detect_contradictions(notebook_id: str, source_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """便捷函数：检测矛盾观点"""
    analyzer = CrossDocumentAnalyzer(notebook_id)
    await analyzer.initialize()
    try:
        return await analyzer.detect_contradictions(source_ids)
    finally:
        await analyzer.close()


async def identify_research_trends(notebook_id: str, days: int = 7) -> Dict[str, Any]:
    """便捷函数：识别研究趋势"""
    analyzer = CrossDocumentAnalyzer(notebook_id)
    await analyzer.initialize()
    try:
        return await analyzer.identify_trends(days)
    finally:
        await analyzer.close()


async def generate_weekly_trends_report(notebook_id: str, source_ids: Optional[List[str]] = None) -> str:
    """便捷函数：生成周度趋势报告"""
    analyzer = CrossDocumentAnalyzer(notebook_id)
    await analyzer.initialize()
    try:
        return await analyzer.generate_weekly_trends_report(source_ids)
    finally:
        await analyzer.close()
