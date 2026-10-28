@echo off
setlocal
cd /d "%~dp0"
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\LocaleInstaller.ps1" -Action Install
set "RC=%errorlevel%"
echo.
if "%RC%"=="0" echo Success. Look for the Traditional Chinese VMware shortcut on the desktop.
if not "%RC%"=="0" echo Operation failed. Please check the error messages above.
pause
exit /b %RC%
