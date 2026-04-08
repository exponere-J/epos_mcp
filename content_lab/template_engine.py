#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
template_engine.py — Communication Template Engine
====================================================================
Constitutional Authority: EPOS Constitution v3.1 — Communication Layer

Loads PS-EM / communication templates from context_vault/templates/
and renders them with avatar-specific overrides + runtime variables.

Core operations:
  - load_template(template_id, category=None)
  - render(template_id, avatar_id, context) -> rendered message dict
  - list_templates(category=None)
  - health_check()

Variable resolution priority:
  1. Runtime context (client-specific values)
  2. Avatar-specific overrides from the template
  3. Avatar profile field lookups (from avatar_registry)
  4. Default placeholder literal (if truly missing)
"""

import json
import re
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from path_utils import get_context_vault

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

VAULT = get_context_vault()
TEMPLATES_ROOT = VAULT / "templates"
RENDER_LOG = TEMPLATES_ROOT / "render_log.jsonl"

VAR_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}")


class TemplateEngine:
    """Load + render avatar-calibrated communication templates."""

    def __init__(self, templates_root: Optional[Path] = None):
        self.root = Path(templates_root) if templates_root else TEMPLATES_ROOT
        self._cache: dict[str, dict] = {}

    # ── Loading ──────────────────────────────────────────────────

    def load_template(self, template_id: str,
                      category: Optional[str] = None) -> Optional[dict]:
        cache_key = f"{category}:{template_id}" if category else template_id
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Search in specific category or scan all
        if category:
            path = self.root / category / f"{template_id}.json"
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                self._cache[cache_key] = data
                return data
        else:
            for cat_dir in self.root.iterdir():
                if not cat_dir.is_dir():
                    continue
                path = cat_dir / f"{template_id}.json"
                if path.exists():
                    data = json.loads(path.read_text(encoding="utf-8"))
                    self._cache[cache_key] = data
                    return data
        return None

    def list_templates(self, category: Optional[str] = None) -> list[dict]:
        out = []
        for cat_dir in self.root.iterdir():
            if not cat_dir.is_dir():
                continue
            if category and cat_dir.name != category:
                continue
            for f in sorted(cat_dir.glob("*.json")):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    out.append({
                        "template_id": data.get("template_id"),
                        "category": data.get("category", cat_dir.name),
                        "description": data.get("description"),
                        "version": data.get("version"),
                    })
                except Exception:
                    continue
        return out

    # ── Rendering ────────────────────────────────────────────────

    def render(self, template_id: str, avatar_id: str,
               context: Optional[dict] = None,
               category: Optional[str] = None) -> dict:
        """Render a template with avatar + runtime context."""
        context = context or {}
        template = self.load_template(template_id, category=category)
        if not template:
            return {"error": f"Template not found: {template_id}", "template_id": template_id}

        # Get avatar profile
        try:
            from nodes.avatar_registry import get_registry
            avatar = get_registry().get_avatar(avatar_id) or {}
        except Exception:
            avatar = {}

        # Assemble variable bag
        variables = self._build_variables(template, avatar_id, avatar, context)

        # Render subject + body
        rendered_subject = self._substitute(template.get("subject", ""), variables)
        body_parts = []
        for section in template.get("body_sections", []):
            section_content = self._substitute(section.get("content", ""), variables)
            body_parts.append(section_content)
        body = "\n\n".join(body_parts)

        # CTA token
        cta_pattern = template.get("cta_token_pattern", "CTA-{{template_id}}-{{avatar_id}}-{{date}}")
        cta_token = self._substitute(cta_pattern, {
            **variables,
            "template_id": template.get("template_id", template_id).upper(),
            "avatar_id": avatar_id.upper(),
            "date": datetime.now(timezone.utc).strftime("%Y%m%d"),
        })

        render_id = f"RENDER-{uuid.uuid4().hex[:10]}"
        result = {
            "render_id": render_id,
            "template_id": template_id,
            "avatar_id": avatar_id,
            "subject": rendered_subject,
            "body": body,
            "cta_token": cta_token,
            "rendered_at": datetime.now(timezone.utc).isoformat(),
            "follow_up_trigger": template.get("follow_up_trigger"),
            "escalation": template.get("escalation"),
            "unresolved_placeholders": self._find_unresolved(rendered_subject + " " + body),
        }

        self._log_render(result)

        if _BUS:
            try:
                _BUS.publish("comm.template.rendered", {
                    "render_id": render_id,
                    "template_id": template_id,
                    "avatar_id": avatar_id,
                    "cta_token": cta_token,
                }, source_module="template_engine")
            except Exception:
                pass

        return result

    def _build_variables(self, template: dict, avatar_id: str,
                         avatar: dict, context: dict) -> dict:
        """Assemble the variable bag with priority: runtime > avatar override > avatar profile > defaults."""
        variables: dict = {}

        # 1. Defaults from avatar profile
        comm = avatar.get("communication_preferences", {}) or {}
        demo = avatar.get("demographics", {}) or {}
        variables.update({
            "avatar_id": avatar_id,
            "avatar_name": avatar.get("display_name", avatar_id),
            "avatar_tone": comm.get("tone", "professional"),
            "avatar_vocabulary": comm.get("vocabulary", ""),
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "week_range": datetime.now(timezone.utc).strftime("Week of %b %d, %Y"),
            "sender_name": context.get("sender_name", "Jamie Purdue"),
            "sender_title": context.get("sender_title", "Sovereign Architect"),
        })

        # 2. Avatar-specific overrides from the template
        avatar_overrides = template.get("avatar_overrides", {}).get(avatar_id, {})
        variables.update(avatar_overrides)

        # 3. Runtime context (highest priority)
        variables.update(context)

        return variables

    def _substitute(self, text: str, variables: dict) -> str:
        """Replace {{var}} and {{obj.field}} patterns."""
        if not text:
            return ""

        def repl(match):
            key = match.group(1)
            if "." in key:
                parts = key.split(".")
                val = variables
                for p in parts:
                    if isinstance(val, dict):
                        val = val.get(p, f"{{{{{key}}}}}")
                    else:
                        val = f"{{{{{key}}}}}"
                        break
                return str(val)
            return str(variables.get(key, f"{{{{{key}}}}}"))

        return VAR_PATTERN.sub(repl, text)

    def _find_unresolved(self, text: str) -> list[str]:
        return sorted(set(VAR_PATTERN.findall(text)))

    def _log_render(self, result: dict):
        try:
            RENDER_LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(RENDER_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "timestamp": result["rendered_at"],
                    "render_id": result["render_id"],
                    "template_id": result["template_id"],
                    "avatar_id": result["avatar_id"],
                    "cta_token": result["cta_token"],
                    "unresolved": result["unresolved_placeholders"],
                }) + "\n")
        except Exception:
            pass

    # ── Health ───────────────────────────────────────────────────

    def health_check(self) -> dict:
        try:
            templates = self.list_templates()
            cats: dict = {}
            for t in templates:
                cats[t["category"]] = cats.get(t["category"], 0) + 1
            return {
                "node": "template_engine",
                "status": "operational" if templates else "degraded",
                "template_count": len(templates),
                "categories": cats,
                "templates_root": str(self.root),
            }
        except Exception as e:
            return {"node": "template_engine", "status": "error", "error": str(e)[:200]}


# ── Self-Test ────────────────────────────────────────────────────

if __name__ == "__main__":
    passed = 0
    engine = TemplateEngine()

    # Test 1: List templates
    templates = engine.list_templates()
    assert len(templates) >= 5, f"Expected 5+ templates, got {len(templates)}"
    print(f"Loaded {len(templates)} templates:")
    for t in templates:
        print(f"  - [{t['category']}] {t['template_id']}")
    passed += 1

    # Test 2: Render cold outreach for local_champion
    result = engine.render(
        "cold_outreach",
        avatar_id="local_champion",
        context={
            "client_name": "Mike",
            "niche": "pressure washing",
            "sender_name": "Jamie Purdue",
            "sender_title": "Sovereign Architect",
        }
    )
    assert "error" not in result
    assert "Mike" in result["body"]
    assert "pressure washing" in result["body"].lower() or "pressure washing" in result["subject"].lower()
    assert result["cta_token"].startswith("CTA-")
    print(f"\nCold outreach -> local_champion:")
    print(f"  Subject: {result['subject']}")
    print(f"  Body preview: {result['body'][:200]}")
    print(f"  CTA token: {result['cta_token']}")
    print(f"  Unresolved: {result['unresolved_placeholders']}")
    passed += 1

    # Test 3: Render welcome for solo_strategic_consultant
    r2 = engine.render(
        "welcome",
        avatar_id="solo_strategic_consultant",
        context={
            "client_name": "Sarah",
            "support_number": "+1-555-0100",
            "kickoff_link": "https://cal.com/jamie/kickoff",
        }
    )
    assert "error" not in r2
    assert "Sarah" in r2["body"]
    print(f"\nWelcome -> solo_strategic_consultant:")
    print(f"  Subject: {r2['subject']}")
    passed += 1

    # Test 4: Render invoice for agency_builder
    r3 = engine.render(
        "invoice",
        avatar_id="agency_builder",
        context={
            "client_name": "Alex",
            "invoice_number": "INV-2026-042",
            "invoice_amount": "$4,997",
            "invoice_description": "Agency Margin Playbook — Month 2 of 6",
            "due_date": "April 15, 2026",
            "payment_link": "https://pay.epos.dev/INV-2026-042",
            "metric_margin_delta": "+6.2",
            "metric_playbooks_rolled": "3",
        }
    )
    assert "error" not in r3
    assert "$4,997" in r3["body"] or "4,997" in r3["body"]
    assert "CTA-INVOICE" in r3["cta_token"]
    print(f"\nInvoice -> agency_builder:")
    print(f"  Subject: {r3['subject']}")
    print(f"  CTA token: {r3['cta_token']}")
    passed += 1

    # Test 5: Missing template returns error without crash
    err = engine.render("nonexistent", avatar_id="local_champion", context={})
    assert "error" in err
    passed += 1

    # Test 6: Missing fields don't crash — leave placeholders visible
    minimal = engine.render("weekly_brief", avatar_id="local_champion", context={})
    assert "error" not in minimal
    assert len(minimal["unresolved_placeholders"]) >= 1  # signal_1/2/3 not provided
    print(f"\nWeekly brief minimal render — unresolved: {minimal['unresolved_placeholders']}")
    passed += 1

    # Test 7: Health
    h = engine.health_check()
    assert h["status"] == "operational"
    assert h["template_count"] >= 5
    print(f"\nHealth: {h['status']} templates={h['template_count']} categories={h['categories']}")
    passed += 1

    print(f"\nPASS: template_engine ({passed} assertions)")
