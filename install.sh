#!/usr/bin/env bash
# One-time macOS install: vendor uv + a portable Python into tools/, sync
# dependencies, fetch the ASR model. macOS counterpart of install.bat.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$root"

# Keep the managed Python inside the folder so the deploy is self-contained.
export UV_PYTHON_INSTALL_DIR="$root/tools/python"
# Never fall back to a system Python: Homebrew's CPython is built without
# _tkinter, which the overlay needs. uv's managed build ships Tk.
export UV_PYTHON_PREFERENCE=only-managed

if [ ! -f .env ]; then
    echo "Creating .env from .env.example ..."
    cp .env.example .env
fi

echo "Ensuring uv is available (portable, no admin) ..."
"$root/scripts/bootstrap_uv.sh"

uv="$root/tools/uv"
[ -x "$uv" ] || uv=uv

echo "Ensuring a portable Python (no admin) ..."
"$root/scripts/bootstrap_python.sh"

echo "Installing dependencies with uv ..."
"$uv" sync

echo "Downloading ASR model ..."
"$uv" run python -m src.download_model

echo
echo "Installation complete. Launch with ./run.sh"
echo "Grant Terminal the Microphone, Accessibility and Input Monitoring"
echo "permissions in System Settings > Privacy & Security on first run."
