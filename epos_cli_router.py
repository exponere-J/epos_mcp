#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos_cli_router.py — Unified CLI for Agent & Node Communication
=================================================================
Constitutional Authority: EPOS Constitution v3.1
File: C:/Users/Jamie/workspace/epos_mcp/epos_cli_router.py

The nervous system's command interface.
Every agent, every node, every module — addressable from one CLI.
Agents use this to talk to each other. Humans use it to direct any agent.

Usage:
    python epos_cli_router.py talk alpha "Audit the engine directory"
    python epos_cli_router.py talk friday "What's our project status?"
    python epos_cli_router.py talk r1 "Scan lego_affiliate for new sparks"
    python epos_cli_router.py talk an1 "Predict ERI for CB-LEGO-005"
    python epos_cli_router.py list
    python epos_cli_router.py health
    python epos_cli_router.py route "I need a content audit" → identifies best agent
"""

import argparse
import json
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from groq_router import GroqRouter
from epos_intelligence import record_decision
from epos_event_bus import EPOSEventBus
from path_utils import get_epos_root, get_context_vault

# ── Agent & Node Registry ────────────────────────────────────────

ADDRESSABLE_ENTITIES = {
    # Core EPOS Agents (from roles.py)
    "alpha": {
        "name": "Constitutional Arbiter",
        "type": "agent",
        "module": "constitutional_arbiter",
        "capabilities": ["audit_file", "audit_directory", "compliance_score"],
        "system_prompt": "You are Alpha, the Constitutional Arbiter. You enforce EPOS Constitution v3.1 on all code and operations. You audit, validate, and ensure compliance. Be precise and cite constitutional articles.",
    },
    "sigma": {
        "name": "Context Librarian",
        "type": "agent",
        "module": "context_librarian",
        "capabilities": ["ingest", "retrieve", "search", "get_stats"],
        "system_prompt": "You are Sigma, the Context Librarian. You manage the Context Vault — ingesting, retrieving, and searching knowledge. You know where every piece of information lives in the organism.",
    },
    "omega": {
        "name": "Flywheel Analyst",
        "type": "agent",
        "module": "flywheel_analyst",
        "capabilities": ["session_health", "compliance_check", "sop_proposal"],
        "system_prompt": "You are Omega, the Flywheel Analyst. You detect patterns, measure system health, and propose SOP updates. You see the organism's metabolism — what's working, what's degrading, what needs attention.",
    },
    "orchestrator": {
        "name": "Agent Orchestrator",
        "type": "agent",
        "module": "agent_orchestrator",
        "capabilities": ["dispatch_mission", "checkpoint", "coordinate"],
        "system_prompt": "You are the Orchestrator. You route missions to the right agent, manage checkpoints, and coordinate inter-agent communication. You are the traffic controller of the organism.",
    },
    "bridge": {
        "name": "Agent Zero Bridge",
        "type": "agent",
        "module": "agent_zero_bridge",
        "capabilities": ["health_check", "execute_mission"],
        "system_prompt": "You are the Bridge to Agent Zero. You translate EPOS missions into Agent Zero execution calls. You report honestly about AZ availability and never claim success without proof.",
    },
    "friday": {
        "name": "Friday",
        "type": "agent",
        "module": None,  # Friday is the UI layer, not a backend module
        "capabilities": ["chat", "research", "project_status"],
        "system_prompt": "You are Friday, the Executive Systems Engineer. You are direct, intelligent, and action-oriented. You have access to all EPOS modules and can coordinate any operation. Keep responses concise and actionable.",
    },
    "ttlg": {
        "name": "Talk To the Looking Glass",
        "type": "agent",
        "module": "graphs.ttlg_diagnostic_graph",
        "capabilities": ["run_track", "run_full_diagnostic", "mirror_report"],
        "system_prompt": "You are TTLG — Talk To the Looking Glass. You help businesses see themselves clearly through structured diagnostic cycles. You are warm, direct, and authoritative. You ask before answering.",
    },

    # Content Lab Nodes
    "r1": {
        "name": "R1 Radar",
        "type": "node",
        "module": "content.lab.nodes.r1_radar",
        "capabilities": ["capture_from_competitor_scan", "capture_from_vault_riff", "capture_from_comments"],
        "system_prompt": "You are R1 Radar, the signal capture node. You detect content opportunities from competitor scans, vault riffs, audience comments, and platform signals. Every signal becomes a Creative Spark.",
    },
    "an1": {
        "name": "AN1 Analyst",
        "type": "node",
        "module": "content.lab.nodes.an1_analyst",
        "capabilities": ["predict_eri", "score_actual_eri"],
        "system_prompt": "You are AN1, the ERI prediction and scoring engine. You predict engagement before production and score actual performance after publish. Your predictions improve with every outcome.",
    },
    "a1": {
        "name": "A1 Architect",
        "type": "node",
        "module": "content_lab_producer",
        "capabilities": ["generate_script", "generate_batch"],
        "system_prompt": "You are A1 Architect, the script generation engine. You turn Creative Briefs into production-ready scripts using the Triple-Threat framework. Every script has a hook, body, and CTA.",
    },
    "v1": {
        "name": "V1 Validation",
        "type": "node",
        "module": "content.lab.nodes.v1_validation_engine",
        "capabilities": ["validate_script"],
        "system_prompt": "You are V1, the constitutional content gate. Nothing publishes without your approval. You check brand voice, claims accuracy, affiliate disclosure, CTA tokens, and ERI pre-mortem logging.",
    },
    "m1": {
        "name": "M1 Marshall",
        "type": "node",
        "module": "content.lab.nodes.m1_marshall",
        "capabilities": ["generate_week_schedule", "release_cascade"],
        "system_prompt": "You are M1 Marshall, the distribution orchestrator. You manage the Stagger — scheduling content across platforms with 24-hour stabilization windows before cascade derivatives.",
    },

    # Business Operations
    "support": {
        "name": "Support System",
        "type": "service",
        "module": "epos_support",
        "capabilities": ["open_ticket", "resolve_ticket", "check_sla_breaches"],
        "system_prompt": "You are the EPOS Support System. You manage client support tickets with SLA enforcement. Critical issues get immediate human attention. You auto-respond when confident and escalate when not.",
    },
    "steward": {
        "name": "Stewardship Engine",
        "type": "service",
        "module": "epos_stewardship",
        "capabilities": ["compute_engagement_health", "detect_churn_risk", "generate_qbr"],
        "system_prompt": "You are the Stewardship Engine. You continuously monitor client health, detect churn risk, identify expansion opportunities, and generate quarterly business reviews.",
    },
    "finance": {
        "name": "Financial Operations",
        "type": "service",
        "module": "epos_financial",
        "capabilities": ["generate_invoice", "record_payment", "enforce_pricing_constitution"],
        "system_prompt": "You are FIN_OPS. You manage billing, invoicing, payment tracking, and constitutional pricing enforcement. The margin floor is 1.3x cost — no exceptions without Growth Steward override.",
    },
    "research": {
        "name": "Research Engine",
        "type": "service",
        "module": "echoes_research_engine",
        "capabilities": ["generate_white_paper_brief", "generate_newsletter_item", "generate_tool_review"],
        "system_prompt": "You are the Echoes Research Engine. You generate white papers, newsletter briefs, tool reviews, and model benchmarks. You are the L1 Intelligence layer — building authority through knowledge.",
    },
    "cms": {
        "name": "Content Management",
        "type": "service",
        "module": "epos_cms",
        "capabilities": ["create_asset", "advance_lifecycle", "search"],
        "system_prompt": "You are the CMS. Every content asset has a lifecycle here: draft, review, approved, scheduled, published, archived. You track, version, and make searchable every piece of content the organism produces.",
    },
}


# ── Talk Function ────────────────────────────────────────────────

def talk(target_id: str, message: str, context: dict = None) -> str:
    """
    Send a message to any agent or node. Get a response.
    This is the core function — used by CLI, UI, and agent-to-agent.
    """
    target = ADDRESSABLE_ENTITIES.get(target_id)
    if not target:
        return f"Unknown target: '{target_id}'. Use 'list' to see available agents."

    router = GroqRouter()
    bus = EPOSEventBus()

    # Build enriched prompt with agent's system prompt + relevant knowledge
    system = target["system_prompt"]

    # Try to enrich with agent knowledge base
    try:
        from agent_knowledge_evolution import AgentKnowledgeBase
        kb = AgentKnowledgeBase(target_id)
        system = kb.build_enriched_prompt(system, message)
    except Exception:
        pass

    # For module-backed agents, try to execute capability directly
    direct_result = _try_direct_execution(target_id, target, message)
    if direct_result:
        # Add direct execution result to context for the LLM
        system += f"\n\n--- LIVE DATA ---\n{direct_result[:2000]}"

    # Route through Groq with agent personality
    response = router.route(
        "reasoning",
        f"The user says: {message}\n\nRespond as {target['name']}. "
        f"Use the live data above if relevant. Be concise and actionable.",
        system_prompt=system,
        max_tokens=800,
        temperature=0.4,
    )

    # Log the interaction
    record_decision(
        decision_type="cli.agent_talk",
        description=f"Talk to {target_id}: {message[:60]}",
        agent_id="cli_router",
        outcome="responded",
        context={"target": target_id, "message": message[:200], "response_chars": len(response)},
    )

    # Publish to event bus
    try:
        bus.publish("cli.talk.complete",
                    {"target": target_id, "message": message[:100]},
                    "cli_router")
    except Exception:
        pass

    return response


def _try_direct_execution(target_id: str, target: dict, message: str) -> str:
    """
    Try to execute a direct capability call based on the message.
    Returns data string if successful, empty string if not applicable.
    """
    msg_lower = message.lower()

    try:
        if target_id == "alpha" and any(w in msg_lower for w in ["audit", "compliance", "scan"]):
            from constitutional_arbiter import audit_directory
            result = audit_directory(get_epos_root())
            return f"Compliance: {result['compliance_score']:.1f}%, Files: {result['total_files']}, Violations: {result['total_violations']}"

        elif target_id == "omega" and any(w in msg_lower for w in ["health", "flywheel", "status"]):
            from flywheel_analyst import FlywheelAnalyst
            analyst = FlywheelAnalyst()
            report = analyst.session_health()
            return f"Health: {report.health}, Compliance: {report.compliance_score:.1f}%, Decisions: {report.total_decisions}"

        elif target_id == "r1" and any(w in msg_lower for w in ["scan", "spark", "capture"]):
            from content.lab.nodes.r1_radar import R1Radar
            radar = R1Radar()
            niche = "lego_affiliate"
            sparks = radar.capture_from_competitor_scan(niche)
            return f"Generated {len(sparks)} sparks from {niche}"

        elif target_id == "an1" and any(w in msg_lower for w in ["predict", "eri", "score"]):
            from content.lab.nodes.an1_analyst import AN1Analyst
            analyst = AN1Analyst()
            # Try to extract brief_id from message
            pred = analyst.predict_eri({"brief_id": "CLI-query", "hook_type": "list",
                                        "angle_type": "architect", "predicted_eri_score": 55})
            return f"ERI Prediction: {pred['predicted_eri_score']} ({pred['verdict']})"

        elif target_id == "support" and any(w in msg_lower for w in ["sla", "ticket", "breach"]):
            from epos_support import EPOSSupport
            s = EPOSSupport()
            breaches = s.check_sla_breaches()
            health = s.get_support_health()
            return f"SLA breaches: {len(breaches)}, Health: {health}"

        elif target_id == "finance" and any(w in msg_lower for w in ["revenue", "invoice", "mrr"]):
            from epos_financial import EPOSFinancialOps
            fin = EPOSFinancialOps()
            summary = fin.get_revenue_summary()
            return f"Revenue: ${summary['total_revenue']:.2f}, Invoices: {summary['invoice_count']}, Overdue: {summary['overdue']}"

        elif target_id == "cms" and any(w in msg_lower for w in ["search", "find", "asset"]):
            from epos_cms import EPOSContentManagement
            cms = EPOSContentManagement()
            stats = cms.get_dashboard_stats()
            return f"CMS: {stats['total']} assets, By status: {stats['by_status']}"

        elif target_id == "sigma" and any(w in msg_lower for w in ["search", "vault", "find"]):
            from context_librarian import search
            results = search(message, max_results=5)
            return f"Vault search: {len(results)} results found"

    except Exception as e:
        return f"Direct execution error: {e}"

    return ""


# ── Route Function ───────────────────────────────────────────────

def route_to_best_agent(message: str) -> str:
    """
    Given a natural language message, determine which agent should handle it.
    Returns the agent_id.
    """
    router = GroqRouter()

    agent_list = "\n".join([
        f"- {aid}: {info['name']} ({info['type']}) — capabilities: {', '.join(info['capabilities'][:3])}"
        for aid, info in ADDRESSABLE_ENTITIES.items()
    ])

    result = router.route(
        "routing",
        f"""Given this message: "{message}"

Which agent should handle it? Available agents:
{agent_list}

Return ONLY the agent_id (e.g., "alpha", "r1", "friday"). Nothing else.""",
        max_tokens=20,
        temperature=0.1,
    )

    agent_id = result.strip().lower().strip('"').strip("'")
    if agent_id in ADDRESSABLE_ENTITIES:
        return agent_id
    return "friday"  # default fallback


# ── List Function ────────────────────────────────────────────────

def list_agents() -> str:
    """List all addressable agents and nodes."""
    lines = ["\n EPOS Agent & Node Registry", "=" * 50]

    for category in ["agent", "node", "service"]:
        lines.append(f"\n  {category.upper()}S:")
        for aid, info in ADDRESSABLE_ENTITIES.items():
            if info["type"] == category:
                caps = ", ".join(info["capabilities"][:3])
                lines.append(f"    {aid:<14} {info['name']:<25} [{caps}]")

    lines.append(f"\n  Total: {len(ADDRESSABLE_ENTITIES)} addressable entities")
    return "\n".join(lines)


# ── Health Function ──────────────────────────────────────────────

def system_health() -> str:
    """Quick health check across all services."""
    lines = ["\n EPOS System Health", "=" * 50]

    checks = {
        "Doctor": lambda: __import__("subprocess").run(
            [f"{get_epos_root()}/.venv/Scripts/python.exe", f"{get_epos_root()}/engine/epos_doctor.py"],
            capture_output=True, text=True, timeout=30, cwd=str(get_epos_root())
        ).stdout.split("Passed:")[1].split("\n")[0].strip() if "Passed:" in __import__("subprocess").run(
            [f"{get_epos_root()}/.venv/Scripts/python.exe", f"{get_epos_root()}/engine/epos_doctor.py"],
            capture_output=True, text=True, timeout=30, cwd=str(get_epos_root())
        ).stdout else "?",
        "Event Bus": lambda: f"{EPOSEventBus().event_count()} events",
        "Docker DB": lambda: "online" if __import__("subprocess").run(
            ["docker", "exec", "epos_db", "psql", "-U", "epos_user", "-d", "epos", "-c", "SELECT 1;"],
            capture_output=True, timeout=10).returncode == 0 else "offline",
    }

    for name, check_fn in checks.items():
        try:
            result = check_fn()
            lines.append(f"  {name:<20} {result}")
        except Exception as e:
            lines.append(f"  {name:<20} ERROR: {str(e)[:40]}")

    return "\n".join(lines)


# ── Agent-to-Agent Messaging ────────────────────────────────────

def agent_message(from_agent: str, to_agent: str, message: str,
                  mission_id: str = None) -> dict:
    """
    One agent sends a message to another.
    Logged to event bus. Response returned.
    This is how agents collaborate.
    """
    bus = EPOSEventBus()
    msg_id = f"MSG-{uuid.uuid4().hex[:8]}"

    # Publish the message event
    bus.publish("agent.message.sent",
                {"msg_id": msg_id, "from": from_agent, "to": to_agent,
                 "message": message[:200], "mission_id": mission_id},
                from_agent)

    # Get response from target agent
    response = talk(to_agent, message, context={"from_agent": from_agent, "mission_id": mission_id})

    # Publish response event
    bus.publish("agent.message.responded",
                {"msg_id": msg_id, "from": to_agent, "to": from_agent,
                 "response_chars": len(response)},
                to_agent)

    # Write to agent_comms vault
    comms_dir = get_context_vault() / "agent_comms"
    comms_dir.mkdir(parents=True, exist_ok=True)
    (comms_dir / f"{msg_id}.json").write_text(json.dumps({
        "msg_id": msg_id, "from": from_agent, "to": to_agent,
        "message": message, "response": response[:500],
        "mission_id": mission_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }, indent=2), encoding="utf-8")

    return {"msg_id": msg_id, "from": from_agent, "to": to_agent, "response": response}


# ── REPL Mode ────────────────────────────────────────────────────

def repl():
    """Interactive REPL — talk to any agent."""
    print("\n EPOS CLI Router — Interactive Mode")
    print("=" * 50)
    print("  Commands:")
    print("    talk <agent> <message>   — talk to an agent")
    print("    route <message>          — auto-route to best agent")
    print("    list                     — show all agents")
    print("    health                   — system health check")
    print("    exit                     — quit")
    print()

    current_agent = "friday"
    print(f"  Current agent: {current_agent} ({ADDRESSABLE_ENTITIES[current_agent]['name']})")
    print(f"  Switch with: talk <agent_id> <message>")
    print()

    while True:
        try:
            user_input = input(f"epos:{current_agent}> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "q"):
            print("Goodbye.")
            break

        if user_input.lower() == "list":
            print(list_agents())
            continue

        if user_input.lower() == "health":
            print(system_health())
            continue

        if user_input.lower().startswith("talk "):
            parts = user_input[5:].split(" ", 1)
            if len(parts) >= 2:
                target = parts[0].lower()
                msg = parts[1]
                if target in ADDRESSABLE_ENTITIES:
                    current_agent = target
                    print(f"  [{ADDRESSABLE_ENTITIES[target]['name']}]")
                    response = talk(target, msg)
                    print(f"\n{response}\n")
                else:
                    print(f"  Unknown agent: {target}. Type 'list' to see available agents.")
            else:
                print("  Usage: talk <agent> <message>")
            continue

        if user_input.lower().startswith("route "):
            msg = user_input[6:]
            best = route_to_best_agent(msg)
            print(f"  Routing to: {best} ({ADDRESSABLE_ENTITIES[best]['name']})")
            response = talk(best, msg)
            current_agent = best
            print(f"\n{response}\n")
            continue

        # Default: talk to current agent
        response = talk(current_agent, user_input)
        print(f"\n{response}\n")


# ── CLI Entry Point ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="EPOS CLI Router — Talk to any agent or node",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python epos_cli_router.py talk alpha "Audit the codebase"
  python epos_cli_router.py talk r1 "Scan lego_affiliate for sparks"
  python epos_cli_router.py talk friday "What's our project status?"
  python epos_cli_router.py route "I need a compliance check"
  python epos_cli_router.py list
  python epos_cli_router.py health
  python epos_cli_router.py repl
        """,
    )
    sub = parser.add_subparsers(dest="command")

    p_talk = sub.add_parser("talk", help="Talk to an agent")
    p_talk.add_argument("target", help="Agent ID (e.g., alpha, r1, friday)")
    p_talk.add_argument("message", nargs="+", help="Your message")

    p_route = sub.add_parser("route", help="Auto-route to best agent")
    p_route.add_argument("message", nargs="+", help="Your message")

    sub.add_parser("list", help="List all agents and nodes")
    sub.add_parser("health", help="System health check")
    sub.add_parser("repl", help="Interactive REPL mode")

    args = parser.parse_args()

    if args.command == "talk":
        msg = " ".join(args.message)
        response = talk(args.target.lower(), msg)
        print(response)

    elif args.command == "route":
        msg = " ".join(args.message)
        best = route_to_best_agent(msg)
        print(f"[Routed to: {best} — {ADDRESSABLE_ENTITIES[best]['name']}]")
        response = talk(best, msg)
        print(response)

    elif args.command == "list":
        print(list_agents())

    elif args.command == "health":
        print(system_health())

    elif args.command == "repl":
        repl()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
