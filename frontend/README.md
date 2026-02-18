# Open Notebook Frontend

基于 React + TypeScript + Vite 的前端应用，提供 P0/P1/C/B/A 所有功能的图形界面。

## 🚀 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

### 3. 构建生产版本

```bash
npm run build
```

## 📦 核心功能

### P0 - 一键报告生成器
- 学习指南
- 文献综述
- 研究简报
- 周度趋势
- 概念图谱

### P1 - 体验增强
- 可视化知识图谱（思维导图、时间线、网络图）
- 批量导入工具（文件夹、URL、Zotero、Mendeley）

### C - 性能优化
- 缓存系统
- 查询优化
- 性能监控

### B - UI 集成
- 快捷操作按钮
- 实时通知
- 进度追踪

### A - 协作功能 (P2)
- Notebook 共享
- 权限管理
- 评论批注
- 实时会话

## 🔗 API 文档

启动后端服务后访问：http://localhost:8000/docs

查看所有 Skills API 的 Swagger 文档。

## 🛠️ 技术栈

- **React 18** - UI 框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Axios** - HTTP 客户端
- **React Router** - 路由
- **TanStack Query** - 数据获取
- **Zustand** - 状态管理
- **Tailwind CSS** - 样式
- **Lucide React** - 图标
- **Chart.js** - 图表
- **Mermaid** - 思维导图

## 📝 环境变量

创建 `.env` 文件：

```env
VITE_API_URL=http://localhost:8000
```

## 🎯 下一步

1. 安装依赖并启动前端
2. 测试所有 API 端点
3. 添加更多页面和组件
4. 实现实时 WebSocket 连接
5. 添加国际化支持
