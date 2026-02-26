"""
导入 Demo 数据到 Open Notebook

创建一个完整的示例项目，包含：
- 1 个研究 Notebook（AI 编程助手主题）
- 3 个不同类型的 Source（论文/教程/新闻）
- 5 个示例 Note（展示 AI 生成效果）
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict
from pathlib import Path


async def create_demo_notebook():
    """创建演示 Notebook"""
    
    notebook_data = {
        "title": "AI 编程助手深度研究",
        "description": "探索 AI 如何改变编程工作方式，包括 Copilot、Cursor、Codeium 等工具的实战评测与最佳实践",
        "tags": ["AI 编程", "Copilot", "效率工具", "代码生成", "开发者工具"],
        "color": "#3B82F6",
        "is_template": False,
    }
    
    print(f"📓 创建 Notebook: {notebook_data['title']}")
    # TODO: 调用 API 创建 Notebook
    # POST /api/v1/notebooks
    # 返回 notebook_id
    
    return "nb_demo_001"


async def create_demo_sources(notebook_id: str):
    """创建演示 Sources"""
    
    sources = [
        {
            "type": "article",
            "title": "GitHub Copilot 实战指南：提升 55% 编码效率",
            "content": """
# GitHub Copilot 实战指南

## 核心发现
根据最新研究，使用 GitHub Copilot 的开发者编码效率提升了 55%。

## 主要功能
1. **智能代码补全**: 根据上下文自动生成代码建议
2. **多语言支持**: Python, JavaScript, TypeScript, Go, Java 等
3. **自然语言转代码**: 用注释描述需求，AI 自动生成实现

## 实际案例
某创业公司使用 Copilot 后：
- 开发周期从 3 个月缩短到 6 周
- Bug 率降低 30%
- 开发者满意度提升至 92%

## 最佳实践
- 写清晰的注释描述意图
- 审查 AI 生成的每一行代码
- 结合单元测试验证正确性
- 不要完全依赖，保持批判性思维
""",
            "url": "https://example.com/copilot-guide",
            "author": "AI 研究团队",
            "publish_date": "2026-02-20",
            "tags": ["Copilot", "效率", "实战指南"],
        },
        {
            "type": "tutorial",
            "title": "Cursor IDE 完整教程：下一代 AI 编程工具",
            "content": """
# Cursor IDE 完整教程

## 什么是 Cursor？
Cursor 是一款集成了 AI 的代码编辑器，基于 VS Code 构建，但更强大。

## 核心功能

### 1. Chat with Codebase
可以直接问 AI 关于整个代码库的问题：
- "这个函数的作用是什么？"
- "如何添加用户认证功能？"
- "找出所有使用 HTTP 请求的地方"

### 2. AI Pair Programming
- Ctrl+K: 在当前文件生成代码
- Ctrl+L: 打开侧边栏对话
- Ctrl+Shift+K: 让 AI 修改选中代码

### 3. 自动 Debug
粘贴错误信息，AI 会自动分析原因并给出修复方案。

## 安装步骤
1. 访问 cursor.sh 下载
2. 导入 VS Code 配置（可选）
3. 配置 API Key（推荐使用自己的）
4. 开始使用！

## 定价
- Free: 每月 50 次 AI 请求
- Pro: $20/月，无限使用
- Business: $40/月，团队协作功能
""",
            "url": "https://cursor.sh/tutorial",
            "author": "Cursor 官方",
            "publish_date": "2026-02-18",
            "tags": ["Cursor", "IDE", "教程", "AI 编辑器"],
        },
        {
            "type": "news",
            "title": "2026 年 AI 编程工具大比拼：谁最强？",
            "content": """
# 2026 年 AI 编程工具横评

## 参选选手
1. **GitHub Copilot** - 市场领导者
2. **Cursor** - 新兴挑战者
3. **Codeium** - 免费替代品
4. **Amazon CodeWhisperer** - AWS 生态
5. **Tabnine** - 本地部署选项

## 评测维度

### 代码质量
1. Cursor: 9.5/10 ⭐
2. Copilot: 9.0/10
3. Codeium: 8.5/10
4. CodeWhisperer: 8.0/10
5. Tabnine: 7.5/10

### 响应速度
1. Cursor: <500ms 🚀
2. Copilot: <1s
3. Codeium: <1s
4. CodeWhisperer: 1-2s
5. Tabnine: 2-3s

### 价格性价比
1. Codeium: 免费 💰
2. Copilot: $10/月
3. Cursor: $20/月
4. CodeWhisperer: 免费（AWS 用户）
5. Tabnine: $12/月

## 最终推荐

🏆 **最佳整体**: Cursor
- 最强的代码理解能力
- 最快的响应速度
- 完整的 IDE 体验

💰 **最佳免费**: Codeium
- 完全免费
- 质量不错
- 适合学生和个人开发者

🏢 **最佳企业**: GitHub Copilot Enterprise
- 完善的权限管理
- 代码隐私保护
- 企业级支持

## 趋势预测
2026 年下半年将有更多 AI 原生编程工具出现，传统 IDE（VS Code、JetBrains）将面临巨大挑战。
""",
            "url": "https://techcrunch.com/ai-coding-tools-2026",
            "author": "TechCrunch",
            "publish_date": "2026-02-25",
            "tags": ["横评", "AI 工具", "2026 趋势"],
        },
    ]
    
    created_source_ids = []
    
    for i, source in enumerate(sources, 1):
        print(f"📄 创建 Source {i}/3: {source['title']}")
        # TODO: 调用 API 创建 Source
        # POST /api/v1/sources
        # 返回 source_id
        created_source_ids.append(f"source_demo_{i:03d}")
    
    return created_source_ids


async def create_demo_notes(notebook_id: str, source_ids: List[str]):
    """创建演示 Notes"""
    
    notes = [
        {
            "title": "AI 编程工具效率提升数据汇总",
            "content": """
# AI 编程工具效率提升数据

## 关键数据点

### GitHub Copilot
- 效率提升：**55%** (来源：GitHub 官方研究)
- Bug 减少：**30%**
- 开发者满意度：**92%**

### Cursor IDE
- 代码理解速度提升：**3x**
- Debug 时间减少：**60%**
- 新用户上手时间：**1 天**

### Codeium
- 免费用户的效率提升：**40%**
- 准确率：**85%**
- 支持语言：**70+**

## 投资回报率计算

假设开发者年薪 ¥300,000：
- 效率提升 55% = 节省 0.55 * ¥300,000 = **¥165,000/年**
- AI 工具成本：$120/年 ≈ ¥860/年
- **ROI = 165000 / 860 = 191x**

结论：投资 AI 编程工具是超高回报的决策。
""",
            "tags": ["数据分析", "ROI", "效率"],
        },
        {
            "title": "Cursor vs Copilot：选择指南",
            "content": """
# Cursor vs Copilot 选择指南

## 核心差异

| 维度 | Cursor | Copilot |
|------|--------|---------|
| 形态 | 完整 IDE | 插件 |
| AI 能力 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 速度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 价格 | $20/月 | $10/月 |
| 学习成本 | 低（VS Code 兼容） | 低 |

## 选择建议

### 选 Cursor 如果：
✅ 想要最强大的 AI 能力
✅ 不介意换一个新的 IDE
✅ 预算充足
✅ 追求极致体验

### 选 Copilot 如果：
✅ 习惯现有 IDE（VS Code/JetBrains）
✅ 只需要基础代码补全
✅ 预算有限
✅ 已经在用 GitHub 生态

## 我的推荐

**新手**: 直接上 Cursor，一步到位
**老手**: Copilot 足够，继续用熟悉的环境
**企业**: Copilot Enterprise，权限管理完善
""",
            "tags": ["对比", "选购指南"],
        },
        {
            "title": "AI 编程最佳实践清单",
            "content": """
# AI 编程最佳实践

## ✅ DO（应该做的）

1. **写清晰的注释**
   ```python
   # 计算用户平均订单金额
   # 输入：订单列表
   # 输出：平均值（保留 2 位小数）
   ```

2. **审查每一行 AI 代码**
   - 理解逻辑
   - 检查边界条件
   - 验证安全性

3. **配合单元测试**
   - 让 AI 生成测试用例
   - 自己补充边缘情况
   - 保持高覆盖率

4. **迭代式提问**
   - 先问整体思路
   - 再问具体实现
   - 最后优化性能

5. **保持批判性思维**
   - AI 会犯错
   - AI 知识有截止日期
   - AI 不了解你的业务上下文

## ❌ DON'T（不应该做的）

1. ❌ 盲目复制粘贴 AI 代码
2. ❌ 完全依赖 AI 不做审查
3. ❌ 用 AI 处理敏感数据
4. ❌ 放弃学习和思考
5. ❌ 忽视代码可读性

## 🎯 黄金法则

> AI 是副驾驶，你才是机长。
> 对代码质量负最终责任的是你，不是 AI。
""",
            "tags": ["最佳实践", "避坑指南"],
        },
        {
            "title": "AI 编程工具未来趋势预测",
            "content": """
# AI 编程工具未来趋势（2026-2027）

## 短期趋势（6-12 个月）

### 1. 多模态 AI 编程
- 语音 + 文字混合输入
- 手绘草图转代码
- 屏幕录制自动分析

### 2. 垂直领域专业化
- 法律科技专用 AI
- 医疗行业专用 AI
- 金融科技专用 AI

### 3. 团队协作增强
- 共享 AI 知识库
- 团队代码风格学习
- 跨项目经验迁移

## 中期趋势（1-2 年）

### 1. 自主 Agent 崛起
- AI 独立完成完整功能模块
- 自动 Debug 和修复
- 自主编写文档和测试

### 2. 低代码 + AI 融合
- 可视化界面 + AI 生成后端
- 自然语言描述 → 完整应用
- 非技术人员也能开发复杂系统

### 3. 开源模型挑战闭源
- Llama 系列持续改进
- 专业代码训练模型涌现
- 成本大幅下降

## 长期影响

### 对开发者的影响
✅ 入门门槛降低
✅ 对创造力要求提高
❌ 纯 CRUD 工程师将被淘汰
✅ 系统架构师价值提升

### 对教育的影响
- 编程教育重心转移
- 更注重问题拆解能力
- 减少对语法记忆的重视

### 对行业的影响
- 软件开发成本下降 50%+
- 创业公司技术门槛降低
- 传统软件公司面临挑战

## 行动建议

1. **立即开始使用 AI 工具**
   - 每天至少用 1 小时
   - 记录使用心得
   - 建立个人知识库

2. **培养 AI 无法替代的能力**
   - 系统设计
   - 业务理解
   - 沟通协调
   - 创新思维

3. **保持学习**
   - 关注最新工具
   - 参与社区讨论
   - 分享实践经验
""",
            "tags": ["趋势预测", "未来展望"],
        },
        {
            "title": "本周行动计划",
            "content": """
# 本周 AI 编程工具学习计划

## Day 1-2: 环境搭建
- [ ] 安装 Cursor IDE
- [ ] 配置 API Key
- [ ] 导入现有项目
- [ ] 熟悉基本操作

## Day 3-4: 实战练习
- [ ] 用 AI 完成一个小功能
- [ ] 尝试 Chat with Codebase
- [ ] 让 AI 生成单元测试
- [ ] 记录遇到的问题

## Day 5-6: 深度探索
- [ ] 学习高级技巧
- [ ] 阅读官方文档
- [ ] 观看教学视频
- [ ] 参与社区讨论

## Day 7: 总结复盘
- [ ] 整理学习笔记
- [ ] 评估效率提升
- [ ] 制定下步计划
- [ ] 分享给团队成员

## 成功标准

✅ 能够熟练使用基本功能
✅ 完成至少 3 个实际任务
✅ 效率提升感觉明显
✅ 愿意继续使用

## 资源链接

- [Cursor 官方文档](https://docs.cursor.sh)
- [AI 编程最佳实践](https://example.com/best-practices)
- [Discord 社区](https://discord.gg/cursor)
- [Reddit 讨论区](https://reddit.com/r/cursor)
""",
            "tags": ["学习计划", "行动计划"],
        },
    ]
    
    created_note_ids = []
    
    for i, note in enumerate(notes, 1):
        print(f"📝 创建 Note {i}/5: {note['title']}")
        # TODO: 调用 API 创建 Note
        # POST /api/v1/notebooks/{notebook_id}/notes
        # 返回 note_id
        created_note_ids.append(f"note_demo_{i:03d}")
    
    return created_note_ids


async def main():
    """主函数"""
    print("🚀 开始导入 Demo 数据...\n")
    
    # Step 1: 创建 Notebook
    notebook_id = await create_demo_notebook()
    print(f"✅ Notebook 创建完成：{notebook_id}\n")
    
    # Step 2: 创建 Sources
    source_ids = await create_demo_sources(notebook_id)
    print(f"✅ 创建了 {len(source_ids)} 个 Sources\n")
    
    # Step 3: 创建 Notes
    note_ids = await create_demo_notes(notebook_id, source_ids)
    print(f"✅ 创建了 {len(note_ids)} 个 Notes\n")
    
    print("=" * 60)
    print("🎉 Demo 数据导入完成！")
    print("=" * 60)
    print("\n📦 数据结构:")
    print(f"   - Notebook: 1 个 (AI 编程助手深度研究)")
    print(f"   - Sources: 3 个 (文章/教程/新闻)")
    print(f"   - Notes: 5 个 (数据分析/对比/实践/趋势/计划)")
    print("\n🎯 下一步:")
    print("   1. 访问 http://localhost:5055/docs 查看 API")
    print("   2. 使用前端界面浏览 Demo 内容")
    print("   3. 尝试使用 Skills 功能")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
