@echo off
setlocal
cd /d "%~dp0"
if not exist "VM17_zh_TW.zip" (
    echo Missing VM17_zh_TW.zip. Place your own licensed source locale ZIP beside this CMD.
    pause
    exit /b 2
)
where py >nul 2>nul
if errorlevel 1 (
    echo Python 3 launcher not found. Install Python 3, or run builder/build_payload.py manually.
    pause
    exit /b 3
)
py -3 "%~dp0builder\build_payload.py" --old "%~dp0VM17_zh_TW.zip"
set "RC=%errorlevel%"
echo.
if not "%RC%"=="0" echo Local payload creation failed.
pause
exit /b %RC%
