# 跨平台 AI 工具集研究助手 (Multi-Platform AI Tools Researcher)

## 技能描述

自动从**小红书、知乎、微博、视频号、公众号、抖音**等 6 大中文社交媒体平台搜集"一人公司的 AI 工具集"相关信息，智能识别 AI 工具内容，生成结构化日报汇总并保存到知识库。

## 使用场景

### 🎯 典型应用场景

1. **市场调研** - 了解 AI 工具在各大平台的传播趋势和热度
2. **竞品分析** - 发现同类 AI 工具的推广策略和用户反馈
3. **趋势洞察** - 识别新兴 AI 工具和热门应用场景
4. **内容创作** - 基于热门话题和工具创作相关内容
5. **学习追踪** - 持续跟进 AI 工具领域的最新动态

### 💼 适用人群

- 一人公司创业者
- 自由职业者
- 独立开发者
- 内容创作者
- AI 工具研究者
- 数字营销人员

## 核心功能

### 1. 多平台数据采集

**支持平台**：
- ✅ **小红书** - 完整支持搜索和数据提取
- 🔄 **知乎** - 框架就绪（待实现具体采集逻辑）
- 🔄 **微博** - 框架就绪（待实现具体采集逻辑）
- ⏳ **视频号** - 计划中
- ⏳ **公众号** - 计划中
- ⏳ **抖音** - 计划中

**采集数据**：
- 标题/内容摘要
- 作者信息
- 互动数据（点赞、收藏、评论）
- 发布时间
- 链接地址

### 2. AI 工具智能识别

**识别能力**：
- 自动过滤非 AI 工具相关内容
- 支持 15+ 个预定义 AI 工具关键词
- 可自定义扩展关键词库
- 智能匹配同义词和变体

**支持的 AI 工具类型**：
- 文本生成（ChatGPT、Jasper、Copy.ai）
- 图像生成（Midjourney、Stable Diffusion、Firefly）
- 办公效率（Notion AI、Grammarly）
- 视频制作（Runway、Descript）
- 语音处理（Otter.ai）
- 国产 AI（通义千问、文心一言、Kimi、智谱 AI）

### 3. 结构化日报生成

**报告模块**：
- 📊 **今日概览** - 内容总量、平台分布、互动统计
- 🔥 **热门 AI 工具 TOP15** - 按提及次数排序
- 💡 **热门话题** - 8 大维度话题聚类
- 📱 **平台分析** - 各平台活跃度对比
- 🎯 **核心洞察** - 高价值内容发现
- 📋 **行动建议** - 指导下一步操作

### 4. 自动化工作流

**支持模式**：
- 立即执行 - 单次研究任务
- 定时调度 - 每日早 9 点自动生成
- 后台运行 - 持续监控和更新

**保存方式**：
- 自动保存到 Open Notebook 知识库
- 支持导出 Markdown 格式报告
- JSON 格式原始数据可供二次分析

## 输入参数

```json
{
  "platforms": ["xiaohongshu"],
  "keywords": ["一人公司 AI 工具", "AI 效率工具"],
  "max_results_per_platform": 20,
  "generate_report": true,
  "save_to_notebook": true,
  "export_markdown": false
}
```

### 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `platforms` | Array | 否 | `["xiaohongshu"]` | 要搜索的平台列表，可选值：xiaohongshu, zhihu, weibo, video_account, official_account, douyin |
| `keywords` | Array | 否 | `["一人公司 AI 工具", "solo 创业 AI", "AI 效率工具", "AIGC 工具"]` | 搜索关键词列表 |
| `max_results_per_platform` | Integer | 否 | `20` | 每个平台最多采集的结果数（范围：1-100） |
| `generate_report` | Boolean | 否 | `true` | 是否生成日报 |
| `save_to_notebook` | Boolean | 否 | `true` | 是否保存到 Notebook |
| `export_markdown` | Boolean | 否 | `false` | 是否导出 Markdown 文件 |

## 输出示例

### 基础输出

```json
{
  "total_collected": 45,
  "ai_tools_related": 38,
  "platforms_searched": ["小红书", "知乎"],
  "report_generated": true,
  "report": {
    "title": "AI 工具集信息日报 - 2026-02-18",
    "date": "2026-02-18",
    "generated_at": "2026-02-18T09:00:00+08:00",
    "summary": {
      "total_items": 38,
      "platforms_covered": 2,
      "total_engagement": 5678,
      "average_engagement_per_item": 149.4,
      "data_collection_period": "24h"
    },
    "trending_tools": [
      {"tool_name": "ChatGPT", "mention_count": 18, "trend": "rising"},
      {"tool_name": "Notion AI", "mention_count": 12, "trend": "stable"},
      {"tool_name": "Midjourney", "mention_count": 9, "trend": "rising"}
    ],
    "hot_topics": [
      "效率提升",
      "内容创作",
      "办公应用",
      "营销推广"
    ],
    "insights": [
      "发现 5 篇高互动内容（点赞 + 收藏>100），建议深入分析其内容特征",
      "小红书是最活跃平台（25 条内容），建议重点关注该平台动态",
      "ChatGPT 提及率显著上升，建议关注最新使用技巧"
    ]
  }
}
```

### Markdown 报告示例

```markdown
# AI 工具集信息日报 - 2026-02-18

**生成时间**: 2026-02-18T09:00:00+08:00

---

## 📊 今日概览

- **内容总数**: 38 条
- **覆盖平台**: 2 个
- **总互动量**: 5678
- **平均互动**: 149.4

---

## 🔥 热门 AI 工具

1. **ChatGPT** (18 次提及)
2. **Notion AI** (12 次提及)
3. **Midjourney** (9 次提及)
...

---

## 💡 热门话题

- 效率提升
- 内容创作
- 办公应用
...

---

## 🎯 核心洞察

- 发现 5 篇高互动内容，建议深入分析
- 小红书最活跃，建议重点关注
...
```

## 使用示例

### Python 调用

#### 基础用法 - 单平台快速调研

```python
from open_notebook.skills.multi_platform_ai_researcher import research_ai_tools
import asyncio

async def main():
    result = await research_ai_tools(
        platforms=['xiaohongshu'],
        keywords=['一人公司 AI 工具', 'AI 效率工具'],
        max_results_per_platform=20,
        generate_report=True,
        save_to_notebook=True
    )
    
    print(f"采集了 {result['total_collected']} 条内容")
    print(f"AI 工具相关：{result['ai_tools_related']} 条")
    
    # 查看热门工具
    if result.get('report'):
        report = result['report']
        print("\n🔥 热门 AI 工具:")
        for tool in report['trending_tools'][:5]:
            print(f"  - {tool['tool_name']}: {tool['mention_count']}次")

asyncio.run(main())
```

#### 高级用法 - 多平台对比

```python
result = await research_ai_tools(
    platforms=['xiaohongshu', 'zhihu', 'weibo'],
    keywords=[
        'ChatGPT 一人公司',
        'AI 工具推荐',
        'AIGC 创业'
    ],
    max_results_per_platform=30,
    generate_report=True,
    save_to_notebook=True
)
```

#### 自定义关键词深度研究

```python
result = await research_ai_tools(
    platforms=['xiaohongshu'],
    keywords=[
        'Midjourney 商用案例',
        'Stable Diffusion 教程',
        'Notion AI 实战技巧'
    ],
    max_results_per_platform=50,
    generate_report=True,
    export_markdown=True,
    save_to_notebook=True
)
```

### 定时任务 - 每日自动生成

```python
from open_notebook.skills.ai_tools_scheduler import setup_daily_schedule
import asyncio

async def main():
    # 设置每天上午 9 点自动生成报告
    await setup_daily_schedule(run_hour=9, run_minute=0)

# 启动调度器（会持续运行）
asyncio.run(main())
```

### 导出 Markdown 报告

```python
from open_notebook.skills.daily_report_generator import DailyReportGenerator
from datetime import datetime

generator = DailyReportGenerator()

# 假设已有采集数据
collected_items = [...]  

# 生成报告
report = generator.generate(collected_items, date=datetime.now())

# 导出为 Markdown 文件
output_path = generator.export_markdown(
    report, 
    f"d:\\Antigravity\\opc\\open-notebook\\reports\\ai_tools_daily_{datetime.now().strftime('%Y%m%d')}.md"
)

print(f"报告已导出到：{output_path}")
```

## 数据保存

### Notebook 结构

**Notebook 命名**: `AI 工具集研究 - {日期}`

**Source 结构**:
- 标题：`AI 工具集日报 - {日期}`
- 类型：`ai_tools_daily_report`
- 内容：完整 JSON 格式报告
- 元数据：包含报告日期、平台数、内容总量等

### 数据库查询

```sql
-- 查询所有 AI 工具集报告
SELECT * FROM source 
WHERE source_type = 'ai_tools_daily_report'
ORDER BY metadata.report_date DESC;

-- 查询最近 7 天的报告
SELECT * FROM source 
WHERE source_type = 'ai_tools_daily_report' 
AND collected_at >= DATE_SUB(NOW(), INTERVAL 7 DAY);

-- 统计某平台的报告数量
SELECT 
    metadata.platforms AS platforms,
    COUNT(*) AS report_count
FROM source 
WHERE source_type = 'ai_tools_daily_report'
GROUP BY metadata.platforms;
```

## 注意事项

### 使用限制

1. **登录要求** - 部分平台可能需要登录才能查看完整内容
2. **频率控制** - 建议控制采集频率，避免触发平台反爬机制
3. **数据合规** - 仅用于个人学习和研究，请勿商业用途

### 性能建议

- 首次运行需要 1-2 分钟（包括浏览器启动时间）
- 建议从少量数据开始测试（max_results_per_platform=10-20）
- 批量搜索时平台数量控制在 3 个以内
- 关键词数量建议不超过 10 个

### 故障排查

**问题 1: 采集数量为 0**
- 检查网络连接
- 验证平台是否可用
- 尝试更换关键词
- 查看日志中的选择器匹配信息

**问题 2: 保存失败**
- 验证数据库连接状态
- 检查 Notebook 权限
- 查看错误日志详情

**问题 3: 定时任务未执行**
- 确认调度器进程是否运行
- 查看系统时间是否正确
- 检查日志是否有报错

## 技术实现

### 架构设计

```
┌─────────────────────────────────────────┐
│   Multi-Platform AI Researcher Skill   │
├─────────────────────────────────────────┤
│  Platform Collectors                    │
│  ├─ Xiaohongshu Collector              │
│  ├─ Zhihu Collector (TODO)             │
│  └─ Weibo Collector (TODO)             │
├─────────────────────────────────────────┤
│  AI Tools Identifier                    │
│  ├─ Keyword Matching                   │
│  └─ Content Filtering                  │
├─────────────────────────────────────────┤
│  Report Generator                       │
│  ├─ Trending Analysis                  │
│  ├─ Topic Clustering                   │
│  └─ Insights Generation                │
├─────────────────────────────────────────┤
│  Scheduler                              │
│  └─ Daily Automation                    │
└─────────────────────────────────────────┘
```

### 核心技术栈

- **浏览器自动化**: Playwright
- **HTML 解析**: BeautifulSoup4
- **数据存储**: SurrealDB (via Repository pattern)
- **日志记录**: Loguru

## 扩展方向

欢迎基于此 Skill 进行二次开发：

1. **更多平台支持** - 实现知乎、微博、抖音等平台的采集器
2. **深度分析** - 添加情感分析、话题演化追踪
3. **可视化展示** - 生成图表和仪表盘
4. **定期回顾** - 生成周报、月报、季度报告
5. **自动试用** - 发现新工具后自动注册试用并生成评测

## License

MIT License

## 作者

Open Notebook Team

## 相关链接

- [GitHub Repository](https://github.com/jackeyunjie/open-notebook)
- [完整使用指南](skills/AI_TOOLS_RESEARCHER_GUIDE.md)
- [Open Notebook 文档](https://github.com/jackeyunjie/open-notebook/tree/main/open_notebook/skills)

---

**最后更新**: 2026-02-18
