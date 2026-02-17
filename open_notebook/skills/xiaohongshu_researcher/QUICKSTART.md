# 小红书研究助手 - 快速开始指南

## 🎯 功能说明

这个 Skill 可以自动在小红书上搜索"一人公司"相关内容，并分析爆款笔记的特征。

## 📦 安装依赖

已经自动安装，无需手动操作。

包含：
- playwright (浏览器自动化)
- beautifulsoup4 (HTML 解析)
- Chromium 浏览器

## 🚀 使用方法

### 方法 1: 使用测试脚本（推荐新手）

```bash
cd d:\Antigravity\opc\open-notebook
uv run python test_xiaohongshu_skill.py
```

**预期输出**：
```
🔍 开始测试小红书研究助手...
------------------------------------------------------------
✅ 研究完成！
📊 收集笔记数：5
💾 创建 Source 数：1
💡 洞察发现:
   1. 爆款标题多包含数字（60% 以上高赞笔记使用）
   2. 平均点赞数：1234
   3. 平均收藏数：456
   4. 收藏/点赞比=0.37，内容实用性强（用户倾向于收藏）
------------------------------------------------------------
```

### 方法 2: Python 代码调用

```python
from open_notebook.skills.xiaohongshu_researcher import research_xiaohongshu
import asyncio

async def main():
    result = await research_xiaohongshu(
        keywords=["一人公司", "solo 创业", "独立开发者"],
        max_results=10,  # 每个关键词最多收集 10 篇笔记
        save_to_notebook=True  # 保存到 Notebook
    )
    
    print(f"收集了 {result['total_notes']} 篇笔记")
    print(f"创建了 {result['sources_created']} 个 Source")
    print("洞察:")
    for insight in result["insights"]:
        print(f"  - {insight}")

asyncio.run(main())
```

### 方法 3: 在 Open Notebook 中使用

如果你配置了 Skill Runner:

```python
from open_notebook.skills import get_skill_runner

runner = get_skill_runner()
result = await runner.execute(
    skill_name="xiaohongshu-researcher",
    params={
        "keywords": ["一人公司"],
        "max_results": 20
    }
)
```

## 📊 数据保存位置

收集的笔记会自动保存到：

**Notebook**: `小红书研究 - 2026-02-17` (以今天日期命名)

**Source 结构**:
- 标题：`一人公司 - 爆款笔记分析 (5 篇)`
- 类型：`xiaohongshu_research`
- 内容：JSON 格式，包含所有笔记数据和洞察分析

**每篇笔记的数据**:
```json
{
  "title": "95 后裸辞做一人公司，我赚了多少钱？",
  "author": "创业的小明",
  "like_count": 1234,
  "collect_count": 456,
  "url": "https://www.xiaohongshu.com/explore/xxx",
  "collected_at": "2026-02-17T20:30:00"
}
```

## 💡 洞察分析示例

Skill 会自动分析以下模式：

1. **标题特征**
   - 是否包含数字（如"95 后"、"3 个技巧"）
   - 是否使用情绪词（如"绝了"、"必看"）

2. **互动数据**
   - 平均点赞数
   - 平均收藏数
   - 收藏/点赞比例（判断内容实用性）

3. **创作者分布**
   - 最活跃的创作者 TOP3
   - 高频出现的话题标签

## ⚠️ 注意事项

1. **首次运行较慢**
   - 需要打开浏览器
   - 加载小红书页面
   - 建议耐心等待

2. **可能需要登录**
   - 如果小红书要求登录，手动在浏览器中登录即可
   - Cookie 会保存在本地

3. **频率限制**
   - 默认每个关键词间隔 3 秒
   - 不要一次性搜索太多关键词（建议≤5 个）

4. **数据准确性**
   - 小红书前端结构可能变化
   - 如果遇到解析错误，检查 HTML 选择器是否需要更新

## 🔧 故障排除

### 问题 1: 浏览器无法启动

**解决方案**：
```bash
uv run playwright install chromium --force
```

### 问题 2: 搜索结果为空

**可能原因**：
- 网络问题导致页面加载失败
- 小红书反爬限制

**解决方案**：
- 检查网络连接
- 降低 `max_results` 数量
- 稍后再试

### 问题 3: 保存失败

**检查**：
```bash
# 验证数据库连接
uv run python -c "from open_notebook.database.repository import repo_query; print(repo_query('SELECT COUNT(*) FROM notebook'))"
```

## 🎨 自定义扩展

你可以修改 `skill.py` 中的 `analyze_patterns` 方法来添加自己的分析逻辑：

```python
async def analyze_patterns(self, notes):
    insights = []
    
    # 添加你自己的分析规则
    # 例如：分析笔记长度
    avg_length = sum(len(n["title"]) for n in notes) / len(notes)
    insights.append(f"平均标题长度：{avg_length:.1f}字")
    
    return insights
```

## 📝 下一步

收集完数据后，你可以：

1. 在 Open Notebook 界面查看整理好的笔记数据
2. 使用其他 Skill 进一步分析（如内容摘要、标签提取）
3. 基于爆款模式创作自己的内容

---

**祝你研究愉快！🎉**
