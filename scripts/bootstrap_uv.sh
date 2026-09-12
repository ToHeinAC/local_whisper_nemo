#!/usr/bin/env bash
# Ensure a local, self-contained uv exists under tools/ so the app needs no
# pre-installed uv and no admin rights. Downloads the portable uv binary from
# GitHub releases (a single static executable). Safe to re-run: no-op if already
# present. macOS counterpart of bootstrap_uv.ps1.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tools="$root/tools"
uv="$tools/uv"

if [ -x "$uv" ]; then
    echo "uv already vendored: $uv"
    exit 0
fi

mkdir -p "$tools"

# If uv is already on PATH, copy it in so the folder stays self-contained/portable.
if on_path="$(command -v uv)"; then
    cp "$on_path" "$uv"
    echo "Vendored uv from PATH: $on_path"
    exit 0
fi

case "$(uname -m)" in
    arm64) target="aarch64-apple-darwin" ;;
    x86_64) target="x86_64-apple-darwin" ;;
    *) echo "Unsupported architecture: $(uname -m)" >&2; exit 1 ;;
esac

tarball="uv-$target.tar.gz"
url="https://github.com/astral-sh/uv/releases/latest/download/$tarball"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

echo "Downloading portable uv (no admin) from $url ..."
curl -fsSL "$url" -o "$tmp/$tarball"
tar -xzf "$tmp/$tarball" -C "$tmp"
cp "$tmp/uv-$target/uv" "$uv"
chmod +x "$uv"
echo "uv ready: $uv"
