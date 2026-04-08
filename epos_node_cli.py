#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos_node_cli.py — Node Operations CLI
========================================
Constitutional Authority: EPOS Constitution v3.1

Usage:
  python epos_node_cli.py event_bus --tail 10
  python epos_node_cli.py vault --search "LEGO"
  python epos_node_cli.py doctor
  python epos_node_cli.py graph --hooks lego_affiliate
  python epos_node_cli.py cms --stats
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")


def cmd_event_bus(args):
    """Tail or query the event bus."""
    from epos_event_bus import EPOSEventBus
    bus = EPOSEventBus()

    if args.tail:
        events = bus.get_recent(minutes=60)
        for e in events[-args.tail:]:
            ts = e.published_at[:19] if hasattr(e, "published_at") else "?"
            etype = e.event_type if hasattr(e, "event_type") else "?"
            src = e.source_module if hasattr(e, "source_module") else "?"
            print(f"  {ts} | {etype:<40} | {src}")
        print(f"\n  Total events in log: {bus.event_count()}")
    elif args.count:
        print(f"  Events in bus: {bus.event_count()}")


def cmd_vault(args):
    """Search the context vault."""
    from path_utils import get_context_vault
    vault = get_context_vault()

    if args.search:
        query = args.search.lower()
        matches = []
        for f in vault.rglob("*"):
            if f.is_file() and query in f.name.lower():
                matches.append(str(f.relative_to(vault)))
            elif f.is_file() and f.suffix in (".json", ".jsonl", ".md", ".txt"):
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")[:5000]
                    if query in content.lower():
                        matches.append(str(f.relative_to(vault)))
                except Exception:
                    pass
        print(f"\n  Vault search: '{args.search}' — {len(matches)} matches\n")
        for m in matches[:20]:
            print(f"    {m}")
    elif args.stats:
        namespaces = {}
        for d in vault.iterdir():
            if d.is_dir():
                count = sum(1 for _ in d.rglob("*") if _.is_file())
                namespaces[d.name] = count
        print(f"\n  Context Vault — {sum(namespaces.values())} files\n")
        for ns, count in sorted(namespaces.items()):
            print(f"    {ns}: {count}")


def cmd_doctor(args):
    """Run EPOS Doctor."""
    import subprocess
    result = subprocess.run(
        [sys.executable, "engine/epos_doctor.py"],
        capture_output=True, text=True, timeout=30,
        cwd=str(Path(__file__).parent),
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)


def cmd_graph(args):
    """Query the Context Graph."""
    from context_graph import ContextGraph
    graph = ContextGraph()

    if args.hooks:
        hooks = graph.query_best_hook_for_niche(args.hooks)
        print(f"\n  Hook performance for {args.hooks}:\n")
        for hook, weight in hooks:
            bar = "#" * int(weight * 20)
            print(f"    {hook:<15} {weight:.3f} {bar}")
    elif args.edges:
        data = json.loads(graph.GRAPH_PATH.read_text(encoding="utf-8"))
        print(f"\n  Graph: {len(data['nodes'])} nodes, {len(data['edges'])} edges\n")
        for eid, e in list(data["edges"].items())[:10]:
            print(f"    {eid}: {e['weight']:.3f} (evidence: {e['evidence_count']})")


def cmd_cms(args):
    """CMS operations."""
    from epos_cms import EPOSContentManagement
    cms = EPOSContentManagement()

    if args.stats:
        stats = cms.get_dashboard_stats()
        print(f"\n  CMS — {stats['total']} assets\n")
        for stage, count in stats["by_status"].items():
            if count > 0:
                print(f"    {stage}: {count}")
    elif args.search:
        results = cms.search(query=args.search, limit=10)
        print(f"\n  CMS search: '{args.search}' — {len(results)} results\n")
        for r in results:
            print(f"    [{r.get('asset_type','')}] {r.get('title','')[:50]} ({r.get('status','')})")


def main():
    parser = argparse.ArgumentParser(description="EPOS Node CLI")
    sub = parser.add_subparsers(dest="node")

    # Event bus
    eb = sub.add_parser("event_bus", help="Event bus operations")
    eb.add_argument("--tail", type=int, help="Show last N events")
    eb.add_argument("--count", action="store_true", help="Event count")

    # Vault
    v = sub.add_parser("vault", help="Context vault operations")
    v.add_argument("--search", type=str, help="Search vault")
    v.add_argument("--stats", action="store_true", help="Vault stats")

    # Doctor
    sub.add_parser("doctor", help="Run EPOS Doctor")

    # Graph
    g = sub.add_parser("graph", help="Context Graph operations")
    g.add_argument("--hooks", type=str, help="Hook performance for niche")
    g.add_argument("--edges", action="store_true", help="Show graph edges")

    # CMS
    c = sub.add_parser("cms", help="CMS operations")
    c.add_argument("--stats", action="store_true", help="CMS stats")
    c.add_argument("--search", type=str, help="Search CMS assets")

    args = parser.parse_args()

    handlers = {
        "event_bus": cmd_event_bus,
        "vault": cmd_vault,
        "doctor": cmd_doctor,
        "graph": cmd_graph,
        "cms": cmd_cms,
    }

    if args.node in handlers:
        handlers[args.node](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
