#!/usr/bin/env bash
# Ensure a portable CPython lives *inside* the project (tools/python) so the
# folder is self-contained and needs no system Python: uv downloads a managed
# Python (no admin, no installer) into UV_PYTHON_INSTALL_DIR. Safe to re-run.
#
# Also purges any .venv not built from that in-folder Python, so `uv sync`
# rebuilds it: one copied from another machine points at a path that is gone
# here, and one built against a system Python is a trap of its own - Homebrew's
# CPython ships without _tkinter, which the overlay needs.
# macOS counterpart of bootstrap_python.ps1.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export UV_PYTHON_INSTALL_DIR="$root/tools/python"

cfg="$root/.venv/pyvenv.cfg"
if [ -f "$cfg" ]; then
    venv_home="$(sed -n 's/^[[:space:]]*home[[:space:]]*=[[:space:]]*//p' "$cfg" | head -1)"
    case "$venv_home" in
        "$UV_PYTHON_INSTALL_DIR"/*) ;;
        *)
            echo "Rebuilding .venv: its Python '$venv_home' is not the in-folder one."
            rm -rf "$root/.venv"
            ;;
    esac
fi

uv="$root/tools/uv"
[ -x "$uv" ] || uv=uv

echo "Ensuring a portable Python under $UV_PYTHON_INSTALL_DIR ..."
"$uv" python install
echo "Python ready under $UV_PYTHON_INSTALL_DIR"
