@echo off
REM =============================================================================
REM RAG Conversation System - Startup Script (Windows)
REM =============================================================================
REM This script validates the environment, builds and starts all services,
REM waits for them to become healthy, and provides access information.

setlocal enabledelayedexpansion

REM Colors for output (Windows compatible)
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

REM Print functions
echo.
echo %BLUE%═══════════════════════════════════════════════════════════════%NC%
echo %BLUE%  RAG Conversation System - Starting%NC%
echo %BLUE%═══════════════════════════════════════════════════════════════%NC%
echo.

REM Check if Docker is installed and running
echo %BLUE%Checking Docker Environment%NC%

where docker >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo %RED%✗ Docker is not installed. Please install Docker first.%NC%
    exit /b 1
)
echo %GREEN%✓ Docker command found%NC%

docker compose version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    docker-compose version >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo %RED%✗ Docker Compose is not installed. Please install Docker Compose first.%NC%
        exit /b 1
    )
    set COMPOSE_CMD=docker-compose
) else (
    set COMPOSE_CMD=docker compose
)
echo %GREEN%✓ Docker Compose found%NC%

docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo %RED%✗ Docker daemon is not running. Please start Docker.%NC%
    exit /b 1
)
echo %GREEN%✓ Docker daemon is running%NC%

REM Create .env file from .env.example if it doesn't exist
echo.
echo %BLUE%Setting Up Environment%NC%

if not exist .env (
    if exist .env.example (
        copy /Y .env.example .env >nul
        echo %GREEN%✓ .env created from .env.example%NC%
        echo %YELLOW%⚠ Please update .env with your API keys and configuration%NC%
    ) else (
        echo %RED%✗ .env.example not found. Cannot create .env%NC%
        exit /b 1
    )
) else (
    echo %GREEN%✓ .env already exists%NC%
)

REM Build and start services
echo.
echo %BLUE%Building and Starting Services%NC%

echo %BLUE%ℹ Building Docker images...%NC%
%COMPOSE_CMD% build --parallel
if %ERRORLEVEL% neq 0 (
    echo %RED%✗ Failed to build Docker images%NC%
    exit /b 1
)
echo %GREEN%✓ All images built%NC%

echo %BLUE%ℹ Starting Docker containers...%NC%
%COMPOSE_CMD% up -d
if %ERRORLEVEL% neq 0 (
    echo %RED%✗ Failed to start Docker containers%NC%
    exit /b 1
)
echo %GREEN%✓ All containers started%NC%

REM Wait for services to become healthy
echo.
echo %BLUE%Waiting for Services to Become Healthy%NC%

set "SERVICES=postgres redis auth-service query-service document-service conversation-service backend frontend"
set MAX_ATTEMPTS=60

for %%S in (%SERVICES%) do (
    echo %BLUE%ℹ Waiting for %%S...%NC%
    set ATTEMPT=0
    :wait_loop_%%S
    if !ATTEMPT! LSS %MAX_ATTEMPTS% (
        docker inspect --format="{{.State.Health.Status}}" rag-%%S >nul 2>&1
        if !ERRORLEVEL! equ 0 (
            for /f "delims=" %%A in ('docker inspect --format="{{.State.Health.Status}}" rag-%%S 2^>nul') do (
                if "%%A"=="healthy" (
                    echo %GREEN%✓ %%S is healthy%NC%
                    goto :end_wait_%%S
                )
            )
        )
        timeout /t 2 /nobreak >nul
        set /a ATTEMPT+=1
        goto :wait_loop_%%S
    )
    :end_wait_%%S
)

REM Show service status
echo.
echo %BLUE%Service Status%NC%
%COMPOSE_CMD% ps

REM Print access information
echo.
echo %BLUE%═══════════════════════════════════════════════════════════════%NC%
echo %BLUE%  Access Information%NC%
echo %BLUE%═══════════════════════════════════════════════════════════════%NC%
echo.
echo %GREEN%Application is ready!%NC%
echo.
echo   %BLUE%Frontend:%NC%   http://localhost:3000
echo   %BLUE%API Gateway:%NC% http://localhost:8000
echo   %BLUE%Health Check:%NC% http://localhost:8000/health
echo.
echo %YELLOW%Service Ports:%NC%
echo   Auth Service:         8001
echo   Query Service:       8002
echo   Document Service:    8003
echo   Conversation Service: 8004
echo   PostgreSQL:           5432
echo   Redis:                6379
echo.
echo %YELLOW%Useful Commands:%NC%
echo   View logs:     %BLUE%docker compose logs -f%NC%
echo   Stop services: %BLUE%docker compose down%NC%
echo   Restart:       %BLUE%docker compose restart%NC%
echo.
echo %GREEN%All services started successfully!%NC%

endlocal
exit /b 0
