@echo off
REM ==============================================================================
REM Build Windows executable and Inno Setup installer for Pa-O Converter
REM Usage: scripts\build_windows.bat
REM ==============================================================================

setlocal enabledelayedexpansion

cd /d "%~dp0\.."

echo ==> Cleaning previous build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist Output rmdir /s /q Output

echo ==> Building Windows binary folder with PyInstaller...
pyinstaller --clean pao_converter.spec

if errorlevel 1 (
    echo [ERROR] PyInstaller build failed!
    exit /b 1
)

echo ==> Checking for Inno Setup Compiler (ISCC)...
set "ISCC_PATH="

if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
) else if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
) else if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=%ProgramFiles%\Inno Setup 6\ISCC.exe"
) else (
    where ISCC.exe >nul 2>nul
    if !errorlevel! equ 0 (
        set "ISCC_PATH=ISCC.exe"
    ) else (
        where iscc.exe >nul 2>nul
        if !errorlevel! equ 0 (
            set "ISCC_PATH=iscc.exe"
        )
    )
)

if defined ISCC_PATH (
    echo ==> Compiling Windows Installer with Inno Setup using: "!ISCC_PATH!"
    "!ISCC_PATH!" installer.iss
    if errorlevel 1 (
        echo [ERROR] Inno Setup compilation failed!
        exit /b 1
    )
    echo.
    echo ==================================================
    echo  SUCCESS: Windows Setup installer created in Output\
    echo ==================================================
) else (
    echo.
    echo [ERROR] Inno Setup compiler (ISCC.exe) not found!
    echo Please install Inno Setup 6 to compile the Windows installer.
    exit /b 1
)
