"""Multi-Platform AI Tools Researcher Skill.

Automatically collects information about "AI tools for solopreneurs" from
multiple Chinese social media platforms and generates daily research reports.

This is the main skill module that can be used as a Claude Skill.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│          智能内容创作与分发系统（全自动化）                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
        ┌────────────────┴────────────────┐
        ↓                                  ↓
┌──────────────────┐            ┌──────────────────┐
│   输入端（采集）  │            │   输出端（分发）  │
├──────────────────┤            ├──────────────────┤
│ 社交媒体 6 平台   │            │  小红书          │
│ 飞书知识库        │            │  知乎            │
│ 微信群聊（可选）  │            │  微博            │
│ AI 社群文档       │            │  视频号          │
└──────────────────┘            │  公众号          │
        ↓                       │  抖音            │
┌──────────────────┐            └──────────────────┘
│   处理端（加工）  │                    ↓
├──────────────────┤            ┌──────────────────┐
│ 选题发现          │            │   沉淀端（存储）  │
│ 素材整理          │            ├──────────────────┤
│ 文案生成          │            │ SurrealDB        │
│ 差异化适配        │            │ 飞书多维表格     │
│ 发布计划          │            │ Markdown 导出    │
└──────────────────┘            └──────────────────┘
```

## Three Core Systems

### 1. Multi-Platform AI Tools Collector
- 6 social media platforms (Xiaohongshu, Zhihu, Weibo, Video Account, Official Account, Douyin)
- Feishu knowledge base collection
- AI tools content identification
- Daily report generation

### 2. Content Creation Workflow
- Topic discovery (TopicSelector)
- Material collection (MaterialCollector)
- Copywriting generation (CopywritingGenerator)
- Distribution planning (DistributionManager)
- Platform content optimization (PlatformContentOptimizer)

### 3. Feishu Integration
- Knowledge base collection
- Meeting minutes extraction
- Daily report push
- Cloud sheet sync

## Quick Start

```python
# 1. Collect from social media
from open_notebook.skills.multi_platform_ai_researcher import research_ai_tools

result = await research_ai_tools(
    platforms=['xiaohongshu', 'zhihu', 'douyin'],
    keywords=['AI tools', 'productivity'],
    max_results_per_platform=20
)

# 2. Collect from Feishu
from open_notebook.skills.multi_platform_ai_researcher.feishu_knowledge_collector import (
    collect_from_feishu
)

feishu_result = await collect_from_feishu(
    app_id="your_app_id",
    app_secret="your_app_secret",
    keywords=['AI tools']
)

# 3. Create content project
from open_notebook.skills.multi_platform_ai_researcher import create_content_project

content = await create_content_project(
    topic_keywords=["AI tools", "productivity"],
    platforms=["xiaohongshu", "zhihu", "weibo"]
)
```

## Platform Characteristics

| Platform | Optimal Length | Tone | Best Time |
|----------|---------------|------|-----------|
| Xiaohongshu | 300 chars | Friendly, emoji-rich | 19:00 |
| Zhihu | 2000 chars | Professional, analytical | 21:00 |
| Weibo | 140 chars | Casual, trending | 12:00 |
| Video Account | 100 chars | Authentic, value-driven | 20:00 |
| Official Account | 2000 chars | Professional, well-written | 21:00 |
| Douyin | 50 chars | Fast-paced, high-energy | 18:00 |

## Documentation

- SYSTEM_OVERVIEW.md - Complete system architecture
- CONTENT_WORKFLOW_GUIDE.md - Content creation workflow guide
- FEISHU_KNOWLEDGE_GUIDE.md - Feishu collection guide

"""

from .multi_platform_ai_researcher import (
    MultiPlatformAIResearcher,
    research_ai_tools,
    collect_multi_platform_ai_tools
)
from .platform_content_optimizer import (
    PlatformContentOptimizer,
    optimize_for_platform,
    create_multi_platform_content,
    get_platform_guide
)
from .content_creation_workflow import (
    ContentCreationWorkflow,
    TopicSelector,
    MaterialCollector,
    CopywritingGenerator,
    DistributionManager,
    create_content_project,
    generate_platform_content,
    get_platform_comparison
)

__all__ = [
    # Core researcher
    "MultiPlatformAIResearcher",
    "research_ai_tools",
    "collect_multi_platform_ai_tools",
    # Platform optimizer
    "PlatformContentOptimizer",
    "optimize_for_platform",
    "create_multi_platform_content",
    "get_platform_guide",
    # Content workflow
    "ContentCreationWorkflow",
    "TopicSelector",
    "MaterialCollector",
    "CopywritingGenerator",
    "DistributionManager",
    "create_content_project",
    "generate_platform_content",
    "get_platform_comparison"
]
