#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$root"

# Resolve the in-folder managed Python (matches install.sh).
export UV_PYTHON_INSTALL_DIR="$root/tools/python"
# Never fall back to a system Python: Homebrew's CPython is built without
# _tkinter, which the overlay needs. uv's managed build ships Tk.
export UV_PYTHON_PREFERENCE=only-managed

uv="$root/tools/uv"
if [ ! -x "$uv" ]; then
    if command -v uv >/dev/null 2>&1; then
        uv=uv
    else
        echo "[local_whisper_nemo] uv not found. Please run ./install.sh first." >&2
        exit 1
    fi
fi

exec "$uv" run python -m src.main
