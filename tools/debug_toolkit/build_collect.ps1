param([string]$PackageRoot)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
if ([string]::IsNullOrWhiteSpace($PackageRoot)) {
    $PackageRoot = Join-Path $RepoRoot 'dist\debug-toolkit-collector'
}
$PackageParent = Split-Path -Parent $PackageRoot
New-Item -ItemType Directory -Force -Path $PackageParent | Out-Null

$BuildRoot = Join-Path $RepoRoot ".tmp\debug-toolkit-collector"
$DistRoot = Join-Path $BuildRoot "dist"
$WorkRoot = Join-Path $BuildRoot "work"
$AdbRoot = Join-Path $RepoRoot 'autowsgr\common\device\_resources\bin'
$EntryPoint = Join-Path $PSScriptRoot 'function\collect.py'

if (Test-Path $PackageRoot) {
    throw "目标目录已经存在，请先确认并移走旧版本：$PackageRoot"
}

$RequiredAdbFiles = @(
    "adb.exe",
    "AdbWinApi.dll",
    "AdbWinUsbApi.dll"
)
foreach ($FileName in $RequiredAdbFiles) {
    $FilePath = Join-Path $AdbRoot $FileName
    if (-not (Test-Path $FilePath)) {
        throw "缺少 ADB 文件：$FilePath"
    }
}

New-Item -ItemType Directory -Path $BuildRoot -Force | Out-Null

$PyInstallerArgs = @(
    "run",
    "--with",
    "pyinstaller==6.16.0",
    "pyinstaller",
    "--noconfirm",
    "--clean",
    "--onedir",
    "--console",
    "--noupx",
    "--name",
    "main",
    "--distpath",
    $DistRoot,
    "--workpath",
    $WorkRoot,
    "--specpath",
    $BuildRoot,
    "--collect-all",
    "autowsgr_native",
    "--hidden-import",
    "autowsgr_native._native",
    "--add-binary",
    "$(Join-Path $AdbRoot 'adb.exe');adb",
    "--add-binary",
    "$(Join-Path $AdbRoot 'AdbWinApi.dll');adb",
    "--add-binary",
    "$(Join-Path $AdbRoot 'AdbWinUsbApi.dll');adb",
    $EntryPoint
)

Write-Host "正在生成 main.exe..."
& uv @PyInstallerArgs
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller 打包失败，退出码：$LASTEXITCODE"
}

$GeneratedRoot = Join-Path $DistRoot "main"
if (-not (Test-Path (Join-Path $GeneratedRoot "main.exe"))) {
    throw "打包完成但未找到 main.exe"
}

Move-Item -Path $GeneratedRoot -Destination $PackageRoot
Copy-Item `
    -Path (Join-Path $PSScriptRoot 'README.md') `
    -Destination (Join-Path $PackageRoot 'README.md')
Copy-Item `
    -Path (Join-Path $PSScriptRoot 'start-collector.cmd') `
    -Destination (Join-Path $PackageRoot 'start-collector.cmd')

Write-Host "工具已生成：$PackageRoot"
