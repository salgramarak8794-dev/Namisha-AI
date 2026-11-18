@echo off
title Stopping Namisha...
echo ===================================================
echo   Stopping Namisha 2.0 & Cleaning Up Background Tasks
echo ===================================================
taskkill /F /FI "WINDOWTITLE eq Namisha*" >nul 2>&1
wmic process where "commandline like '%run_desktop.py%'" delete >nul 2>&1
wmic process where "commandline like '%uvicorn%'" delete >nul 2>&1
echo All Namisha companion processes have been cleanly terminated.
timeout /t 2 >nul
exit
