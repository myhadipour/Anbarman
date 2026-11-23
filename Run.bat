@echo off
setlocal
cd /d "%~dp0"
title Anbarman

where pythonw >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    start "" pythonw "%~dp0anbarman.pyw"
    exit /b 0
)
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    start "" python "%~dp0anbarman.pyw"
    exit /b 0
)
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    start "" py -3 "%~dp0anbarman.pyw"
    exit /b 0
)
echo Python not found. Install from https://www.python.org/downloads/
pause
exit /b 1
