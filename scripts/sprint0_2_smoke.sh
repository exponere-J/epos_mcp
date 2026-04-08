#!/usr/bin/env bash
set -euo pipefail

echo "[1/4] Installing python deps..."
python -m pip install --upgrade pip >/dev/null
python -m pip install requests jsonschema >/dev/null

echo "[2/4] Pinging Ollama..."
python -c "from engine.llm_client import ping; import json; print(json.dumps(ping(), indent=2)[:1500])"

echo "[3/4] Running Duet worker once..."
# Set models (adjust if phi4 isn't available yet)
export LLM_MODE="ollama"
export LLM_BASE_URL="${LLM_BASE_URL:-http://localhost:11434}"
export CADENCE_MODEL="${CADENCE_MODEL:-phi3:mini}"
export METAPHOR_MODEL="${METAPHOR_MODEL:-phi4}"
export CRITIC_MODEL="${CRITIC_MODEL:-mistral:instruct}"

python -m engine.duet_sprint_worker

echo "[4/4] Showing output..."
ls -la out/duet_runs || true
echo "Latest contract:"
ls -t out/duet_runs/duet_contract_*.json 2>/dev/null | head -n 1 | xargs -I{} sh -c 'echo {}; python -c "import json; print(json.dumps(json.load(open(\"{}\")), indent=2)[:2000])"'
