@echo off
setlocal
if not exist "%~dp0.venv\Scripts\python.exe" (
    echo Run Setup-Hadith.cmd first to install the project environment.
    pause
    exit /b 1
)
for /d %%P in ("%~dp0.tools\python\cpython-*") do (
    if exist "%%~fP\python.exe" (
        "%%~fP\python.exe" -u "%~dp0run_hadith.py"
        goto finished
    )
)
"%~dp0.venv\Scripts\python.exe" -u "%~dp0run_hadith.py"
:finished
set "result=%errorlevel%"
if not "%result%"=="0" (
    echo Hadith app failed to start. See the error above.
    pause
)
exit /b %result%
