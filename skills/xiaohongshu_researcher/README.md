# 小红书研究助手 (Xiaohongshu Researcher)

## 功能说明

自动搜索并分析小红书上关于"一人公司"、"solo 创业"等主题的内容，提取爆款笔记特征，保存到 Notebook 供进一步分析。

## 使用场景

- **市场调研**：了解一人公司在小红书的传播趋势
- **内容创作**：学习爆款笔记的标题、结构、互动技巧
- **竞品分析**：发现同领域的优质创作者和内容方向

## 安装依赖

```bash
uv add playwright beautifulsoup4
playwright install chromium
```

## 使用方法

### 基础用法

```python
from open_notebook.skills.xiaohongshu_researcher import XiaohongshuResearcherSkill

skill = XiaohongshuResearcherSkill()
result = await skill.execute({
    "keywords": ["一人公司", "solo 创业"],
    "max_results": 10
})
```

### 参数说明

- `keywords` (必填): 搜索关键词列表
- `max_results` (可选): 每个关键词最多收集多少篇笔记（默认 10）
- `save_to_notebook` (可选): 是否保存到 Notebook（默认 True）

### 输出示例

```json
{
  "total_notes": 20,
  "sources_created": 2,
  "insights": [
    "爆款标题多包含数字和情绪词",
    "图文比例 3:1 效果最佳",
    "话题标签集中在 #个人成长 #创业"
  ]
}
```

## 数据保存

收集的笔记会自动保存到 Notebook：
- **Notebook**: "小红书研究 - {日期}"
- **Source 类型**: xiaohongshu_research
- **元数据**: 包含点赞数、收藏数、评论数等互动数据

## 注意事项

1. **登录状态**：需要小红书登录 cookie（首次运行会提示）
2. **频率限制**：建议每次搜索间隔 3-5 秒，避免触发反爬
3. **数据合规**：仅用于个人研究，请勿大规模采集或商用

## 技术实现

- **浏览器自动化**: Playwright
- **HTML 解析**: BeautifulSoup4
- **数据存储**: SurrealDB (via Repository pattern)

## 扩展方向

- 添加更多平台支持（知乎、B 站、抖音）
- AI 自动生成内容分析报告
- 定期自动更新研究数据

## License

MIT
