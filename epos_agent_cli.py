#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos_agent_cli.py — Agent Communication CLI
=============================================
Constitutional Authority: EPOS Constitution v3.1

Usage:
  python epos_agent_cli.py --list
  python epos_agent_cli.py --agent doctor
  python epos_agent_cli.py --agent friday --message "what is our health?"
  python epos_agent_cli.py --chat
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

from epos_cli_router import ADDRESSABLE_ENTITIES, agent_message, list_agents


def cmd_list():
    """List all addressable agents."""
    print(f"\nEPOS Agent Registry — {len(ADDRESSABLE_ENTITIES)} agents\n")
    print(f"  {'ID':<20} {'Description'}")
    print(f"  {'-'*20} {'-'*50}")
    for agent_id, info in sorted(ADDRESSABLE_ENTITIES.items()):
        desc = info.get("description", "") if isinstance(info, dict) else str(info)[:50]
        print(f"  {agent_id:<20} {desc[:50]}")
    print()


def cmd_agent(agent_id: str, message: str = None):
    """Send a message to a specific agent."""
    if agent_id not in ADDRESSABLE_ENTITIES:
        print(f"Unknown agent: {agent_id}")
        print(f"Available: {', '.join(sorted(ADDRESSABLE_ENTITIES.keys()))}")
        return

    if not message:
        # Default action per agent
        message = "health_check"

    result = agent_message(agent_id, message)
    if isinstance(result, dict):
        print(json.dumps(result, indent=2, default=str))
    else:
        print(result)


def cmd_chat():
    """Interactive agent chat REPL."""
    print("\nEPOS Agent Chat — type 'exit' to quit")
    print(f"Available agents: {', '.join(sorted(ADDRESSABLE_ENTITIES.keys()))}")
    print("Format: @agent_id message  (e.g., @doctor health_check)\n")

    while True:
        try:
            user_input = input("epos> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input or user_input.lower() in ("exit", "quit", "q"):
            if user_input.lower() in ("exit", "quit", "q"):
                print("Goodbye.")
            break

        if user_input.startswith("@"):
            parts = user_input[1:].split(" ", 1)
            agent_id = parts[0]
            message = parts[1] if len(parts) > 1 else "health_check"
            result = agent_message(agent_id, message)
            if isinstance(result, dict):
                print(json.dumps(result, indent=2, default=str))
            else:
                print(result)
        else:
            # Default to friday
            result = agent_message("friday", user_input)
            print(result if not isinstance(result, dict)
                  else json.dumps(result, indent=2, default=str))


def main():
    parser = argparse.ArgumentParser(description="EPOS Agent CLI")
    parser.add_argument("--list", action="store_true", help="List all agents")
    parser.add_argument("--agent", type=str, help="Agent ID to communicate with")
    parser.add_argument("--message", "-m", type=str, help="Message to send")
    parser.add_argument("--chat", action="store_true", help="Interactive chat mode")
    args = parser.parse_args()

    if args.list:
        cmd_list()
    elif args.agent:
        cmd_agent(args.agent, args.message)
    elif args.chat:
        cmd_chat()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
