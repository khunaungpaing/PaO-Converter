@echo off
REM Forward to PowerShell build script to avoid cmd.exe parsing issues
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_windows.ps1"
if %errorlevel% neq 0 exit /b %errorlevel%
