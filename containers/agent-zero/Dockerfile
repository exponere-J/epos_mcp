# Agent Zero Container - Governed Autonomous Executor
# Constitutional Authority: Article V (Agents)
FROM python:3.11-slim

LABEL maintainer="EPOS System"
LABEL constitutional_authority="Article_V"
LABEL role="governed_executor"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy EPOS engine for governance integration
COPY engine/ ./engine/

# Create required directories
RUN mkdir -p /app/inbox /app/outbox /app/context_vault

# Copy Agent Zero bridge
COPY containers/agent-zero/az_bridge.py ./az_bridge.py

EXPOSE 8105

# Governed entry point
CMD ["python", "az_bridge.py"]
