# 小红书研究助手 (Xiaohongshu Researcher)

## 技能描述

自动在小红书上搜索指定主题内容，提取爆款笔记数据并分析传播模式，将研究结果保存到 Open Notebook 知识库。

## 使用场景

- **市场调研**：了解特定话题在小红书的传播趋势和热度
- **竞品分析**：发现同领域的优质创作者和热门内容方向  
- **内容创作**：学习爆款笔记的标题技巧、内容结构和互动策略
- **趋势洞察**：识别高价值话题标签和用户关注焦点

## 能力说明

### 核心功能
1. **自动化搜索** - 支持多个关键词批量搜索
2. **数据采集** - 提取笔记标题、作者、点赞数、收藏数、URL 等关键数据
3. **模式分析** - 识别爆款内容的共同特征（数字标题、情绪词、互动比例等）
4. **知识沉淀** - 自动保存到 Notebook，支持后续分析和内容创作

### 技术特性
- 基于 Playwright 实现浏览器自动化
- 模拟真实用户行为避免反爬检测
- 智能滚动加载更多搜索结果
- 结构化数据存储到 SurrealDB

## 输入参数

```json
{
  "keywords": ["一人公司", "solo 创业", "独立开发者"],
  "max_results": 10,
  "save_to_notebook": true
}
```

### 参数说明
- `keywords` (数组，必填): 要搜索的关键词列表
- `max_results` (整数，可选): 每个关键词最多收集的笔记数量，默认 10，范围 1-50
- `save_to_notebook` (布尔值，可选): 是否保存到 Notebook，默认 true

## 输出示例

```json
{
  "total_notes": 30,
  "sources_created": 3,
  "insights": [
    "爆款标题多包含数字（60% 以上高赞笔记使用）",
    "情绪词使用频繁（50% 以上标题包含强烈情感表达）",
    "平均点赞数：1234",
    "平均收藏数：456",
    "收藏/点赞比=0.37，内容实用性强（用户倾向于收藏）",
    "活跃创作者：创业小明、solo 达人、独立开发者张三"
  ],
  "keywords_searched": ["一人公司", "solo 创业", "独立开发者"]
}
```

## 使用示例

### Python 调用

```python
from open_notebook.skills.xiaohongshu_researcher import research_xiaohongshu

# 基础用法
result = await research_xiaohongshu(
    keywords=["一人公司"],
    max_results=10
)

# 高级用法 - 多关键词 + 不保存
result = await research_xiaohongshu(
    keywords=["一人公司", "solo 创业", "轻资产创业"],
    max_results=20,
    save_to_notebook=False
)
```

### 命令行运行

```bash
cd d:\Antigravity\opc\open-notebook
uv run python test_xiaohongshu_skill.py
```

## 数据保存结构

收集的数据会自动组织到 Open Notebook：

**Notebook 命名**: `小红书研究 - {日期}`

**Source 结构**:
- 标题：`{关键词} - 爆款笔记分析 ({笔记数}篇)`
- 类型：`xiaohongshu_research`
- 内容：完整 JSON 数据（包含所有笔记元数据和洞察分析）

**单条笔记数据**:
```json
{
  "title": "95 后裸辞做一人公司，月入 5 万的实战经验分享",
  "author": "创业的小明",
  "like_count": 2345,
  "collect_count": 678,
  "url": "https://www.xiaohongshu.com/explore/xxx",
  "search_keyword": "一人公司",
  "collected_at": "2026-02-17T20:30:00+08:00"
}
```

## 注意事项

### 使用限制
1. **登录要求** - 首次运行可能需要在打开的浏览器中手动登录小红书账号
2. **频率控制** - 建议每次搜索间隔 3-5 秒，避免触发平台反爬机制
3. **数据合规** - 仅用于个人学习和研究，请勿大规模采集或商业用途

### 性能建议
- 首次运行需要 1-2 分钟（包括浏览器启动时间）
- 建议从少量数据开始测试（max_results=5）
- 批量搜索时关键词数量控制在 5 个以内

### 故障排查
- 如果浏览器无法启动：`uv run playwright install chromium --force`
- 如果搜索结果为空：检查网络连接，降低 max_results 数量
- 如果保存失败：验证数据库连接状态

## 依赖环境

- Python 3.11+
- Playwright >= 1.40.0
- BeautifulSoup4 >= 4.12.0
- Chromium 浏览器（自动下载）

## 扩展方向

欢迎基于此 Skill 进行二次开发：

1. **多平台支持** - 扩展到知乎、B 站、抖音等平台
2. **深度分析** - 添加内容摘要生成、情感分析、话题聚类等 AI 分析
3. **定期追踪** - 设置定时任务监控话题热度变化
4. **可视化报告** - 生成 PDF/Markdown 格式的研究分析报告

## License

MIT License

## 作者

Open Notebook Team

---

**最后更新**: 2026-02-17
