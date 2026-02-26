@echo off
chcp 65001 >nul
:: Open Notebook - Quick Start Script for Windows
:: One-command setup for new users

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║         Open Notebook - Quick Start Script                ║
echo ║         Privacy-First AI Research Platform                ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

:: Check Docker
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker not found. Please install Docker Desktop:
    echo         https://www.docker.com/products/docker-desktop/
    exit /b 1
)

echo [OK] Docker is installed

:: Download docker-compose.yml
echo [INFO] Downloading docker-compose.yml...
powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/lfnovo/open-notebook/main/docker-compose.yml' -OutFile 'docker-compose.yml' -ErrorAction SilentlyContinue"

if not exist docker-compose.yml (
    echo [WARN] Download failed, creating minimal compose file...
    call :create_minimal_compose
) else (
    echo [OK] docker-compose.yml downloaded
)

:: Create demo data
echo [INFO] Setting up demo data...
if not exist demo-data mkdir demo-data

echo # Open Notebook - Demo Data > demo-data\README.md
echo. >> demo-data\README.md
echo This folder contains sample data to help you explore Open Notebook's features. >> demo-data\README.md
echo [OK] Demo data ready

:: Start services
echo [INFO] Starting Open Notebook...
docker compose up -d

if %errorlevel% neq 0 (
    echo [ERROR] Failed to start services
    exit /b 1
)

echo [OK] Services started successfully!
echo.
echo Waiting for services to be ready (this may take 30-60 seconds)...
timeout /t 30 /nobreak >nul

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                     SUCCESS!                                ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 📍 Open Notebook is running at: http://localhost:8502
echo.
echo 📋 Next Steps:
echo    1. Open http://localhost:8502 in your browser
echo    2. Go to Settings → API Keys → Add your AI provider
echo    3. Create your first notebook
echo.
echo 🆘 Need help?
echo    • Discord: https://discord.gg/37XJPXfz2w
echo    • Docs: https://docs.open-notebook.ai
echo.
echo ⚡ Quick Commands:
echo    docker compose logs -f     [View logs]
echo    docker compose down        [Stop services]
echo.
pause
exit /b 0

:create_minimal_compose
>docker-compose.yml (
echo services:
echo   surrealdb:
echo     image: surrealdb/surrealdb:v2
echo     command: start --log info --user root --pass root rocksdb:/mydata/mydatabase.db
echo     user: root
echo     ports:
echo       - "8000:8000"
echo     volumes:
echo       - ./surreal_data:/mydata
echo     restart: always

echo.
echo   open_notebook:
echo     image: lfnovo/open_notebook:v1-latest
echo     ports:
echo       - "8502:8502"
echo       - "5055:5055"
echo     environment:
echo       - OPEN_NOTEBOOK_ENCRYPTION_KEY=quick-start-demo-key-change-me
echo       - SURREAL_URL=ws://surrealdb:8000/rpc
echo       - SURREAL_USER=root
echo       - SURREAL_PASSWORD=root
echo     volumes:
echo       - ./notebook_data:/app/data
echo     depends_on:
echo       - surrealdb
echo     restart: always
)
echo [OK] Created docker-compose.yml
goto :eof
