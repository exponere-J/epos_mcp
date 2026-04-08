cat > launch_epos.sh << 'EOF'
#!/bin/bash

# Ensure we are running from the project root and Python can see the package
export PYTHONPATH=$PYTHONPATH:.

echo "🚀 INITIALIZING EPOS SOVEREIGN STACK (PACKAGE MODE)..."
echo "======================================================"

# 1. Start Sidecar (The Nervous System)
echo "🔵 Starting Sidecar (Port 8010)..."
source .venv/Scripts/activate
# USE MODULE SYNTAX (-m)
python -m epos_hq.sidecar.server > epos_hq/logs/sidecar.log 2>&1 &
SIDECAR_PID=$!
echo "   ✅ Sidecar Online (PID $SIDECAR_PID)"

# Wait for Sidecar to boot
sleep 3

# 2. Start Analyst (The Brain)
echo "🧠 Starting Analyst Worker..."
# USE MODULE SYNTAX (-m)
python -m epos_hq.workers.analyst > epos_hq/logs/analyst.log 2>&1 &
ANALYST_PID=$!
echo "   ✅ Analyst Online (PID $ANALYST_PID)"

# 3. Start Console (The Eyes)
echo "🛸 Launching Command Deck..."
echo "========================================"
echo "Press CTRL+C to Shutdown System"
echo "========================================"

mkdir -p epos_hq/logs

# Streamlit needs PYTHONPATH to see 'epos_hq' package
streamlit run epos_hq/ui/console.py

cleanup() {
    echo ""
    echo "🛑 SHUTTING DOWN EPOS..."
    kill $SIDECAR_PID
    kill $ANALYST_PID
    echo "✅ System Halted."
    exit
}

trap cleanup SIGINT
wait
EOF