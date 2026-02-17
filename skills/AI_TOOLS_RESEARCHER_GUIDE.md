# 跨平台 AI 工具集研究助手 - 使用指南

## 📋 功能概述

自动从**小红书、知乎、微博、视频号、公众号、抖音**等 6 大平台搜集"一人公司的 AI 工具集"相关信息，生成结构化日报汇总。

---

## 🚀 快速开始

### 1. 立即运行一次研究

```bash
cd d:\Antigravity\opc\open-notebook
uv run python test_ai_tools_researcher.py
```

**预期输出**：
```
============================================================
🤖 跨平台 AI 工具集研究助手 - 测试
============================================================

✅ 研究完成！
📊 采集总数：15 条
🎯 AI 工具相关：12 条
📱 覆盖平台：小红书
📝 报告生成：是

📋 今日概览:
   - 内容总数：12 条
   - 总互动量：3456

🔥 热门 AI 工具:
   1. ChatGPT (8 次)
   2. Notion AI (5 次)
   3. Midjourney (4 次)

💡 核心洞察:
   • 发现 3 篇高互动内容（点赞 + 收藏>100），建议深入分析其内容特征
   • 小红书是最活跃平台（12 条内容），建议重点关注该平台动态
============================================================
```

---

## 💻 使用方式

### 方式 1: Python 代码调用

#### 基础用法 - 立即执行

```python
from open_notebook.skills.multi_platform_ai_researcher import research_ai_tools
import asyncio

async def main():
    result = await research_ai_tools(
        platforms=['xiaohongshu'],  # 只搜索小红书
        keywords=[
            '一人公司 AI 工具',
            'solo 创业 AI',
            'AI 效率工具'
        ],
        max_results=20,  # 每个关键词最多 20 条
        generate_report=True,  # 生成日报
        save_to_notebook=True  # 保存到 Notebook
    )
    
    print(f"采集了 {result['total_collected']} 条内容")
    print(f"AI 工具相关：{result['ai_tools_related']} 条")
    
    # 查看报告
    if result.get('report'):
        report = result['report']
        print(f"\n今日热门工具:")
        for tool in report['trending_tools'][:5]:
            print(f"  - {tool['tool_name']}: {tool['mention_count']}次")

asyncio.run(main())
```

#### 高级用法 - 自定义平台

```python
result = await research_ai_tools(
    platforms=['xiaohongshu', 'zhihu', 'weibo'],  # 多平台
    keywords=[
        'ChatGPT 一人公司',
        'AI 工具推荐',
        'AIGC 创业'
    ],
    max_results=30,
    generate_report=True,
    save_to_notebook=True
)
```

---

### 方式 2: 设置每日自动任务

#### 每天早上 9 点自动生成报告

```python
from open_notebook.skills.ai_tools_scheduler import setup_daily_schedule
import asyncio

async def main():
    # 设置每天上午 9 点运行
    await setup_daily_schedule(run_hour=9, run_minute=0)

# 启动调度器（会持续运行）
asyncio.run(main())
```

**后台运行建议**：
- 在服务器上作为 systemd 服务运行
- 本地开发环境可以使用 tmux 或 nohup

---

### 方式 3: 导出 Markdown 报告

```python
from open_notebook.skills.daily_report_generator import DailyReportGenerator
from datetime import datetime

generator = DailyReportGenerator()

# 假设已有采集数据
collected_items = [...]  # 从数据库或其他来源获取

# 生成报告
report = generator.generate(collected_items, date=datetime.now())

# 导出为 Markdown 文件
output_path = generator.export_markdown(
    report, 
    f"d:\\Antigravity\\opc\\open-notebook\\reports\\ai_tools_daily_{datetime.now().strftime('%Y%m%d')}.md"
)

print(f"报告已导出到：{output_path}")
```

---

## 📊 生成的报告结构

### 1. 数据保存到 Notebook

**Notebook 名称**: `AI 工具集研究 - 2026-02-18`

**Source 结构**:
- 标题：`AI 工具集日报 - 2026-02-18`
- 类型：`ai_tools_daily_report`
- 内容：完整 JSON 格式报告

### 2. 报告包含的模块

#### 📊 今日概览
- 内容总数
- 覆盖平台数
- 总互动量（点赞 + 收藏 + 评论）
- 平均每条互动量

#### 🔥 热门 AI 工具 TOP15
按提及次数排序：
1. ChatGPT (12 次)
2. Notion AI (8 次)
3. Midjourney (6 次)
...

#### 💡 热门话题
- 效率提升
- 内容创作
- 办公应用
- 营销推广
...

#### 📱 平台分布
- 小红书：15 条
- 知乎：8 条
- 微博：5 条
...

#### 🎯 核心洞察
- "发现 X 篇高互动内容，建议深入分析"
- "XX 平台最活跃，建议重点关注"
- ...

#### 📋 行动建议
- "重点关注热门工具「ChatGPT」的最新使用技巧"
- "围绕热门话题「效率提升」创作相关内容"
- ...

---

## 🛠️ 平台支持情况

| 平台 | 状态 | 说明 |
|------|------|------|
| ✅ 小红书 | **已实现** | 完整支持搜索和数据提取 |
| 🔄 知乎 | 待扩展 | 框架已就绪，需实现具体采集逻辑 |
| 🔄 微博 | 待扩展 | 框架已就绪，需实现具体采集逻辑 |
| ⏳ 视频号 | 计划中 | 需要微信生态支持 |
| ⏳ 公众号 | 计划中 | 需要微信 API 或爬虫 |
| ⏳ 抖音 | 计划中 | 需要官方 API 或逆向 |

**当前可用平台**：仅小红书

**扩展其他平台**：参考 `multi_platform_ai_researcher.py` 中的 `_collect_zhihu()` 方法模板

---

## ⚙️ 配置选项

### 关键词配置

默认使用的关键词：
```python
keywords = [
    '一人公司 AI 工具',
    'solo 创业 AI',
    '独立开发者 AI 工具集',
    'AI 效率工具',
    'AIGC 工具'
]
```

可以自定义：
```python
custom_keywords = [
    'ChatGPT 实战',
    'Notion AI 教程',
    'Midjourney 商用'
]

result = await research_ai_tools(keywords=custom_keywords)
```

### 采集数量

```python
# 每个平台每个关键词最多采集数量
result = await research_ai_tools(max_results=50)  # 默认 20
```

### 报告生成

```python
# 不生成报告（仅采集原始数据）
result = await research_ai_tools(generate_report=False)

# 不保存到 Notebook（仅在内存中处理）
result = await research_ai_tools(save_to_notebook=False)
```

---

## 📁 数据导出

### 导出 JSON

```python
import json

with open('ai_tools_report.json', 'w', encoding='utf-8') as f:
    json.dump(result['report'], f, ensure_ascii=False, indent=2)
```

### 导出 Markdown

见上方"方式 3: 导出 Markdown 报告"

### 从 Notebook 查询

所有报告都保存在 SurrealDB 中，可以通过 SQL 查询：

```sql
-- 查询所有 AI 工具集报告
SELECT * FROM source WHERE source_type = 'ai_tools_daily_report'

-- 查询特定日期的报告
SELECT * FROM source 
WHERE source_type = 'ai_tools_daily_report' 
AND metadata.report_date = '2026-02-18'
```

---

## 🔧 故障排除

### 问题 1: 采集数量为 0

**可能原因**：
- 网络问题导致页面加载失败
- 小红书前端结构变化
- 关键词不匹配

**解决方案**：
1. 检查网络连接
2. 查看日志中的选择器匹配信息
3. 尝试更换关键词

### 问题 2: 定时任务未执行

**检查点**：
- 确认调度器进程是否运行
- 查看日志是否有报错
- 验证系统时间是否正确

### 问题 3: 保存失败

**验证数据库连接**：
```bash
uv run python -c "from open_notebook.database.repository import repo_query; print(repo_query('SELECT COUNT(*) FROM notebook'))"
```

---

## 📈 进阶用法

### 1. 多关键词组合策略

```python
# 按场景分类
scene_keywords = [
    'AI 写作工具',
    'AI 绘画工具',
    'AI 视频工具',
    'AI 编程工具'
]

# 按人群分类
audience_keywords = [
    '一人公司 AI',
    '自由职业者 AI',
    '独立开发者 AI',
    '创作者 AI 工具'
]

result = await research_ai_tools(
    keywords=scene_keywords + audience_keywords,
    max_results=30
)
```

### 2. 历史数据对比

```python
# 查询昨天的报告
yesterday = datetime.now() - timedelta(days=1)
yesterday_report = get_report_by_date(yesterday)

# 查询今天的报告
today_report = get_report_by_date(datetime.now())

# 对比趋势
compare_reports(yesterday_report, today_report)
```

### 3. 自定义分析维度

在 `daily_report_generator.py` 中添加自己的分析逻辑：

```python
def _my_custom_analysis(self, items):
    """添加你自己的分析维度"""
    # 例如：分析 AI 工具的付费/免费比例
    # 例如：分析内容的发布时间分布
    pass
```

---

## 🎯 下一步计划

### Phase 1: 完善现有平台（本周）
- ✅ 小红书采集器
- ⏳ 知乎采集器（需实现）
- ⏳ 微博采集器（需实现）

### Phase 2: 深度分析（下周）
- AI 工具情感分析（正面/负面评价）
- 工具使用场景聚类
- 创作者影响力评估

### Phase 3: 自动化工作流（未来）
- 发现新工具 → 自动试用 → 生成评测
- 热点话题 → 自动创作 → 发布到社交媒体
- 定期回顾 → 生成月度/季度报告

---

## 📞 技术支持

遇到问题或有改进建议，欢迎反馈！

---

**最后更新**: 2026-02-18
