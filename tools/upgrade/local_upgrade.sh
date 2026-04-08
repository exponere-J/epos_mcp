#!/usr/bin/env bash
set -euo pipefail

echo "[EPOS] Local upgrade starting..."

# Must run from repo root
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

# If a venv is active, use it. Otherwise, proceed anyway.
python -V

echo "[EPOS] Installing/updating python deps..."
python -m pip install -U pip setuptools wheel

# Install app in editable mode (enables module injection + imports)
echo "[EPOS] Installing EPOS Console (editable)..."
python -m pip install -e .

echo "[EPOS] Upgrade complete."
