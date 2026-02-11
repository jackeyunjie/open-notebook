# Open Notebook 项目恢复脚本
# 用法: .\scripts\resume.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Open Notebook 项目恢复工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 DOKER 状态
Write-Host "[1/5] 检查 DOKER 状态..." -ForegroundColor Yellow
try {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ DOKER 正在运行" -ForegroundColor Green
    } else {
        Write-Host "  ✗ DOKER 未启动，请先启动 DOKER Desktop" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ✗ DOKER 未安装或未启动" -ForegroundColor Red
    exit 1
}

# 显示当前容器状态
Write-Host ""
Write-Host "[2/5] 当前容器状态:" -ForegroundColor Yellow
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  无运行中的容器" -ForegroundColor Gray
}

# 检查 Git 状态
Write-Host ""
Write-Host "[3/5] Git 状态:" -ForegroundColor Yellow
$gitStatus = git status --short 2>$null
if ($gitStatus) {
    Write-Host "  有未提交的更改:" -ForegroundColor Yellow
    Write-Host $gitStatus
} else {
    Write-Host "  ✓ 工作区干净" -ForegroundColor Green
}

# 显示最近提交
Write-Host ""
Write-Host "  最近提交:" -ForegroundColor Gray
$recentCommits = git log --oneline -5 2>$null
if ($recentCommits) {
    $recentCommits | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
}

# 检查服务端口
Write-Host ""
Write-Host "[4/5] 服务端口检查:" -ForegroundColor Yellow
$ports = @(8502, 5055, 8000)
foreach ($port in $ports) {
    $connection = Test-NetConnection -ComputerName localhost -Port $port -WarningAction SilentlyContinue
    if ($connection.TcpTestSucceeded) {
        Write-Host "  ✓ 端口 $port 已占用 (服务运行中)" -ForegroundColor Green
    } else {
        Write-Host "  ✗ 端口 $port 空闲" -ForegroundColor Gray
    }
}

# 显示项目摘要
Write-Host ""
Write-Host "[5/5] 项目状态摘要:" -ForegroundColor Yellow
Write-Host "  项目名称: Open Notebook" -ForegroundColor White
Write-Host "  技术栈: Python/FastAPI + Next.js + SurrealDB" -ForegroundColor White
Write-Host "  主要功能:" -ForegroundColor White
Write-Host "    - Skill 系统 (6个内置 Skill)" -ForegroundColor Gray
Write-Host "    - APScheduler 定时调度" -ForegroundColor Gray
Write-Host "    - Browser-use 浏览器自动化" -ForegroundColor Gray
Write-Host "    - 多 AI Provider 支持" -ForegroundColor Gray
Write-Host ""
Write-Host "  访问地址:" -ForegroundColor White
Write-Host "    - Web UI: http://localhost:8502" -ForegroundColor Cyan
Write-Host "    - API: http://localhost:5055" -ForegroundColor Cyan
Write-Host "    - 文档: http://localhost:8000" -ForegroundColor Cyan

# 提供操作建议
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  可用操作" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. 启动服务:     docker-compose up -d" -ForegroundColor White
Write-Host "  2. 查看日志:     docker-compose logs -f" -ForegroundColor White
Write-Host "  3. 停止服务:     docker-compose down" -ForegroundColor White
Write-Host "  4. 重启服务:     docker-compose restart" -ForegroundColor White
Write-Host "  5. 查看 Skill:   http://localhost:8502/skills" -ForegroundColor White
Write-Host ""
Write-Host "  前端开发:        cd frontend; npm run dev" -ForegroundColor White
Write-Host "  后端开发:        cd api; uvicorn main:app --reload" -ForegroundColor White
Write-Host ""

# 询问是否启动服务
$startService = Read-Host "是否启动 DOKER 服务? (y/n)"
if ($startService -eq 'y' -or $startService -eq 'Y') {
    Write-Host ""
    Write-Host "正在启动服务..." -ForegroundColor Green
    docker-compose up -d
    Write-Host ""
    Write-Host "服务启动完成!" -ForegroundColor Green
    Write-Host "请访问: http://localhost:8502" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "恢复脚本执行完成!" -ForegroundColor Green
