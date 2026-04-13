# =============================================================================
# EPOS SOVEREIGN STACK — Root Dockerfile
# Base: python:3.11-slim
# Entrypoint: command_center (FastAPI, port 8001)
# Created: 2026-04-08 (M2 Docker migration)
# =============================================================================

FROM python:3.11-slim

# System dependencies: lxml, browser automation, build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser (Chromium only)
RUN playwright install chromium --with-deps

# Install Node.js + Claude Code CLI (|| true — graceful if unavailable)
RUN apt-get update && apt-get install -y --no-install-recommends nodejs npm \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g @anthropic-ai/claude-code || true

# Copy application source
COPY . .

# Runtime environment
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV EPOS_ROOT=/app
ENV LLM_MODE=groq_direct

# Health check: import doctor, verify EPOS is wired
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "from engine.epos_doctor import EPOSDoctor; EPOSDoctor()" || exit 1

# Default: run the command center API
CMD ["uvicorn", "command_center:app", "--host", "0.0.0.0", "--port", "8001"]
