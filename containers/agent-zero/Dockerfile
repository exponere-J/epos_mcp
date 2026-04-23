# EPOS Agent Zero — Governed Autonomous Executor + Execution Arm
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X, XIV, XVI
#
# This image carries the four execution-arm variants:
#   browser_use.headless    browser_use.headed
#   computer_use.headless   computer_use.headed
#
# Headed mode runs on Xvfb :99 inside the container; host-side X11 or
# VNC forwarding can attach for Sovereign observability.

FROM python:3.11-slim

LABEL maintainer="EPOS System"
LABEL constitutional_authority="Articles V, X, XIV, XVI"
LABEL role="governed_executor_with_arms"

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    EPOS_ARM_LOG_DIR=/app/context_vault/execution_arm \
    EPOS_DELETION_LOG=/app/context_vault/bi/deletion_attempts.jsonl \
    DISPLAY=:99 \
    EPOS_XVFB_DISPLAY=:99 \
    EPOS_HEADED_DEFAULT=false

WORKDIR /app

# ── System deps ─────────────────────────────────────────────────
# - xvfb      : virtual framebuffer for headless-headed runs
# - xdotool   : mouse/keyboard control for ComputerUse
# - scrot     : screenshot tool
# - x11-utils : xdpyinfo (display probing)
# - fluxbox   : minimal WM so apps that demand one have something
# - fonts + locales so rendered pages and apps look normal
# - Chromium runtime deps (installed by Playwright below)
RUN apt-get update && apt-get install -y --no-install-recommends \
        git curl ca-certificates \
        xvfb xdotool scrot x11-utils fluxbox \
        fonts-liberation fonts-noto-core \
        locales \
    && sed -i 's/^# *\(en_US.UTF-8\)/\1/' /etc/locale.gen \
    && locale-gen \
    && rm -rf /var/lib/apt/lists/*

ENV LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8

# ── Python deps ─────────────────────────────────────────────────
RUN pip install --upgrade pip \
 && pip install \
        requests \
        python-dotenv \
        "anthropic>=0.40.0" \
        "browser-use>=0.1.40" \
        "playwright>=1.45.0" \
        "firecrawl-py>=1.0.0" \
        "notebooklm-py>=0.1.0" \
        "fastapi>=0.110.0" \
        "uvicorn>=0.29.0" \
        "httpx>=0.27.0"

# Install only Chromium (skipping firefox/webkit saves ~700MB).
RUN playwright install --with-deps chromium

# ── App code ────────────────────────────────────────────────────
# engine/ — governance + event bus primitives shared with the bridge
COPY engine/ ./engine/

# nodes/execution_arm/ — the four-variant arm + Firecrawl arm
COPY nodes/execution_arm/ ./nodes/execution_arm/
# nodes/bridge/ — ingestion runner + persona reloader + directive queue
COPY nodes/bridge/ ./nodes/bridge/
# nodes/scc/personas/ — Architect persona for SCC proxy mode
COPY nodes/scc/personas/ ./nodes/scc/personas/
# path_utils referenced by various nodes; safe to include
COPY path_utils.py ./path_utils.py

# Agent Zero bridge (HTTP + event bus + inbox router)
COPY containers/agent-zero/az_bridge.py ./az_bridge.py

# Xvfb startup script — boots virtual display before az_bridge starts
COPY containers/agent-zero/start.sh ./start.sh
RUN chmod +x /app/start.sh

RUN mkdir -p /app/inbox /app/outbox /app/context_vault \
             /app/context_vault/execution_arm /app/context_vault/bi

EXPOSE 8105

# Healthcheck — HTTP /api/health
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8105/api/health || exit 1

# Entrypoint starts Xvfb then the bridge.
# Headed/headless toggle is per-call (mode_hint) — the container always
# has a virtual display ready; "headless" still works (Chromium ignores DISPLAY).
CMD ["/app/start.sh"]
