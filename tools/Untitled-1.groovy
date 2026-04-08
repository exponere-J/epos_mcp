r"""
# File: C:\Users\Jamie\workspace\epos_mcp\tools\litellm_client.py
# Purpose: Role-based LLM client for EPOS agent trinity.
#          Resolves agent roles (orchestrator, surgeon, researcher)
#          to models via .env aliases. Routes to Google Generative AI
#          directly (fastest path), with OpenRouter fallback.
# Authority: EPOS_CONSTITUTION_v3.1.md, Article II
# Constitutional: Alias Rule — all model IDs resolved via env, never hardcoded.
"""

import os
import sys
import json
import argparse
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

# --- Constitutional: load .env before any env reads ---
from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)

# --- Logging ---
EPOS_ROOT = Path(os.getenv("EPOS_ROOT", Path(__file__).resolve().parent.parent))
LOGS_DIR = EPOS_ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(LOGS_DIR / "litellm_client.log"),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("litellm_client")

# ─────────────────────────────────────────────
# ROLE → MODEL RESOLUTION (from .env)
# ─────────────────────────────────────────────

ROLE_ENV_MAP = {
    "orchestrator": ("FRIDAY_MODEL", "FRIDAY_FALLBACK"),
    "friday": ("FRIDAY_MODEL", "FRIDAY_FALLBACK"),
    "surgeon": ("CLAUDE_CODE_MODEL", "CLAUDE_CODE_FALLBACK"),
    "claude_code": ("CLAUDE_CODE_MODEL", "CLAUDE_CODE_FALLBACK"),
    "cc": ("CLAUDE_CODE_MODEL", "CLAUDE_CODE_FALLBACK"),
    "researcher": ("AZ_MODEL", "AZ_FALLBACK"),
    "az": ("AZ_MODEL", "AZ_FALLBACK"),
    "agent_zero": ("AZ_MODEL", "AZ_FALLBACK"),
}

# Hardcoded last-resort defaults (only if .env is completely empty)
DEFAULT_MODELS = {
    "orchestrator": "gemini-2.0-flash-lite",
    "surgeon": "gemini-2.5-flash",
    "researcher": "gemini-2.5-flash",
}


def resolve_model(role: str) -> tuple[str, Optional[str]]:
    """Resolve an agent role to (primary_model, fallback_model) from .env."""
    role_lower = role.strip().lower()

    if role_lower not in ROLE_ENV_MAP:
        raise ValueError(
            f"Unknown role: '{role}'. "
            f"Valid roles: {sorted(set(ROLE_ENV_MAP.keys()))}"
        )

    primary_key, fallback_key = ROLE_ENV_MAP[role_lower]
    primary = os.getenv(primary_key, "").strip().strip('"').strip("'")
    fallback = os.getenv(fallback_key, "").strip().strip('"').strip("'")

    if not primary:
        # Map to canonical role name for default lookup
        canonical = {
            "friday": "orchestrator",
            "claude_code": "surgeon",
            "cc": "surgeon",
            "agent_zero": "researcher",
            "az": "researcher",
        }.get(role_lower, role_lower)
        primary = DEFAULT_MODELS.get(canonical, "gemini-2.0-flash-lite")
        logger.warning(
            f"No {primary_key} in .env, using default: {primary}"
        )

    return primary, fallback if fallback else None


# ─────────────────────────────────────────────
# MODEL → PROVIDER ROUTING
# ─────────────────────────────────────────────

def _strip_provider_prefix(model: str) -> str:
    """Remove 'google/' or 'openrouter/' prefix for direct API calls."""
    for prefix in ("google/", "openrouter/"):
        if model.lower().startswith(prefix):
            return model[len(prefix):]
    return model


def _call_google_direct(model: str, system: str, prompt: str) -> str:
    """Call Google Generative AI SDK directly. Fastest path."""
    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError(
            "google-generativeai not installed. Run:\n"
            "  pip install google-generativeai --break-system-packages\n"
            "Or in your venv:\n"
            "  pip install google-generativeai"
        )

    api_key = os.getenv("GEMINI_API_KEY", "").strip().strip('"').strip("'")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in .env")

    genai.configure(api_key=api_key)

    clean_model = _strip_provider_prefix(model)
    logger.info(f"Google Direct → {clean_model}")

    gen_model = genai.GenerativeModel(
        model_name=clean_model,
        system_instruction=system if system else None,
    )

    response = gen_model.generate_content(prompt)

    if not response or not response.text:
        raise RuntimeError(f"Empty response from {clean_model}")

    return response.text


def _call_openrouter(model: str, system: str, prompt: str) -> str:
    """Call OpenRouter API. Fallback path."""
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError(
            "openai package not installed. Run:\n"
            "  pip install openai --break-system-packages"
        )

    api_key = os.getenv("OPENROUTER_API_KEY", "").strip().strip('"').strip("'")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not set in .env")

    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )

    # Ensure model has provider prefix for OpenRouter
    or_model = model if "/" in model else f"google/{model}"
    logger.info(f"OpenRouter → {or_model}")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=or_model,
        messages=messages,
        max_tokens=4096,
    )

    if not response.choices:
        raise RuntimeError(f"No choices returned from OpenRouter for {or_model}")

    return response.choices[0].message.content


def _call_anthropic(model: str, system: str, prompt: str) -> str:
    """Call Anthropic API directly."""
    try:
        import anthropic
    except ImportError:
        raise ImportError(
            "anthropic package not installed. Run:\n"
            "  pip install anthropic --break-system-packages"
        )

    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip().strip('"').strip("'")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set in .env")

    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system if system else "",
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text


# ─────────────────────────────────────────────
# UNIFIED CALL INTERFACE
# ─────────────────────────────────────────────

def call(
    role: str,
    prompt: str,
    system: str = "",
    model_override: Optional[str] = None,
) -> dict:
    """
    Call an LLM by agent role.

    Args:
        role: Agent role (orchestrator, surgeon, researcher, friday, cc, az)
        prompt: The user message / task
        system: Optional system prompt
        model_override: Skip role resolution, use this model directly

    Returns:
        dict with keys: role, model, response, fallback_used, timestamp, error
    """
    primary, fallback = resolve_model(role)
    model = model_override or primary
    fallback_used = False
    error = None

    # Determine provider and call
    for attempt_model in [model, fallback]:
        if attempt_model is None:
            continue

        try:
            model_lower = attempt_model.strip().lower()

            if model_lower.startswith("claude-"):
                response_text = _call_anthropic(attempt_model, system, prompt)
            elif (
                model_lower.startswith("google/")
                or "gemini" in model_lower
            ):
                try:
                    response_text = _call_google_direct(
                        attempt_model, system, prompt
                    )
                except Exception as google_err:
                    logger.warning(
                        f"Google direct failed ({google_err}), "
                        f"trying OpenRouter..."
                    )
                    response_text = _call_openrouter(
                        attempt_model, system, prompt
                    )
            else:
                # Default: try OpenRouter for everything else
                response_text = _call_openrouter(attempt_model, system, prompt)

            result = {
                "role": role,
                "model": attempt_model,
                "response": response_text,
                "fallback_used": fallback_used,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": None,
            }

            logger.info(
                f"SUCCESS role={role} model={attempt_model} "
                f"fallback={fallback_used} "
                f"chars={len(response_text)}"
            )

            return result

        except Exception as e:
            error = str(e)
            logger.warning(
                f"FAILED role={role} model={attempt_model} error={error}"
            )
            if attempt_model == model and fallback:
                logger.info(f"Falling back to {fallback}")
                fallback_used = True
                continue
            break

    # All attempts failed
    result = {
        "role": role,
        "model": model,
        "response": None,
        "fallback_used": fallback_used,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "error": error,
    }

    logger.error(f"ALL ATTEMPTS FAILED role={role} error={error}")
    return result


# ─────────────────────────────────────────────
# TTLGClient — Constitutional Wrapper
# ─────────────────────────────────────────────

class TTLGClient:
    """
    High-level client for TTLG phase agents.
    Wraps call() with constitutional context injection,
    JSONL audit logging, and _meta block generation.
    """

    def __init__(self, role: str, constitutional_context: str = ""):
        self.role = role
        self.constitutional_context = constitutional_context
        self._audit_log = LOGS_DIR / "litellm_audit.jsonl"

    def invoke(
        self,
        prompt: str,
        system: str = "",
        scan_id: Optional[str] = None,
        phase: Optional[str] = None,
    ) -> dict:
        """Invoke with full audit trail and optional _meta generation."""
        full_system = self.constitutional_context
        if system:
            full_system = f"{full_system}\n\n{system}" if full_system else system

        result = call(role=self.role, prompt=prompt, system=full_system)

        # Audit log entry
        audit_entry = {
            "timestamp": result["timestamp"],
            "role": self.role,
            "model": result["model"],
            "scan_id": scan_id,
            "phase": phase,
            "prompt_chars": len(prompt),
            "response_chars": len(result["response"]) if result["response"] else 0,
            "fallback_used": result["fallback_used"],
            "error": result["error"],
        }

        try:
            with self._audit_log.open("a", encoding="utf-8") as f:
                f.write(json.dumps(audit_entry) + "\n")
        except Exception as log_err:
            logger.warning(f"Audit log write failed: {log_err}")

        return result

    def generate_meta(
        self,
        scan_id: str,
        phase: str,
        vault_ref: str,
        data: Optional[dict] = None,
    ) -> dict:
        """Generate a _meta block for any artifact."""
        content_str = json.dumps(data, sort_keys=True) if data else ""
        checksum = hashlib.sha256(content_str.encode()).hexdigest()

        return {
            "_meta": {
                "schema_version": "1.0.0",
                "scan_id": scan_id,
                "trace_id": f"trace-{scan_id}-{datetime.now(timezone.utc).strftime('%H%M%S')}",
                "pattern_id": None,
                "agent": self.role,
                "phase": phase,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "checksum": f"sha256:{checksum}",
                "vault_ref": vault_ref,
                "version": 1,
            }
        }


# ─────────────────────────────────────────────
# CLI — Test harness for immediate verification
# ─────────────────────────────────────────────

def _print_env_status():
    """Print current model wiring from .env."""
    print("\n═══ EPOS Model Wiring Status ═══\n")

    for role, (primary_key, fallback_key) in {
        "orchestrator (Friday)": ("FRIDAY_MODEL", "FRIDAY_FALLBACK"),
        "surgeon (Claude Code)": ("CLAUDE_CODE_MODEL", "CLAUDE_CODE_FALLBACK"),
        "researcher (Agent Zero)": ("AZ_MODEL", "AZ_FALLBACK"),
    }.items():
        primary = os.getenv(primary_key, "NOT SET")
        fallback = os.getenv(fallback_key, "NOT SET")
        print(f"  {role}:")
        print(f"    Primary:  {primary}")
        print(f"    Fallback: {fallback}")
        print()

    gemini = "SET" if os.getenv("GEMINI_API_KEY") else "NOT SET"
    openrouter = "SET" if os.getenv("OPENROUTER_API_KEY") else "NOT SET"
    anthropic = "SET" if os.getenv("ANTHROPIC_API_KEY") else "NOT SET"

    print(f"  API Keys:")
    print(f"    GEMINI_API_KEY:     {gemini}")
    print(f"    OPENROUTER_API_KEY: {openrouter}")
    print(f"    ANTHROPIC_API_KEY:  {anthropic}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="EPOS Role-Based LLM Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/litellm_client.py --status
  python tools/litellm_client.py --role surgeon --prompt "What files are in the tools/ directory?"
  python tools/litellm_client.py --role orchestrator --prompt "Summarize system health"
  python tools/litellm_client.py --role researcher --prompt "Analyze the context_vault topology"
        """,
    )
    parser.add_argument(
        "--role",
        choices=["orchestrator", "friday", "surgeon", "claude_code", "cc",
                 "researcher", "az", "agent_zero"],
        help="Agent role to invoke",
    )
    parser.add_argument("--prompt", help="Prompt text to send")
    parser.add_argument("--system", default="", help="System prompt (optional)")
    parser.add_argument(
        "--model", default=None, help="Override model (skip role resolution)"
    )
    parser.add_argument(
        "--status", action="store_true", help="Print .env model wiring status"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output raw JSON response"
    )

    args = parser.parse_args()

    if args.status:
        _print_env_status()
        return

    if not args.role or not args.prompt:
        parser.print_help()
        print("\nError: --role and --prompt are required (or use --status)")
        sys.exit(1)

    print(f"\n═══ EPOS LLM Call ═══")
    print(f"  Role:   {args.role}")

    primary, fallback = resolve_model(args.role)
    print(f"  Model:  {args.model or primary}")
    if fallback:
        print(f"  Fallback: {fallback}")
    print(f"  Prompt: {args.prompt[:80]}{'...' if len(args.prompt) > 80 else ''}")
    print(f"  Calling...\n")

    result = call(
        role=args.role,
        prompt=args.prompt,
        system=args.system,
        model_override=args.model,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    elif result["error"]:
        print(f"ERROR: {result['error']}")
        sys.exit(1)
    else:
        print(f"═══ Response ({result['model']}) ═══\n")
        print(result["response"])
        print(f"\n═══ End ({len(result['response'])} chars, "
              f"fallback={'yes' if result['fallback_used'] else 'no'}) ═══")


if __name__ == "__main__":
    main()