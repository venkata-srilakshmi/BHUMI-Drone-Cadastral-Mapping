@echo off
title BHOOMI-AI Backend Server
cd /d %~dp0backend
echo ============================================================
echo Starting BHOOMI-AI FastAPI Backend (Port 8000)...
echo ============================================================
python main.py
pause
