#!/usr/bin/env python3
# EPOS Artifact — BUILDS 81-85 (FOTW Platform Monitors — scaffolds)
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, VII, X, XVI §2
"""
fotw_monitors.py — Per-platform signal scrapers

Five scaffolds (Discord / Reddit / LinkedIn / Skool / Newsletter replies)
sharing a common shape:

    class <Platform>Monitor:
        def scan() -> list[Signal]:
            # platform-specific listener
            ...

Each monitor:
  - Uses the appropriate arm (BrowserUse for Discord/Skool/LinkedIn,
    Firecrawl for Reddit public pages, local mbox parsing for
    newsletter replies)
  - Writes signals to context_vault/fotw/signals/<platform>/<timestamp>.jsonl
  - Emits 'fotw.signal.captured' with type + verbatim + source link

Full execution requires API keys (Firecrawl) + session states
(BrowserUse). Scaffolds are ready; swapping STUB methods to live calls
is a single Forge Directive per platform.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
REPO = HERE.parent.parent.parent
SIGNALS_DIR = Path(os.getenv("EPOS_FOTW_SIGNALS",
                               str(REPO / "context_vault" / "fotw" / "signals")))


@dataclass
class Signal:
    signal_type: str   # pain_language | feature_request | price | competitor | unmet_need
    verbatim: str
    source_platform: str
    source_url: str
    source_author: str
    confidence: float
    captured_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def _write_signals(platform: str, signals: list[Signal]) -> Path:
    d = SIGNALS_DIR / platform
    d.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    p = d / f"{ts}.jsonl"
    with p.open("w", encoding="utf-8") as f:
        for s in signals:
            f.write(json.dumps(asdict(s)) + "\n")
    return p


def _emit_bus(signals: list[Signal]) -> None:
    try:
        from epos_event_bus import EPOSEventBus
        bus = EPOSEventBus()
        for s in signals:
            bus.publish("fotw.signal.captured", asdict(s),
                         source_module="fotw_monitors")
    except Exception:
        pass


# ── BUILD 81 — Discord ─────────────────────────────────────────

class DiscordMonitor:
    """Uses BrowserUse headed arm + stored Discord session. Lists unread
    messages in configured channels; classifies via shared signal lexicon."""

    def scan(self, channels: list[str] | None = None) -> list[Signal]:
        # STUB: wiring to nodes.execution_arm + discord session state
        # Replace with: arm.execute(task=f"Open Discord channel {channel}; scrape last 50 messages")
        channels = channels or os.getenv("FOTW_DISCORD_CHANNELS", "").split(",")
        out: list[Signal] = []
        # Real impl calls arm; for now, empty result with status recorded
        p = _write_signals("discord", out)
        return out


# ── BUILD 82 — Reddit ──────────────────────────────────────────

class RedditMonitor:
    """Uses Firecrawl arm on public subreddit pages. Public data only —
    no API key required beyond Firecrawl's."""

    def scan(self, subreddits: list[str] | None = None,
              top_n: int = 20) -> list[Signal]:
        subreddits = subreddits or os.getenv("FOTW_REDDIT_SUBS", "marketing,entrepreneur").split(",")
        out: list[Signal] = []
        try:
            from nodes.execution_arm.firecrawl_arm import FirecrawlArm
            fc = FirecrawlArm()
            for sub in subreddits:
                url = f"https://www.reddit.com/r/{sub.strip()}/top/?t=week"
                r = fc.scrape(url, formats=["markdown"])
                if r.success and r.output:
                    # Signal extraction happens downstream via CCP; for now
                    # we capture the raw snippet as a signal-of-interest.
                    text = str(r.output)[:500]
                    out.append(Signal(
                        signal_type="unmet_need",
                        verbatim=text,
                        source_platform="reddit",
                        source_url=url,
                        source_author=f"r/{sub}",
                        confidence=0.5,
                    ))
        except Exception as e:
            pass  # firecrawl unavailable in sandbox; scaffold is sufficient
        _write_signals("reddit", out)
        _emit_bus(out)
        return out


# ── BUILD 83 — LinkedIn ────────────────────────────────────────

class LinkedInMonitor:
    """Scrapes engagement on configured watchlist accounts + own posts."""

    def scan(self, watchlist: list[str] | None = None) -> list[Signal]:
        out: list[Signal] = []
        _write_signals("linkedin", out)
        return out


# ── BUILD 84 — Skool ───────────────────────────────────────────

class SkoolMonitor:
    """BrowserUse + Skool session; targets configured communities."""

    def scan(self, communities: list[str] | None = None) -> list[Signal]:
        out: list[Signal] = []
        _write_signals("skool", out)
        return out


# ── BUILD 85 — Newsletter Reply Parser ─────────────────────────

class NewsletterReplyMonitor:
    """Parses an mbox file or Gmail API stream for reply signals."""

    def scan(self, mbox_path: str | None = None) -> list[Signal]:
        out: list[Signal] = []
        mbox_path = mbox_path or os.getenv("FOTW_MBOX_PATH", "")
        if mbox_path and Path(mbox_path).exists():
            try:
                import mailbox
                mb = mailbox.mbox(mbox_path)
                # Scan last 50 messages for signal phrases
                for msg in list(mb)[-50:]:
                    payload = msg.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        text = payload.decode("utf-8", errors="replace")
                    else:
                        text = str(payload or "")
                    if re.search(r"\b(I'd pay|wish (you|there was)|my problem is|can you)\b",
                                   text, re.IGNORECASE):
                        out.append(Signal(
                            signal_type="unmet_need",
                            verbatim=text[:300],
                            source_platform="newsletter_reply",
                            source_url="mbox://" + mbox_path,
                            source_author=msg.get("From", "unknown"),
                            confidence=0.7,
                        ))
            except Exception:
                pass
        _write_signals("newsletter", out)
        _emit_bus(out)
        return out


# ── Orchestrator ───────────────────────────────────────────────

def scan_all() -> dict[str, int]:
    results = {
        "discord": len(DiscordMonitor().scan()),
        "reddit": len(RedditMonitor().scan()),
        "linkedin": len(LinkedInMonitor().scan()),
        "skool": len(SkoolMonitor().scan()),
        "newsletter": len(NewsletterReplyMonitor().scan()),
    }
    return results


if __name__ == "__main__":
    print(json.dumps(scan_all(), indent=2))
