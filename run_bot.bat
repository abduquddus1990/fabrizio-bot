@echo off
title Fabrizio Romano Bot
cd /d "%~dp0"
echo ======================================================
echo    Fabrizio Romano Bot (Doimiy kuzatuv rejimi)
echo ======================================================
echo.
venv\Scripts\python.exe main.py --loop
pause

