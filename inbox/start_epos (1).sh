#!/bin/bash
# EPOS Daily Startup Script
# Launches all EPOS services in correct order

echo "╔════════════════════════════════════════════════════════╗"
echo "║         EPOS STARTUP — Initializing Services          ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Check if Ollama is running
if ! pgrep -x "ollama" > /dev/null; then
    echo "▶ Starting Ollama..."
    ollama serve &
    sleep 3
else
    echo "✓ Ollama already running"
fi

# Start MCP servers (if implemented)
# echo "▶ Starting MCP servers..."
# python mcp/event_bus.py &
# python mcp/context_server.py &
# sleep 2

# Launch Phi-3 Command Center
echo "▶ Launching Phi-3 Command Center..."
echo "   Opening browser at http://localhost:8501"
echo ""
streamlit run phi3_command_center.py --server.port 8501

