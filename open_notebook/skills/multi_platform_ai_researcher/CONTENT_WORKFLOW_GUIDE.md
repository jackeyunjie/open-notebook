# 多平台内容创作工作流指南

## 概述

本系统提供从**选题**、**素材**、**文案**到**分发**的完整内容创作工作流，支持6大平台的内容差异化优化。

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│           内容创作工作流 (Content Creation Workflow)        │
├─────────────────────────────────────────────────────────┤
│  1. 选题模块 (Topic Selector)                             │
│     - AI辅助选题                                          │
│     - 热度分析                                            │
│     - 竞争度评估                                          │
├─────────────────────────────────────────────────────────┤
│  2. 素材模块 (Material Collector)                         │
│     - 多平台素材采集                                      │
│     - 智能分类整理                                        │
│     - 洞察生成                                            │
├─────────────────────────────────────────────────────────┤
│  3. 文案模块 (Copywriting Generator)                      │
│     - 平台特性分析                                        │
│     - 差异化文案生成                                      │
│     - 自动优化                                            │
├─────────────────────────────────────────────────────────┤
│  4. 分发模块 (Distribution Manager)                       │
│     - 发布计划制定                                        │
│     - 时间优化                                            │
│     - 效果预估                                            │
└─────────────────────────────────────────────────────────┘
```

## 平台内容特性对比

| 平台 | 最佳字数 | 调性风格 | 发布时间 | 内容类型 |
|------|----------|----------|----------|----------|
| **小红书** | 300字 | 亲切种草、emoji多 | 19:00 | 图文笔记 |
| **知乎** | 2000字 | 专业深度、逻辑严谨 | 21:00 | 长文回答 |
| **微博** | 140字 | 轻松活泼、跟热点 | 12:00 | 短内容 |
| **视频号** | 100字 | 真实自然、价值输出 | 20:00 | 短视频 |
| **公众号** | 2000字 | 专业深度、文笔流畅 | 21:00 | 长图文 |
| **抖音** | 50字 | 短平快、高能量 | 18:00 | 短视频 |

## 快速开始

### 1. 完整工作流

```python
import asyncio
from open_notebook.skills.multi_platform_ai_researcher.content_creation_workflow import (
    create_content_project
)

async def main():
    # 执行完整工作流
    result = await create_content_project(
        topic_keywords=["AI工具", "效率提升"],
        platforms=["xiaohongshu", "zhihu", "weibo", "douyin"],
        style="informative"  # informative/persuasive/storytelling
    )

    print("=== 项目报告 ===")
    print(f"选题: {result['topic']['title']}")
    print(f"采集素材: {result['materials_summary']['total']} 条")

    for copy in result['copywritings']:
        print(f"\n【{copy['platform']}】")
        print(f"标题: {copy['title']}")
        print(f"标签: {' '.join(copy['hashtags'])}")

asyncio.run(main())
```

### 2. 单独使用某平台优化

```python
from open_notebook.skills.multi_platform_ai_researcher.content_creation_workflow import (
    generate_platform_content
)

async def main():
    # 为特定平台生成内容
    content = await generate_platform_content(
        topic_title="10个提升效率的AI工具",
        topic_description="分享10个可以大幅提升工作效率的AI工具",
        platform="xiaohongshu",  # 或 zhihu/weibo/video_account/official_account/douyin
        reference_materials=[
            "ChatGPT可以用于文案写作和代码生成",
            "Midjourney可以快速生成高质量图片",
            "Notion AI可以帮助整理笔记和思路"
        ]
    )

    print(f"平台: {content['platform']}")
    print(f"标题: {content['title']}")
    print(f"内容:\n{content['content']}")
    print(f"标签: {' '.join(content['hashtags'])}")
    print(f"CTA: {content['call_to_action']}")

asyncio.run(main())
```

### 3. 平台特性分析

```python
from open_notebook.skills.multi_platform_ai_researcher.content_creation_workflow import (
    get_platform_comparison
)

# 获取平台对比
comparison = get_platform_comparison()
print(f"支持平台数: {comparison['summary']['total_platforms']}")

for platform, info in comparison['platforms'].items():
    print(f"\n{info['name_cn']}:")
    print(f"  内容类型: {info['content_type']}")
    print(f"  最佳字数: {info['optimal_length']} 字")
    print(f"  调性: {info['tone_style']}")
```

## 高级用法

### 1. 自定义选题策略

```python
from open_notebook.skills.multi_platform_ai_researcher.content_creation_workflow import (
    ContentCreationWorkflow
)

async def custom_topic_selection():
    workflow = ContentCreationWorkflow()

    # 发现话题
    topics = await workflow.topic_selector.discover_topics(
        category="ai_tools",
        count=10
    )

    # 根据自定义标准选择
    selected = workflow.topic_selector.select_topic(
        topics,
        criteria={
            "min_trend_score": 80,
            "max_competition": "medium"
        }
    )

    print(f"选中话题: {selected.title}")
    print(f"热度分数: {selected.trend_score}")
    print(f"竞争程度: {selected.competition_level}")

asyncio.run(custom_topic_selection())
```

### 2. 素材深度分析

```python
# 采集素材后进行分析
materials = await workflow.material_collector.collect_from_platforms(
    topic=selected_topic,
    platforms=["xiaohongshu", "zhihu"],
    max_per_platform=20
)

# 按相关性组织
organized = workflow.material_collector.organize_materials(materials)
print(f"高相关素材: {len(organized['high_relevance'])} 条")
print(f"中相关素材: {len(organized['medium_relevance'])} 条")

# 生成洞察
insights = workflow.material_collector.generate_insights(materials)
print(f"\n总互动量: {insights['total_engagement']['likes']} 赞")
print(f"热门标签: {insights['trending_tags']}")
```

### 3. 批量生成多平台内容

```python
# 为所有平台生成差异化内容
copies = await workflow.copywriting_generator.generate_multi_platform_copies(
    topic=selected_topic,
    materials=materials,
    platforms=["xiaohongshu", "zhihu", "weibo", "video_account", "official_account", "douyin"],
    style="informative"
)

for copy in copies:
    print(f"\n{'='*40}")
    print(f"平台: {copy.platform_name}")
    print(f"标题: {copy.title}")
    print(f"字数: {len(copy.content)} 字")
    print(f"预计互动: {copy.expected_engagement}")
```

### 4. 智能分发计划

```python
# 创建分发计划
plans = workflow.distribution_manager.create_distribution_plan(copies)

# 优化发布时间（错开高峰）
optimized = workflow.distribution_manager.optimize_schedule(plans)

for plan in optimized:
    print(f"{plan.platform_name}: {plan.scheduled_time}")

# 生成报告
report = workflow.distribution_manager.generate_distribution_report()
print(f"\n预计总触达: {report['estimated_reach']['estimated_total_reach']} 人")
```

## 平台内容模板

### 小红书模板

```
✨ 【标题】痛点 + 解决方案 + emoji

【开场】
姐妹们！今天发现了一个超实用的...

【正文】
💡 要点1：xxx
💡 要点2：xxx
💡 要点3：xxx

📌 总结：
- 重点1
- 重点2

💬 你用过哪些AI工具？评论区告诉我！

#AI工具 #效率提升 #打工人必备
```

### 知乎模板

```
【标题】如何xxx？万字长文深度解析

【引言】
作为一个xxx，我用过xxx。今天系统的分享一下...

## 一、概念阐述
...

## 二、核心分析
### 2.1 xxx
### 2.2 xxx

## 三、实践建议
...

【总结】
...

赞同收藏，感谢支持！
```

### 微博模板

```
【短微博】
#话题# 发现了一个超好用的AI工具！xxx [doge]

或

【长微博】
今天和大家分享10个提升效率的AI工具：

1. ChatGPT - 文案生成
2. Midjourney - 图像创作
...

你用过哪些？评论区聊聊！

#AI工具 #效率神器
```

## 内容风格选择

| 风格 | 适用场景 | 特点 |
|------|----------|------|
| **informative** | 知识分享、教程 | 信息密度高、逻辑清晰 |
| **persuasive** | 产品推荐、种草 | 强调价值、引导行动 |
| **storytelling** | 经验分享、案例 | 叙事性强、情感共鸣 |

## 数据流向

```
多平台采集器 (Multi-Platform Researcher)
  ↓ 提供热门话题和素材
选题模块 → 素材模块 → 文案模块 → 分发模块
  ↓
平台内容优化器 (Platform Content Optimizer)
  ↓
生成差异化内容
  ↓
飞书同步 / Open Notebook 存储
```

## 集成到现有系统

```python
# 结合多平台研究助手的完整流程
from open_notebook.skills.multi_platform_ai_researcher import research_ai_tools
from open_notebook.skills.multi_platform_ai_researcher.content_creation_workflow import (
    ContentCreationWorkflow
)

async def integrated_workflow():
    # 第一步：研究热门话题
    research_result = await research_ai_tools(
        platforms=["xiaohongshu", "zhihu", "weibo"],
        keywords=["AI工具", "效率提升"],
        max_results=30,
        generate_report=True
    )

    # 获取热门话题
    trending_tools = research_result['report']['trending_tools']

    # 第二步：创建内容项目
    workflow = ContentCreationWorkflow()

    # 使用研究数据发现话题
    topics = await workflow.topic_selector.discover_topics(
        research_data=research_result['report']['items']
    )

    selected_topic = workflow.topic_selector.select_topic(topics)

    # 第三步：生成内容
    project = await workflow.execute_full_workflow(
        topic_criteria={"min_trend_score": 70},
        platforms=["xiaohongshu", "zhihu", "weibo"]
    )

    # 第四步：同步到飞书
    await workflow.distribution_manager.sync_to_feishu(project)

    return project
```

## 常见问题

### Q: 如何确保内容原创性？
A: 系统基于素材提供灵感和参考，但最终文案是重新组织生成的。建议结合个人经验和观点进行最终修改。

### Q: 各平台内容差异多大？
A: 系统会根据平台特性（字数、风格、格式）生成完全不同的内容版本，而非简单复制。

### Q: 可以定时发布吗？
A: 当前版本生成发布计划，实际发布需要手动或配合平台API实现。

### Q: 如何评估内容效果？
A: 建议发布后追踪各平台的互动数据（点赞、评论、转发），作为后续优化的参考。

## 扩展开发

### 添加新的内容风格

```python
# 在 CopywritingGenerator 中扩展风格
STYLE_TEMPLATES = {
    "humorous": {
        "opening": "段子式开场",
        "tone": "轻松幽默",
        "emoji_density": "high"
    },
    "professional": {
        "opening": "专业背景介绍",
        "tone": "权威专业",
        "emoji_density": "low"
    }
}
```

### 集成AI大模型生成文案

```python
# 使用LLM生成更高质量的文案
async def generate_with_llm(topic, materials, platform):
    from open_notebook.ai.model_manager import ModelManager

    model = await ModelManager.get_model()

    prompt = f"""
    基于以下素材，为{platform}平台创作内容：

    话题：{topic.title}
    素材：{[m.content for m in materials[:3]]}
    平台特性：{platform_characteristics}

    要求：
    1. 符合平台调性
    2. 原创性强
    3. 包含互动引导
    """

    response = await model.generate(prompt)
    return response
```

## 总结

本系统核心价值：

1. **数据驱动选题** - 基于多平台热门数据发现话题
2. **素材智能整理** - 自动采集、分类、提取洞察
3. **平台差异化** - 同一主题生成6种不同风格内容
4. **流程自动化** - 从选题到分发计划一站式完成

**推荐工作流**：
```
周一：执行研究，发现本周热门话题
周二：采集素材，分析竞品内容
周三：生成文案，多平台版本
周四：制作配图/视频
周五：按计划分发，追踪效果
```
