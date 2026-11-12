@echo off
title Hero Invoice Converter - Web App
cd /d "%~dp0"

echo ========================================================
echo        Hero Invoice Converter Web App
echo        Shanti Motors to Annapurna Motors
echo ========================================================
echo.
echo Starting Web Server at http://localhost:5000 ...
start http://localhost:5000
python server.py
pause
