# Ensure a portable CPython lives *inside* the project (tools\python) so the
# folder is self-contained and needs no system Python. Mirrors bootstrap_uv.ps1:
# uv downloads a managed Python (no admin, no installer/registry) into
# UV_PYTHON_INSTALL_DIR. Safe to re-run: uv no-ops if the version is present.
#
# Also purges a stale .venv - one copied from another machine whose pyvenv.cfg
# still points at a python.exe that doesn't exist here - so `uv sync` rebuilds it
# with paths valid for THIS folder instead of erroring on the dead interpreter.
$ErrorActionPreference = 'Stop'
$root   = Split-Path -Parent $PSScriptRoot
$tools  = Join-Path $root 'tools'
$pyDir  = Join-Path $tools 'python'
$env:UV_PYTHON_INSTALL_DIR = $pyDir

# Drop a stale .venv (absolute python path from another machine) if its base
# interpreter is gone - uv then recreates a correct one during `uv sync`.
$cfg = Join-Path $root '.venv\pyvenv.cfg'
if (Test-Path $cfg) {
    $m = Select-String -Path $cfg -Pattern '^\s*home\s*=\s*(.+?)\s*$'
    if ($m) {
        $venvHome = $m.Matches[0].Groups[1].Value
        if (-not (Test-Path (Join-Path $venvHome 'python.exe'))) {
            Write-Host "Stale .venv (its Python '$venvHome' is missing) - removing so uv can rebuild it."
            Remove-Item -Recurse -Force (Join-Path $root '.venv')
        }
    }
}

$uv = Join-Path $tools 'uv.exe'
if (-not (Test-Path $uv)) { $uv = 'uv' }

Write-Host "Ensuring a portable Python under $pyDir ..."
& $uv python install
Write-Host "Python ready under $pyDir"
