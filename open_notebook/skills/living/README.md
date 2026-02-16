# 活体知识系统 (Living Knowledge System)

基于生物学启发的智能体架构，将知识管理系统类比为人体组织，实现自组织、自运行的有机系统。

## 核心设计理念

```
软件组件    →    生物类比
─────────────────────────────────
Skill      →    Cell (细胞)      基本功能单元
Agent      →    Tissue (组织)     协作单元组合
System     →    Organ (器官)      复杂功能系统
Flow       →    Meridian (经络)   数据/控制/时序流
Trigger    →    Acupoint (穴位)   外部刺激接入点
```

## 五层架构

```
┌─────────────────────────────────────────────────────────┐
│                    活体知识系统                           │
├─────────────────────────────────────────────────────────┤
│  器官层 (Organs)     P0/P1/P2/P3 复杂功能系统              │
├─────────────────────────────────────────────────────────┤
│  组织层 (Tissues)    Agent 协作单元                      │
├─────────────────────────────────────────────────────────┤
│  细胞层 (Cells)      Skill 基本功能单元                   │
├─────────────────────────────────────────────────────────┤
│  经络层 (Meridians)  数据/控制/时序流                     │
├─────────────────────────────────────────────────────────┤
│  穴位层 (Acupoints)  Agently/时间/事件触发器              │
└─────────────────────────────────────────────────────────┘
```

## 快速开始

### 1. 创建 Skill (细胞)

```python
from open_notebook.skills.living import LivingSkill, SkillTemporal, SkillResource

skill = LivingSkill(
    skill_id="my.skill",
    name="My Skill",
    description="A living skill",
    temporal=SkillTemporal(
        cron="0 */4 * * *",  # 每4小时执行
        timeout=timedelta(minutes=10)
    ),
    resources=[
        SkillResource(
            name="executor",
            type="python",
            content="""
async def execute():
    context = globals().get('context', {})
    return {"result": "success"}
""",
            entry_point="execute"
        )
    ]
)

# 执行 skill
result = await skill.invoke({"input": "data"})
```

### 2. 创建 Agent (组织)

```python
from open_notebook.skills.living import AgentTissue, AgentCoordination, CoordinationPattern

agent = AgentTissue(
    agent_id="my.agent",
    name="My Agent",
    description="A tissue of skills",
    purpose="Complete a specific task",
    skills=["skill.1", "skill.2", "skill.3"],
    coordination=AgentCoordination(
        pattern=CoordinationPattern.PARALLEL,  # 并行执行
        max_parallel=3
    )
)

# 执行 agent
result = await agent.execute(context={"input": "data"})
```

### 3. 创建 Meridian (经络)

```python
from open_notebook.skills.living import DataMeridian, MeridianSystem

# 创建数据经络
data_meridian = DataMeridian(
    meridian_id="data.flow",
    name="Data Flow",
    capacity=1000
)

# 注册到系统
MeridianSystem.register(data_meridian)

# 发送数据
await data_meridian.send(
    source="sender_id",
    payload={"data": "value"},
    destination="receiver_id"
)

# 广播
await data_meridian.broadcast(
    source="sender_id",
    payload={"data": "value"}
)
```

### 4. 创建 Acupoint (穴位)

```python
from open_notebook.skills.living import acupoint, TriggerType

@acupoint(
    name="content_created",
    trigger_type=TriggerType.EVENT,
    target_agents=["my.agent"],
    meridians=["data.flow"],
    cooldown_seconds=60
)
async def on_content_created(event_data):
    """当内容创建时触发"""
    print(f"Content created: {event_data}")
    return {"status": "processed"}

# 手动触发
from open_notebook.skills.living.acupoint_trigger import TriggerRegistry
trigger = TriggerRegistry.get("__main__.on_content_created")
await trigger.activate({"content": "hello"})
```

## 核心概念详解

### Skill 时序属性 (SkillTemporal)

| 属性 | 类型 | 说明 |
|------|------|------|
| `cron` | str | Cron 表达式，如 `"0 9 * * *"` |
| `interval` | timedelta | 执行间隔 |
| `delay` | timedelta | 首次执行延迟 |
| `timeout` | timedelta | 执行超时 |
| `timezone` | str | 时区，默认 `"UTC"` |
| `max_retries` | int | 最大重试次数 |

### Skill 生命周期 (SkillLifecycle)

状态流转：
```
IDLE → RUNNING → COMPLETED/FAILED → IDLE
  ↓       ↓
PAUSED ←──┘
```

- `IDLE`: 等待执行
- `RUNNING`: 正在执行
- `COMPLETED`: 成功完成
- `FAILED`: 执行失败
- `PAUSED`: 已暂停
- `EXPIRED`: 已过期
- `DISABLED`: 已禁用

### Agent 协调模式 (CoordinationPattern)

| 模式 | 说明 |
|------|------|
| `SEQUENCE` | 顺序执行，一个接一个 |
| `PARALLEL` | 并行执行，同时运行 |
| `PIPELINE` | 管道模式，前一输出作为后一输入 |
| `CONDITIONAL` | 条件执行，满足条件才执行 |
| `LOOP` | 循环执行，直到条件满足 |
| `VOTING` | 投票模式，多个结果投票决定 |
| `RACE` | 竞争模式，第一个完成的获胜 |

### Meridian 流动类型 (FlowType)

| 类型 | 说明 |
|------|------|
| `DATA` | 数据流，传输信息 |
| `CONTROL` | 控制流，传输命令 |
| `TEMPORAL` | 时序流，同步时间 |
| `ENERGY` | 能量流，资源分配 |

### Trigger 类型 (TriggerType)

| 类型 | 说明 |
|------|------|
| `TEMPORAL` | 时间触发，Cron/间隔 |
| `EVENT` | 事件触发，数据到达/状态变更 |
| `CONDITION` | 条件触发，阈值/模式匹配 |
| `MANUAL` | 手动触发，API/UI/CLI |
| `AGENTLY` | Agently 工作流触发 |
| `WEBHOOK` | Webhook 外部触发 |

## 完整示例: P0 感知系统

```python
import asyncio
from open_notebook.skills.living.examples.p0_perception_organ import initialize_p0_organ

async def main():
    # 初始化完整的 P0 感知器官
    p0 = await initialize_p0_organ()

    # 获取组件
    skills = p0["skills"]      # 4个感知技能
    agent = p0["agent"]        # P0 代理
    meridians = p0["meridians"] # 数据/控制经络
    triggers = p0["triggers"]   # 触发器

    # 执行单个技能
    pain_scanner = skills[0]
    result = await pain_scanner.invoke({
        "platform_data": {"comments": [...]}
    })

    # 执行整个 Agent
    result = await agent.execute()

asyncio.run(main())
```

## 架构优势

1. **自组织**: Skill 细胞可自主决定何时执行（基于时序）
2. **自愈合**: Agent 组织监控 Skill 健康状态，自动重试失败任务
3. **可扩展**: 新增 Skill/Agent 只需注册到相应 Registry
4. **松耦合**: Meridians 实现组件间解耦通信
5. **可观测**: 完整的生命周期和指标追踪

## 系统启动流程

```python
from open_notebook.skills.living import (
    MeridianSystem,
    TemporalScheduler,
)

async def start_system():
    """启动活体知识系统"""

    # 1. 启动所有经络
    await MeridianSystem.start_all()

    # 2. 启动时序调度器
    scheduler = TemporalScheduler()
    await scheduler.start()

    # 3. 系统运行中...
    print("Living Knowledge System started")

async def stop_system():
    """停止系统"""
    await MeridianSystem.stop_all()
```

## 文件结构

```
living/
├── __init__.py              # 模块导出
├── README.md                # 本文档
├── skill_cell.py            # 细胞层 - Skill 实现
├── agent_tissue.py          # 组织层 - Agent 实现
├── meridian_flow.py         # 经络层 - Flow 实现
├── acupoint_trigger.py      # 穴位层 - Trigger 实现
└── examples/
    ├── __init__.py
    └── p0_perception_organ.py  # P0 完整示例
```

## 下一步

1. 将 P1 (判断层)、P2 (关系层)、P3 (进化层) 重构为 Living System
2. 集成 Agently Adapter 实现工作流触发
3. 添加 Webhook Server 接收外部事件
4. 实现持久化存储 (SurrealDB 集成)
