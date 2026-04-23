#!/usr/bin/env bash
# EPOS Agent Zero — Startup Script
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X, XIV, XVI §3
#
# Boots Xvfb on :99 (so headed BrowserUse / ComputerUse can run inside the
# container without a real display), then launches the AZ bridge.
#
# Per-call headed/headless toggle: callers pass mode_hint to the execution
# arm; the container is permanently ready for either.

set -e

DISPLAY_NUM="${EPOS_XVFB_DISPLAY:-:99}"
SCREEN_GEOM="${EPOS_XVFB_SCREEN:-1280x800x24}"

echo "[az-start] booting Xvfb on $DISPLAY_NUM (screen $SCREEN_GEOM)"
Xvfb "$DISPLAY_NUM" -screen 0 "$SCREEN_GEOM" -ac +extension RANDR -nolisten tcp &
XVFB_PID=$!

# Give Xvfb a moment to initialize, then verify
sleep 0.5
if ! xdpyinfo -display "$DISPLAY_NUM" >/dev/null 2>&1; then
  echo "[az-start] WARNING: Xvfb did not become reachable on $DISPLAY_NUM"
  echo "[az-start]          headed mode may fall back to headless"
fi

# Optional: minimal window manager so apps that demand one don't crash.
if command -v fluxbox >/dev/null 2>&1; then
  fluxbox >/dev/null 2>&1 &
  echo "[az-start] fluxbox WM started"
fi

export DISPLAY="$DISPLAY_NUM"
echo "[az-start] DISPLAY=$DISPLAY exported; launching az_bridge.py"

# Trap to clean up Xvfb on exit
trap 'kill $XVFB_PID 2>/dev/null || true' EXIT

exec python az_bridge.py
