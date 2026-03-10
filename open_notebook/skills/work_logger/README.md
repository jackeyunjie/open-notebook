# Work Logger Skill - 工作日志与复盘系统 v2.0

自动记录每天的工作，支持定时复盘、目标管理、AI洞察和数据导出。
使用Skill结构化方式和文件夹结构实现对话和上下文工程。

---

## 📁 完整文件夹结构

```
~/.claude/work_logs/          # 工作区根目录
├── sessions/                 # 工作会话记录
│   └── 2026/
│       └── 03/
│           └── 10/
│               ├── 09-00-xxxx.json
│               └── 14-30-yyyy.json
├── daily/                    # 日报
├── weekly/                   # 周报
├── mood/                     # 情绪追踪
├── goals/                    # 目标管理 (G)
│   ├── weekly_goal.json
│   ├── okr_objective.json
│   └── okr_key_result.json
├── weekly_plans/             # 周计划
├── exports/                  # 导出文件 (H)
│   ├── daily-20260310.md
│   ├── weekly-2026-10.md
│   └── export-20260310.json
├── templates/                # 复盘模板
└── .scheduler_config.json    # 调度器配置
```

---

## 🚀 快速使用

### 开始工作会话

```python
from open_notebook.skills.work_logger import WorkLoggerSkill
from open_notebook.skills.base import SkillConfig, SkillContext

config = SkillConfig(
    skill_type="work_logger",
    name="My Logger",
    parameters={
        "workspace_path": "~/.claude/work_logs",
        "project_paths": ["~/projects/open-notebook"],
        "current_action": "start_session",
        "session_title": "开发新功能",
        "session_type": "coding",
        "session_project": "open-notebook"
    }
)

skill = WorkLoggerSkill(config)
result = await skill.run(SkillContext(skill_id="xxx", trigger_type="manual"))
```

---

## 📋 功能模块

### A. 核心功能 (A)
| Action | 说明 |
|--------|------|
| `start_session` | 开始工作会话，自动追踪Git和文件活动 |
| `end_session` | 结束会话，计算时长和统计 |
| `get_daily` | 获取今日工作摘要 |
| `get_weekly` | 获取本周工作统计 |
| `review_daily` | 生成每日复盘模板和问题 |
| `export_daily` | 导出Markdown格式日报 |

### B. 定时调度 (B)
| Action | 说明 |
|--------|------|
| `check_reviews` | 检查哪些复盘待完成 |
| 自动触发 | 每日18:00复盘，周五17:00周复盘，每月1日月复盘 |

### C. 情绪追踪 (C)
| Action | 说明 |
|--------|------|
| `log_mood` | 记录情绪状态 |
| `get_mood_report` | 生成情绪报告 |
| `mood_check_in` | 情绪检查交互 |

### G. 目标管理 (G)
```python
from open_notebook.skills.work_logger import GoalTracker

tracker = GoalTracker("~/.claude/work_logs")

# 创建周目标
tracker.create_weekly_goal(
    title="完成Work Logger开发",
    description="实现G/F/H功能",
    week_id="2026-10"
)

# 创建OKR
okr = tracker.create_okr(
    objective="构建完整工作日志系统",
    key_results=["实现核心功能", "添加AI洞察", "完成导出功能"],
    quarter="2026-Q1"
)

# 更新进度
tracker.update_progress(goal_id, 75)

# 获取周报
report = tracker.get_weekly_report("2026-10")
```

### F. AI洞察 (F)
```python
from open_notebook.skills.work_logger import AIInsightsEngine

engine = AIInsightsEngine("~/.claude/work_logs")

# 分析工作模式
patterns = engine.analyze_work_patterns(days=30)

# 获取效率洞察
insights = engine.get_efficiency_insights()

# 生成个性化建议
recommendations = engine.generate_recommendations()

# 获取生产力指标
metrics = engine.get_productivity_metrics(days=7)

# 生成AI周报
report = engine.generate_weekly_ai_report()
```

### H. 导出增强 (H)
```python
from open_notebook.skills.work_logger import ExportManager, EmailConfig

manager = ExportManager("~/.claude/work_logs")

# 导出Markdown
md_report = manager.export_daily_markdown()
weekly_md = manager.export_weekly_markdown()

# 导出JSON
json_data = manager.export_json(days=7)

# 准备第三方导出
notion_data = manager.prepare_notion_export()
feishu_data = manager.prepare_feishu_export()

# 发送邮件报告
config = EmailConfig(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    username="your@email.com",
    password="your_password",
    from_address="your@email.com",
    to_addresses=["boss@company.com"]
)
manager.send_daily_email(config)
```

---

## 🔧 核心组件

### ContextEngine - 上下文引擎
自动监控Git活动和文件变化：
```python
from open_notebook.skills.work_logger import ContextEngine

engine = ContextEngine("/path/to/project")
snapshot = engine.build_context_snapshot()
```

### ReviewScheduler - 复盘调度
管理复盘计划和模板：
```python
from open_notebook.skills.work_logger import ReviewScheduler

scheduler = ReviewScheduler("~/.claude/work_logs")
if scheduler.is_review_due("daily"):
    questions = scheduler.get_review_questions("daily")
```

### WorkLoggerScheduler - 定时任务调度器
自动触发复盘和提醒：
```python
from open_notebook.skills.work_logger import WorkLoggerScheduler

scheduler = WorkLoggerScheduler("~/.claude/work_logs")
scheduler.on_daily_review(lambda: print("Time for daily review!"))
await scheduler.start()
```

### MoodTracker - 情绪追踪
追踪工作状态和情绪：
```python
from open_notebook.skills.work_logger import MoodTracker, MoodLevel, EnergyLevel, FocusLevel

tracker = MoodTracker("~/.claude/work_logs")

tracker.log_mood(
    mood=MoodLevel.GOOD,
    energy=EnergyLevel.HIGH,
    focus=FocusLevel.FOCUSED,
    stress=3,
    satisfaction=8
)

insights = tracker.get_weekly_insights()
report = tracker.generate_mood_report(days=7)
```

### GoalTracker - 目标管理 (G)
管理OKR和周目标：
```python
from open_notebook.skills.work_logger import GoalTracker, GoalType

tracker = GoalTracker("~/.claude/work_logs")

# 周目标
tracker.create_weekly_goal(title="完成开发", description="实现功能")

# OKR
tracker.create_okr(
    objective="提升效率",
    key_results=["每日3个番茄", "完成5个任务"],
    quarter="2026-Q1"
)

# 进度追踪
tracker.update_progress(goal_id, 75)
progress = tracker.get_goal_progress()
```

### AIInsightsEngine - AI洞察 (F)
智能分析工作模式：
```python
from open_notebook.skills.work_logger import AIInsightsEngine

engine = AIInsightsEngine("~/.claude/work_logs")

# 工作模式识别
patterns = engine.analyze_work_patterns(days=30)

# 效率分析
insights = engine.get_efficiency_insights()

# 生产力指标
metrics = engine.get_productivity_metrics()
```

### ExportManager - 导出管理 (H)
多格式导出支持：
```python
from open_notebook.skills.work_logger import ExportManager

manager = ExportManager("~/.claude/work_logs")

# Markdown
manager.export_daily_markdown()
manager.export_weekly_markdown()

# JSON
manager.export_json(days=7)

# 第三方平台
manager.prepare_notion_export()
manager.prepare_feishu_export()

# 邮件
manager.send_daily_email(config)
manager.send_weekly_email(config)
```

---

## 📝 命令行演示

```bash
# 基础功能 (A/B/C)
uv run python scripts/work_logger_demo.py start
uv run python scripts/work_logger_demo.py daily
uv run python scripts/work_logger_demo.py mood
uv run python scripts/work_logger_demo.py check

# 测试新功能 (G/F/H)
uv run python scripts/test_gfh_features.py

# 调度器测试
uv run python scripts/test_scheduler.py
```

---

## 🔄 自动复盘流程

1. **Daily (每日18:00)**
   - 自动生成复盘问题
   - 展示今日统计
   - 引导对话式复盘

2. **Weekly (每周五17:00)**
   - 汇总本周数据
   - 生成周复盘模板
   - 分析模式和趋势

3. **Monthly (每月1日10:00)**
   - 月度成就回顾
   - 技能成长记录
   - 战略重点规划

---

## 📊 AI洞察报告示例

```markdown
# AI-Powered Weekly Report

## Productivity Metrics (Last 7 Days)
- Total Sessions: 12
- Total Time: 15.5 hours
- Avg Session: 77 minutes
- Best Day: Tuesday
- Best Hour: 10:00
- Consistency: 85%
- Deep Work Ratio: 60%
- Trend: accelerating

## Identified Patterns
1. **Productivity Peak**
   - Confidence: 80%
   - Peak hours: 10:00, 14:00, 09:00
   - Recommendation: Schedule important tasks during 10:00-11:00

2. **Mood-Productivity Correlation**
   - Correlation: r=0.89
   - Strong positive correlation detected
   - Recommendation: Prioritize emotional well-being before important work

## Efficiency Analysis
- Time Management: 65/100
  - Bottleneck: High variability in session length
- Focus Quality: 80/100
  - Finding: Strong ability to maintain long focus sessions
- Energy Management: 72/100

## Top Recommendations
- [HIGH] Optimize your peak hours
- [HIGH] Prioritize emotional well-being
- [MEDIUM] Improve focus sessions
```

---

## 💡 使用场景

### 场景1：开始一天工作
```
用户: 开始工作，今天要开发Skill系统
Claude: [启动session，自动检测Git状态]
       [开始] 工作会话: 开发Skill系统
       最近1小时: 0次提交, 8个文件修改
```

### 场景2：设置周目标
```
用户: 设置本周OKR
Claude: [创建OKR]
       Objective: 完成Work Logger v2.0
       KR1: 实现目标管理 (G)
       KR2: 添加AI洞察 (F)
       KR3: 完成导出功能 (H)
```

### 场景3：AI复盘
```
Claude: # AI-Powered Weekly Report
       - 本周会话: 15个
       - 最佳时段: 10:00-11:00
       - 发现: 情绪与生产力高度相关 (r=0.89)
       - 建议: 在高效时段安排重要任务
```

### 场景4：导出分享
```
用户: 导出本周报告
Claude: [生成Markdown报告]
       [准备Notion格式]
       [发送邮件给团队]
```

---

## 🔮 未来扩展

- [ ] IDE集成（自动检测代码编辑）
- [ ] 团队协作功能
- [ ] 更多第三方平台集成
- [ ] 机器学习预测
- [ ] 自定义报表模板
