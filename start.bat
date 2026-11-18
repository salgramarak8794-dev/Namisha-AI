@echo off
title Starting Namisha Desktop Companion...
cd /d "%~dp0"
echo ===================================================
echo   Namisha 2.0 ? Local AI Anime Desktop Companion
echo ===================================================
echo Starting backend and Edge WebView2 desktop window...
start "" pythonw run_desktop.py
exit
