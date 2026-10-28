@echo off
setlocal
cd /d "%~dp0"
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\LocaleInstaller.ps1" -Action Uninstall
set "RC=%errorlevel%"
echo.
if "%RC%"=="0" echo Success. The prior ES locale backup was restored when available.
if not "%RC%"=="0" echo Operation failed. Please check the error messages above.
pause
exit /b %RC%
