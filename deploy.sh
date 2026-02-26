#!/bin/bash
# Open Notebook 一键部署脚本 (Linux/Mac)
# 预计耗时：5 分钟

set -e

echo "🚀 Open Notebook 一键部署开始..."
echo ""

# Step 1: 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

echo "✅ Docker 已安装"

# Step 2: 检查 Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装"
    exit 1
fi

echo "✅ Docker Compose 已安装"

# Step 3: 克隆项目（如果当前目录不是 open-notebook）
if [ ! -f "docker-compose.yml" ]; then
    echo "📦 克隆 Open Notebook 项目..."
    git clone https://github.com/jackeyunjie/open-notebook.git
    cd open-notebook
fi

# Step 4: 复制环境变量文件
if [ ! -f ".env" ]; then
    echo "⚙️  创建环境配置文件..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件配置以下必需项:"
    echo "   - ANTHROPIC_API_KEY (或其他 AI 提供商密钥)"
    echo "   - SURREALDB_URL=ws://surrealdb:8000"
    echo ""
    read -p "配置完成后按回车继续..."
fi

# Step 5: 启动服务
echo "🔧 启动 DOKER 服务..."
docker-compose up -d surrealdb ollama

echo "⏳ 等待 SurrealDB 启动 (约 30 秒)..."
sleep 30

# Step 6: 运行数据库迁移
echo "📊 运行数据库迁移..."
docker-compose run --rm api python -m open_notebook.database.migrate

# Step 7: 导入 Demo 数据
echo "📦 导入示例数据..."
docker-compose run --rm api python scripts/import_demo_data.py

# Step 8: 启动 API
echo "🚀 启动 API 服务..."
docker-compose up -d api

# Step 9: 启动前端（可选）
read -p "是否启动前端界面？(y/n): " start_frontend
if [ "$start_frontend" = "y" ]; then
    echo "🎨 启动前端..."
    cd frontend
    npm install
    npm run dev
fi

echo ""
echo "✅ 部署完成！"
echo ""
echo "📱 访问地址:"
echo "   - API: http://localhost:5055"
echo "   - Swagger Docs: http://localhost:5055/docs"
echo "   - Frontend: http://localhost:5173 (如果启动)"
echo ""
echo "🎉 开始使用吧！"
