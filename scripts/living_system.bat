@echo off
REM Living Knowledge System - Startup Script
REM Usage: .\scripts\living_system.bat [command]

set COMPOSE_FILE=docker-compose.living.yml

if "%1"=="up" goto up
if "%1"=="down" goto down
if "%1"=="logs" goto logs
if "%1"=="status" goto status
if "%1"=="psql" goto psql
if "%1"=="api-local" goto api_local
if "%1"=="api-postgres" goto api_postgres
if "%1"=="help" goto help
if "%1"=="" goto help

echo Unknown command: %1
goto help

:up
echo [START] Launching Living Knowledge System...
docker-compose -f %COMPOSE_FILE% up -d
echo.
echo [OK] Services started!
echo.
echo Access URLs:
echo   API:        http://localhost:8888
echo   Docs:       http://localhost:8888/docs
echo   PostgreSQL: localhost:5433 (living/living)
echo   pgAdmin:    http://localhost:5050 (admin/admin)
echo.
goto eof

:down
echo [STOP] Stopping Living Knowledge System...
docker-compose -f %COMPOSE_FILE% down
echo [OK] Services stopped
goto eof

:logs
echo [LOGS] Viewing logs...
docker-compose -f %COMPOSE_FILE% logs -f
goto eof

:status
echo [STATUS] Service status:
docker-compose -f %COMPOSE_FILE% ps
goto eof

:psql
echo [PSQL] Connecting to PostgreSQL...
docker exec -it living_postgres psql -U living -d living_system
goto eof

:api_local
echo [API] Starting local API (memory mode)...
set PYTHONPATH=d:\Antigravity\opc\open-notebook
python -m uvicorn open_notebook.skills.living.api_main:app --host 0.0.0.0 --port 8000 --reload
goto eof

:api_postgres
echo [API] Starting local API (PostgreSQL mode)...
set PYTHONPATH=d:\Antigravity\opc\open-notebook
set LIVING_DB_HOST=localhost
set LIVING_DB_PORT=5433
set LIVING_DB_NAME=living_system
set LIVING_DB_USER=living
set LIVING_DB_PASSWORD=living
python -m uvicorn open_notebook.skills.living.api_postgres:app --host 0.0.0.0 --port 8000 --reload
goto eof

:help
echo Living Knowledge System - Management Script
echo.
echo Usage: .\scripts\living_system.bat [command]
echo.
echo Commands:
echo   up           - Start all services (PostgreSQL + API + Data Agent)
echo   down         - Stop all services
echo   logs         - View logs
echo   status       - View service status
echo   psql         - Connect to PostgreSQL
echo   api-local    - Start local API (memory mode)
echo   api-postgres - Start local API (PostgreSQL mode)
echo   help         - Show this help
echo.
echo Examples:
echo   .\scripts\living_system.bat up
echo   .\scripts\living_system.bat logs
echo   .\scripts\living_system.bat psql
goto eof

:eof
