# Open Notebook 一键部署脚本 (Windows PowerShell)
# 预计耗时：5 分钟

Write-Host "🚀 Open Notebook 一键部署开始..." -ForegroundColor Green
Write-Host ""

# Step 1: 检查 Docker
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker 已安装：$dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker 未安装，请先安装 Docker Desktop" -ForegroundColor Red
    Write-Host "下载地址：https://www.docker.com/products/docker-desktop"
    exit 1
}

# Step 2: 检查 Docker Compose
try {
    $composeVersion = docker-compose --version
    Write-Host "✅ Docker Compose 已安装：$composeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose 未安装" -ForegroundColor Red
    exit 1
}

# Step 3: 克隆项目（如果当前目录不是 open-notebook）
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "📦 克隆 Open Notebook 项目..." -ForegroundColor Yellow
    git clone https://github.com/jackeyunjie/open-notebook.git
    Set-Location open-notebook
}

# Step 4: 复制环境变量文件
if (-not (Test-Path ".env")) {
    Write-Host "⚙️  创建环境配置文件..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    
    Write-Host "⚠️  请编辑 .env 文件配置以下必需项:" -ForegroundColor Yellow
    Write-Host "   - ANTHROPIC_API_KEY (或其他 AI 提供商密钥)"
    Write-Host "   - SURREALDB_URL=ws://surrealdb:8000"
    Write-Host ""
    Read-Host "配置完成后按回车继续"
}

# Step 5: 启动服务
Write-Host "🔧 启动 DOKER 服务..." -ForegroundColor Yellow
docker-compose up -d surrealdb ollama

Write-Host "⏳ 等待 SurrealDB 启动 (约 30 秒)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Step 6: 运行数据库迁移
Write-Host "📊 运行数据库迁移..." -ForegroundColor Yellow
docker-compose run --rm api python -m open_notebook.database.migrate

# Step 7: 导入 Demo 数据
Write-Host "📦 导入示例数据..." -ForegroundColor Yellow
docker-compose run --rm api python scripts/import_demo_data.py

# Step 8: 启动 API
Write-Host "🚀 启动 API 服务..." -ForegroundColor Green
docker-compose up -d api

# Step 9: 启动前端（可选）
$startFrontend = Read-Host "是否启动前端界面？(y/n)"
if ($startFrontend -eq "y") {
    Write-Host "🎨 启动前端..." -ForegroundColor Yellow
    Set-Location frontend
    npm install
    npm run dev
}

Write-Host ""
Write-Host "✅ 部署完成！" -ForegroundColor Green
Write-Host ""
Write-Host "📱 访问地址:" -ForegroundColor Cyan
Write-Host "   - API: http://localhost:5055"
Write-Host "   - Swagger Docs: http://localhost:5055/docs"
Write-Host "   - Frontend: http://localhost:5173 (如果启动)"
Write-Host ""
Write-Host "🎉 开始使用吧！" -ForegroundColor Green
