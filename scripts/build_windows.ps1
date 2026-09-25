# Build Windows Executable and Inno Setup installer for Pa-O Converter
$ErrorActionPreference = "Stop"

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RootDir

Write-Host "==> Cleaning previous build artifacts..."
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "Output") { Remove-Item -Recurse -Force "Output" }

Write-Host "==> Building Windows binary folder with PyInstaller..."
pyinstaller --clean pao_converter.spec
if ($LASTEXITCODE -ne 0) {
    Write-Error "PyInstaller build failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host "==> Locating Inno Setup Compiler (ISCC.exe)..."
$isccCandidates = @(
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe",
    "C:\ProgramData\chocolatey\bin\iscc.exe"
)

$iscc = $null
foreach ($path in $isccCandidates) {
    if (Test-Path $path) {
        $iscc = $path
        break
    }
}

if (-not $iscc) {
    $cmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($cmd) { $iscc = $cmd.Source }
}

if (-not $iscc) {
    Write-Error "Inno Setup compiler (ISCC.exe) not found! Please install Inno Setup 6."
    exit 1
}

Write-Host "==> Compiling Windows Installer with: $iscc"
& "$iscc" installer.iss
if ($LASTEXITCODE -ne 0) {
    Write-Error "Inno Setup compilation failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "=================================================="
Write-Host " SUCCESS: Windows Setup installer created in Output\"
Write-Host "=================================================="
