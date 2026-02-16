# P0 Daily Sync 协调器实现完成

## 新增文件

```
open_notebook/skills/
├── p0_agents.py          # 4个P0 Agent (Q1P0-Q4P0)
├── p0_orchestrator.py    # Daily Sync 协调器
└── __init__.py           # 已更新导出
```

---

## 核心组件

### 1. P0OrchestratorAgent - 协调中枢
- 触发4个P0 Agent并行扫描
- 收集 DailySyncReport
- 合成跨象限信号 (Cross-Quadrant Signals)
- 管理 SharedMemory 共享状态

### 2. SharedMemory - 共享记忆
- P0层系统状态存储
- 信号持久化 (默认48小时TTL)
- 历史会话查询

### 3. 跨象限模式检测

| 模式 | 检测逻辑 | 优先级 | 路由目标 |
|------|----------|--------|----------|
| Pain+Trend | 紧急痛点 + 热门趋势 | 🔴 CRITICAL | Q1P1, Q3P1 |
| Emotion+Scene | 强烈情绪 + 具体场景 | 🟡 HIGH | Q2P1, Q4P1 |
| Pain+Emotion | 痛点 + 高情绪强度 | 🟡 HIGH | Q1P1, Q2P1 |

---

## 使用方式

### 运行 Daily Sync:

```python
from open_notebook.skills import P0OrchestratorAgent, SkillConfig

config = SkillConfig(
    skill_type="p0_orchestrator",
    name="P0 Orchestrator",
    parameters={
        "agents_to_run": ["Q1P0", "Q2P0", "Q3P0", "Q4P0"],
        "enable_cross_synthesis": True,
        "min_confidence_threshold": 0.7,
        "target_notebook_id": "notebook:system"
    }
)

orchestrator = P0OrchestratorAgent(config)
result = await orchestrator.execute(context)
```

### 获取活跃信号:

```python
# 从 SharedMemory 读取
signals = orchestrator.get_active_signals()

# 获取最近会话
sessions = orchestrator.get_recent_sessions(count=5)
```

---

## Daily Sync 流程

```
Hour 0:00  ┌─────────────────┐
           │  Orchestrator   │
           │   triggers      │
           │  all 4 agents   │
           └────────┬────────┘
                    │
     ┌──────────────┼──────────────┐
     │              │              │
     ▼              ▼              ▼
  Q1P0           Q2P0           Q3P0           Q4P0
(Pain)        (Emotion)       (Trend)       (Scene)
     │              │              │              │
     └──────────────┴──────────────┴──────────────┘
                    │
                    ▼
           ┌─────────────────┐
           │   Synthesize    │
           │ Cross-Quadrant  │
           │    Signals      │
           └────────┬────────┘
                    │
                    ▼
           ┌─────────────────┐
           │  Store to       │
           │  SharedMemory   │
           └────────┬────────┘
                    │
                    ▼
              ┌──────────┐
              │   P1     │
              │  Layer   │ (Value Judgment)
              └──────────┘
```

---

## 下一步选择

**A.** 实现 P1 层 Agent（Q1P1 价值判断, Q2P1 立场对齐等）

**B.** 添加定时调度（让 Daily Sync 自动每天运行）

**C.** 实现前端 Dashboard（可视化展示跨象限信号）

你倾向哪个方向？
