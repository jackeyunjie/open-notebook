# 飞书知识库自动化采集指南

## 🎯 解决方案概述

通过**飞书开放 API**自动获取您有权限访问的 AI 工具相关文档和会议记录，无需手动导出。

---

## 📋 前置准备

### 1. 创建飞书自建应用

**步骤**：
1. 访问 https://open.feishu.cn
2. 登录您的飞书账号
3. 进入「企业管理」→「自建应用」
4. 点击「创建应用」
5. 填写应用信息：
   - 应用名称：`AI 工具集采集器`
   - 应用图标：可选
   - 应用描述：自动采集 AI 工具相关知识

### 2. 配置应用权限

**需要开通的权限**：

#### 文档权限
```
✅ 获取云文档列表
✅ 读取云文档内容
✅ 搜索云文档
```

#### 会议权限
```
✅ 获取会议列表
✅ 读取会议纪要
```

**操作步骤**：
1. 在应用管理页面，进入「权限管理」
2. 搜索并添加上述权限
3. 提交审核（通常自动通过）

### 3. 获取凭证信息

在应用管理页面找到：
- **App ID** (cli_xxxxxxxxxxxxx)
- **App Secret** (xxxxxxxxxxxxxxxx)

---

## 💻 使用方法

### 方式一：快速采集

```python
from open_notebook.skills.multi_platform_ai_researcher.feishu_knowledge_collector import (
    collect_from_feishu
)
import asyncio

async def main():
    result = await collect_from_feishu(
        app_id="cli_xxxxxxxxxxxxx",
        app_secret="xxxxxxxxxxxxxxxx",
        keywords=[
            'AI 工具', 'ChatGPT', 'Kimi',
            'Midjourney', 'Notion AI'
        ],
        max_docs=50,
        max_meetings=20
    )
    
    print(f"✅ 完成！")
    print(f"文档总数：{result['total_docs']}")
    print(f"AI 工具相关：{result['ai_docs']}")
    print(f"会议总数：{result['total_meetings']}")
    print(f"AI 工具相关：{result['ai_meetings']}")
    
    # 查看文档标题
    for doc in result['docs'][:5]:
        print(f"  - {doc['title']}")

asyncio.run(main())
```

### 方式二：高级用法（指定文件夹）

```python
from open_notebook.skills.multi_platform_ai_researcher.feishu_knowledge_collector import (
    FeishuKnowledgeCollector
)
import asyncio

async def main():
    collector = FeishuKnowledgeCollector(
        app_id="cli_xxxxxxxxxxxxx",
        app_secret="xxxxxxxxxxxxxxxx",
        tenant_key="your-company-key"  # 可选
    )
    
    # 列出所有文档
    docs = await collector.list_docs(max_results=100)
    print(f"找到 {len(docs)} 个文档")
    
    # 筛选 AI 工具相关文档
    ai_keywords = ['AI', 'ChatGPT', 'Kimi', 'Midjourney']
    ai_docs = [
        doc for doc in docs
        if any(kw.lower() in doc.get('name', '').lower() for kw in ai_keywords)
    ]
    print(f"AI 工具相关：{len(ai_docs)} 个")
    
    # 获取具体文档内容
    if ai_docs:
        content = await collector.get_doc_content(ai_docs[0]['obj_token'])
        print(f"\n第一个文档内容预览:")
        print(content[:500])  # 预览前 500 字
    
    # 查询最近会议
    meetings = await collector.list_meetings(max_results=20)
    print(f"\n最近会议：{len(meetings)} 场")
    
    # 获取会议纪要
    if meetings:
        minutes = await collector.get_meeting_minutes(meetings[0]['meeting_id'])
        print(f"\n第一个会议纪要:")
        print(minutes[:500])

asyncio.run(main())
```

### 方式三：集成到多平台采集系统

```python
from open_notebook.skills.multi_platform_ai_researcher import research_ai_tools
import asyncio

async def main():
    # 同时从社交媒体和飞书知识库采集
    result = await research_ai_tools(
        platforms=[
            'xiaohongshu', 'zhihu', 'weibo',
            'video_account', 'official_account', 'douyin'
        ],
        keywords=['一人公司 AI 工具', 'AI 效率工具'],
        max_results_per_platform=20,
        generate_report=True,
        save_to_notebook=True,
        
        # 新增：启用飞书知识库采集
        collect_from_feishu_docs=True,
        feishu_app_id="cli_xxxxxxxxxxxxx",
        feishu_app_secret="xxxxxxxxxxxxxxxx",
        feishu_keywords=['AI 工具', 'ChatGPT', 'Kimi']
    )
    
    print(f"✅ 全平台 + 飞书采集完成！")

asyncio.run(main())
```

---

## 🔧 配置文件（推荐）

### .env 文件

```bash
# 飞书配置
FEISHU_APP_ID=cli_xxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxx
FEISHU_TENANT_KEY=your-company-key

# 采集参数
FEISHU_MAX_DOCS=50
FEISHU_MAX_MEETINGS=20
FEISHU_KEYWORDS=AI 工具，ChatGPT,Kimi,Midjourney,Notion AI
```

### 代码中使用环境变量

```python
import os
from dotenv import load_dotenv

load_dotenv()

result = await collect_from_feishu(
    app_id=os.getenv('FEISHU_APP_ID'),
    app_secret=os.getenv('FEISHU_APP_SECRET'),
    keywords=os.getenv('FEISHU_KEYWORDS', '').split(','),
    max_docs=int(os.getenv('FEISHU_MAX_DOCS', '50')),
    max_meetings=int(os.getenv('FEISHU_MAX_MEETINGS', '20'))
)
```

---

## 📊 输出数据格式

### 返回结果结构

```json
{
  "total_docs": 45,
  "ai_docs": 12,
  "total_meetings": 8,
  "ai_meetings": 3,
  "docs": [
    {
      "title": "ChatGPT 高级技巧分享",
      "content": "# ChatGPT 高级技巧\n\n## 提示词工程...",
      "created_time": "2026-02-10T10:00:00Z",
      "url": "https://your-company.feishu.cn/docs/xxx"
    }
  ],
  "meetings": [
    {
      "title": "AI 工具选型讨论会",
      "start_time": "2026-02-15T14:00:00Z",
      "participants": ["张三", "李四"],
      "minutes": "## 会议纪要\n\n### 决议事项...",
      "url": "https://your-company.feishu.cn/meeting/xxx"
    }
  ],
  "collected_at": "2026-02-18T12:00:00"
}
```

### 保存到 Notebook

采集的数据会自动保存到 SurrealDB：

```sql
-- 查询飞书文档
SELECT 
    title,
    created_time,
    url
FROM source
WHERE source_type = 'feishu_doc'
ORDER BY created_time DESC;

-- 查询会议纪要
SELECT 
    title,
    start_time,
    participants
FROM source
WHERE source_type = 'feishu_meeting'
ORDER BY start_time DESC;
```

---

## ⚙️ 定时任务（完全自动化）

### 每天自动采集

```python
from open_notebook.skills.multi_platform_ai_researcher.feishu_knowledge_collector import (
    FeishuKnowledgeCollector
)
import asyncio
from datetime import time

class FeishuDailyScheduler:
    """飞书知识库每日自动采集器"""
    
    def __init__(self, app_id: str, app_secret: str):
        self.collector = FeishuKnowledgeCollector(app_id, app_secret)
        self.is_running = False
    
    async def run_daily_collection(self):
        """执行每日采集任务"""
        logger.info("开始执行飞书知识库每日采集...")
        
        result = await self.collector.collect_ai_tools_knowledge(
            max_docs=50,
            max_meetings=20
        )
        
        logger.info(f"采集完成：{result['ai_docs']} 篇文档，{result['ai_meetings']} 场会议")
        
        # 保存结果到数据库或发送到飞书群
        return result
    
    async def start_scheduler(self, run_time: time = time(9, 0)):
        """启动定时任务（每天早上 9 点）"""
        from datetime import datetime, timedelta
        
        logger.info(f"飞书采集器已启动，每天 {run_time.hour}:{run_time.minute:02d} 运行")
        
        self.is_running = True
        
        while self.is_running:
            now = datetime.now()
            scheduled_time = now.replace(
                hour=run_time.hour,
                minute=run_time.minute,
                second=0,
                microsecond=0
            )
            
            if now > scheduled_time:
                scheduled_time += timedelta(days=1)
            
            sleep_seconds = (scheduled_time - now).total_seconds()
            logger.info(f"下次运行时间：{scheduled_time}")
            
            await asyncio.sleep(sleep_seconds)
            await self.run_daily_collection()


# 使用示例
async def main():
    scheduler = FeishuDailyScheduler(
        app_id="cli_xxxxxxxxxxxxx",
        app_secret="xxxxxxxxxxxxxxxx"
    )
    
    # 立即执行一次
    await scheduler.run_daily_collection()
    
    # 启动定时任务
    # await scheduler.start_scheduler(run_time=time(9, 0))

asyncio.run(main())
```

---

## 🔐 安全注意事项

### 1. 权限最小化原则
- 只申请必要的权限
- 不要申请写入权限（仅读取）
- 定期审查权限列表

### 2. 密钥保护
- App Secret 不要提交到 Git
- 使用环境变量存储敏感信息
- 定期轮换密钥

### 3. 访问控制
- 限制应用只能访问特定文件夹
- 设置合理的速率限制
- 监控异常访问行为

---

## 🐛 常见问题

### Q1: 提示"没有权限访问该文档"？

**A**: 检查以下几点：
1. 确认已添加「获取云文档列表」权限
2. 确认文档对应用可见（公开或有权限）
3. 检查租户 key 是否正确

### Q2: 如何获取特定文件夹的文档？

**A**: 使用 folder_token 参数：

```python
# 先获取文件夹 token
folder_token = "bascnxxxxxxxxxxxxx"

# 只采集该文件夹下的文档
docs = await collector.list_docs(folder_token=folder_token)
```

### Q3: 会议纪要获取失败？

**A**: 可能原因：
1. 会议没有生成纪要
2. 缺少「读取会议纪要」权限
3. 会议已结束超过查询期限

### Q4: 速率限制如何处理？

**A**: 建议：
1. 单次请求不超过 100 条
2. 批量操作时添加延迟（`await asyncio.sleep(0.5)`）
3. 分批次处理大量数据

---

## 📈 进阶功能

### 智能分类和标签

```python
def categorize_content(content: str) -> Dict[str, Any]:
    """智能分类 AI 工具内容"""
    
    # 工具类型识别
    tool_categories = {
        '文本生成': ['ChatGPT', '文心一言', '通义千问'],
        '图像生成': ['Midjourney', 'Stable Diffusion', 'DALL-E'],
        '办公效率': ['Notion AI', 'FlowUs', 'Wolai'],
        '语音处理': ['讯飞星火', 'Azure TTS'],
        '视频制作': ['Runway', 'Pika', '剪映']
    }
    
    detected_categories = []
    for category, tools in tool_categories.items():
        if any(tool.lower() in content.lower() for tool in tools):
            detected_categories.append(category)
    
    return {
        'categories': detected_categories,
        'tools_mentioned': sum(len(tools) for tools in tool_categories.values())
    }
```

### 自动生成知识图谱

```python
def build_knowledge_graph(docs: List[Dict]) -> Dict[str, Any]:
    """构建 AI 工具知识图谱"""
    
    graph = {
        'nodes': [],  # 工具、概念
        'edges': []   # 关系
    }
    
    # 提取工具和概念
    for doc in docs:
        content = doc.get('content', '')
        # 使用 NLP 或关键词匹配提取实体
        # ...
    
    return graph
```

---

## 🎯 下一步优化

1. **语义搜索** - 使用向量数据库实现智能检索
2. **自动摘要** - 为长文档生成摘要
3. **趋势分析** - 追踪 AI 工具提及频率变化
4. **关联推荐** - 发现相关内容和人员

---

**最后更新**: 2026-02-18  
**版本**: v1.0.0
