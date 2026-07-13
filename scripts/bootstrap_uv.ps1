# Ensure a local, self-contained uv.exe exists under tools\ so the app needs no
# pre-installed uv and no admin rights. Downloads the portable uv binary from
# GitHub releases (a single static exe). Safe to re-run: no-op if already present.
$ErrorActionPreference = 'Stop'
$root  = Split-Path -Parent $PSScriptRoot
$tools = Join-Path $root 'tools'
$uv    = Join-Path $tools 'uv.exe'

if (Test-Path $uv) { Write-Host "uv already vendored: $uv"; exit 0 }

New-Item -ItemType Directory -Force -Path $tools | Out-Null

# If uv is already on PATH, copy it in so the folder stays self-contained/portable.
$onPath = Get-Command uv -ErrorAction SilentlyContinue
if ($onPath) {
    Copy-Item $onPath.Source $uv -Force
    Write-Host "Vendored uv from PATH: $($onPath.Source)"
    exit 0
}

$arch = if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64') { 'aarch64' } else { 'x86_64' }
$zip  = "uv-$arch-pc-windows-msvc.zip"
$url  = "https://github.com/astral-sh/uv/releases/latest/download/$zip"
$tmpZip     = Join-Path $env:TEMP $zip
$tmpExtract = Join-Path $env:TEMP 'uv_bootstrap_extract'

Write-Host "Downloading portable uv (no admin) from $url ..."
Invoke-WebRequest -Uri $url -OutFile $tmpZip -UseBasicParsing
if (Test-Path $tmpExtract) { Remove-Item -Recurse -Force $tmpExtract }
Expand-Archive -Path $tmpZip -DestinationPath $tmpExtract -Force
Copy-Item (Join-Path $tmpExtract 'uv.exe') $uv -Force

Remove-Item $tmpZip -Force
Remove-Item -Recurse -Force $tmpExtract
Write-Host "uv ready: $uv"
