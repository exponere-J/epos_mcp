#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
claude_code_executor.py — DEPRECATED compatibility shim
=========================================================
The Sovereign Coding Component (SCC) has replaced Desktop CODE.
This file exists only for import compatibility during transition.

Use scc_executor.py and SCCExecutor directly.
This shim will be removed in a future session.
"""

# Re-export everything from the canonical SCC executor
from friday.executors.scc_executor import SCCExecutor, run, _publish

# Legacy alias — code that imported ClaudeCodeExecutor still works
ClaudeCodeExecutor = SCCExecutor
