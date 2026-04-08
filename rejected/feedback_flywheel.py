from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

QUEUE_DIR = Path("queue/feedback")
OUT_DIR   = Path("out/feedback")
KB_DIR    = Path("knowledge/feedback")

EVENTS_DIR  = KB_DIR / "events"
DIGESTS_DIR = KB_DIR / "digests"
VOC_DIR     = KB_DIR / "voc"

for d in [QUEUE_DIR, OUT_DIR, KB_DIR, EVENTS_DIR, DIGESTS_DIR, VOC_DIR]:
    d.mkdir(parents=True, exist_ok=True)

VOC_CATEGORIES = [
    "data_ownership",
    "export_formats",
    "automation_templates",
    "thread_capture",
    "summarization_memory",
    "privacy_localfirst",
    "workflow_compiler",
    "headless_capture",
    "bug_report",
    "performance",
    "pricing_packaging",
    "documentation_onboarding",
    "other",
]

@dataclass
class FeedbackEvent:
    id: str
    created_at: str
    source: str               # "user", "sprint", "runtime", "market_recon"
    kind: str                 # "wish", "complaint", "bug", "idea", "praise", "metric"
    category: str             # from VOC_CATEGORIES
    severity: int             # 1-5 (bugs/complaints) or 0-5
    signal_strength: int      # 1-5 (how strong the demand)
    title: str
    body: str
    tags: List[str]
    context: Dict[str, Any]

def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")

def _safe_read_json(path: Path) -> Optional[dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def rule_classify(title: str, body: str) -> Dict[str, Any]:
    text = f"{title}\n{body}".lower()

    # BUG patterns
    if "traceback" in text or "exception" in text or "error:" in text or "modulenotfounderror" in text:
        return {"kind": "bug", "category": "bug_report", "severity": 4, "signal_strength": 3, "tags": ["bug"]}

    # WISH patterns (high-level requests)
    wish_hits = [
        ("headless", "headless_capture"),
        ("playwright", "headless_capture"),
        ("browser", "headless_capture"),
        ("export", "export_formats"),
        ("markdown", "export_formats"),
        ("obsidian", "export_formats"),
        ("notion", "export_formats"),
        ("airtable", "automation_templates"),
        ("zapier", "automation_templates"),
        ("make.com", "automation_templates"),
        ("n8n", "automation_templates"),
        ("workflow", "workflow_compiler"),
        ("router", "summarization_memory"),
        ("memory", "summarization_memory"),
        ("privacy", "privacy_localfirst"),
        ("local-first", "privacy_localfirst"),
        ("own my data", "data_ownership"),
        ("thread", "thread_capture"),
        ("chatgpt", "thread_capture"),
        ("claude", "thread_capture"),
        ("perplexity", "thread_capture"),
        ("docs", "documentation_onboarding"),
        ("onboarding", "documentation_onboarding"),
        ("pricing", "pricing_packaging"),
        ("gumroad", "pricing_packaging"),
    ]

    for needle, cat in wish_hits:
        if needle in text:
            return {"kind": "wish", "category": cat, "severity": 2, "signal_strength": 4, "tags": ["voc"]}

    # Complaint patterns
    if any(x in text for x in ["doesn't work", "broken", "fail", "annoying", "hard", "confusing", "slow"]):
        return {"kind": "complaint", "category": "other", "severity": 3, "signal_strength": 3, "tags": ["voc"]}

    return {"kind": "idea", "category": "other", "severity": 1, "signal_strength": 2, "tags": ["misc"]}

def write_jsonl(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def update_rollups(event: FeedbackEvent):
    # 1) Append full event log
    write_jsonl(EVENTS_DIR / "events.jsonl", asdict(event))

    # 2) Append VOC-only
    if "voc" in event.tags or event.kind in ("wish", "complaint"):
        write_jsonl(VOC_DIR / "voc.jsonl", asdict(event))

    # 3) Update counters (cheap analytics)
    metrics_path = KB_DIR / "metrics.json"
    metrics = _safe_read_json(metrics_path) or {"by_category": {}, "by_kind": {}, "total": 0}
    metrics["total"] = int(metrics.get("total", 0)) + 1
    metrics["by_category"][event.category] = int(metrics["by_category"].get(event.category, 0)) + 1
    metrics["by_kind"][event.kind] = int(metrics["by_kind"].get(event.kind, 0)) + 1
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

def create_event(
    *,
    source: str,
    title: str,
    body: str,
    context: Optional[Dict[str, Any]] = None,
    event_id: Optional[str] = None
) -> FeedbackEvent:
    context = context or {}
    meta = rule_classify(title, body)

    event_id = event_id or f"fb_{int(datetime.now().timestamp())}"
    return FeedbackEvent(
        id=event_id,
        created_at=now_iso(),
        source=source,
        kind=meta["kind"],
        category=meta["category"],
        severity=int(meta["severity"]),
        signal_strength=int(meta["signal_strength"]),
        title=title.strip()[:200],
        body=body.strip(),
        tags=list(dict.fromkeys(meta["tags"] + context.get("tags", []))),  # de-dupe preserve order
        context={k: v for k, v in context.items() if k != "tags"},
    )

def process_queue_once() -> int:
    processed = 0
    for p in sorted(QUEUE_DIR.glob("*.json")):
        payload = _safe_read_json(p)
        if not payload:
            # quarantine unreadable files
            bad = OUT_DIR / "bad"
            bad.mkdir(parents=True, exist_ok=True)
            p.rename(bad / p.name)
            continue

        title = payload.get("title", "")
        body = payload.get("body", "")
        source = payload.get("source", "user")
        context = payload.get("context", {})
        event_id = payload.get("id")

        event = create_event(source=source, title=title, body=body, context=context, event_id=event_id)
        update_rollups(event)

        # archive original event
        out_path = OUT_DIR / p.name
        out_path.write_text(json.dumps({"status": "processed", "event": asdict(event)}, indent=2), encoding="utf-8")
        p.unlink(missing_ok=True)
        processed += 1

    return processed

def build_daily_digest() -> Path:
    # simple daily digest: last N events
    events_path = EVENTS_DIR / "events.jsonl"
    if not events_path.exists():
        digest_path = DIGESTS_DIR / f"digest_{datetime.now().date().isoformat()}.md"
        digest_path.write_text("# Feedback Digest\n\nNo events yet.\n", encoding="utf-8")
        return digest_path

    lines = events_path.read_text(encoding="utf-8").splitlines()
    tail = lines[-50:]  # last 50 items
    items = [json.loads(x) for x in tail if x.strip()]

    # Sort by signal*severity descending
    items.sort(key=lambda e: (int(e.get("signal_strength",0))*int(e.get("severity",0))), reverse=True)

    md = []
    md.append(f"# Feedback Digest — {datetime.now().date().isoformat()}\n")
    md.append("## Top Signals (sorted by signal_strength × severity)\n")
    for e in items[:15]:
        score = int(e.get("signal_strength",0))*int(e.get("severity",0))
        md.append(f"- **[{e.get('kind')}/{e.get('category')}]** ({score}) {e.get('title')}\n  - Source: {e.get('source')} | Severity: {e.get('severity')} | Signal: {e.get('signal_strength')}\n")
    md.append("\n## Raw (last 50)\n")
    for e in items:
        md.append(f"- {e.get('created_at')} — {e.get('kind')}/{e.get('category')}: {e.get('title')}\n")

    digest_path = DIGESTS_DIR / f"digest_{datetime.now().date().isoformat()}.md"
    digest_path.write_text("".join(md), encoding="utf-8")
    return digest_path
