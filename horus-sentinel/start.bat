@echo off
title HORUS Sentinel Start
echo ==============================================
echo        Starting HORUS Sentinel
echo ==============================================
echo.

:: Check if Docker is running
docker info >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker is not running or not installed.
    echo Please start Docker Desktop and run this script again.
    pause
    exit /b
)

:: Check for .env file
IF NOT EXIST ".env" (
    echo [INFO] .env file not found. Creating default .env from .env.example...
    copy .env.example .env >nul
    echo [INFO] .env file created successfully.
)

echo [INFO] Building and starting containers...
docker compose -f deploy/docker-compose.yml up -d --build

echo.
echo ==============================================
echo        HORUS Sentinel is Running!
echo ==============================================
echo - Backend API Docs : http://localhost:8000/docs
echo - Neo4j Graph DB   : http://localhost:7474
echo - MinIO (S3)       : http://localhost:9001
echo.
echo To see the logs, run: docker compose -f deploy/docker-compose.yml logs -f
echo ==============================================
pause
