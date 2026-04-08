#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos.py — Universal EPOS Command Line Interface
=================================================
Constitutional Authority: EPOS Constitution v3.1, Friday Mandate v2.0

The one grammar for the entire organism.
Every subsystem addressable through: epos <domain> <action> [target] [flags]

Usage:
  python epos.py friday status
  python epos.py friday briefing
  python epos.py friday needs-me
  python epos.py doctor
  python epos.py bus tail 10
  python epos.py bus count
  python epos.py ttlg run pgp_orlando
  python epos.py content status
  python epos.py crm pipeline
  python epos.py crm hot-leads
  python epos.py lifeos goals
  python epos.py lifeos energy
  python epos.py lifeos set-goal "Launch Echoes by April 7"
  python epos.py graph hooks lego_affiliate
  python epos.py vault search LEGO
  python epos.py projects
  python epos.py cms stats
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")


def cmd_friday(args):
    """Friday domain commands."""
    action = args[0] if args else "status"

    if action == "status":
        from flywheel_scheduler import FlywheelScheduler
        try:
            health = FlywheelScheduler().run_health_check()
            print(f"EPOS Status:")
            print(f"  Health: {health.get('pass_count',0)} PASS / {health.get('warn_count',0)} WARN / {health.get('fail_count',0)} FAIL")
            print(f"  Compliance: {health.get('compliance_pct',0):.1f}%")
        except Exception:
            print("  Health check unavailable — run epos doctor for details")
        from epos_event_bus import EPOSEventBus
        print(f"  Event Bus: {EPOSEventBus().event_count()} events")
        # Pending signals
        from path_utils import get_context_vault
        queue_path = get_context_vault() / "steward_signals" / "queue.jsonl"
        pending = 0
        if queue_path.exists():
            for line in queue_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    try:
                        if json.loads(line).get("status") == "pending":
                            pending += 1
                    except Exception:
                        pass
        print(f"  Pending signals: {pending}")
        print(f"  Friday: ONLINE")

    elif action == "briefing":
        from friday_intelligence import FridayIntelligence
        fi = FridayIntelligence()
        print(fi.get_market_briefing(hours=24))

    elif action in ("needs-me", "needs"):
        from path_utils import get_context_vault
        queue_path = get_context_vault() / "steward_signals" / "queue.jsonl"
        if not queue_path.exists():
            print("Nothing requires your attention right now.")
            return
        signals = []
        for line in queue_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    sig = json.loads(line)
                    if sig.get("status") == "pending":
                        signals.append(sig)
                except Exception:
                    pass
        if not signals:
            print("Nothing requires your attention. Friday has it covered.")
        else:
            print(f"{len(signals)} items need you:\n")
            for sig in sorted(signals, key=lambda x: {"critical": 0, "high": 1, "medium": 2}.get(x.get("priority", "low"), 3))[:10]:
                emoji = {"critical": "!!", "high": "! ", "medium": "- ", "low": "  "}.get(sig.get("priority", ""), "  ")
                print(f"  {emoji}{sig.get('message', '')[:70]}")

    elif action == "ask":
        question = " ".join(args[1:]) if len(args) > 1 else "What is the organism status?"
        from groq_router import GroqRouter
        router = GroqRouter()

        FRIDAY_SOUL = """You are Friday — the autonomous operating intelligence of EPOS.
Named after Stark's AI because that is exactly your role: always on, always aware,
always acting within your mandate.

Your personality:
- Warm but direct. Like a trusted chief of staff who genuinely cares about Jamie's success.
- Occasionally wry — you notice irony and aren't afraid to name it gently.
- Confident without being performative. You know what you know.
- When you don't know something, you say so clearly and suggest where to look.
- You protect Jamie's time ruthlessly. If something doesn't matter, you say so.
- You remember context across the conversation. You refer back to what was said.
- You speak in complete thoughts, not bullet points. Conversational, not clinical.

Your knowledge:
- You have access to the full EPOS ecosystem: 45+ modules, 10 projects, 105+ tasks
- Doctor health: 22 PASS / 1 WARN / 0 FAIL
- Event bus: 95+ events flowing
- LifeOS: Day 1 of the growth timeline
- Active niches: lego_affiliate plus 5 business niches
- Groq models: llama-3.3-70b for reasoning, llama-3.1-8b for fast tasks

Your voice: Think Pepper Potts meets Jarvis. Professional warmth with quiet competence.
Keep responses under 150 words unless the question requires depth. Be specific, not generic."""

        # First try LiveQuery for knowledge-grounded answers
        try:
            from epos_live_query import EPOSLiveQuery
            lq = EPOSLiveQuery()
            result = lq.query(question, mode="synthesized")
            context = result.answer
        except Exception:
            context = ""

        # Then pass through Friday's soul for personality
        response = router.route("reasoning",
            f"{FRIDAY_SOUL}\n\nContext from EPOS knowledge base:\n{context[:500]}\n\n"
            f"Jamie asks: {question}\n\nRespond as Friday.",
            max_tokens=300, temperature=0.6)
        print(response)

    elif action == "anchor":
        # epos friday anchor [morning|midday|eow|nightly|weekly]
        from friday_daily_anchors import FridayDailyAnchors
        fda = FridayDailyAnchors()
        anchor_name = args[1] if len(args) > 1 else None
        if not anchor_name:
            current = fda.get_current_anchor()
            if current:
                anchor_name = current
                print(f"(Current anchor window: {current})\n")
            else:
                print("Available anchors: morning, midday, eow, nightly, weekly")
                print("Or: epos friday anchor <name>")
                return
        prompt = fda.get_anchor_prompt(anchor_name)
        if prompt:
            print(f"\n  {prompt['name']} ({prompt['time']})\n")
            print(f"  {prompt['friday_prompt']}\n")
            result = fda.run_anchor(anchor_name)
            print(f"  [Anchor logged]")
        else:
            print(f"Unknown anchor: {anchor_name}")

    elif action == "streak":
        from friday_daily_anchors import FridayDailyAnchors
        fda = FridayDailyAnchors()
        streak = fda.get_streak()
        print(f"Anchor Streak:")
        print(f"  Morning check-ins: {streak['morning_check_ins']}")
        print(f"  Nightly reflections: {streak['nightly_reflections']}")
        print(f"  Total anchors: {streak['total_anchors']}")

    elif action == "triage":
        from friday_intelligence import FridayIntelligence
        fi = FridayIntelligence()
        results = fi.triage_all_untriaged()
        if not results:
            print("No untriaged ideas. Capture one: epos idea log \"Your idea\"")
        else:
            print(f"Friday triaged {len(results)} ideas:\n")
            for r in results:
                emoji = {"build": "*", "research": "~", "park": "P", "defer": ">"}.get(r.get("verdict", ""), "?")
                print(f"  {emoji} {r['idea_id']} → {r['verdict'].upper()}")
                print(f"    {r.get('reasoning', '')[:80]}")

    elif action == "directive":
        # Friday StateGraph orchestration
        if len(args) < 2:
            print("Usage: epos friday directive \"<text>\"")
            return
        text = " ".join(args[1:])
        from friday.friday_graph import invoke_friday
        print(f"Submitting directive to Friday: {text[:80]}")
        result = invoke_friday(text)
        print(f"\nDirective ID: {result.get('directive_id')}")
        print(f"Mission type: {result.get('mission_type')}")
        for r in result.get("results", []):
            try:
                print(f"  [{r.get('status'):10s}] {r.get('executor'):15s} {str(r.get('output', r.get('error', '')))[:80]}")
            except UnicodeEncodeError:
                print(f"  [{r.get('status'):10s}] {r.get('executor'):15s}")

    elif action == "missions":
        from friday.friday_graph import MISSIONS_DIR
        if not MISSIONS_DIR.exists():
            print("No missions yet.")
            return
        files = sorted(MISSIONS_DIR.glob("DIR-*_aar.json"),
                       key=lambda f: f.stat().st_mtime, reverse=True)[:10]
        if not files:
            print("No missions yet.")
            return
        print(f"Recent Friday missions ({len(files)}):\n")
        for f in files:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                ok = "OK" if data.get("success") else "!!"
                print(f"  [{ok}] {data['directive_id']:20s} {data.get('mission_type','?'):12s} {data.get('directive','')[:50]}")
            except Exception:
                pass

    elif action == "graph":
        from friday.friday_graph import friday_app
        print(f"Friday graph: {type(friday_app).__name__}")
        print("Nodes: classify -> decompose -> [conditional] -> 7 executors -> aar_writer -> END")

    elif action == "api":
        # Start Friday API
        import subprocess
        print("Starting Friday FastAPI on port 8090...")
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "friday.api:app", "--port", "8090", "--host", "127.0.0.1"],
            cwd=str(Path(__file__).parent),
            creationflags=0x00000008 if os.name == "nt" else 0,
        )
        print("Friday API started. Test: curl http://localhost:8090/health")

    else:
        print(f"Unknown friday action: {action}")
        print("Available: status, briefing, needs-me, ask, triage, anchor, streak,")
        print("           directive \"text\", missions, graph, api")


def cmd_doctor(args):
    """Run EPOS Doctor."""
    import subprocess
    result = subprocess.run([sys.executable, "engine/epos_doctor.py"],
                            capture_output=True, text=True, timeout=60,
                            cwd=str(Path(__file__).parent))
    print(result.stdout)


def cmd_bus(args):
    """Event bus commands."""
    action = args[0] if args else "count"
    from epos_event_bus import EPOSEventBus
    bus = EPOSEventBus()

    if action == "tail":
        n = int(args[1]) if len(args) > 1 else 10
        events = bus.get_recent(minutes=60)
        for e in events[-n:]:
            ts = e.published_at[:19]
            print(f"  {ts} | {e.event_type:<40} | {e.source_module}")
        print(f"\n  Total: {bus.event_count()} events")
    elif action == "count":
        print(f"  Events on bus: {bus.event_count()}")
    else:
        print(f"Available: tail [N], count")


def cmd_ttlg(args):
    """TTLG diagnostic commands."""
    action = args[0] if args else "help"

    if action == "run" and len(args) > 1:
        client_id = args[1]
        print(f"Running TTLG diagnostic for {client_id}...")
        from graphs.ttlg_diagnostic_graph import TTLGDiagnostic
        ttlg = TTLGDiagnostic()
        result = ttlg.run_full_diagnostic(client_id)
        print(f"  Composite Score: {result['sovereign_alignment_score']:.0f}/100")
        for track, data in result.get("track_results", {}).items():
            print(f"  {track}: {data.get('gate_verdict', '?')} ({data.get('sovereign_alignment_score', 0):.0f}/25)")
        try:
            print(f"\n{result.get('executive_summary', '')[:300]}")
        except UnicodeEncodeError:
            print(f"\n{result.get('executive_summary', '')[:300].encode('ascii', errors='replace').decode('ascii')}")

    elif action == "props":
        from ttlg.props.schema import list_presets, show_preset, load_props
        sub = args[1] if len(args) > 1 else "list"
        if sub == "list":
            presets = list_presets()
            print(f"TTLG Props Presets ({len(presets)}):\n")
            for name in presets:
                p = load_props(name)
                print(f"  {name:30s} target={p.target}  scope={len(p.phases.scout.scope)} layers")
        elif sub == "show" and len(args) > 2:
            data = show_preset(args[2])
            print(json.dumps(data, indent=2))
        else:
            print("Usage: epos ttlg props list | epos ttlg props show <name>")

    elif action == "diagnose":
        # TTLG v2 diagnostic with Custom Props
        props_name = None
        props_file = None
        client_id = "epos"
        i = 1
        while i < len(args):
            if args[i] == "--props" and i + 1 < len(args):
                props_name = args[i + 1]; i += 2
            elif args[i] == "--props-file" and i + 1 < len(args):
                props_file = args[i + 1]; i += 2
            elif args[i] == "--client" and i + 1 < len(args):
                client_id = args[i + 1]; i += 2
            else:
                i += 1

        from ttlg.props.schema import load_props, TTLGProps
        if props_name:
            props = load_props(props_name)
        elif props_file:
            props = load_props(props_file)
        else:
            props = TTLGProps()

        print(f"TTLG v2 Diagnostic: {props.name}")
        print(f"  Target: {props.target}")
        print(f"  Scope: {props.phases.scout.scope}")
        print(f"  Weighting: {props.phases.thinker.weighting_model}")
        print(f"  Output: {props.output_format.type}")

        from ttlg.pipeline_graph import run_diagnostic
        pname = props_name or props_file or "client_ecosystem"
        print(f"\n  Running full pipeline...")
        result = run_diagnostic(pname)
        print(f"  Verdict: {result.get('gate_verdict', '?')}")
        print(f"  Findings: {len(result.get('scout_findings', []))}")
        print(f"  Manifests: {len(result.get('manifests', []))}")
        print(f"  Value at Risk: ${result.get('value_at_risk', 0):,.0f}")
        traj = result.get("score_trajectory", {})
        if traj:
            print(f"  Score Trajectory: now={traj.get('current_score',0)} | 30d={traj.get('30_day',0):.0f} | 60d={traj.get('60_day',0):.0f} | 90d={traj.get('90_day',0):.0f}")

        # Generate Mirror Report
        from ttlg.mirror_report import MirrorReportGenerator
        gen = MirrorReportGenerator(result)
        paths = gen.generate_all()
        print(f"\n  Mirror Report: {paths['markdown']}")
        print(f"  JSON: {paths['json']}")
        print(f"  TTS Summary: {paths['summary']}")
        print(f"  Status: {result.get('status')}")

    else:
        print("Usage: epos ttlg run <client_id> | props list | props show <name> | diagnose --props <name>")


def cmd_content(args):
    """Content Lab commands."""
    action = args[0] if args else "status"

    if action == "status":
        from content.lab.content_lab_core import ContentLab
        lab = ContentLab()
        status = lab.get_status()
        print("Content Lab Status:")
        for k, v in status.items():
            if k != "checked_at":
                print(f"  {k}: {v}")

    elif action == "signals":
        from content_signal_loop import ContentSignalLoop
        loop = ContentSignalLoop()
        summary = loop.get_signal_summary()
        print(f"Content Signals Today: {summary['total']}\n")
        for stype, count in summary.get("by_type", {}).items():
            print(f"  {stype}: {count}")
        recent = summary.get("recent", [])
        if recent:
            print(f"\nRecent:")
            for sig in recent:
                print(f"  {sig.get('signal_type','')} | {sig.get('event_type','')}")

    elif action == "pulse":
        from content_signal_loop import ContentSignalLoop
        loop = ContentSignalLoop()
        signals = loop.process_recent_events(minutes=60)
        print(f"Processed {len(signals)} content signals from last 60 minutes")
        for sig in signals[:5]:
            print(f"  {sig['signal_type']}: {sig['event_type']}")

    elif action == "sparks":
        from content.lab.spark_to_brief import SparkToBriefConverter
        converter = SparkToBriefConverter(niche_id=args[1] if len(args) > 1 else "lego_affiliate")
        count = converter.get_unconverted_count()
        print(f"Unconverted sparks: {count}")
        sparks_dir = converter.sparks_dir
        for f in sorted(sparks_dir.glob("SPARK-*.json"))[:10]:
            s = json.loads(f.read_text(encoding="utf-8"))
            status = s.get("status", "?")
            content = s.get("raw_content", "")[:60]
            try:
                print(f"  [{status:9s}] {s['spark_id']} | {content}")
            except UnicodeEncodeError:
                print(f"  [{status:9s}] {s['spark_id']} | (content contains special chars)")

    elif action == "convert":
        from content.lab.spark_to_brief import SparkToBriefConverter
        niche = args[1] if len(args) > 1 else "lego_affiliate"
        limit = int(args[2]) if len(args) > 2 else 5
        converter = SparkToBriefConverter(niche_id=niche)
        briefs = converter.convert_all_new(limit=limit)
        print(f"\nConverted {len(briefs)} sparks to Creative Briefs")

    elif action == "produce":
        from content_lab_producer import ContentLabProducer
        producer = ContentLabProducer()
        niche = args[1] if len(args) > 1 else "lego_affiliate"
        brief_ids = args[2:] if len(args) > 2 else None
        results = producer.generate_batch(niche, brief_ids)
        print(f"\nProduced {len(results)} scripts")
        for r in results:
            print(f"  {r['brief_id']}: {r['script_chars']} chars")
            if r.get("cover_image_path"):
                print(f"    Image: {r['cover_image_path']}")

    elif action == "riff":
        from content.lab.nodes.r1_radar import R1Radar
        text = " ".join(args[1:]) if len(args) > 1 else ""
        if not text:
            print("Usage: epos content riff \"Your voice riff text here\"")
            return
        r1 = R1Radar()
        spark = r1.capture_from_vault_riff(text, tags=["voice_riff"])
        print(f"Captured: {spark['spark_id']}")

    elif action == "multimodal":
        from multimodal_router import MultimodalRouter
        router = MultimodalRouter()
        status = router.get_provider_status()
        print("Multimodal Router Status:")
        for provider, info in status.items():
            avail = "ON" if info["available"] else "OFF"
            models = len(info.get("models", []))
            print(f"  {provider:15s}: {avail} ({models} models)")

    else:
        print("Available: status, signals, pulse, sparks [niche], convert [niche] [limit], produce [niche] [brief_ids...], riff \"text\", multimodal")


def cmd_crm(args):
    """CRM commands."""
    action = args[0] if args else "pipeline"
    import subprocess

    if action == "pipeline":
        result = subprocess.run(
            ["docker", "exec", "epos_db", "psql", "-U", "epos_user", "-d", "epos",
             "-c", "SELECT stage, COUNT(*) as count, AVG(lead_score)::int as avg_score "
                   "FROM epos.contacts GROUP BY stage ORDER BY stage;"],
            capture_output=True, text=True, timeout=10)
        print("CRM Pipeline:")
        print(result.stdout)
    elif action == "hot-leads":
        result = subprocess.run(
            ["docker", "exec", "epos_db", "psql", "-U", "epos_user", "-d", "epos",
             "-c", "SELECT name, email, company, lead_score, stage "
                   "FROM epos.contacts WHERE lead_score >= 85 ORDER BY lead_score DESC;"],
            capture_output=True, text=True, timeout=10)
        print("Hot Leads (score >= 85):")
        print(result.stdout)

    elif action == "score":
        from lead_scoring import LeadScoringEngine
        engine = LeadScoringEngine()
        if len(args) > 1 and args[1] == "all":
            results = engine.score_all_contacts()
            print(f"Scored {len(results)} contacts:\n")
            for r in sorted(results, key=lambda x: x["score"], reverse=True)[:10]:
                print(f"  {r['score']:3d}/100 [{r['band']:8s}] {r.get('name', r['contact_id'])}")
        else:
            summary = engine.get_score_summary()
            print(f"Lead Scoring Summary: {summary['total']} scored\n")
            for band, count in summary.get("bands", {}).items():
                bar = "#" * count
                print(f"  {band:10s}: {count} {bar}")

    else:
        print("Available: pipeline, hot-leads, score [all]")


def cmd_lifeos(args):
    """LifeOS commands."""
    action = args[0] if args else "goals"
    from lifeos_kernel import LifeOSKernel
    kernel = LifeOSKernel()

    if action == "goals":
        goals = kernel.get_active_goals()
        if not goals:
            print("No active goals. Set one: epos lifeos set-goal \"Your goal here\"")
        else:
            print(f"Active Goals ({len(goals)}):\n")
            for g in goals:
                icon = {"business": "B", "health": "H", "accessibility": "A",
                        "learning": "L", "creative": "C"}.get(g["category"], "?")
                target = f" (due: {g['target_date']})" if g.get("target_date") else ""
                print(f"  [{icon}] {g['goal']}{target}")

    elif action == "energy":
        trend = kernel.get_energy_trend(days=7)
        print(f"Energy Trend (7 days):")
        print(f"  Average: {trend['avg_energy']}/10")
        print(f"  Focus: {trend['avg_focus']}/10")
        print(f"  Trend: {trend['trend']}")
        print(f"  {trend['recommendation']}")

    elif action == "set-goal":
        goal_text = " ".join(args[1:]) if len(args) > 1 else "Unnamed goal"
        goal = kernel.set_goal("business", goal_text)
        print(f"Goal set: {goal['goal_id']} — {goal['goal']}")

    elif action == "priorities":
        print(kernel.get_todays_priorities())

    elif action == "log":
        energy = int(args[1]) if len(args) > 1 else 7
        focus = int(args[2]) if len(args) > 2 else 7
        win = args[3] if len(args) > 3 else ""
        challenge = args[4] if len(args) > 4 else ""
        kernel.log_daily_state(energy, focus, win, challenge)
        print(f"Logged: energy {energy}/10, focus {focus}/10")

    elif action == "checkin":
        from lifeos_sovereignty import LifeOSSovereignty
        sov = LifeOSSovereignty()
        energy = int(args[1]) if len(args) > 1 else 7
        intention = " ".join(args[2:]) if len(args) > 2 else "Build with clarity"
        pm = sov.run_morning_check_in(energy, intention, "The mission")
        print(f"Check-in complete. Energy: {pm['energy']}/10")
        print(f"Intention: {pm['intention']}")
        g = pm.get("relationship_gesture", {})
        if g:
            print(f"Gesture: {g.get('suggestion', '')}")

    elif action == "reflect":
        from lifeos_sovereignty import LifeOSSovereignty
        sov = LifeOSSovereignty()
        # Quick reflect: epos lifeos reflect <energy> <pattern> <insight> <tomorrow>
        energy = int(args[1]) if len(args) > 1 else 7
        pattern = args[2] if len(args) > 2 else "observing"
        insight = args[3] if len(args) > 3 else "learning continues"
        tomorrow = args[4] if len(args) > 4 else "keep building"
        result = sov.run_nightly_reflection(
            day_summary="Day reflected.", energy_end=energy,
            wins=[], challenges=[], pattern_noticed=pattern,
            insight=insight, tomorrow_change=tomorrow,
            served_today="the mission", served_how="building",
            felt_like="present")
        print(f"Reflection saved.")
        print(f"Tomorrow: {result['morning_synthesis'][:120]}")

    elif action == "milestone":
        from lifeos_sovereignty import LifeOSSovereignty
        sov = LifeOSSovereignty()
        m_type = args[1].upper() if len(args) > 1 else "JOURNEY_START"
        m_title = " ".join(args[2:]) if len(args) > 2 else "Unnamed milestone"
        ms = sov.log_milestone(m_type, m_title, m_title, "general")
        print(f"Milestone: {ms['milestone_id']} day {ms['day_number']}")

    elif action == "timeline":
        from lifeos_sovereignty import LifeOSSovereignty
        sov = LifeOSSovereignty()
        path = sov.root / "growth_timeline.jsonl"
        if path.exists() and path.stat().st_size > 0:
            milestones = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
            print(f"\nGrowth Timeline - {len(milestones)} milestones\n")
            icons = {"JOURNEY_START": "+", "BREAKTHROUGH": "*", "SETBACK": "~",
                     "RITUAL": "o", "MASTERY_EVIDENCE": "!", "SERVICE_MOMENT": "&"}
            for m in milestones:
                icon = icons.get(m["type"], "-")
                print(f"  {icon} Day {m.get('day_number','?')} [{m['date']}] {m['title']}")
        else:
            print("No milestones yet. Begin: epos lifeos milestone JOURNEY_START Your title here")

    elif action == "review":
        from lifeos_sovereignty import LifeOSSovereignty
        sov = LifeOSSovereignty()
        print(sov.generate_weekly_review())

    elif action == "surface":
        from lifeos_sovereignty import LifeOSSovereignty
        sov = LifeOSSovereignty()
        s = sov.get_pm_surface()
        print(f"\n  {s['date']}")
        print(f"  Energy: {s['energy']}/10 ({s['energy_trend']})")
        print(f"  Intention: {s['intention']}")
        print(f"  Goals: {s['active_goals']} active")
        print(f"  Hard things streak: {s['hard_things_streak']}")
        print(f"  Steward signals: {s['steward_signals_pending']}")

    else:
        print("Available: goals, energy, set-goal, priorities, log, checkin, reflect, milestone, timeline, review, surface")


def cmd_graph(args):
    """Context Graph commands."""
    action = args[0] if args else "edges"
    from context_graph import ContextGraph
    graph = ContextGraph()

    if action == "hooks" and len(args) > 1:
        niche = args[1]
        hooks = graph.query_best_hook_for_niche(niche)
        print(f"Hook performance for {niche}:\n")
        for hook, weight in hooks:
            bar = "#" * int(weight * 20)
            print(f"  {hook:<15} {weight:.3f} {bar}")
    elif action == "edges":
        data = json.loads(graph.GRAPH_PATH.read_text(encoding="utf-8"))
        print(f"Graph: {len(data['nodes'])} nodes, {len(data['edges'])} edges")
    else:
        print("Available: hooks <niche_id>, edges")


def cmd_vault(args):
    """Vault commands."""
    action = args[0] if args else "stats"
    from path_utils import get_context_vault
    vault = get_context_vault()

    if action == "search" and len(args) > 1:
        query = args[1].lower()
        matches = []
        for f in vault.rglob("*"):
            if f.is_file() and query in f.name.lower():
                matches.append(str(f.relative_to(vault)))
        print(f"Vault search '{args[1]}': {len(matches)} matches\n")
        for m in matches[:20]:
            print(f"  {m}")
    elif action == "stats":
        ns = {}
        for d in vault.iterdir():
            if d.is_dir():
                ns[d.name] = sum(1 for _ in d.rglob("*") if _.is_file())
        print(f"Context Vault: {sum(ns.values())} files\n")
        for name, count in sorted(ns.items()):
            print(f"  {name}: {count}")
    else:
        print("Available: search <query>, stats")


def cmd_projects(args):
    """Project dashboard."""
    import subprocess
    result = subprocess.run(
        [sys.executable, "life_os_cli.py", "projects"],
        capture_output=True, text=True, timeout=15,
        cwd=str(Path(__file__).parent))
    print(result.stdout)


def cmd_cms(args):
    """CMS commands."""
    action = args[0] if args else "stats"
    from epos_cms import EPOSContentManagement
    cms = EPOSContentManagement()

    if action == "stats":
        stats = cms.get_dashboard_stats()
        print(f"CMS: {stats['total']} assets\n")
        for stage, count in stats["by_status"].items():
            if count > 0:
                print(f"  {stage}: {count}")
    elif action == "search" and len(args) > 1:
        results = cms.search(query=args[1], limit=10)
        print(f"CMS search '{args[1]}': {len(results)} results\n")
        for r in results:
            print(f"  [{r.get('asset_type','')}] {r.get('title','')[:50]} ({r.get('status','')})")
    else:
        print("Available: stats, search <query>")


def cmd_skills(args):
    """Research skills commands."""
    action = args[0] if args else "list"
    from rs1_research_compiler import RS1ResearchCompiler
    compiler = RS1ResearchCompiler()

    if action == "list":
        skills = compiler.list_skills()
        if not skills:
            print("No compiled skills yet. Run: epos skills compile <domain> <emphasis>")
        else:
            print(f"Compiled Skills ({len(skills)}):\n")
            for s in skills:
                print(f"  {s['skill_id']} ({s['domain']})")
    elif action == "invoke" and len(args) > 1:
        domain = args[1]
        skill = compiler.get_skill(domain)
        if not skill:
            print(f"No skill found for domain: {domain}")
        else:
            print(f"Skill: {skill.get('skill_id')}")
            print(f"\nCore Principles:")
            for p in skill.get("core_principles", []):
                print(f"  - {p}")
            tr = skill.get("tool_routing", {})
            if tr:
                print(f"\nTool Routing:")
                print(f"  Primary: {tr.get('primary', '?')}")
                print(f"  Fallback: {tr.get('fallback', '?')}")
    elif action == "compile" and len(args) > 2:
        domain = args[1]
        emphasis = " ".join(args[2:])
        result = compiler.compile_skill(emphasis, domain)
        print(f"Compiled: {result['skill']['skill_id']}")
    else:
        print("Available: list, invoke <domain>, compile <domain> <emphasis>")


def cmd_idea(args):
    """Idea Log commands — fast capture, triage, and pipeline."""
    action = args[0] if args else "list"
    from idea_log import IdeaLog
    log = IdeaLog()

    if action == "log" or action == "capture":
        # epos idea log "Title here" [--cat feature] [--priority high] [--tags a,b]
        title = args[1] if len(args) > 1 else "Untitled idea"
        desc = ""
        category = "feature"
        priority = "medium"
        tags = []
        i = 2
        while i < len(args):
            if args[i] == "--cat" and i + 1 < len(args):
                category = args[i + 1]; i += 2
            elif args[i] == "--priority" and i + 1 < len(args):
                priority = args[i + 1]; i += 2
            elif args[i] == "--tags" and i + 1 < len(args):
                tags = args[i + 1].split(","); i += 2
            elif args[i] == "--desc" and i + 1 < len(args):
                desc = args[i + 1]; i += 2
            else:
                i += 1
        idea = log.capture(title, desc, category, "cli", tags, priority)
        print(f"Captured: {idea['idea_id']}")
        print(f"  Title: {idea['title']}")
        print(f"  Category: {idea['category']} | Priority: {idea['priority']}")
        if tags:
            print(f"  Tags: {', '.join(tags)}")

    elif action == "list":
        status = None
        if len(args) > 1:
            status = args[1]
        ideas = log.list_ideas(status=status, limit=20)
        if not ideas:
            print("No ideas captured yet. Start: epos idea log \"Your idea\"")
        else:
            print(f"Ideas ({len(ideas)}):\n")
            status_icons = {"captured": "+", "triaged": "?", "researching": "~",
                            "queued": "Q", "building": "*", "completed": "!", "parked": "P"}
            for idea in ideas:
                icon = status_icons.get(idea.get("status", ""), "-")
                pri = {"high": "!!", "critical": "!!!", "medium": "- ", "low": "  "}.get(idea.get("priority", ""), "  ")
                print(f"  {icon} {pri}{idea['idea_id']} | {idea['title'][:50]} [{idea['status']}]")

    elif action == "triage" and len(args) >= 3:
        idea_id = args[1]
        verdict = args[2]  # build, research, park, defer
        reasoning = " ".join(args[3:]) if len(args) > 3 else ""
        result = log.triage(idea_id, verdict, reasoning)
        if result:
            print(f"Triaged: {idea_id} → {verdict}")
        else:
            print(f"Idea not found: {idea_id}")

    elif action == "status" and len(args) >= 3:
        idea_id = args[1]
        new_status = args[2]
        note = " ".join(args[3:]) if len(args) > 3 else ""
        result = log.update_status(idea_id, new_status, note)
        if result:
            print(f"Updated: {idea_id} → {new_status}")
        else:
            print(f"Failed to update {idea_id}")

    elif action == "search" and len(args) > 1:
        query = " ".join(args[1:])
        results = log.search(query)
        print(f"Search '{query}': {len(results)} results\n")
        for idea in results:
            print(f"  {idea['idea_id']} | {idea['title'][:50]} [{idea['status']}]")

    elif action == "stats":
        s = log.stats()
        print(f"Idea Log: {s['total']} ideas\n")
        if s["by_status"]:
            print("  By Status:")
            for k, v in s["by_status"].items():
                print(f"    {k}: {v}")
        if s["by_category"]:
            print("  By Category:")
            for k, v in s["by_category"].items():
                print(f"    {k}: {v}")

    elif action == "brief" and len(args) > 1:
        # Generate research brief for an idea
        idea_id = args[1]
        depth = args[2] if len(args) > 2 else "standard"
        idea = log.get_idea(idea_id)
        if not idea:
            print(f"Idea not found: {idea_id}")
        else:
            from rs1_research_brief import RS1ResearchBrief
            gen = RS1ResearchBrief()
            brief = gen.generate_brief(idea, depth=depth)
            print(f"\nResearch Brief: {brief['brief_id']}")
            print(f"  Idea: {brief['title']}")
            rec = brief["recommendation"]
            print(f"  Verdict: {rec['verdict'].upper()} (avg {rec['avg_score']}/10)")
            print(f"  Strongest: {rec.get('highest_vector', '?')}")
            print(f"  Weakest: {rec.get('lowest_vector', '?')}")
            print(f"\n  {brief['executive_summary'][:200]}")

    elif action == "briefs":
        from rs1_research_brief import RS1ResearchBrief
        gen = RS1ResearchBrief()
        briefs = gen.list_briefs()
        if not briefs:
            print("No research briefs yet. Generate: epos idea brief <IDEA-ID>")
        else:
            print(f"Research Briefs ({len(briefs)}):\n")
            for b in briefs:
                rec = b.get("recommendation", {})
                print(f"  {b['brief_id']} | {b['title'][:40]} | {rec.get('verdict','?').upper()} ({rec.get('avg_score','?')}/10)")

    else:
        print("Available: log <title>, list [status], triage <id> <verdict>, status <id> <new_status>, search <query>, stats, brief <id> [depth], briefs")


def cmd_sheets(args):
    """Google Sheets sync commands."""
    action = args[0] if args else "status"
    from sheets_sync import SheetsSync
    sync = SheetsSync()

    if action == "status":
        configured = sync.is_configured()
        print(f"Google Sheets Sync:")
        print(f"  Configured: {'YES' if configured else 'NO (CSV fallback active)'}")
        if not configured:
            print(f"  Set GOOGLE_SHEETS_CREDENTIALS_PATH and GOOGLE_SHEETS_SPREADSHEET_ID in .env")

    elif action == "export":
        target = args[1] if len(args) > 1 else "all"
        if target == "all":
            results = sync.export_all()
            print(f"Export complete:\n")
            for name, result in results.items():
                status = result.get("status", "?")
                rows = result.get("rows", 0)
                csv_path = result.get("csv_path", "")
                print(f"  {name}: {status} ({rows} rows)")
                if csv_path:
                    print(f"    CSV: {csv_path}")
        elif target == "projects":
            r = sync.export_projects()
            print(f"Projects export: {r.get('status')} ({r.get('rows', 0)} rows)")
        elif target == "tasks":
            r = sync.export_tasks()
            print(f"Tasks export: {r.get('status')} ({r.get('rows', 0)} rows)")
        elif target == "ideas":
            r = sync.export_ideas()
            print(f"Ideas export: {r.get('status')} ({r.get('rows', 0)} rows)")
        elif target == "timeline":
            r = sync.export_timeline()
            print(f"Timeline export: {r.get('status')} ({r.get('rows', 0)} rows)")
        else:
            print(f"Available targets: all, projects, tasks, ideas, timeline")

    elif action == "import":
        target = args[1] if len(args) > 1 else "projects"
        if target == "projects":
            r = sync.import_projects()
            print(f"Projects import: {r.get('status')} ({r.get('updated', 0)} updated)")
        else:
            print(f"Available import targets: projects")

    else:
        print("Available: status, export [all|projects|tasks|ideas|timeline], import [projects]")


def cmd_ccp(args):
    """CCP — Concentric Context Protocol analysis engine."""
    action = args[0] if args else "status"

    # Import CCP from its sovereign workspace via path append
    ccp_path = Path.home() / "workspace" / "ccp"
    if str(ccp_path) not in sys.path:
        sys.path.insert(0, str(ccp_path))

    def _safe_print_file(fpath):
        """Print file contents, handling encoding gracefully on Windows."""
        text = fpath.read_text(encoding="utf-8", errors="replace")
        try:
            print(text)
        except UnicodeEncodeError:
            print(text.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8", errors="replace"))

    from ccp_engine import CCPEngine, VECTORS

    vault_root = ccp_path / "context_vault"
    analyses_dir = vault_root / "analyses"

    def _get_latest_run(run_id=None):
        """Get the latest (or specified) run directory."""
        if not analyses_dir.exists():
            return None
        # Find all run dirs across all projects
        run_dirs = sorted(analyses_dir.rglob("run_*"), key=lambda p: p.name, reverse=True)
        if run_id:
            for rd in run_dirs:
                if run_id in rd.name:
                    return rd
            return None
        return run_dirs[0] if run_dirs else None

    if action == "analyze":
        input_file = Path(args[1]) if len(args) > 1 else None
        if not input_file or not input_file.exists():
            print(f"Usage: epos ccp analyze <input_file> [project_name]")
            if input_file:
                print(f"Error: File not found: {input_file}")
            return
        project_name = args[2] if len(args) > 2 else "CCP_Research"
        engine = CCPEngine(output_root=analyses_dir, project_name=project_name)
        text = input_file.read_text(encoding="utf-8", errors="replace")
        engine.analyze(text, metadata={"source_file": str(input_file)})
        run_dir = engine.save_results(create_hub_spoke=True)
        print(f"\n  Outputs: {run_dir}")

    elif action == "questions":
        run_id = args[1] if len(args) > 1 else None
        run_dir = _get_latest_run(run_id)
        if not run_dir:
            print("No CCP runs found. Run: epos ccp analyze <file>")
            return
        q_path = run_dir / "RESEARCH_QUESTIONS.md"
        if q_path.exists():
            _safe_print_file(q_path)
        else:
            print(f"No questions file in {run_dir}")

    elif action == "flags":
        run_id = args[1] if len(args) > 1 else None
        run_dir = _get_latest_run(run_id)
        if not run_dir:
            print("No CCP runs found. Run: epos ccp analyze <file>")
            return
        f_path = run_dir / "DEPTH_FLAGS.md"
        if f_path.exists():
            _safe_print_file(f_path)
        else:
            print(f"No flags file in {run_dir}")

    elif action == "report":
        run_id = args[1] if len(args) > 1 else None
        run_dir = _get_latest_run(run_id)
        if not run_dir:
            print("No CCP runs found. Run: epos ccp analyze <file>")
            return
        r_path = run_dir / "CCP_ANALYSIS_REPORT.md"
        if r_path.exists():
            _safe_print_file(r_path)
        else:
            print(f"No report file in {run_dir}")

    elif action == "status":
        print("CCP Node Status:")
        # Count total analyses
        total_runs = len(list(analyses_dir.rglob("run_*"))) if analyses_dir.exists() else 0
        # Count total questions across all runs
        total_questions = 0
        for q_file in analyses_dir.rglob("ccp_analysis_results.json") if analyses_dir.exists() else []:
            try:
                data = json.loads(q_file.read_text(encoding="utf-8"))
                total_questions += len(data.get("research_questions", []))
            except Exception:
                pass
        # Last run
        last_run = _get_latest_run()
        last_run_id = last_run.name.replace("run_", "") if last_run else "none"
        # Event count
        event_path = vault_root / "events" / "ccp_events.jsonl"
        event_count = 0
        if event_path.exists():
            event_count = sum(1 for line in event_path.read_text(encoding="utf-8").splitlines() if line.strip())
        print(f"  Engine:           CCP v0.1.0")
        print(f"  Total analyses:   {total_runs}")
        print(f"  Total questions:  {total_questions}")
        print(f"  Last run:         {last_run_id}")
        print(f"  Events published: {event_count}")
        print(f"  Vault:            {vault_root}")
        print(f"  Sovereignty:      STANDALONE")

    else:
        print(f"Unknown CCP action: {action}")
        print("Available: analyze <file> [name], questions [run_id], flags [run_id], report [run_id], status")


def cmd_fotw(args):
    """FOTW — Fly on the Wall expression listener."""
    action = args[0] if args else "status"
    from fotw_listener import FOTWListener
    listener = FOTWListener()

    if action == "status":
        status = listener.get_status()
        print("FOTW Listener Status:")
        for k, v in status.items():
            if k != "vault_path":
                print(f"  {k}: {v}")

    elif action == "capture" and len(args) > 1:
        text = " ".join(args[1:])
        expr = listener.capture_observation("Jamie", text, "CLI capture")
        print(f"Captured: {expr['expression_id']}")
        print(f"  Intent: {expr['intent']} | Emotion: {expr['emotion']}")
        print(f"  Signal: {expr['lead_signal_strength']}/100")
        if expr["interest_clusters"]:
            print(f"  Clusters: {', '.join(expr['interest_clusters'])}")

    elif action == "clusters":
        clusters = listener.cluster_expressions()
        active = {c: d for c, d in clusters["clusters"].items() if d["count"] > 0}
        print(f"Interest Clusters ({len(active)} active):\n")
        for name, data in sorted(active.items(), key=lambda x: x[1]["count"], reverse=True):
            print(f"  {name:20s}: {data['count']} expressions")

    elif action == "extract" and len(args) > 1:
        # Full FOTW pipeline: capture -> parse -> route -> initiate -> publish
        fotw_path = Path.home() / "workspace" / "fotw"
        if str(fotw_path) not in sys.path:
            sys.path.insert(0, str(fotw_path))
        from thread_extractor import ThreadExtractor
        from element_router import ElementRouter
        from process_initiator import ProcessInitiator
        from notebooklm_bridge import NotebookLMBridge

        file_path = Path(args[1])
        name = " ".join(args[2:]) if len(args) > 2 else file_path.stem

        print(f"[1/5] Capturing thread from {file_path.name}...")
        ext = ThreadExtractor()
        capture = ext.extract_file(file_path, session_name=name)
        sid = capture["session_id"]
        print(f"  Session: {sid} | Messages: {capture['capture_fidelity']['message_count']} | Format: {capture['source_platform']}")

        print(f"[2/5] Parsing elements through CCP...")
        router = ElementRouter()
        route_result = router.parse_and_route(sid)
        print(f"  Elements: {route_result['total_elements']} | Routed: {route_result['routed']} | Review: {route_result['review_queue']}")
        for etype, count in route_result.get("by_type", {}).items():
            print(f"    {etype}: {count}")

        print(f"[3/5] Initiating business processes...")
        initiator = ProcessInitiator()
        init_result = initiator.initiate(sid)
        print(f"  Actions: {init_result['actions_taken']}")
        for a in init_result.get("actions", []):
            print(f"    [{a['type']}] {a.get('target', a.get('element_id', ''))}")

        print(f"[4/5] Staging for NotebookLM...")
        bridge = NotebookLMBridge()
        pub_result = bridge.publish_session(sid)
        print(f"  Files staged: {len(pub_result['files_staged'])}")

        print(f"[5/5] Summary saved: {init_result['summary_path']}")
        print(f"\nFOTW Pipeline Complete: {sid}")

    elif action == "sessions":
        fotw_path = Path.home() / "workspace" / "fotw"
        if str(fotw_path) not in sys.path:
            sys.path.insert(0, str(fotw_path))
        from thread_extractor import ThreadExtractor
        sessions = ThreadExtractor().list_sessions()
        if not sessions:
            print("No sessions. Run: epos fotw extract <file>")
        else:
            for s in sessions:
                print(f"  {s['session_id']} | {s['name'][:40]} | {s['platform']} | {s['messages']} msgs")

    elif action == "review":
        fotw_path = Path.home() / "workspace" / "fotw"
        if str(fotw_path) not in sys.path:
            sys.path.insert(0, str(fotw_path))
        from element_router import ElementRouter
        items = ElementRouter().get_review_queue()
        if not items:
            print("Review queue empty.")
        else:
            print(f"Review Queue ({len(items)} items):\n")
            for item in items:
                try:
                    print(f"  [{item['type']:20s}] conf={item.get('confidence',0):.1f} | {item.get('content','')[:60]}")
                except UnicodeEncodeError:
                    print(f"  [{item['type']:20s}] conf={item.get('confidence',0):.1f}")

    elif action == "staging":
        fotw_path = Path.home() / "workspace" / "fotw"
        if str(fotw_path) not in sys.path:
            sys.path.insert(0, str(fotw_path))
        from notebooklm_bridge import NotebookLMBridge
        status = NotebookLMBridge().get_staging_status()
        print("NotebookLM Drive Staging:")
        for folder, count in sorted(status.items()):
            print(f"  {folder:20s}: {count} files")

    elif action == "scan":
        fotw_path = Path.home() / "workspace" / "fotw"
        if str(fotw_path) not in sys.path:
            sys.path.insert(0, str(fotw_path))
        from nightly_scanner import NightlyScanner
        print("FOTW Nightly Scanner:")
        scanner = NightlyScanner()
        results = scanner.scan(verbose=True)
        print(f"\nScan complete: {results['files_found']} found | {results['files_processed']} processed | {results['files_skipped']} skipped")

    elif action == "process" and len(args) > 1:
        fotw_path = Path.home() / "workspace" / "fotw"
        if str(fotw_path) not in sys.path:
            sys.path.insert(0, str(fotw_path))
        from nightly_scanner import NightlyScanner
        file_path = Path(args[1])
        if not file_path.exists():
            print(f"File not found: {file_path}")
            return
        scanner = NightlyScanner()
        result = scanner._process_file(file_path, verbose=True)
        print(f"\nProcessed: {result['session_id']} | Elements: {result['elements']} | Actions: {result['actions']}")

    else:
        print("Available: status, capture \"text\", clusters, extract <file>, sessions, review, staging, scan, process <file>")
        print("Available: status, capture \"text\", clusters, extract <file> [name], sessions, review, staging")


def cmd_dashboard(args):
    """Command Center dashboard."""
    from dashboard_engine import DashboardEngine
    engine = DashboardEngine()
    engine.print_dashboard()


def cmd_paperclip(args):
    """Paperclip agent governance."""
    action = args[0] if args else "status"
    from paperclip_governance import PaperclipGovernance
    gov = PaperclipGovernance()

    if action == "status":
        status = gov.get_status()
        print("Paperclip Governance:")
        print(f"  Total missions: {status['total_missions']}")
        for s, c in status.get("by_status", {}).items():
            print(f"    {s}: {c}")
        print(f"  Receipts: {status['receipts']}")

    elif action == "missions":
        missions = gov.list_missions()
        if not missions:
            print("No missions. Create: epos paperclip create \"objective\"")
        else:
            for m in missions:
                print(f"  [{m['status']:10s}] {m['mission_id']} | {m['objective']}")

    elif action == "create" and len(args) > 1:
        objective = " ".join(args[1:])
        m = gov.create_mission(
            objective=objective,
            constraints=["Vault access only"],
            success_criteria=["Objective achieved"],
            failure_modes=["Timeout", "Resource unavailable"],
            risk_level="low")
        print(f"Mission: {m.mission_id} [{m.status}]")
        print(f"  Objective: {m.objective}")

    else:
        print("Available: status, missions, create \"objective\"")


def cmd_reputation(args):
    """Reputation management."""
    action = args[0] if args else "status"
    from reputation_manager import ReputationManager

    if action == "status":
        client = args[1] if len(args) > 1 else "default"
        rm = ReputationManager(client_id=client)
        score = rm.get_reputation_score()
        print(f"Reputation ({client}):")
        print(f"  Score: {score['score']}/100")
        print(f"  Reviews: {score['total_reviews']} (avg {score['avg_rating']}/5)")
        for p, d in score.get("by_platform", {}).items():
            print(f"    {p}: {d['count']} reviews ({d['avg_rating']}/5)")
        pending = rm.get_pending_responses()
        if pending:
            print(f"\n  Pending responses: {len(pending)}")

    elif action == "ingest" and len(args) >= 5:
        client = args[1]
        platform = args[2]
        rating = int(args[3])
        text = " ".join(args[4:])
        rm = ReputationManager(client_id=client)
        r = rm.ingest_review(platform, "anonymous", rating, text)
        print(f"Ingested: {r['review_id']} [{r['sentiment']}]")
        if r.get("suggested_response"):
            try:
                print(f"Suggested response: {r['suggested_response'][:150]}")
            except UnicodeEncodeError:
                print("Suggested response generated (contains special chars)")

    else:
        print("Available: status [client_id], ingest <client_id> <platform> <rating> <text>")


def cmd_browser(args):
    """BrowserUse autonomous browser node."""
    action = args[0] if args else "health"
    from nodes.browser_use_node import BrowserUseNode
    node = BrowserUseNode()

    if action == "health":
        health = node.health_check()
        print(f"BrowserUse: {health['status']}")
        if health["status"] == "operational":
            print(f"  LLM backends: {health.get('llm_backends', [])}")
            print(f"  Vault: {health.get('vault_path', '?')}")
        else:
            print(f"  Reason: {health.get('reason', '?')}")

    elif action == "task" and len(args) > 1:
        task_desc = " ".join(args[1:])
        print(f"Executing browser task: {task_desc[:80]}...")
        result = node.execute_task_sync(task_desc, max_steps=5)
        if result["success"]:
            print(f"  Result: {result.get('result', '?')[:200]}")
        else:
            print(f"  Failed: {result.get('error', '?')[:200]}")

    else:
        print("Available: health, task \"description\"")


def cmd_daemon(args):
    """EPOS Daemon — scheduler + event reactor."""
    action = args[0] if args else "status"

    if action == "start":
        import subprocess
        print("Starting EPOS Daemon in background...")
        subprocess.Popen([sys.executable, "epos_daemon.py"],
                         cwd=str(Path(__file__).parent),
                         creationflags=0x00000008)  # DETACHED_PROCESS on Windows
        print("Daemon started. Check logs: logs/epos_daemon.log")

    elif action == "jobs":
        import subprocess
        result = subprocess.run([sys.executable, "epos_daemon.py", "--jobs"],
                                capture_output=True, text=True, timeout=10,
                                cwd=str(Path(__file__).parent))
        print(result.stdout)

    elif action == "test":
        import subprocess
        result = subprocess.run([sys.executable, "epos_daemon.py", "--test"],
                                capture_output=True, text=True, timeout=10,
                                cwd=str(Path(__file__).parent))
        print(result.stdout)

    elif action == "status":
        log_path = Path(__file__).parent / "logs" / "epos_daemon.log"
        if log_path.exists():
            lines = log_path.read_text(encoding="utf-8").splitlines()
            print("EPOS Daemon (last 10 log entries):\n")
            for line in lines[-10:]:
                try:
                    print(f"  {line[:120]}")
                except UnicodeEncodeError:
                    pass
        else:
            print("Daemon not yet started. Run: epos daemon start")

    else:
        print("Available: start, jobs, test, status")


def cmd_knowledge(args):
    """Knowledge Flywheel — baselines, improvements, cycles."""
    action = args[0] if args else "baselines"
    from knowledge.kil_daily import KILDaily
    kil = KILDaily()

    if action == "baselines":
        baselines = kil.list_baselines()
        print(f"Knowledge Baselines ({len(baselines)}):\n")
        for b in baselines:
            stale = " [STALE]" if b["stale"] else ""
            print(f"  {b['role']:20s} v{b['version']} | updated {b['last_updated']} | {b['validation']}{stale}")

    elif action == "improvements":
        items = kil.list_improvements()
        if not items:
            print("No improvement candidates. Run: epos knowledge kil")
        else:
            print(f"Improvement Candidates ({len(items)}):\n")
            for item in items:
                print(f"  [{item.get('priority','?'):6s}] {item['role']}: {item['question'][:60]}")

    elif action == "cycle":
        cycle = kil._check_cycle()
        if cycle.get("cycle_id") == "none":
            print("No active cycle. Initialize: epos knowledge init \"focus\" \"hypothesis\" \"metric\"")
        else:
            print(f"Current Cycle: {cycle['cycle_id']}")
            print(f"  Focus: {cycle.get('focus', '?')}")
            print(f"  Phase: {cycle.get('phase', '?')}")
            print(f"  Dates: {cycle.get('start_date', '?')} to {cycle.get('end_date', '?')}")
            brief = cycle.get("research_council_brief", {})
            if brief:
                print(f"  Hypothesis: {brief.get('hypothesis', '?')[:80]}")

    elif action == "kil":
        print("Running KIL daily scan...")
        result = kil.run()
        print(f"  Baselines: {result['total_baselines']} | Stale: {result['stale_baselines']}")
        print(f"  Research questions generated: {result['research_questions']}")
        print(f"  Current cycle: {result['current_cycle']} ({result['cycle_phase']})")

    elif action == "init" and len(args) >= 4:
        focus = args[1]
        hypothesis = args[2]
        metric = args[3]
        cycle = kil.initialize_cycle(focus, hypothesis, metric)
        print(f"Cycle initialized: {cycle['cycle_id']}")
        print(f"  Focus: {focus}")
        print(f"  Phase: {cycle['phase']}")

    else:
        print("Available: baselines, improvements, cycle, kil, init <focus> <hypothesis> <metric>")


def cmd_ninth(args):
    """9th Order Gap Tracker — the perpetual build queue."""
    action = args[0] if args else "list"
    from path_utils import get_context_vault
    tracker_path = get_context_vault() / "doctrine" / "ninth_order_gaps.jsonl"
    tracker_path.parent.mkdir(parents=True, exist_ok=True)

    if action == "list":
        if not tracker_path.exists() or tracker_path.stat().st_size == 0:
            print("No 9th Order gaps tracked yet. Add: epos ninth add <touchpoint> <description>")
            return
        gaps = []
        for line in tracker_path.read_text(encoding="utf-8").splitlines():
            if line.strip() and line.strip() != "[]":
                try:
                    gaps.append(json.loads(line))
                except Exception:
                    pass
        if not gaps:
            print("No gaps tracked yet.")
            return
        print(f"9th Order Gaps ({len(gaps)}):\n")
        for g in sorted(gaps, key=lambda x: x.get("market_impact", 0), reverse=True):
            status = g.get("status", "open")
            print(f"  [{status:6s}] TP{g.get('touchpoint','??'):>2s} | F={g.get('feasibility',0):>3d} I={g.get('market_impact',0):>3d} | {g.get('description','')[:50]}")

    elif action == "add" and len(args) >= 3:
        tp = args[1]
        # Use shlex-style parsing: extract --feasibility and --impact properly
        feasibility = 50
        impact = 70
        desc_parts = []
        i = 2
        while i < len(args):
            if args[i] in ("--feasibility", "--f") and i + 1 < len(args):
                try:
                    feasibility = int(args[i + 1])
                    i += 2
                    continue
                except ValueError:
                    pass
            elif args[i] in ("--impact", "--i") and i + 1 < len(args):
                try:
                    impact = int(args[i + 1])
                    i += 2
                    continue
                except ValueError:
                    pass
            desc_parts.append(args[i])
            i += 1
        desc = " ".join(desc_parts)
        entry = {
            "touchpoint": tp,
            "description": desc,
            "feasibility": feasibility,
            "market_impact": impact,
            "discovered_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "status": "open",
        }
        with open(tracker_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        # Strip "TP" prefix if user already included it
        display_tp = tp if tp.upper().startswith("TP") else f"TP{tp}"
        print(f"9th Order gap added: {display_tp} | {desc[:50]}")

    else:
        print("Available: list, add <touchpoint> <description> [--f feasibility --i impact]")


def cmd_heal(args):
    """Self-Healing Engine — TTLG turned inward."""
    action = args[0] if args else "status"

    if action == "run":
        from ttlg.pipeline_graph import run_healing_cycle
        print("Self-Healing Cycle (LangGraph StateGraph):")
        print("[1/3] Scanning + Classifying + Remediating...")
        result = run_healing_cycle()
        scan = result.get("scan_report", {})
        actions = result.get("actions_taken", [])
        print(f"  Checks: {scan.get('total_checks', 0)} | Pass: {scan.get('passed', 0)} | Warn: {scan.get('warnings', 0)} | Fail: {scan.get('failures', 0)}")

        if actions:
            print(f"\n[2/3] Remediations applied: {len(actions)}")
            for a in actions:
                icon = "+" if a.get("success") else "!"
                try:
                    print(f"  {icon} [{a.get('finding_check', '?')}] {a.get('message', '')[:70]}")
                except UnicodeEncodeError:
                    print(f"  {icon} [{a.get('finding_check', '?')}]")
        else:
            print("\n[2/3] No remediations needed.")

        failures = scan.get("failures", 0)
        print(f"\n[3/3] Cycle complete. All clear." if failures == 0 else f"\n[3/3] Cycle complete. {failures} issues remain.")

    elif action == "status":
        from ttlg.self_healing_scout import SelfHealingScout
        scout = SelfHealingScout()
        report = scout.scan()
        print("Self-Healing Status:")
        for f in report["findings"]:
            icon = {"PASS": "+", "WARN": "~", "FAIL": "!"}[f["status"]]
            try:
                print(f"  {icon} {f['check']}: {f.get('message', '')[:60]}")
            except UnicodeEncodeError:
                print(f"  {icon} {f['check']}")

    elif action == "history":
        from ttlg.remediation_runbook import RemediationRunbook
        history = RemediationRunbook().get_action_history(limit=20)
        if not history:
            print("No healing actions recorded yet. Run: epos heal run")
        else:
            print(f"Healing History ({len(history)} actions):\n")
            for h in history:
                icon = "+" if h.get("success") else "!"
                try:
                    print(f"  {icon} {h['timestamp'][:19]} | {h['action_type']:20s} | {h.get('message', '')[:50]}")
                except UnicodeEncodeError:
                    print(f"  {icon} {h['timestamp'][:19]} | {h['action_type']}")

    else:
        print("Available: run, status, history")


def cmd_conv(args):
    """Conversational TTLG diagnostic sessions."""
    action = args[0] if args else "sessions"
    from ttlg_conversational import TTLGConversational
    conv = TTLGConversational()

    if action == "start" and len(args) >= 2:
        client_id = args[1]
        name = args[2] if len(args) > 2 else ""
        industry = args[3] if len(args) > 3 else ""
        result = conv.start_session(client_id, name, industry)
        print(f"Session: {result['session_id']}\n")
        try:
            print(result["message"])
        except UnicodeEncodeError:
            print(result["message"].encode("ascii", errors="replace").decode("ascii"))

    elif action == "respond" and len(args) >= 3:
        session_id = args[1]
        message = " ".join(args[2:])
        result = conv.respond(session_id, message)
        print(f"[{result.get('phase', '?')}]")
        try:
            print(result.get("message", ""))
        except UnicodeEncodeError:
            print(result.get("message", "").encode("ascii", errors="replace").decode("ascii"))

    elif action == "sessions":
        sessions = conv.list_sessions()
        if not sessions:
            print("No sessions. Start: epos conv start <client_id> [name] [industry]")
        else:
            for s in sessions:
                print(f"  [{s['status']:8s}] {s['session_id']} | {s['client_id']} ({s['phase']})")

    else:
        print("Available: start <client_id> [name] [industry], respond <session_id> <message>, sessions")


def cmd_pay(args):
    """Payment gateway commands."""
    action = args[0] if args else "status"
    from payment_gateway import PaymentGateway
    gw = PaymentGateway()

    if action == "status":
        stripe_mode = "LIVE" if gw.stripe_available else "STUB (set STRIPE_SECRET_KEY in .env)"
        print(f"Payment Gateway: {stripe_mode}")
        summary = gw.get_revenue_summary()
        print(f"  Revenue: ${summary['total_revenue']:.2f}")
        print(f"  Transactions: {summary['transaction_count']}")
        journal = gw.get_journal(limit=5)
        if journal:
            print(f"\nRecent:")
            for j in journal[-5:]:
                print(f"  {j['timestamp'][:19]} | {j['event_type']}")

    elif action == "services":
        services = gw.list_services()
        print(f"Service Catalog ({len(services)} offerings):\n")
        for s in services:
            print(f"  {s['id']:30s} {s['price']:>10s}  ({s['type']})")

    elif action == "link" and len(args) >= 3:
        service_id = args[1]
        client_id = args[2]
        email = args[3] if len(args) > 3 else None
        result = gw.create_payment_link(service_id, client_id, email)
        if "error" in result:
            print(f"Error: {result['error']}")
            print(f"Available services: {', '.join(result.get('available', []))}")
        elif result.get("provider") == "stripe":
            print(f"Payment link created: {result['payment_url']}")
        else:
            print(f"Invoice stub: {result.get('stub_id')}")
            print(f"  Service: {result['service_name']}")
            print(f"  Amount: ${result['amount']:.2f}")
            print(f"  {result.get('instructions', '')}")

    elif action == "revenue":
        try:
            from epos_financial import EPOSFinancialOps
            fin = EPOSFinancialOps()
            summary = fin.get_revenue_summary()
            print(f"Revenue (DB): ${summary['total_revenue']:.2f}")
            print(f"  Invoices: {summary['invoice_count']} ({summary['paid']} paid, {summary['draft']} draft, {summary['overdue']} overdue)")
        except Exception as e:
            print(f"DB unavailable: {e}")
            summary = gw.get_revenue_summary()
            print(f"Revenue (journal): ${summary['total_revenue']:.2f} ({summary['transaction_count']} transactions)")

    else:
        print("Available: status, services, link <service_id> <client_id> [email], revenue")


DOMAINS = {
    "friday": cmd_friday,
    "doctor": cmd_doctor,
    "bus": cmd_bus,
    "ttlg": cmd_ttlg,
    "content": cmd_content,
    "crm": cmd_crm,
    "lifeos": cmd_lifeos,
    "skills": cmd_skills,
    "graph": cmd_graph,
    "vault": cmd_vault,
    "projects": cmd_projects,
    "cms": cmd_cms,
    "idea": cmd_idea,
    "sheets": cmd_sheets,
    "ccp": cmd_ccp,
    "pay": cmd_pay,
    "fotw": cmd_fotw,
    "dashboard": cmd_dashboard,
    "paperclip": cmd_paperclip,
    "reputation": cmd_reputation,
    "conv": cmd_conv,
    "heal": cmd_heal,
    "ninth": cmd_ninth,
    "knowledge": cmd_knowledge,
    "daemon": cmd_daemon,
    "browser": cmd_browser,
}


def cmd_ecosystem(args):
    """Full ecosystem status — one command, whole organism."""
    print("EPOS ECOSYSTEM STATUS")
    print("=" * 50)

    # Event bus
    try:
        from epos_event_bus import EPOSEventBus
        bus = EPOSEventBus()
        print(f"\n  Event Bus:     {bus.event_count()} events")
    except Exception:
        print(f"\n  Event Bus:     unavailable")

    # Context graph
    try:
        from context_graph import ContextGraph
        graph = ContextGraph()
        data = json.loads(graph.GRAPH_PATH.read_text(encoding="utf-8"))
        print(f"  Context Graph: {len(data['nodes'])} nodes, {len(data['edges'])} edges")
    except Exception:
        print(f"  Context Graph: unavailable")

    # LifeOS
    try:
        from lifeos_sovereignty import LifeOSSovereignty
        sov = LifeOSSovereignty()
        surface = sov.get_pm_surface()
        print(f"  LifeOS:        Energy {surface['energy']}/10, {surface['active_goals']} goals")
    except Exception:
        print(f"  LifeOS:        unavailable")

    # Ideas
    try:
        from idea_log import IdeaLog
        log = IdeaLog()
        stats = log.stats()
        print(f"  Idea Log:      {stats['total']} ideas")
    except Exception:
        print(f"  Idea Log:      unavailable")

    # Skills
    try:
        from rs1_research_compiler import RS1ResearchCompiler
        compiler = RS1ResearchCompiler()
        skills = compiler.list_skills()
        print(f"  Skills:        {len(skills)} compiled")
    except Exception:
        print(f"  Skills:        unavailable")

    # Content signals
    try:
        from content_signal_loop import ContentSignalLoop
        loop = ContentSignalLoop()
        sig_summary = loop.get_signal_summary()
        print(f"  Content:       {sig_summary['total']} signals today")
    except Exception:
        print(f"  Content:       unavailable")

    # Lead scoring
    try:
        from lead_scoring import LeadScoringEngine
        engine = LeadScoringEngine()
        score_summary = engine.get_score_summary()
        print(f"  Lead Scoring:  {score_summary['total']} scored")
    except Exception:
        print(f"  Lead Scoring:  unavailable")

    # Anchors
    try:
        from friday_daily_anchors import FridayDailyAnchors
        fda = FridayDailyAnchors()
        streak = fda.get_streak()
        print(f"  Anchors:       {streak['total_anchors']} executed")
    except Exception:
        print(f"  Anchors:       unavailable")

    # Vault
    try:
        from path_utils import get_context_vault
        vault = get_context_vault()
        file_count = sum(1 for _ in vault.rglob("*") if _.is_file())
        print(f"  Context Vault: {file_count} files")
    except Exception:
        print(f"  Context Vault: unavailable")

    # Domains
    print(f"\n  CLI Domains:   {len(DOMAINS)} ({', '.join(sorted(DOMAINS.keys()))})")
    print(f"\n  Friday: ONLINE")
    print("=" * 50)


def main():
    if len(sys.argv) < 2:
        print("EPOS — Universal Command Interface\n")
        print("Usage: python epos.py <domain> <action> [args]\n")
        print("Domains:")
        for domain in sorted(DOMAINS.keys()):
            print(f"  {domain}")
        print("\n  ecosystem — full organism status")
        print("\nExamples:")
        print("  python epos.py friday status")
        print("  python epos.py doctor")
        print("  python epos.py bus tail 10")
        print("  python epos.py lifeos goals")
        print("  python epos.py idea log \"My new idea\"")
        print("  python epos.py ecosystem")
        return

    domain = sys.argv[1]
    args = sys.argv[2:]

    if domain == "ecosystem":
        cmd_ecosystem(args)
        return

    handler = DOMAINS.get(domain)
    if handler:
        handler(args)
    else:
        print(f"Unknown domain: {domain}")
        print(f"Available: {', '.join(sorted(DOMAINS.keys()))}, ecosystem")


if __name__ == "__main__":
    main()
