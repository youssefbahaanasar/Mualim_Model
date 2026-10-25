@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if not errorlevel 1 (
    py -3.12 scripts\setup_hadith.py
    goto finished
)
where python >nul 2>&1
if not errorlevel 1 (
    python scripts\setup_hadith.py
    goto finished
)
echo Install Python 3.12 from https://www.python.org/downloads/ and enable Add Python to PATH.
pause
exit /b 1
:finished
set "result=%errorlevel%"
if not "%result%"=="0" echo Setup failed. Read the error above before closing this window.
pause
exit /b %result%
