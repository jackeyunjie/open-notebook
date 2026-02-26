# Open Notebook Skills 完整能力展示

**版本**: v2.0  
**更新日期**: 2026-02-25  
**总计**: 10 个 AI Skills

---

## 📦 Skills 总览

Open Notebook 提供 **10 个强大的 AI Skills**，覆盖知识管理的完整工作流。

```
Phase 1 (核心体验)          Phase 2 (差异化超越)        Bonus (创新功能)
├─ SmartSourceAnalyzer     ├─ KnowledgeConnector      ├─ VideoGenerator
├─ CitationEnhancer        ├─ AutoPodcastPlanner      ├─ PPTGenerator
└─ MultiModelRouter        └─ ResearchAssistant       └─ MindMapGenerator
                                                    └─ MeetingSummarizer
```

---

## 🎯 Phase 1: 核心体验（3 个 Skills）

### 1️⃣ SmartSourceAnalyzer - 智能 Source 分析器

**一句话介绍**: 上传文档后自动提取关键信息，让内容理解更高效

**核心能力**:
- ✅ 自动摘要生成（200-500 字可配置）
- ✅ 主题标签提取（3-5 个核心标签）
- ✅ 实体识别（人名/组织/技术/地点）
- ✅ 内容大纲生成（目录式结构）
- ✅ 内容类型识别（论文/新闻/教程/文档）

**使用场景**:
```
📚 学术论文 → 摘要 + 关键词 + 研究方法
📰 新闻报道 → 摘要 + 关键人物 + 事件脉络
💻 技术教程 → 摘要 + 技术栈 + 步骤大纲
📊 行业报告 → 摘要 + 核心数据 + 趋势判断
```

**API 端点**:
```bash
POST /api/v1/sources/analyze    # 分析单个 Source
GET  /api/v1/sources/{id}/summary  # 获取摘要
```

**实际效果示例**:
```markdown
输入：一篇 5000 字的 AI 编程工具评测文章

输出:
📝 摘要（300 字）: 
"本文对比了 5 款主流 AI 编程工具..."

🏷️ 标签: #AI 编程 #Copilot #Cursor #效率工具 #开发者工具

👥 实体:
- 工具：GitHub Copilot, Cursor, Codeium
- 公司：Microsoft, Anthropic, Google
- 技术：LLM, RAG, Code Completion

📑 大纲:
1. 引言
2. 工具横评
3. 性能对比
4. 最佳实践
5. 未来趋势
```

---

### 2️⃣ CitationEnhancer - 引用增强器

**一句话介绍**: 为 AI 回答添加精准的段落级引用，让每个观点都有据可查

**核心能力**:
- ✅ 段落级精确引用 `[cite_1]` `[cite_2]`
- ✅ 引用跳转（点击跳转到原文位置）
- ✅ 悬浮显示上下文（前 100 字）
- ✅ 多格式导出（APA/MLA/GB/T 7714）
- ✅ 引用溯源图（显示引用关系链）

**使用场景**:
```
🎓 学术研究 → 精准引用，避免抄袭
📝 文章写作 → 标注来源，提升可信度
⚖️ 法律文件 → 精确到条款项的引用
🔬 科学报告 → 数据来源可追溯
```

**引用格式示例**:
```markdown
根据最新研究[cite_1]，使用 AI 编程工具可以提升 55% 的效率。
另一项针对 1000 名开发者的调查显示[cite_2]，满意度达到 92%。

[cite_1]: 《GitHub Copilot 效能研究》- 第 3 页，第 2 段
  "实验组使用 Copilot 后，编码速度提升 55%，Bug 率降低 30%..."

[cite_2]: 《2026 开发者工具调查报告》- 第 15 页，表格 2
  "N=1000, 满意度 92%, 推荐度 89%..."
```

**API 端点**:
```bash
POST /api/v1/notebooks/{id}/ask     # 带引用的问答
GET  /api/v1/citations/export       # 导出引用（多格式）
```

---

### 3️⃣ MultiModelRouter - 多模型智能路由

**一句话介绍**: 根据任务类型自动选择最优 AI 模型，成本降低 40%

**支持的 16+ 模型**:
```
国内模型:
├─ Qwen3.5（通义千问）- 中文理解强
├─ Qwen3.5-Turbo - 成本低
├─ Qwen3.5-128K - 长文本处理
├─ HunYuan（腾讯混元）
└─ ERNIE Bot（百度文心）

国际模型:
├─ Claude 3.5 Sonnet - 代码/分析强
├─ Claude 3.5 Haiku - 快速响应
├─ Claude 3 Opus - 最强推理
├─ GPT-4o - 多模态
├─ GPT-4 Turbo
└─ Llama 3（Groq）- 超快响应

专用模型:
├─ Seedance - 视频生成
├─ Runway - 视频生成
├─ Pika - 视频生成
└─ Kling - 视频生成
```

**智能路由策略**:
```python
if 任务类型 == "中文内容":
    return "Qwen3.5-Turbo"  # 成本低，中文强
elif 任务类型 == "代码生成":
    return "Claude 3.5 Sonnet"  # 代码能力顶尖
elif 任务类型 == "复杂推理":
    return "Claude 3.5 Sonnet"  # 逻辑推理强
elif 任务类型 == "快速响应":
    return "Groq Llama3"  # 延迟 <100ms
elif 任务类型 == "长文本":
    return "Qwen3.5-128K"  # 整本书分析
```

**成本对比**:
```
固定使用 Claude 3.5: ¥5/M tokens
智能路由优化后：¥3/M tokens
节省：40%
```

**API 端点**:
```bash
POST /api/v1/models/route    # 获取模型推荐
GET  /api/v1/models/list     # 获取可用模型列表
```

---

## 🚀 Phase 2: 差异化超越（3 个 Skills）

### 4️⃣ KnowledgeConnector - 知识图谱连接器

**一句话介绍**: AI 自动构建知识图谱，发现跨文档的隐藏关联

**核心能力**:
- ✅ 实体识别与标准化
- ✅ 关系抽取（因果/从属/对比/时间序列）
- ✅ 跨文档知识融合
- ✅ 交互式可视化知识图谱
- ✅ 基于图谱的智能问答

**知识图谱示例**:
```
AI 编程工具发展史:

2021 ─→ GitHub Copilot 发布
         │
         ├─→ 引发争议（开源代码训练）
         │
2022 ─→ Tabnine 崛起
         │
         ├─→ 本地部署选项
         │
2023 ─→ Cursor IDE 诞生
         │
         ├─→ 首个 AI 原生编辑器
         │
2024 ─→ Codeium 免费开放
         │
         └─→ 市场份额快速提升

人物关系网络:
Dario Amodei (Anthropic CEO)
    │
    ├─→ 前 OpenAI 副总裁
    │
    └─→ 创立 Anthropic
         │
         ├─→ Claude 系列模型
         └─→ Constitutional AI 理念
```

**应用场景**:
```
🎓 文献综述 → 发现论文之间的引用关系
🔍 竞品分析 → 梳理公司发展脉络
📊 行业研究 → 绘制产业链图谱
🧠 学习新知 → 建立概念之间的联系
```

**API 端点**:
```bash
POST /api/v1/skills/knowledge/graph    # 生成知识图谱
POST /api/v1/skills/knowledge/query    # 图谱问答
GET  /api/v1/skills/knowledge/status   # 获取能力说明
```

---

### 5️⃣ AutoPodcastPlanner - 智能播客策划器

**一句话介绍**: 根据内容自动设计最优播客方案，支持 7 种格式和 1-4 人灵活配置

**7 种播客格式**:

| 格式 | 说话人数 | 时长 | 适用场景 |
|------|---------|------|---------|
| Monologue（独白） | 1 人 | 5-10 分钟 | 个人观点、故事叙述 |
| Interview（访谈） | 2 人 | 15-20 分钟 | 专家对话、技术教程 |
| Panel（圆桌） | 3-4 人 | 20-30 分钟 | 深度分析、多方观点 |
| Debate（辩论） | 2-4 人 | 15-25 分钟 | 争议话题、对立观点 |
| Storytelling（叙事） | 2 人 | 10-15 分钟 | 历史事件、案例研究 |
| Educational（教育） | 1-2 人 | 10-20 分钟 | 教学课程、技能培训 |
| News（新闻） | 1-2 人 | 5-10 分钟 | 资讯播报、行业动态 |

**智能策划输出**:
```markdown
# 播客策划方案

## 基本信息
标题：AI 如何改变编程的未来？
格式：Interview（访谈）
时长：18 分钟
说话人：主持人 + AI 专家

## 结构大纲

### Hook（0:00-1:30）
开场问题："如果 AI 能写代码，程序员会失业吗？"

### Part 1: 现状分析（1:30-6:00）
- GitHub Copilot 的普及率
- 实际效率提升数据
- 开发者的真实反馈

### Part 2: 深度讨论（6:00-12:00）
- AI 的局限性在哪里？
- 哪些工作不会被替代？
- 未来的人机协作模式

### Part 3: 展望未来（12:00-16:00）
- 5 年后的编程工作
- 教育体系需要如何改变
- 给开发者的建议

### Closing（16:00-18:00）
总结要点 + 行动号召

## 角色设定
主持人：好奇、追问、代表普通开发者
专家：理性、数据驱动、平衡观点

## 语气节奏
轻松但专业，适当幽默，避免过于技术化
```

**API 端点**:
```bash
POST /api/podcasts/plan              # 生成策划方案
POST /api/podcasts/suggest-formats   # 获取格式推荐
POST /api/podcasts/plan-and-generate # 一键策划并生成
```

---

### 6️⃣ ResearchAssistant - 深度研究助手

**一句话介绍**: 像专业研究员一样进行多轮迭代研究，输出结构化报告

**核心能力**:
- ✅ 多轮迭代研究（1-5 轮深度调研）
- ✅ 子查询自动生成（分解研究问题）
- ✅ 交叉验证（多源验证发现）
- ✅ 置信度评分（0-1.0 分数）
- ✅ 结构化报告输出

**研究流程示例**:
```
用户提问："AI 对程序员就业市场的影响是什么？"

第 1 轮：初步探索
├─ 检索现有研究报告
├─ 收集统计数据
└─ 识别主要观点

第 2 轮：深入分析
├─ 分解为子问题：
│   ├─ 岗位需求变化？
│   ├─ 技能要求变化？
│   └─ 薪资水平影响？
├─ 分别检索每个子问题
└─ 交叉验证发现

第 3 轮：补充缺口
├─ 识别知识缺口
│   └─ 缺少中国市场的數據
├─ 针对性补充检索
└─ 更新结论

输出报告:
├─ Executive Summary
├─ Key Findings (带置信度)
├─ Knowledge Gaps
└─ Recommendations
```

**报告结构示例**:
```markdown
# Executive Summary
AI 正在重塑程序员就业市场：初级岗位需求下降 30%，
但 AI 相关岗位增长 150%。适应者薪资提升 40%。

# Key Findings

## Finding 1: 岗位需求结构性变化 (置信度：0.92)
- 初级 CRUD 岗位：↓30%
- AI 工程化岗位：↑150%
- 提示词工程师：从 0 到 5000+ 岗位

证据来源：[cite_1], [cite_2], [cite_3]
验证状态：✅ 已验证

## Finding 2: 技能要求升级 (置信度：0.85)
- 必备技能：AI 工具使用 + 系统设计
- 淘汰技能：纯语法记忆 + 重复编码

证据来源：[cite_4], [cite_5]
验证状态：✅ 已验证

## Finding 3: 薪资分化加剧 (置信度：0.68)
- 适应 AI 者：+40%
- 拒绝 AI 者：-15%

证据来源：[cite_6]
验证状态：⚠️ 待更多数据验证

# Knowledge Gaps
- 缺少 3-5 年长期追踪数据
- 中国市场特定研究不足

# Recommendations
1. 立即开始学习 AI 工具
2. 培养系统设计和架构能力
3. 关注 AI 无法替代的技能（沟通/创意）
```

**API 端点**:
```bash
POST /api/v1/skills/research/conduct  # 执行深度研究
GET  /api/v1/skills/research/status   # 获取能力说明
```

---

## 🎁 Bonus: 创新功能（4 个 Skills）

### 7️⃣ VideoGenerator - 视频生成器

**一句话介绍**: 将内容转为 AI 视频，支持 6 种风格和多提供商

**6 种视频风格**:
- 🎓 Educational（教育）- 教学课程
- 📖 Narrative（叙事）- 故事叙述
- 📊 Visualization（可视化）- 数据展示
- 📰 News（新闻）- 资讯播报
- 🎙️ Interview（访谈）- 专家对话
- ⚡ Short（短视频）- 社交媒体

**输出示例**:
```markdown
# 视频脚本：AI 编程工具入门

## Scene 1: Hook（0:00-0:15）
视觉：动态文字动画
配音："想知道如何用 AI 提升 3 倍编码效率吗？"
字幕：AI 编程工具入门指南

## Scene 2: 介绍（0:15-1:00）
视觉：工具 Logo 轮播
配音："今天我们来对比 5 款主流 AI 编程工具..."
字幕：GitHub Copilot | Cursor | Codeium | ...

## Scene 3: 实战演示（1:00-3:00）
视觉：屏幕录制 + 代码高亮
配音："看我如何用 Copilot 自动生成这个函数..."
字幕：效率提升 55%

## Scene 4: 总结（3:00-3:30）
视觉：要点列表
配音："记住这 3 个最佳实践..."
字幕：1.写清晰注释 2.审查每行代码 3.配合测试

## Scene 5: CTA（3:30-4:00）
视觉：订阅按钮动画
配音："点赞关注，下期讲高级技巧！"
```

**API 端点**:
```bash
POST /api/v1/skills/videos/generate  # 生成视频
GET  /api/v1/skills/videos/styles    # 获取风格列表
```

---

### 8️⃣ PPTGenerator - PPT 生成器

**一句话介绍**: 一键将内容转为专业演示文稿

**输出格式**:
- Markdown（可导入 Marp/Slidev）
- PowerPoint (.pptx)
- PDF 导出

**PPT 结构示例**:
```markdown
---
marp: true
theme: gaia
class: lead
---

# AI 编程工具实战指南

副标题：提升 55% 编码效率的秘密武器

演讲者：张三
日期：2026-02-25

---

# 目录

1. 为什么需要 AI 编程工具？
2. 主流工具对比
3. 实战演示
4. 最佳实践
5. Q&A

---

# 效率提升数据

## GitHub Copilot 官方研究
- 编码速度：**+55%** 🚀
- Bug 率：**-30%** ✅
- 满意度：**92%** ⭐

> 投资回报率：191x

---

# 工具横评

| 工具 | 代码质量 | 速度 | 价格 |
|------|---------|------|------|
| Cursor | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | $20/月 |
| Copilot | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $10/月 |
| Codeium | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 免费 |

---

# 最佳实践清单

## ✅ DO
1. 写清晰的注释
2. 审查每一行 AI 代码
3. 配合单元测试

## ❌ DON'T
1. 盲目复制粘贴
2. 完全依赖 AI
3. 处理敏感数据

---

# 总结

## 关键要点
1. AI 是副驾驶，你才是机长
2. 立即开始使用，边用边学
3. 培养 AI 无法替代的能力

## 行动号召
今天就安装一个 AI 工具，尝试完成一个小功能！
```

---

### 9️⃣ MindMapGenerator - 思维导图生成器

**一句话介绍**: 将复杂内容转为清晰的思维导图

**输出格式**:
- Markdown（层级列表）
- XMind (.xmind)
- FreeMind (.mm)
- PNG/SVG 图片

**思维导图示例**:
```markdown
# AI 编程工具知识体系

## 核心概念
- AI Pair Programming
- Code Completion
- Natural Language to Code
- Chat with Codebase

## 主流工具
- GitHub Copilot
  - 插件形式
  - $10/月
  - 适合：企业用户
- Cursor IDE
  - 完整编辑器
  - $20/月
  - 适合：追求极致体验
- Codeium
  - 免费开源
  - 适合：学生/个人开发者

## 最佳实践
- 使用前
  - 明确意图
  - 写清晰注释
- 使用中
  - 审查代码
  - 迭代优化
- 使用后
  - 单元测试
  - 代码审查

## 未来趋势
- 多模态 AI
- 自主 Agent
- 低代码 + AI 融合
```

---

### 🔟 MeetingSummarizer - 会议纪要生成器

**一句话介绍**: 会议录音/文字记录转结构化纪要，自动提取行动项

**7 种会议类型**:
- standup（每日站会）
- review（评审会议）
- planning（规划会议）
- brainstorm（头脑风暴）
- one_on_one（一对一）
- client（客户会议）
- board（董事会）

**输出内容**:
1. **正式会议纪要** (Markdown)
2. **跟进邮件草稿**
3. **行动项追踪表**
4. **决策记录**

**会议纪要示例**:
```markdown
# 会议纪要：产品规划会议

## 基本信息
日期：2026-02-25
时间：14:00-15:30
参会人：张三、李四、王五
类型：planning

## 关键议题

### 议题 1: Q2 产品路线图
决策：优先开发 AI 集成功能
理由：市场需求强烈，竞品已上线
利益相关者：产品部、研发部

### 议题 2: 资源分配
决策：增加 2 名后端工程师
理由：当前人力不足，项目延期风险高

## 行动项

| 任务 | 负责人 | 截止日期 | 优先级 |
|------|--------|---------|--------|
| 完成 PRD 文档 | 张三 | 2026-03-01 | 🔴 高 |
| 技术方案设计 | 李四 | 2026-03-05 | 🟡 中 |
| 招聘 2 名后端 | 王五 | 2026-03-15 | 🔴 高 |

## 跟进邮件草稿

Subject: 【会议纪要】产品规划会议 - 2026-02-25

各位好，

感谢参加今天的产品规划会议。以下是会议要点和行动项：

【关键决策】
1. Q2 优先开发 AI 集成功能
2. 增加 2 名后端工程师

【行动项】
- 张三：完成 PRD 文档（3 月 1 日）
- 李四：技术方案设计（3 月 5 日）
- 王五：招聘 2 名后端（3 月 15 日）

详细纪要请见附件。

Best regards,
[你的名字]
```

---

## 📊 Skills 应用矩阵

### 按用户角色推荐

| 用户角色 | 推荐 Skills | 典型工作流 |
|---------|-----------|----------|
| **研究人员** | SmartSourceAnalyzer + CitationEnhancer + ResearchAssistant | 文献收集→分析→深度研究→论文写作 |
| **内容创作者** | SmartSourceAnalyzer + VideoGenerator + PPTGenerator | 素材收集→内容创作→视频/PPT 输出 |
| **产品经理** | MeetingSummarizer + KnowledgeConnector + MindMapGenerator | 会议记录→需求整理→思维导图→知识库 |
| **开发者** | MultiModelRouter + CitationEnhancer + MeetingSummarizer | 代码生成→文档编写→会议记录 |
| **学生** | SmartSourceAnalyzer + CitationEnhancer + MindMapGenerator | 文献阅读→笔记整理→复习导图 |
| **咨询师** | ResearchAssistant + KnowledgeConnector + PPTGenerator | 行业研究→知识图谱→客户演示 |

---

## 🚀 快速开始

想立即体验这些 Skills？

```bash
# 5 分钟部署
git clone https://github.com/jackeyunjie/open-notebook.git
cd open-notebook
./deploy.sh          # Mac/Linux
.\deploy.ps1         # Windows
```

访问 http://localhost:5055/docs 查看完整 API 文档！

---

**文档版本**: v2.0  
**最后更新**: 2026-02-25
