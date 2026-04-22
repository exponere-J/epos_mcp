# EPOS MiroFish — Swarm Intelligence Simulator (Stage 1)
# Constitutional Authority: Articles V, X, XIV, XVI §2

FROM python:3.11-slim

LABEL maintainer="EPOS System"
LABEL constitutional_authority="Articles V, X, XVI §2"
LABEL role="simulation_engine"

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MIROFISH_PORT=8110 \
    MIROFISH_RESULTS=/app/results

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

COPY containers/mirofish/requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY containers/mirofish/simulator.py ./simulator.py
COPY nodes/simulation/avatars.py ./avatars.py
COPY nodes/simulation/scenario.py ./scenario.py

RUN mkdir -p /app/results

EXPOSE 8110

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8110/health || exit 1

CMD ["python", "simulator.py"]
