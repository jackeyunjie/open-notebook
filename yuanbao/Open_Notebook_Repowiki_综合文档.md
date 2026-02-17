# Open Notebook Repowiki 综合文档

**生成日期**: 2026-02-17  
**版本**: 1.0  
**来源**: `.qoder/repowiki/zh/`

---

## 总结

> Open Notebook 是一个基于 FastAPI + Next.js + SurrealDB 的开源研究笔记应用，支持 AI 辅助的内容分析、知识管理和播客生成。本文档综合了 repowiki 中的所有核心知识，提供从快速开始、核心概念到 API 参考的完整指南。

---

## 目录

1. [项目概述](#项目概述)
2. [快速开始](#快速开始)
3. [核心概念](#核心概念)
4. [架构设计](#架构设计)
5. [API 参考](#api-参考)
6. [开发者指南](#开发者指南)
7. [故障排除](#故障排除)

---

## 项目概述

### 项目简介

Open Notebook 是一个面向研究人员、内容创作者和知识工作者的开源笔记应用，核心特性包括：

- **研究笔记本**: 项目级容器，隔离不同研究主题
- **内容源管理**: 支持 PDF、URL、音频、视频、纯文本等多种格式
- **AI 辅助分析**: RAG (检索增强生成) 驱动的智能问答
- **内容转换**: 自动提取洞察、生成笔记
- **播客生成**: 将内容转换为音频播客
- **多模型支持**: OpenAI、Anthropic、Google、Groq、Ollama 等

### 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | Next.js 14 + React + TypeScript + Tailwind CSS | 现代化 UI |
| 后端 | FastAPI + Python 3.11-3.12 | 高性能 API |
| 数据库 | SurrealDB | 多模型数据库 |
| 容器 | Docker + Docker Compose | 部署编排 |
| 进程管理 | Supervisor | 服务管理 |
| AI 框架 | LangChain | LLM 集成 |

---

## 快速开始

### 系统要求

- **最低配置**: 4GB 内存、2GB 存储
- **推荐配置**: 8GB+ 内存、10GB+ 存储、多核 CPU
- **软件依赖**: Docker Desktop 或 Node.js 18+

### 安装方式对比

| 方式 | 适用场景 | 时间 | 复杂度 |
|------|----------|------|--------|
| Docker Compose | 大多数用户 | ~5 分钟 | 低 |
| 单容器 | 云平台部署 | ~3 分钟 | 最低 |
| 源码安装 | 开发者 | ~10 分钟 | 高 |

### Docker Compose 安装（推荐）

```bash
# 1. 获取 docker-compose.yml
wget https://raw.githubusercontent.com/lfnovo/open-notebook/main/docker-compose.yml

# 2. 修改加密密钥 (必须)
# 编辑 docker-compose.yml，将 OPEN_NOTEBOOK_ENCRYPTION_KEY 替换为强口令

# 3. 启动服务
docker compose up -d

# 4. 验证安装
curl http://localhost:5055/health

# 5. 访问前端
open http://localhost:8502
```

### 环境变量配置

**必填项**:
- `OPEN_NOTEBOOK_ENCRYPTION_KEY`: 数据库加密密钥（至少 16 位）

**数据库配置**:
- `SURREAL_URL`: 数据库连接地址
- `SURREAL_USER`: 数据库用户名
- `SURREAL_PASSWORD`: 数据库密码
- `SURREAL_NAMESPACE`: 命名空间
- `SURREAL_DATABASE`: 数据库名

**完整环境变量参考**:
- API 配置: `API_URL`, `INTERNAL_API_URL`, `API_CLIENT_TIMEOUT`
- 重试策略: `SURREAL_COMMANDS_RETRY_ENABLED`, `SURREAL_COMMANDS_RETRY_MAX_ATTEMPTS`
- LLM 配置: `ESPERANTO_LLM_TIMEOUT`, `ESPERANTO_SSL_VERIFY`
- 网络代理: `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`
- 调试监控: `LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`

---

## 核心概念

### 三层模型

Open Notebook 采用"容器-输入-输出"的三层模型：

```
┌─────────────────────────────────────────┐
│           容器层 (Notebook)              │
│    项目级容器，承载上下文与范围控制        │
├─────────────────────────────────────────┤
│           输入层 (Source)                │
│    PDF、URL、音频、视频、纯文本等         │
│    自动索引、嵌入、不可变                 │
├─────────────────────────────────────────┤
│           输出层                         │
│    笔记 (Note)      - 加工后的内容       │
│    洞察 (Insight)   - 结构化见解         │
│    播客 (Podcast)   - 音频内容           │
└─────────────────────────────────────────┘
```

### 核心实体

#### 1. 研究笔记本 (Notebook)
- **职责**: 项目级容器，隔离不同研究主题
- **特性**: 独立的源集合、笔记集合、AI 上下文
- **使用**: 为每个研究主题创建独立笔记本

#### 2. 内容源 (Source)
- **支持的格式**:
  - 文档: PDF, DOCX, PPTX, XLSX
  - 网页: URL (自动抓取)
  - 媒体: 音频(MP3, WAV), 视频(MP4)
  - 文本: 纯文本, Markdown
- **处理流程**: 上传 → 解析 → 切片 → 嵌入 → 索引
- **特性**: 不可变，自动版本控制

#### 3. 笔记 (Note)
- **类型**: 手动撰写 或 AI 生成
- **功能**: 可被引用、分享、导出
- **关联**: 链接到源、其他笔记

#### 4. 洞察 (SourceInsight)
- **定义**: 从源内容提取的结构化见解
- **生成**: AI 自动分析提取
- **用途**: 快速理解内容要点

### RAG 工作原理

```
用户提问
    ↓
查询理解 → 关键词提取 → 向量检索
    ↓
多路召回 (关键词 + 语义 + 概念)
    ↓
重排序 (Re-ranking)
    ↓
上下文构建 (ContextBuilder)
    ↓
LLM 生成回答
    ↓
引用标注
```

**关键技术**:
- **向量嵌入**: 文本切片 → 批量嵌入 → 均值池化
- **语义检索**: 基于向量相似度的内容召回
- **上下文构建**: 按优先级和令牌限制组装上下文

### 聊天 vs 转换

| 特性 | AI 聊天 (Chat) | 内容转换 (Transformation) |
|------|----------------|---------------------------|
| **目的** | 问答交互 | 内容加工生成 |
| **输出** | 流式回答 | 结构化笔记/洞察 |
| **上下文** | 会话历史 | 选定源/笔记 |
| **使用场景** | 探索性查询 | 批量处理、报告生成 |

---

## 架构设计

### 系统架构

```
┌─────────────────────────────────────────────┐
│                 前端 (Next.js)               │
│         8502 端口 / 3000 (开发)              │
├─────────────────────────────────────────────┤
│              API 层 (FastAPI)                │
│         5055 端口 / uvicorn 服务             │
│  路由: notebooks, sources, notes, chat, ...  │
├─────────────────────────────────────────────┤
│           领域层 (Domain)                     │
│  Notebook, Source, Note, Session, Settings   │
├─────────────────────────────────────────────┤
│           工具层 (Utils)                      │
│  ContextBuilder, Embedding, GraphBuilder     │
├─────────────────────────────────────────────┤
│           AI 层                               │
│  Models, LangChain, RAG Pipeline             │
├─────────────────────────────────────────────┤
│           数据层                              │
│  SurrealDB (8000 端口)                        │
└─────────────────────────────────────────────┘
```

### 容器编排

**Docker Compose 服务**:
- `surrealdb`: 数据库服务
- `open_notebook`: 主应用 (API + 前端 + Worker)
- `ollama` (可选): 本地 AI 推理

**Supervisor 进程管理**:
- API 服务 (uvicorn)
- Worker 进程 (surreal-commands)
- 前端服务 (server.js)

**启动顺序保障**:
1. 前端启动前等待 API 健康检查
2. API 初始化数据库连接
3. Worker 注册命令处理器

---

## API 参考

### 认证 API

```http
POST /api/token
Content-Type: application/x-www-form-urlencoded

username={email}&password={password}
```

响应:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### 笔记本 API

**创建笔记本**:
```http
POST /api/notebooks
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "研究项目",
  "description": "AI 趋势分析"
}
```

**列出笔记本**:
```http
GET /api/notebooks
Authorization: Bearer {token}
```

### 内容源 API

**添加 URL 源**:
```http
POST /api/sources
Authorization: Bearer {token}
Content-Type: application/json

{
  "notebook_id": "notebook:abc",
  "title": "文章标题",
  "source_type": "url",
  "url": "https://example.com/article"
}
```

**上传文件**:
```http
POST /api/sources/upload
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: (binary)
notebook_id: notebook:abc
```

### AI 聊天 API

**发送消息**:
```http
POST /api/chat
Authorization: Bearer {token}
Content-Type: application/json

{
  "notebook_id": "notebook:abc",
  "message": "总结这些文档的关键点",
  "stream": true
}
```

**流式响应**:
```
data: {"content": "根据文档分析..."}
data: {"content": "关键发现包括..."}
data: [DONE]
```

### 搜索 API

**语义搜索**:
```http
POST /api/search
Authorization: Bearer {token}
Content-Type: application/json

{
  "notebook_id": "notebook:abc",
  "query": "机器学习应用",
  "search_type": "vector",
  "limit": 10
}
```

**混合搜索** (关键词 + 语义):
```http
POST /api/search
Content-Type: application/json

{
  "query": "深度学习",
  "search_type": "hybrid",
  "weights": {
    "keyword": 0.3,
    "vector": 0.7
  }
}
```

### 播客 API

**生成播客**:
```http
POST /api/podcasts
Authorization: Bearer {token}
Content-Type: application/json

{
  "notebook_id": "notebook:abc",
  "title": "AI 趋势播客",
  "source_ids": ["source:abc", "source:def"],
  "voice_config": {
    "host_voice": "en-US-AriaNeural",
    "guest_voice": "en-US-GuyNeural"
  }
}
```

### 工作流 API

**执行工作流**:
```http
POST /api/workflows/{workflow_id}/execute
Authorization: Bearer {token}
Content-Type: application/json

{
  "notebook_id": "notebook:abc",
  "parameters": {
    "source_type": "url",
    "auto_process": true
  }
}
```

---

## 开发者指南

### 开发环境搭建

**1. 克隆仓库**:
```bash
git clone https://github.com/lfnovo/open-notebook.git
cd open-notebook
```

**2. 安装 Python 依赖**:
```bash
pip install uv
uv venv
uv pip install -e ".[dev]"
```

**3. 安装前端依赖**:
```bash
cd frontend
npm install
```

**4. 启动数据库**:
```bash
docker run -d --name surrealdb \
  -p 8000:8000 \
  surrealdb/surrealdb:latest \
  start --user root --pass root
```

**5. 配置环境**:
```bash
cp .env.example .env
# 编辑 .env 设置密钥和数据库连接
```

**6. 启动服务**:
```bash
# 终端 1: API
python -m uvicorn api.main:app --reload --port 5055

# 终端 2: 前端
cd frontend && npm run dev
```

### 代码规范

**Python**:
- 使用 `ruff` 进行代码格式化
- 类型注解: `from typing import Optional, List`
- 异步优先: `async def` 和 `await`
- 错误处理: 使用 `try/except` 和自定义异常

**TypeScript**:
- 严格模式启用
- 接口定义优先
- 组件函数式编写

### 项目结构

```
open-notebook/
├── api/                    # FastAPI 路由
│   ├── routers/           # API 端点
│   ├── auth.py            # 认证逻辑
│   └── main.py            # 应用入口
├── open_notebook/         # 核心业务逻辑
│   ├── domain/            # 领域模型
│   ├── ai/                # AI 集成
│   ├── utils/             # 工具函数
│   └── graphs/            # 处理流程图
├── frontend/              # Next.js 前端
│   ├── src/
│   │   ├── app/          # 页面路由
│   │   ├── components/   # React 组件
│   │   └── lib/          # 工具函数
│   └── package.json
├── docs/                  # 文档
├── examples/              # 示例配置
├── tests/                 # 测试
└── docker-compose.yml     # 部署配置
```

---

## 故障排除

### 常见问题

**无法连接到服务器**:
- 检查 API 是否运行: `curl http://localhost:5055/health`
- 确认端口未被占用
- 重启服务: `docker compose restart`

**API 密钥无效**:
- 在 UI 中重新添加凭据
- 测试连接状态
- 重新发现模型

**搜索无结果**:
- 确认源已处理完成
- 尝试不同搜索类型
- 简化查询关键词

**播客生成失败**:
- 检查 TTS 配额
- 确认内容长度足够
- 查看网络连接

**数据库连接过多**:
- 降低 `SURREAL_COMMANDS_MAX_TASKS`
- 重启数据库服务

### 日志查看

```bash
# Docker 日志
docker compose logs -f

# 特定服务
docker compose logs -f open_notebook

# 本地开发
# API 日志在终端输出
```

### 性能优化

**内存不足**:
- 增加 Docker 内存限制
- 减少并发任务数
- 使用更小的嵌入模型

**响应慢**:
- 切换更快的 LLM 模型
- 减少上下文长度
- 启用缓存

---

## 附录

### 端口参考

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端 | 8502 | 生产环境 |
| 前端 (开发) | 3000 | 开发环境 |
| API | 5055 | REST API |
| SurrealDB | 8000 | 数据库 |
| Ollama | 11434 | 本地模型 |

### 文件格式支持

**文档**: PDF, DOCX, PPTX, XLSX  
**图片**: JPG, PNG, WebP (需 OCR)  
**音频**: MP3, WAV, M4A, OGG  
**视频**: MP4, AVI, MOV, WebM  
**文本**: TXT, MD, HTML, JSON

### AI 提供商

- **OpenAI**: GPT-4, GPT-3.5, DALL-E, TTS
- **Anthropic**: Claude 3 系列
- **Google**: Gemini Pro
- **Groq**: 高速推理 (Llama, Mixtral)
- **Ollama**: 本地模型部署

---

*文档生成时间: 2026-02-17*  
*基于 Open Notebook Repowiki 综合整理*
