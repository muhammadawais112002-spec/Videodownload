@echo off
echo ============================================
echo  DownloadAnything - Setup Script
echo ============================================
echo.

REM Try to find real Python
set PYTHON_CMD=

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=py
    goto found_python
)

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    python -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set PYTHON_CMD=python
        goto found_python
    )
)

where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python3
    goto found_python
)

echo ERROR: Python 3.8+ not found on your system.
echo.
echo Please download and install Python from:
echo   https://www.python.org/downloads/
echo.
echo IMPORTANT: During installation, tick the checkbox:
echo   [x] Add Python to PATH
echo.
echo Then re-run this script.
pause
exit /b 1

:found_python
echo Found Python: %PYTHON_CMD%
%PYTHON_CMD% --version

echo.
echo Installing dependencies...
%PYTHON_CMD% -m pip install --upgrade flask flask-cors yt-dlp

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo pip install failed. Trying with --user flag...
    %PYTHON_CMD% -m pip install --upgrade --user flask flask-cors yt-dlp
)

echo.
echo ============================================
echo  Starting DownloadAnything server...
echo  Open http://127.0.0.1:5000 in your browser
echo ============================================
echo.
%PYTHON_CMD% app.py
pause
