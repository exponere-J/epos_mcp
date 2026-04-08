#!/bin/bash
# EPOS FOTW Wake-Triggered Scanner
# ==================================
# Source this from your .bashrc to run FOTW scan once per 12-hour window
# on terminal open.
#
# Installation:
#   echo "source ~/workspace/epos_mcp/scripts/bashrc_fotw_hook.sh" >> ~/.bashrc
#
# Or for Windows Git Bash / WSL:
#   echo "source /c/Users/Jamie/workspace/epos_mcp/scripts/bashrc_fotw_hook.sh" >> ~/.bashrc

_epos_fotw_wake() {
  local stamp="$HOME/.epos_last_fotw_scan"
  local now=$(date +%s)

  if [ -f "$stamp" ]; then
    local last=$(cat "$stamp")
    local diff=$((now - last))
    if [ "$diff" -lt 43200 ]; then
      # Less than 12 hours since last scan — skip
      return 0
    fi
  fi

  # Update timestamp
  echo "$now" > "$stamp"

  # Run FOTW scan in background — never block terminal startup
  (
    cd "$HOME/workspace/epos_mcp" 2>/dev/null || cd /c/Users/Jamie/workspace/epos_mcp 2>/dev/null
    if [ -f "epos.py" ]; then
      python epos.py fotw scan > /dev/null 2>&1 &
    fi
  ) &
}

# Run on shell start
_epos_fotw_wake

# Optional: expose as command for manual trigger
alias epos-fotw-wake='_epos_fotw_wake'
