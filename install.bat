@echo off
cd /d "%~dp0"

rem Keep the managed Python inside the folder so the deploy is self-contained.
set "UV_PYTHON_INSTALL_DIR=%~dp0tools\python"

if not exist ".env" (
    echo Creating .env from .env.example ...
    copy /y ".env.example" ".env" >nul
)

echo Ensuring uv is available (portable, no admin) ...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\bootstrap_uv.ps1" || goto :error

set "UV=%~dp0tools\uv.exe"
if not exist "%UV%" set "UV=uv"

echo Ensuring a portable Python (no admin) ...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\bootstrap_python.ps1" || goto :error

echo Installing dependencies with uv ...
"%UV%" sync || goto :error

echo Downloading ASR model ...
"%UV%" run python -m src.download_model || goto :error

echo Creating desktop shortcut ...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\create_shortcut.ps1"

echo.
echo Installation complete. Launch with run.bat or the desktop shortcut.
pause
exit /b 0

:error
echo.
echo Installation failed. See messages above.
pause
exit /b 1
