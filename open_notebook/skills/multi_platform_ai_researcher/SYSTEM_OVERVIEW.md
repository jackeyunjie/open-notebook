# 智能内容创作与分发系统 - 完整架构

## 系统全景图

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

## 三大核心系统

### 1. 多平台 AI 工具采集系统

**文件**: `multi_platform_ai_researcher.py`

**功能**:
- 6 大社交媒体平台采集（小红书、知乎、微博、视频号、公众号、抖音）
- 自动识别 AI 工具相关内容
- 生成趋势报告和洞察
- 飞书消息推送

**使用**:
```python
from open_notebook.skills.multi_platform_ai_researcher import research_ai_tools

result = await research_ai_tools(
    platforms=['xiaohongshu', 'zhihu', 'douyin'],
    keywords=['一人公司 AI 工具'],
    max_results_per_platform=20,
    generate_report=True,
    save_to_notebook=True,
    sync_to_feishu=True
)
```

### 2. 飞书知识库自动化采集

**文件**: `feishu_knowledge_collector.py`

**功能**:
- 自动获取飞书云文档
- 提取会议纪要和妙记
- 智能关键词过滤
- 定时任务支持

**使用**:
```python
from open_notebook.skills.multi_platform_ai_researcher.feishu_knowledge_collector import (
    collect_from_feishu
)

result = await collect_from_feishu(
    app_id="cli_xxx",
    app_secret="xxx",
    keywords=['AI 工具', 'ChatGPT', 'Kimi'],
    max_docs=50,
    max_meetings=20
)
```

### 3. 多平台内容创作工作流

**文件**: `content_creation_workflow.py`, `platform_content_optimizer.py`

**功能**:
- 热点话题发现（TopicSelector）
- 素材自动采集（MaterialCollector）
- 差异化文案生成（CopywritingGenerator）
- 发布计划管理（DistributionManager）

**使用**:
```python
from open_notebook.skills.multi_platform_ai_researcher import create_content_project

result = await create_content_project(
    topic_keywords=["AI 工具推荐", "效率提升"],
    platforms=["xiaohongshu", "zhihu", "weibo"],
    style="informative"
)
```

## 完整数据流向

```
用户输入主题关键词
      ↓
┌─────────────────┐
│ 1. 多平台采集    │ ← 社交媒体 + 飞书知识库
└─────────────────┘
      ↓
┌─────────────────┐
│ 2. AI 工具识别   │ ← 智能过滤和分类
└─────────────────┘
      ↓
┌─────────────────┐
│ 3. 选题分析      │ ← 热点发现和评估
└─────────────────┘
      ↓
┌─────────────────┐
│ 4. 素材整理      │ ← 去重和关联
└─────────────────┘
      ↓
┌─────────────────┐
│ 5. 文案生成      │ ← 差异化多版本
└─────────────────┘
      ↓
┌─────────────────┐
│ 6. 平台适配      │ ← 格式和风格优化
└─────────────────┘
      ↓
┌─────────────────┐
│ 7. 发布计划      │ ← 时间和渠道安排
└─────────────────┘
      ↓
┌─────────────────┐
│ 8. 数据存储      │ → SurrealDB + 飞书表格
└─────────────────┘
      ↓
┌─────────────────┐
│ 9. 报告推送      │ → 飞书群消息
└─────────────────┘
```

## 系统集成方案

### 方案一：快速采集模式

```python
import asyncio
from open_notebook.skills.multi_platform_ai_researcher import (
    research_ai_tools
)
from open_notebook.skills.multi_platform_ai_researcher.feishu_knowledge_collector import (
    collect_from_feishu
)

async def integrated_collection():
    """集成采集：社交媒体 + 飞书知识库"""

    # 1. 社交媒体采集
    social_result = await research_ai_tools(
        platforms=['xiaohongshu', 'zhihu', 'douyin'],
        keywords=['一人公司 AI 工具', '效率工具'],
        max_results_per_platform=20,
        generate_report=True,
        save_to_notebook=True
    )

    # 2. 飞书知识库采集
    feishu_result = await collect_from_feishu(
        app_id="your_app_id",
        app_secret="your_app_secret",
        keywords=['AI 工具', 'ChatGPT', 'Kimi'],
        max_docs=50,
        max_meetings=20
    )

    # 3. 汇总报告
    total_docs = feishu_result['summary']['total_docs']
    total_meetings = feishu_result['summary']['total_meetings']
    ai_related = social_result['ai_tools_related']

    print("=" * 60)
    print("📊 采集完成报告")
    print("=" * 60)
    print(f"社交媒体：{ai_related} 条 AI 相关内容")
    print(f"飞书文档：{feishu_result['ai_docs']} 篇 AI 工具文档")
    print(f"飞书会议：{feishu_result['ai_meetings']} 场 AI 主题会议")
    print(f"总计：{total_docs} 文档 + {total_meetings} 会议")

    return {
        'social': social_result,
        'feishu': feishu_result
    }

asyncio.run(integrated_collection())
```

### 方案二：内容创作 + 飞书素材

```python
import asyncio
from open_notebook.skills.multi_platform_ai_researcher.content_creation_workflow import (
    ContentCreationWorkflow
)
from open_notebook.skills.multi_platform_ai_researcher.feishu_knowledge_collector import (
    FeishuKnowledgeCollector
)

async def create_content_from_feishu():
    """基于飞书素材创建内容"""

    # 1. 从飞书采集素材
    feishu_collector = FeishuKnowledgeCollector(
        app_id="your_app_id",
        app_secret="your_app_secret"
    )

    docs = await feishu_collector.collect_documents(
        keywords=['AI 工具'],
        max_results=10
    )

    # 2. 转换为素材格式
    reference_materials = [
        doc['content'][:500] for doc in docs[:5]
    ]

    # 3. 创建内容项目
    workflow = ContentCreationWorkflow()

    # 使用飞书素材作为参考生成内容
    from open_notebook.skills.multi_platform_ai_researcher.content_creation_workflow import (
        generate_platform_content
    )

    content = await generate_platform_content(
        topic_title="飞书团队推荐的 AI 工具",
        topic_description="基于飞书知识库整理的 AI 工具推荐",
        platform="xiaohongshu",
        reference_materials=reference_materials
    )

    print(f"标题: {content['title']}")
    print(f"内容: {content['content'][:300]}...")

    return content

asyncio.run(create_content_from_feishu())
```

### 方案三：全自动定时任务

```python
from open_notebook.skills.multi_platform_ai_researcher.ai_tools_scheduler import (
    DailyReportScheduler
)
from open_notebook.skills.multi_platform_ai_researcher.feishu_sync import (
    FeishuSyncService
)

async def full_automation():
    """全自动化：采集 + 分析 + 推送"""

    # 配置
    feishu_config = {
        'webhook_url': 'https://open.feishu.cn/open-apis/bot/v2/hook/xxx',
        'app_id': 'cli_xxx',
        'app_secret': 'xxx'
    }

    # 执行日报
    scheduler = DailyReportScheduler()

    result = await scheduler.run_daily_report(
        platforms=['xiaohongshu', 'zhihu', 'douyin'],
        keywords=['AI 工具', '效率工具'],
        max_results=30,
        save_to_notebook=True
    )

    # 推送到飞书
    if result.get('report'):
        feishu = FeishuSyncService(**feishu_config)
        await feishu.send_daily_report(result['report'])

    return result

# 定时运行（每天早上 9 点）
# scheduler.start_scheduler(run_time="09:00")
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

## 文件清单

```
open_notebook/skills/multi_platform_ai_researcher/
├── __init__.py                          # 模块导出
├── multi_platform_ai_researcher.py      # 多平台采集器 (910 行)
├── platform_content_optimizer.py        # 平台内容优化 (729 行)
├── content_creation_workflow.py         # 内容创作工作流 (994 行)
├── feishu_knowledge_collector.py        # 飞书知识库采集 (443 行)
├── feishu_sync.py                       # 飞书同步服务 (452 行)
├── daily_report_generator.py            # 日报生成器 (347 行)
├── ai_tools_scheduler.py                # 定时任务调度 (263 行)
├── SYSTEM_OVERVIEW.md                   # 本文件 - 系统总览
├── CONTENT_WORKFLOW_GUIDE.md            # 内容工作流指南
├── FEISHU_KNOWLEDGE_GUIDE.md            # 飞书采集指南
└── README.md                            # 项目 README
```

## 配置清单

### 1. 环境变量配置 (.env)

```bash
# 飞书配置
FEISHU_APP_ID=cli_xxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx
FEISHU_SHEET_TOKEN=xxxxxxxxxxxxxxxxx

# 采集参数
DEFAULT_PLATFORMS=xiaohongshu,zhihu,douyin
MAX_RESULTS_PER_PLATFORM=20
DEFAULT_KEYWORDS=AI工具,效率工具,ChatGPT

# 内容生成
CONTENT_STYLE=informative
AUTO_GENERATE_HASHTAGS=true
OPTIMAL_POSTING_TIME=auto

# 报告设置
GENERATE_DAILY_REPORT=true
REPORT_TIME=09:00
SYNC_TO_FEISHU=true
```

### 2. 飞书应用权限配置

需要在飞书开放平台申请以下权限：

**文档权限**:
- `docs:document:readonly` - 获取云文档列表
- `docs:document.content:readonly` - 读取云文档内容

**会议权限**:
- `vc:meeting:readonly` - 获取会议列表
- `vc:meeting.minutes:readonly` - 读取会议纪要

**应用权限**:
- `im:message:send` - 发送消息到群组

## 使用建议

### 推荐工作流

```
周一：执行研究，发现本周热门话题
周二：采集素材，分析竞品内容
周三：生成文案，多平台版本
周四：制作配图/视频
周五：按计划分发，追踪效果
```

### 系统扩展建议

1. **添加微信群采集**
   - 使用微信机器人 API
   - 监听关键词消息
   - 自动保存到数据库

2. **集成 LLM 生成文案**
   ```python
   from open_notebook.ai.model_manager import ModelManager

   model = await ModelManager.get_model()
   # 使用大模型生成更高质量的文案
   ```

3. **添加内容效果追踪**
   - 发布后追踪互动数据
   - 分析哪些内容表现好
   - 优化后续生成策略

## 总结

本系统提供了一个**从采集到分发的完整内容生产闭环**：

1. **输入端**: 6 大社交媒体 + 飞书知识库
2. **处理端**: AI 辅助选题 + 素材整理 + 文案生成
3. **输出端**: 6 平台差异化内容 + 智能发布计划
4. **沉淀端**: SurrealDB 数据库 + 飞书多维表格

核心价值：
- ✅ 全自动运行，节省人工
- ✅ 数据驱动，基于热门内容创作
- ✅ 差异化输出，每个平台定制化
- ✅ 持续积累，形成知识库

**系统已就绪，立即开始使用！**
