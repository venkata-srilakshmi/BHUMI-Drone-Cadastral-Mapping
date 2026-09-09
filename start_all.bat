@echo off
title BHOOMI-AI Launcher
cd /d %~dp0
echo ============================================================
echo Launching BHOOMI-AI Cadastral Mapping Platform
echo ============================================================
echo Starting Backend in separate window...
start "BHOOMI-AI Backend" cmd /c run_backend.bat

echo Starting Frontend in separate window...
start "BHOOMI-AI Frontend" cmd /c run_frontend.bat

echo.
echo Both servers are starting!
echo Once started, open your browser at: http://localhost:5173
echo.
timeout /t 5
