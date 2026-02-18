# 六平台 AI 工具集采集系统 - 使用指南

## ✅ 平台支持状态（全部实现）

| 平台 | 状态 | 采集方式 | 数据完整性 |
|------|------|----------|------------|
| **小红书** | ✅ 完整支持 | 直接搜索 + 抓取 | 标题/作者/点赞/收藏/链接 |
| **知乎** | ✅ 完整支持 | 网页搜索 + 抓取 | 标题/作者/赞同数/链接 |
| **微博** | ✅ 完整支持 | 网页搜索 + 抓取 | 内容/作者/转评赞/链接 |
| **视频号** | ✅ 完整支持 | Bing 搜索代理 | 标题/描述/链接 |
| **公众号** | ✅ 完整支持 | 搜狗微信搜索 | 标题/账号/内容/日期/链接 |
| **抖音** | ✅ 完整支持 | 网页版搜索 | 描述/作者/点赞数/链接 |

---

## 🚀 快速开始

### 基础用法

```python
from open_notebook.skills.multi_platform_ai_researcher import research_ai_tools
import asyncio

async def main():
    result = await research_ai_tools(
        platforms=[
            'xiaohongshu',      # 小红书
            'zhihu',           # 知乎
            'weibo',           # 微博
            'video_account',   # 视频号
            'official_account',# 公众号
            'douyin'          # 抖音
        ],
        keywords=['一人公司 AI 工具', 'AI 效率工具'],
        max_results_per_platform=20,
        generate_report=True,
        save_to_notebook=True
    )
    
    print(f"✅ 完成！")
    print(f"采集总数：{result['total_collected']} 条")
    print(f"覆盖平台：{', '.join(result['platforms_searched'])}")

asyncio.run(main())
```

### 飞书同步

```python
result = await research_ai_tools(
    platforms=['xiaohongshu', 'zhihu', 'douyin'],
    keywords=['ChatGPT 实战', 'Midjourney 商用'],
    max_results_per_platform=30,
    generate_report=True,
    save_to_notebook=True,
    sync_to_feishu=True,
    feishu_webhook="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
)
```

---

## 📊 输出示例

### 控制台输出
```
============================================================
🤖 跨平台 AI 工具集研究助手 - 测试
============================================================

✅ 研究完成！
📊 采集总数：156 条
🎯 AI 工具相关：89 条
📱 覆盖平台：小红书，知乎，微博，视频号，公众号，抖音
📝 报告生成：是

📋 今日概览:
   - 内容总数：89 条
   - 覆盖平台：6 个
   - 总互动量：12456

🔥 热门 AI 工具:
   1. ChatGPT (23 次提及)
   2. Notion AI (15 次提及)
   3. Midjourney (12 次提及)
   4. Kimi (8 次提及)
   5. 通义千问 (7 次提及)

💡 核心洞察:
   • 发现 5 篇高互动内容，建议深入分析
   • 小红书是最活跃平台（35 条内容）
   • ChatGPT 提及率显著上升

============================================================
```

### 数据结构

```json
{
  "total_collected": 156,
  "ai_tools_related": 89,
  "platforms_searched": ["小红书", "知乎", "微博", "视频号", "公众号", "抖音"],
  "report_generated": true,
  "report": {
    "summary": {
      "total_items": 89,
      "platforms_covered": 6,
      "total_engagement": 12456
    },
    "trending_tools": [
      {"tool_name": "ChatGPT", "mention_count": 23},
      {"tool_name": "Notion AI", "mention_count": 15}
    ],
    "insights": [
      "发现 5 篇高互动内容，建议深入分析",
      "小红书是最活跃平台（35 条内容）"
    ]
  }
}
```

---

## 🔧 配置选项

### 必选参数

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `platforms` | List[str] | 要采集的平台列表 | 全部 6 平台 |
| `keywords` | List[str] | 搜索关键词 | AI 工具集关键词 |

### 可选参数

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `max_results_per_platform` | int | 每平台最大结果数 | 20 |
| `generate_report` | bool | 是否生成日报 | True |
| `save_to_notebook` | bool | 保存到知识库 | True |
| `sync_to_feishu` | bool | 同步到飞书 | False |
| `feishu_webhook` | str | 飞书机器人 URL | None |
| `feishu_app_id` | str | 飞书应用 ID | None |
| `feishu_app_secret` | str | 飞书应用密钥 | None |

---

## 📈 性能优化

### 快速模式（仅核心平台）

```python
result = await research_ai_tools(
    platforms=['xiaohongshu', 'zhihu', 'douyin'],
    max_results_per_platform=15
)
```

### 全面模式（所有平台）

```python
result = await research_ai_tools(
    platforms=[
        'xiaohongshu', 'zhihu', 'weibo',
        'video_account', 'official_account', 'douyin'
    ],
    max_results_per_platform=30
)
```

### 深度研究模式

```python
result = await research_ai_tools(
    platforms=['xiaohongshu', 'zhihu', 'weibo', 'douyin'],
    keywords=['ChatGPT 高级技巧', 'AI 绘画教程', 'Kimi 使用指南'],
    max_results_per_platform=50
)
```

---

## 💾 数据存储

### SurrealDB 结构

```sql
-- 查询最近 7 天各平台采集量
SELECT 
    platform,
    COUNT(*) as count,
    SUM(like_count) as total_likes
FROM source
WHERE source_type = 'ai_tools_daily_report'
AND collected_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY platform;

-- 查找最热门的 AI 工具
SELECT 
    metadata.trending_tools
FROM source
WHERE source_type = 'ai_tools_daily_report'
ORDER BY metadata.report_date DESC
LIMIT 10;
```

### Notebook 组织

```
AI 工具集研究 - 2026-02-18/
├── AI 工具集日报 - 2026-02-18 (Source)
│   ├── summary: {...}
│   ├── trending_tools: [...]
│   ├── hot_topics: [...]
│   └── raw_data: [
│       {platform: 'xiaohongshu', ...},
│       {platform: 'zhihu', ...},
│       {platform: 'douyin', ...}
│   ]
```

---

## 🎯 使用场景

### 场景 1: 每日例行调研

```python
from open_notebook.skills.multi_platform_ai_researcher.ai_tools_scheduler import (
    DailyReportScheduler
)

scheduler = DailyReportScheduler()
await scheduler.run_daily_report(
    platforms=['xiaohongshu', 'zhihu', 'douyin'],
    keywords=['AI 工具推荐', 'AIGC 应用'],
    max_results=20,
    save_to_notebook=True
)
```

### 场景 2: 特定主题研究

```python
result = await research_ai_tools(
    platforms=['xiaohongshu', 'zhihu'],
    keywords=['Stable Diffusion 教程', 'AI 绘画进阶'],
    max_results_per_platform=40,
    generate_report=True
)
```

### 场景 3: 竞品分析

```python
result = await research_ai_tools(
    platforms=['xiaohongshu', 'zhihu', 'weibo', 'douyin'],
    keywords=['Notion AI', 'FlowUs AI', 'Wolai AI'],
    max_results_per_platform=30,
    generate_report=True
)
```

---

## ⚠️ 注意事项

### 1. 反爬机制

- 每个平台都有智能降级策略
- 自动处理反爬验证
- 建议设置合理的采集数量

### 2. 数据准确性

- 小红书、知乎、微博数据最准确
- 视频号、公众号通过搜索引擎代理
- 抖音数据可能需要二次验证

### 3. 速率限制

- 建议单次运行间隔 > 5 分钟
- 大量采集时添加延迟
- 避免高频访问同一平台

---

## 🐛 故障排查

### 问题 1: 采集结果为 0

**原因**：前端选择器变化  
**解决**：检查日志中的选择器匹配信息，更新 CSS 选择器

### 问题 2: 飞书推送失败

**原因**：Webhook URL 错误或网络问题  
**解决**：验证 Webhook URL，检查网络连接

### 问题 3: 数据库保存失败

**原因**：SurrealDB 连接异常  
**解决**：检查数据库服务状态，验证连接配置

---

## 📞 技术支持

- 项目仓库：https://github.com/jackeyunjie/open-notebook
- 技能文档：`open_notebook/skills/multi_platform_ai_researcher/CLAUDE_SKILL.md`
- 测试脚本：`test_ai_tools_researcher.py`

---

**最后更新**: 2026-02-18  
**版本**: v1.0.0
