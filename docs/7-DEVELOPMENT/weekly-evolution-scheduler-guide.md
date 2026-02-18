# 每周进化调度器使用指南

## 📋 概述

**每周进化调度器**（Weekly Evolution Scheduler）是超级个体 IP 自我进化系统的核心组件，负责每周一自动执行 IP 进化策略分析和优化建议生成。

### 核心功能

- ✅ **自动数据采集** - 收集上周阅读量、涨粉数、互动率等核心指标
- ✅ **智能进化分析** - 识别高价值和低价值内容，生成深度洞察
- ✅ **策略调整建议** - 基于数据表现提供可执行的优化方案
- ✅ **趋势预测** - 预测下周发展趋势，指导资源投入
- ✅ **定时调度** - 每周一 9:00 自动执行，无需人工干预
- ✅ **通知推送** - 支持飞书/微信 webhook 通知

---

## 🚀 快速开始

### 方式 1：立即执行一次

```python
from open_notebook.skills.weekly_evolution_scheduler import run_weekly_evolution

# 执行一次周度进化
result = await run_weekly_evolution()

print(f"进化得分：{result['evolution_score']}/100")
print(f"核心洞察：{len(result['key_insights'])} 条")
print(f"行动项：{len(result['action_items'])} 项")
```

### 方式 2：启动定时调度器

```python
from open_notebook.skills.weekly_evolution_scheduler import start_weekly_scheduler

# 启动定时调度器（每周一 9:00 自动运行）
await start_weekly_scheduler(run_hour=9, run_minute=0)
```

### 方式 3：命令行执行

```bash
# 立即执行一次
python -m open_notebook.skills.weekly_evolution_scheduler --run-now

# 启动定时调度器（默认每周一 9:00）
python -m open_notebook.skills.weekly_evolution_scheduler

# 自定义运行时间（每周三 10:30）
python -m open_notebook.skills.weekly_evolution_scheduler --hour 10 --minute 30
```

---

## 📊 输出示例

### 控制台输出

```
============================================================
📈 WEEKLY EVOLUTION SUMMARY
============================================================
Period: 2026-02-09 to 2026-02-16
Evolution Score: 75/100
Key Insights: 5 items
Action Items: 4 items

🔍 Top 3 Insights:
  1. 互动率优秀 (5.8%)，内容质量获得认可
  2. 涨粉转化率高 (1.2%)，人设定位清晰
  3. 高频高质内容策略见效，建议保持

✅ Priority Actions:
  1. 加大投放预算，放大增长势能
  2. 在内容中植入系列化钩子，引导关注追更
  3. 建立内容日历，提前规划选题
============================================================
```

### 报告数据结构

```python
{
    "period": "2026-02-09 to 2026-02-16",
    "generated_at": "2026-02-18T13:10:05.362Z",
    "metrics": {
        "total_views": 15000,
        "total_followers_gain": 230,
        "total_engagement": 890,
        "content_count": 7,
        "avg_views_per_content": 2142.86,
        "engagement_rate": 5.93,
        "follower_conversion_rate": 1.53
    },
    "key_insights": [
        "互动率优秀 (5.93%)，内容质量获得认可",
        "涨粉转化率高 (1.53%)，人设定位清晰",
        "高频高质内容策略见效，建议保持"
    ],
    "strategy_adjustments": [
        "加大投放预算，放大增长势能",
        "在内容中植入系列化钩子，引导关注追更"
    ],
    "trend_prediction": "上升趋势，预计下周流量和涨粉将持续增长",
    "action_items": [
        "每条内容结尾添加互动问题或行动号召",
        "规划 3-5 期系列内容，形成连续剧效应",
        "制定下周内容发布计划表"
    ],
    "evolution_score": 75
}
```

---

## 🔧 配置选项

### 基础配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `notebook_id` | `str` | `None` | 保存报告的 Notebook ID |
| `run_hour` | `int` | `9` | 每周运行的小时（24 小时制） |
| `run_minute` | `int` | `0` | 每周运行的分钟 |
| `notification_webhook` | `str` | `None` | 飞书/微信 webhook URL |

### 高级配置

```python
scheduler = WeeklyEvolutionScheduler(notebook_id="your-notebook-id")

# 配置通知 webhook
scheduler.notification_webhook = "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"

# 手动执行
await scheduler.run_weekly_evolution()

# 启动定时调度器
await scheduler.start_scheduler(run_hour=9, run_minute=0)
```

---

## 📁 文件结构

```
open_notebook/skills/
├── weekly_evolution_scheduler.py      # 调度器主文件（271 行）
├── weekly_evolution_analyzer.py       # 进化分析器（243 行）
└── __init__.py                        # 模块导出
```

### 核心类说明

#### 1. WeeklyEvolutionScheduler

```python
class WeeklyEvolutionScheduler:
    """每周进化调度器"""
    
    async def initialize(self) -> None:
        """初始化"""
        
    async def collect_last_week_data(self) -> dict:
        """收集上周数据"""
        
    async def run_weekly_evolution(self) -> dict:
        """执行完整的周度进化流程"""
        
    async def start_scheduler(self, run_hour: int = 9, run_minute: int = 0):
        """启动定时调度器"""
        
    async def close(self) -> None:
        """关闭调度器"""
```

#### 2. WeeklyEvolutionAnalyzer

```python
class WeeklyEvolutionAnalyzer:
    """周度进化分析器"""
    
    async def analyze_weekly_evolution(self, data: dict) -> dict:
        """分析周度数据并生成进化报告"""
        
    def _calculate_metrics(self, data: dict) -> dict:
        """计算核心指标"""
        
    def _generate_insights(self, metrics: dict, content_analysis: dict, data: dict) -> list:
        """生成洞察"""
        
    def _calculate_evolution_score(self, metrics: dict, insights: list) -> int:
        """计算进化得分 (0-100)"""
```

---

## 🎯 进化得分计算逻辑

进化得分满分 100 分，由以下维度组成：

### 1. 互动表现（40 分）
- 互动率 > 5%：40 分
- 互动率 > 2%：20-40 分
- 互动率 < 2%：0-20 分

### 2. 涨粉效率（30 分）
- 转化率 > 1%：30 分
- 转化率 > 0.5%：15-30 分
- 转化率 < 0.5%：0-15 分

### 3. 内容产出（20 分）
- 每周 7 篇以上：20 分
- 每周 3-7 篇：10-20 分
- 每周少于 3 篇：0-10 分

### 4. 正面洞察（10 分）
- 每个正面洞察 +2 分
- 最高 10 分

---

## 💡 最佳实践

### 1. 配合数据追踪系统使用

建议先实现 **PerformanceTracker**（数据追踪系统），记录每次内容发布的数据，这样周度进化分析才能基于真实数据进行。

```python
# 示例：发布内容后记录数据
from open_notebook.skills.performance_tracker import track_content_performance

await track_content_performance(
    platform="xiaohongshu",
    content_id="note_123",
    views=2500,
    likes=180,
    favorites=95,
    comments=42,
    new_followers=28
)
```

### 2. 设置通知提醒

配置飞书/微信 webhook，每周一自动接收进化报告：

```python
scheduler = WeeklyEvolutionScheduler()
scheduler.notification_webhook = "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_HOOK_URL"

await scheduler.start_scheduler()
```

### 3. 保存到 Notebook

将周度报告保存到指定的 Notebook，方便后续回顾和分析：

```python
result = await run_weekly_evolution(notebook_id="your-notebook-id")
```

### 4. 定期复盘

建议每月回顾过去 4 周的进化报告，识别长期趋势和模式：

```python
# 查询历史报告
reports = await repo.query("""
    SELECT * FROM weekly_reports 
    WHERE notebook = $notebook_id 
    ORDER BY generated_at DESC 
    LIMIT 4
""", notebook_id="your-notebook-id")
```

---

## 🔍 故障排查

### 问题 1：导入错误

```
ModuleNotFoundError: No module named 'open_notebook.skills.weekly_evolution_scheduler'
```

**解决方案**：确保已更新 `open_notebook/skills/__init__.py`，添加了正确的导入语句。

### 问题 2：数据库连接失败

```
ConnectionError: Failed to connect to SurrealDB
```

**解决方案**：检查环境变量 `SURREAL_URL` 或 `SURREAL_ADDRESS` 是否正确配置。

### 问题 3：定时任务不执行

**可能原因**：
- Python 进程已退出
- 系统进入休眠状态
- 未正确调用 `start_scheduler()`

**解决方案**：
- 使用后台进程管理器（如 systemd、supervisor）
- 或在服务器上部署为 Docker 服务

---

## 🚀 下一步建议

### 1. 实现 PerformanceTracker（数据追踪系统）⭐ 推荐

当前调度器使用的是模拟数据，需要真实的数据源来提供准确的分析。

**核心功能**：
- 记录每次内容发布的数据（阅读量、点赞、评论、涨粉等）
- 自动计算互动率和转化率
- 建立历史数据库
- 提供数据查询接口

### 2. 可视化报告生成器

将周度报告转换为可视化的 HTML/PDF 格式，包含：
- 趋势图表（阅读量、涨粉数变化曲线）
- 平台对比柱状图
- 词云图（热门话题）
- 雷达图（能力维度评估）

### 3. 内容执行助手

根据周度进化生成的行动项，自动生成内容草稿：
- 基于热门话题生成选题
- 根据高表现内容风格生成文案
- 多平台一键分发
- 发布后自动追踪数据

---

## 📞 技术支持

如有问题或建议，请通过以下方式联系：

- **GitHub Issues**: https://github.com/jackeyunjie/open-notebook/issues
- **邮箱**: 1300893414@qq.com
- **文档**: https://github.com/jackeyunjie/open-notebook/tree/main/docs

---

## 📝 更新日志

### v1.0.0 (2026-02-18)
- ✅ 初始版本发布
- ✅ 实现周度进化分析器
- ✅ 实现每周进化调度器
- ✅ 支持定时任务调度
- ✅ 支持飞书/微信通知
- ✅ 测试验证通过

---

**最后更新**: 2026-02-18  
**维护者**: Open Notebook Team  
**许可证**: MIT
