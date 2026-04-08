#!/bin/bash

# 1. SETUP
mkdir -p epos_hq/logs
export PYTHONPATH=$PYTHONPATH:.

echo "🚀 INITIALIZING EPOS SOVEREIGN STACK..."
echo "========================================"

# 2. SIDECAR (Nervous System)
echo "🔵 Starting Sidecar (Port 8010)..."
source .venv/Scripts/activate
python -m epos_hq.sidecar.server > epos_hq/logs/sidecar.log 2>&1 &
SIDECAR_PID=$!
echo "   ✅ Sidecar Online (PID $SIDECAR_PID)"
sleep 3

# 3. ANALYST (The Brain)
echo "🧠 Starting Analyst Worker..."
python -m epos_hq.workers.analyst > epos_hq/logs/analyst.log 2>&1 &
ANALYST_PID=$!
echo "   ✅ Analyst Online (PID $ANALYST_PID)"

# 4. SHADOW COO (The Strategist)
echo "🕵️ Starting Extraction Worker..."
python -m epos_hq.workers.extraction > epos_hq/logs/extraction.log 2>&1 &
EXTRACTION_PID=$!
echo "   ✅ Shadow COO Online (PID $EXTRACTION_PID)"

# 5. CONSOLE (The Eyes)
echo "🛸 Launching Command Deck..."
echo "========================================"
echo "Press CTRL+C to Shutdown System"
echo "========================================"

streamlit run epos_hq/ui/console.py

cleanup() {
    echo ""
    echo "🛑 SHUTTING DOWN EPOS..."
    kill $SIDECAR_PID
    kill $ANALYST_PID
    kill $EXTRACTION_PID
    echo "✅ System Halted."
    exit
}

trap cleanup SIGINT
wait
