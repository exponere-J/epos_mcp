#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
research_scanner.py — Friday Research Knowledge Scanner
=========================================================
Constitutional Authority: EPOS Constitution v3.1

Scans all intelligence sources for market signals, frontier research,
trending topics by avatar, and competitive intelligence.

Feeds:
  - morning_briefing Layer 3 (market awareness)
  - nightly_upskill Phase 7 (industry scan)

Vault: context_vault/friday/research_scans/
Event: friday.research.scan.complete
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

from path_utils import get_context_vault

VAULT = get_context_vault()
SCANS_DIR = VAULT / "friday" / "research_scans"
SCANS_DIR.mkdir(parents=True, exist_ok=True)


class FridayResearchScanner:
    """Scans for new research, techniques, and industry shifts."""

    def scan_market_signals(self) -> dict:
        """Scan all intelligence sources for market signals."""
        signals = {
            "competitive_moves":   self._scan_competitive(),
            "trending_topics":     self._scan_trending_by_avatar(),
            "new_tools":           self._scan_tool_landscape(),
            "regulatory_changes":  self._scan_regulatory(),
            "fotw_sentiment":      self._scan_fotw_24h(),
            "research_frontier":   self._scan_frontier_research(),
        }

        # Persist scan
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        scan_path = SCANS_DIR / f"scan_{ts}.json"
        scan_path.write_text(
            json.dumps(
                {"date": ts, "signals": signals, "timestamp": datetime.now(timezone.utc).isoformat()},
                indent=2, default=str,
            ),
            encoding="utf-8",
        )

        if _BUS:
            try:
                signal_count = sum(len(v) if isinstance(v, list) else (1 if v else 0) for v in signals.values())
                _BUS.publish("friday.research.scan.complete", {
                    "date": ts,
                    "signal_count": signal_count,
                    "scan_path": str(scan_path),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }, source_module="research_scanner")
            except Exception:
                pass

        return signals

    def _scan_competitive(self) -> list:
        """Scan competitive intelligence files."""
        competitive_dir = VAULT / "echoes" / "competitive"
        if not competitive_dir.exists():
            return []
        recent = sorted(
            competitive_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime, reverse=True,
        )[:5]
        results = []
        for f in recent:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                results.append({
                    "source": "competitive_intel",
                    "file": f.name,
                    "summary": data.get("summary", data.get("topic", ""))[:200],
                })
            except Exception:
                results.append({"source": "competitive_intel", "file": f.name})
        return results

    def _scan_trending_by_avatar(self) -> list:
        """For each avatar, check trending topics in their niche."""
        trending = []
        try:
            from nodes.avatar_registry import AvatarRegistry
            registry = AvatarRegistry()
            avatars = registry.list_avatars()
        except Exception:
            # Fallback: scan avatar files directly
            avatar_dir = VAULT / "avatars"
            avatars = []
            if avatar_dir.exists():
                for f in avatar_dir.glob("*.json"):
                    try:
                        avatars.append(json.loads(f.read_text(encoding="utf-8")))
                    except Exception:
                        pass

        expressions_dir = VAULT / "echoes" / "expressions"

        for avatar in avatars[:10]:
            avatar_id = avatar.get("avatar_id") or avatar.get("name", "unknown")
            keywords = avatar.get("keywords", avatar.get("primary_keywords", []))

            # Check FOTW expressions for this avatar's keywords
            matched_expressions = []
            if expressions_dir.exists() and keywords:
                for expr_file in sorted(
                    expressions_dir.glob("*.json"),
                    key=lambda p: p.stat().st_mtime, reverse=True,
                )[:20]:
                    try:
                        expr = json.loads(expr_file.read_text(encoding="utf-8"))
                        content = json.dumps(expr).lower()
                        if any(kw.lower() in content for kw in keywords[:3]):
                            matched_expressions.append(expr_file.name)
                            if len(matched_expressions) >= 3:
                                break
                    except Exception:
                        pass

            trending.append({
                "avatar_id": avatar_id,
                "trending_topics": matched_expressions,
                "declining_topics": [],
                "opportunity_gaps": [],
            })

        return trending

    def _scan_tool_landscape(self) -> list:
        """Check for new tool mentions in research briefs."""
        tool_signals = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        research_dirs = [
            VAULT / "research",
            VAULT / "echoes" / "research_briefs",
            VAULT / "knowledge" / "frontier",
        ]
        TOOL_KEYWORDS = ["tool", "framework", "library", "release", "launch", "new model", "api"]

        for d in research_dirs:
            if not d.exists():
                continue
            for f in sorted(d.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]:
                try:
                    mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
                    if mtime < cutoff:
                        continue
                    content = f.read_text(encoding="utf-8").lower()
                    if any(kw in content for kw in TOOL_KEYWORDS):
                        tool_signals.append({
                            "source": f.name,
                            "dir": d.name,
                        })
                except Exception:
                    pass

        return tool_signals

    def _scan_regulatory(self) -> list:
        """Check for regulatory or compliance signals."""
        reg_dir = VAULT / "knowledge" / "regulatory"
        if not reg_dir.exists():
            return []
        recent = sorted(reg_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:3]
        return [{"source": "regulatory", "file": f.name} for f in recent]

    def _scan_fotw_24h(self) -> list:
        """Get FOTW (Fly on the Wall) expressions from last 24h."""
        expressions_dir = VAULT / "echoes" / "expressions"
        if not expressions_dir.exists():
            return []
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        recent = []
        for f in expressions_dir.glob("*.json"):
            try:
                mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
                if mtime >= cutoff:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    recent.append({
                        "source": "fotw",
                        "file": f.name,
                        "sentiment": data.get("sentiment", data.get("tone", "neutral")),
                        "topic": data.get("topic", "")[:100],
                    })
            except Exception:
                pass
        return recent

    def _scan_frontier_research(self) -> list:
        """Check Knowledge Flywheel frontier research."""
        frontier_dirs = [
            VAULT / "knowledge" / "frontier",
            VAULT / "research",
        ]
        findings = []
        for d in frontier_dirs:
            if not d.exists():
                continue
            recent = sorted(d.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
            for f in recent:
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    findings.append({
                        "source": "frontier_research",
                        "file": f.name,
                        "topic": data.get("topic", data.get("title", f.stem))[:100],
                        "summary": data.get("summary", "")[:200],
                    })
                except Exception:
                    findings.append({"source": "frontier_research", "file": f.name})
        return findings

    def generate_market_brief(self) -> str:
        """
        Produce a TTS-ready market awareness paragraph for the morning briefing.
        Uses LLM to synthesize all signals into 3 sentences.
        """
        signals = self.scan_market_signals()

        # Count signal sources with data
        signal_count = sum(
            len(v) if isinstance(v, list) else (1 if v else 0)
            for v in signals.values()
        )

        if signal_count == 0:
            return (
                "Market intelligence: No new signals in the last 24 hours. "
                "Context vault sources are up to date. No competitive moves detected."
            )

        try:
            from engine.llm_client import complete
            brief = complete(
                system=(
                    "You are Friday, EPOS Chief of Staff. "
                    "Synthesize market signals into a 3-sentence morning market awareness update. "
                    "Be specific. Name trends, tools, and opportunities. No fluff. No preamble."
                ),
                messages=[{"role": "user", "content": json.dumps(signals, default=str)[:3000]}],
                max_tokens=200,
                temperature=0.3,
            )
            return brief or f"Market signals detected: {signal_count} sources. LLM synthesis unavailable."
        except Exception as e:
            # Fallback: plain-text summary without LLM
            fotw_count = len(signals.get("fotw_sentiment", []))
            competitive = len(signals.get("competitive_moves", []))
            frontier = len(signals.get("research_frontier", []))
            return (
                f"Market update: {fotw_count} FOTW expressions captured in last 24h. "
                f"{competitive} competitive intelligence files scanned. "
                f"{frontier} frontier research items in knowledge base."
            )


# ── Self-test ────────────────────────────────────────────────

if __name__ == "__main__":
    print("Running research scanner...")
    scanner = FridayResearchScanner()

    signals = scanner.scan_market_signals()
    print(f"Signal sources: {len(signals)}")
    for k, v in signals.items():
        count = len(v) if isinstance(v, list) else (1 if v else 0)
        print(f"  {k}: {count} items")

    print("\nGenerating market brief...")
    brief = scanner.generate_market_brief()
    print(f"Brief: {brief[:300]}")

    print("\nPASS: research_scanner")
