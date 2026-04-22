#!/usr/bin/env python3
# EPOS Artifact — FORGE_DIRECTIVE_AZ_ARMS_20260421
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X, XVI §3
"""
mode_selector.py — Reasoning Router for the Four Execution Variants
====================================================================
Picks exactly one of:
    browser_use.headless
    browser_use.headed
    computer_use.headless
    computer_use.headed

Given a task description + context, the selector decides:

  1. arm:  BROWSER (task scoped to a web browser)  vs
           COMPUTER (OS/desktop-level, cross-app, non-browser targets)

  2. mode: HEADLESS (default: cheap, fast, server-safe)  vs
           HEADED (when visual verification, supervised observability,
                   CAPTCHA risk, or ambiguous UI is expected)

The selector is rule-based for determinism. Ambiguous cases fall back
to configured defaults; callers can override with `mode_hint`.

Article XVI §3 compliance: every screen-dependent op has a routed path
here — there is no "no-agent-available" answer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

Arm = Literal["browser_use", "computer_use"]
Mode = Literal["headless", "headed"]


@dataclass(frozen=True)
class Selection:
    arm: Arm
    mode: Mode
    reason: str
    confidence: float  # 0.0–1.0; <0.6 means defaulted under ambiguity

    @property
    def variant(self) -> str:
        return f"{self.arm}.{self.mode}"

    def to_dict(self) -> dict:
        return {
            "arm": self.arm,
            "mode": self.mode,
            "variant": self.variant,
            "reason": self.reason,
            "confidence": self.confidence,
        }


# ── Rule Vocabulary ───────────────────────────────────────────────

_BROWSER_HINTS = re.compile(
    r"\b(url|http[s]?://|browser|webpage|website|gumroad|linkedin|twitter|x\.com|"
    r"facebook|instagram|youtube|tiktok|reddit|hacker ?news|gmail|outlook|"
    r"google docs|google sheets|airtable|notion|click the button|scroll|"
    r"form|login|oauth|sign in|captcha|spa|single[- ]page)\b",
    re.IGNORECASE,
)

_COMPUTER_HINTS = re.compile(
    r"\b(desktop|finder|explorer|terminal|shell|docker desktop|vs ?code|"
    r"nocodb app|obsidian|notion app|cursor|slack app|system settings|"
    r"open file in|print|save as|operating system|os-level|cross[- ]app|"
    r"clipboard|take a screenshot of the desktop|control panel|registry)\b",
    re.IGNORECASE,
)

_HEADED_HINTS = re.compile(
    r"\b(show me|watch|visual(ly)? verify|let me see|demonstrat(e|ion)|"
    r"screencast|live (walk|demo)|captcha|two[- ]factor|mfa|"
    r"2fa|manual confirm|human in the loop|record a video|record screen|"
    r"supervis(e|ed|ion))\b",
    re.IGNORECASE,
)

_HEADLESS_HINTS = re.compile(
    r"\b(scheduled|cron|nightly|overnight|batch|ci|pipeline|scrape|ingest|"
    r"back(ground|fill)|bulk|run in parallel|no display|silent|quiet)\b",
    re.IGNORECASE,
)


def select(
    task: str,
    context: dict | None = None,
    mode_hint: str | None = None,
) -> Selection:
    """Pick a variant from task description + context.

    mode_hint accepted forms:
        None | "auto"  → let selector decide
        "browser_use"  → arm forced; mode from rules
        "computer_use" → arm forced; mode from rules
        "headless"     → mode forced; arm from rules
        "headed"       → mode forced; arm from rules
        "browser_use.headless" | "browser_use.headed" | ...  → full override
    """
    ctx = context or {}
    hint = (mode_hint or "auto").lower().strip()

    # Full explicit override
    if hint in {"browser_use.headless", "browser_use.headed",
                "computer_use.headless", "computer_use.headed"}:
        arm_str, mode_str = hint.split(".", 1)
        return Selection(
            arm=arm_str,  # type: ignore[arg-type]
            mode=mode_str,  # type: ignore[arg-type]
            reason=f"explicit override ({hint})",
            confidence=1.0,
        )

    # Partial overrides — arm fixed, mode inferred
    forced_arm: Arm | None = None
    if hint in {"browser_use", "computer_use"}:
        forced_arm = hint  # type: ignore[assignment]

    forced_mode: Mode | None = None
    if hint in {"headless", "headed"}:
        forced_mode = hint  # type: ignore[assignment]

    # ── Arm selection (rules) ─────────────────────────────────
    arm: Arm
    arm_reason: str
    if forced_arm:
        arm = forced_arm
        arm_reason = f"arm forced to {forced_arm}"
    else:
        browser_score = len(_BROWSER_HINTS.findall(task))
        computer_score = len(_COMPUTER_HINTS.findall(task))
        if browser_score > computer_score:
            arm, arm_reason = "browser_use", (
                f"browser signals ({browser_score}) > computer signals ({computer_score})"
            )
        elif computer_score > browser_score:
            arm, arm_reason = "computer_use", (
                f"computer signals ({computer_score}) > browser signals ({browser_score})"
            )
        else:
            # Tie → browser_use (safer, sandboxable, more frequent use case)
            arm, arm_reason = "browser_use", "tie — defaulting to browser_use"

    # ── Mode selection (rules) ────────────────────────────────
    mode: Mode
    mode_reason: str
    if forced_mode:
        mode = forced_mode
        mode_reason = f"mode forced to {forced_mode}"
    else:
        headed_score = len(_HEADED_HINTS.findall(task))
        headless_score = len(_HEADLESS_HINTS.findall(task))

        # Context signals
        sovereign_active = bool(ctx.get("sovereign_active"))
        captcha_expected = bool(ctx.get("captcha_expected"))
        scheduled = bool(ctx.get("scheduled"))
        visual_verify = bool(ctx.get("visual_verify"))

        if captcha_expected or visual_verify:
            mode, mode_reason = "headed", "explicit flag (captcha/visual_verify)"
        elif scheduled and not sovereign_active:
            mode, mode_reason = "headless", "scheduled/background run"
        elif headed_score > headless_score:
            mode, mode_reason = "headed", f"headed signals ({headed_score}) in task"
        elif headless_score > headed_score:
            mode, mode_reason = "headless", f"headless signals ({headless_score}) in task"
        else:
            mode, mode_reason = "headless", "default — no visual-verification signal"

    confidence = 0.95 if (forced_arm or forced_mode or hint != "auto") else 0.7
    if "default" in mode_reason or "tie" in arm_reason:
        confidence = min(confidence, 0.5)

    return Selection(
        arm=arm,
        mode=mode,
        reason=f"{arm_reason}; {mode_reason}",
        confidence=confidence,
    )


if __name__ == "__main__":
    cases = [
        ("Scrape top 20 Gumroad products for 'prompt engineering'", None, "auto"),
        ("Show me the Gumroad listing page after I publish", None, "auto"),
        ("Take a screenshot of the desktop and list open windows", None, "auto"),
        ("Log into LinkedIn and expect a CAPTCHA", {"captcha_expected": True}, "auto"),
        ("Publish content on schedule", {"scheduled": True}, "auto"),
        ("Any task", None, "browser_use.headed"),
        ("Any task", None, "headless"),
    ]
    for task, ctx, hint in cases:
        s = select(task, ctx, hint)
        print(f"[{s.variant}] conf={s.confidence:.2f} — {s.reason} :: {task!r}")
    print("PASS: mode_selector")
