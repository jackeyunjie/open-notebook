# OPC Activity Monitor

OPC 屏幕感知 MVP - 理解超级个体的数字行为模式

## 功能

- **实时活动追踪**: 自动记录浏览器标签切换和停留时间
- **隐私优先**: 所有数据本地存储，不上传云端
- **行为洞察**: AI 分析工作模式，提供效率建议
- **OPC集成**: 可选同步到本地 OPC 系统

## 安装

### 开发模式安装

1. 打开 Chrome/Edge，进入 `chrome://extensions/`
2. 开启"开发者模式"
3. 点击"加载已解压的扩展程序"
4. 选择 `extensions/screen-monitor` 文件夹

### 使用

1. 安装后，点击浏览器工具栏的 OPC 图标
2. 查看今日活动概览和洞察
3. 正常使用浏览器，后台自动记录

## 隐私说明

- ✅ 所有数据存储在浏览器本地
- ✅ 不上传任何数据到远程服务器
- ✅ 可选同步到本地 OPC（localhost:5055）
- ✅ 7天后自动清理旧数据
- ✅ 可随时停用或卸载

## 技术架构

```
浏览器扩展
├── Background Script (Service Worker)
│   └── 监听标签切换，记录活动时间
├── Content Script
│   └── 检测页面类型，收集 engagement 指标
└── Popup Dashboard
    └── 可视化展示活动数据

OPC 后端（可选集成）
├── /api/v1/activity/log
│   └── 接收活动数据
└── 存储到 SurrealDB
```

## 开发计划

### MVP (现在)
- [x] 基础活动追踪
- [x] 分类统计
- [x] 简单洞察

### Phase 2
- [ ] 屏幕录制（本地处理）
- [ ] 应用进程监控
- [ ] 专注度评分

### Phase 3
- [ ] 与 LKS P0-P1 深度集成
- [ ] 预测性建议
- [ ] 自动化工作流触发

## License

MIT - Open Notebook Project
