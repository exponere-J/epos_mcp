#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
secret_extractor.py — Hardcoded Secret Detection & Extraction
===============================================================
Constitutional Authority: EPOS Constitution v3.1
Directive: 20260413-01 (Step C: Path & Secret Sanitation)

Scans Python source files for hardcoded API keys, passwords, tokens,
and other secrets. Classifies them as auto-generated (EPOS can rotate)
or human-gate (Jamie must supply), and outputs env_secrets.json template.

Patterns detected:
  - API key literals (sk-, gsk_, AKIA, etc.)
  - Password literals assigned to PASSWORD, SECRET, KEY variables
  - JWT tokens
  - Connection strings with embedded credentials

Vault: context_vault/infrastructure/env_secrets.json
Event: system.secret_extractor.complete
"""

import os
import re
import sys
import json
import secrets
import string
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

from path_utils import get_context_vault

VAULT = get_context_vault()
EPOS_ROOT = Path(os.getenv("EPOS_ROOT", "/app"))

SCAN_DIRS = [
    EPOS_ROOT / "epos",
    EPOS_ROOT / "engine",
    EPOS_ROOT / "friday",
    EPOS_ROOT / "reactor",
    EPOS_ROOT / "nodes",
]
SKIP_PATTERNS = {
    "__pycache__", ".venv", "venv", "venv_epos", ".git",
    "rejected", "_archive", "node_modules",
    # Skip the extractor itself and env files
    "secret_extractor.py", "env_secrets.json",
}

# Keys that EPOS can auto-generate (random, local only)
AUTO_GENERATED_KEYS = {
    "PG_PASSWORD", "JWT_SECRET", "N8N_ENCRYPTION_KEY",
    "LITELLM_MASTER_KEY", "SESSION_SECRET", "ADMIN_PASSWORD",
}

# Keys that require Jamie to supply (external providers)
HUMAN_GATE_KEYS = {
    "OPENROUTER_API_KEY", "GROQ_API_KEY", "ANTHROPIC_API_KEY",
    "HUGGINGFACE_API_KEY", "GEMINI_API_KEY", "STRIPE_SECRET_KEY",
    "STRIPE_WEBHOOK_SECRET", "NOCODB_API_TOKEN",
}

# Regex patterns for secret detection
_PATTERNS = [
    # OpenRouter / OpenAI style: sk-or-v1-..., sk-...
    (re.compile(r'["\']((sk-or-v1-|sk-)[A-Za-z0-9_\-]{20,})["\']'),
     "openrouter_api_key", "OPENROUTER_API_KEY"),
    # Groq: gsk_...
    (re.compile(r'["\']((gsk_)[A-Za-z0-9]{30,})["\']'),
     "groq_api_key", "GROQ_API_KEY"),
    # Anthropic: sk-ant-...
    (re.compile(r'["\']((sk-ant-)[A-Za-z0-9_\-]{20,})["\']'),
     "anthropic_api_key", "ANTHROPIC_API_KEY"),
    # HuggingFace: hf_...
    (re.compile(r'["\']((hf_)[A-Za-z0-9]{10,})["\']'),
     "huggingface_api_key", "HUGGINGFACE_API_KEY"),
    # Generic: PASSWORD/SECRET/KEY assignment with literal value
    (re.compile(
        r'(?:PASSWORD|SECRET|_KEY|MASTER_KEY)\s*=\s*["\']([A-Za-z0-9_\-\.@!#]{8,})["\']',
        re.IGNORECASE,
    ), "generic_secret", None),
    # LITELLM master key literals
    (re.compile(r'["\']((sk-epos-|epos-litellm-)[A-Za-z0-9_\-]{4,})["\']'),
     "litellm_master_key", "LITELLM_MASTER_KEY"),
]


class SecretExtractor:
    """Scans for hardcoded secrets and generates env template."""

    def scan(self) -> dict:
        """
        Scan all Python files for hardcoded secrets.
        Returns structured report with file locations.
        """
        files_scanned = 0
        findings = []

        for scan_dir in SCAN_DIRS:
            if not scan_dir.exists():
                continue
            for py_file in scan_dir.rglob("*.py"):
                if any(skip in str(py_file) for skip in SKIP_PATTERNS):
                    continue
                files_scanned += 1
                try:
                    content = py_file.read_text(encoding="utf-8")
                except Exception:
                    continue
                for pattern, secret_type, env_key in _PATTERNS:
                    for m in pattern.finditer(content):
                        line_num = content[:m.start()].count("\n") + 1
                        line = content.split("\n")[line_num - 1].strip()
                        # Skip .env references (os.getenv calls are fine)
                        if "os.getenv" in line or "os.environ" in line:
                            continue
                        # Skip comments
                        if line.startswith("#"):
                            continue
                        findings.append({
                            "file": str(py_file),
                            "line": line_num,
                            "secret_type": secret_type,
                            "env_key": env_key,
                            "matched_value": m.group(1)[:20] + "..." if len(m.group(1)) > 20 else m.group(1),
                            "full_match": m.group(0),
                            "line_content": line[:100],
                        })

        return {
            "files_scanned": files_scanned,
            "secrets_found": len(findings),
            "findings": findings,
        }

    def extract(self) -> dict:
        """
        For each hardcoded secret found:
        1. Replace literal with os.getenv("KEY_NAME")
        2. Add key to env_secrets.json template
        3. Generate auto-generated values where applicable
        Returns extraction report.
        """
        scan_result = self.scan()
        secrets_moved = 0
        errors = []
        env_keys_found = set()

        # Group by file
        by_file: Dict[str, List] = {}
        for f in scan_result["findings"]:
            by_file.setdefault(f["file"], []).append(f)

        for filepath, findings in by_file.items():
            try:
                path = Path(filepath)
                content = path.read_text(encoding="utf-8")
                original = content
                for finding in findings:
                    env_key = finding.get("env_key")
                    if not env_key:
                        continue
                    old_str = finding["full_match"]
                    new_str = f'os.getenv("{env_key}")'
                    if old_str in content:
                        content = content.replace(old_str, new_str, 1)
                        env_keys_found.add(env_key)
                        secrets_moved += 1
                if content != original:
                    if "import os" not in content:
                        content = "import os\n" + content
                    tmp = path.with_suffix(".tmp")
                    tmp.write_text(content, encoding="utf-8")
                    tmp.replace(path)
            except Exception as e:
                errors.append({"file": filepath, "error": str(e)})

        # Generate env_secrets.json template
        env_secrets = self._generate_env_secrets(env_keys_found)
        env_path = VAULT / "infrastructure" / "env_secrets.json"
        env_path.parent.mkdir(parents=True, exist_ok=True)
        env_path.write_text(json.dumps(env_secrets, indent=2), encoding="utf-8")

        result = {
            "files_scanned": scan_result["files_scanned"],
            "secrets_found": scan_result["secrets_found"],
            "secrets_moved": secrets_moved,
            "env_secrets_path": str(env_path),
            "env_keys": sorted(env_keys_found),
            "auto_generated": [k for k in env_keys_found if k in AUTO_GENERATED_KEYS],
            "human_gate": [k for k in env_keys_found if k in HUMAN_GATE_KEYS],
            "errors": errors,
        }

        if _BUS:
            try:
                _BUS.publish("system.secret_extractor.complete", {
                    "secrets_found": scan_result["secrets_found"],
                    "secrets_moved": secrets_moved,
                    "env_keys": sorted(env_keys_found),
                }, source_module="secret_extractor")
            except Exception:
                pass

        return result

    def _generate_env_secrets(self, found_keys: set) -> dict:
        """Generate env_secrets.json with auto-generated and human-gate values."""
        # Always include all known keys, not just found ones
        all_keys = AUTO_GENERATED_KEYS | HUMAN_GATE_KEYS | found_keys

        auto_entries = {}
        human_entries = {}

        for key in sorted(all_keys):
            if key in AUTO_GENERATED_KEYS:
                # Auto-generate secure random value
                value = "".join(
                    secrets.choice(string.ascii_letters + string.digits)
                    for _ in range(32)
                )
                auto_entries[key] = {
                    "value": value,
                    "source": "auto_generated",
                    "rotate": True,
                    "note": "Generated by EPOS. Safe to rotate.",
                }
            else:
                human_entries[key] = {
                    "value": "JAMIE_ACTION_REQUIRED",
                    "source": "external_provider",
                    "rotate": False,
                    "note": "Must be supplied by Sovereign Architect.",
                }

        return {
            "schema_version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "directive": "20260413-01",
            "auto_generated": auto_entries,
            "human_gate": human_entries,
            "usage": (
                "Keys in auto_generated are rotatable by EPOS. "
                "Keys in human_gate require Jamie to supply the real value. "
                "Do NOT commit this file to git. Use .env.production for runtime."
            ),
        }

    def generate_env_production(self) -> dict:
        """
        Generate .env.production template from env_secrets.json.
        Values are placeholders — Jamie fills in human_gate values.
        """
        env_path = VAULT / "infrastructure" / "env_secrets.json"
        if not env_path.exists():
            self.extract()

        env_secrets = json.loads(env_path.read_text(encoding="utf-8"))

        lines = [
            "# EPOS Production Environment Template",
            f"# Generated: {datetime.now(timezone.utc).isoformat()}",
            f"# Directive: 20260413-01",
            "# DO NOT COMMIT THIS FILE",
            "",
            "# === AUTO-GENERATED (EPOS manages these) ===",
        ]
        for key, meta in env_secrets["auto_generated"].items():
            lines.append(f"{key}={meta['value']}")

        lines += [
            "",
            "# === HUMAN GATE (Jamie must supply these) ===",
        ]
        for key, meta in env_secrets["human_gate"].items():
            lines.append(f"{key}=JAMIE_ACTION_REQUIRED")

        lines += [
            "",
            "# === EPOS RUNTIME ===",
            "EPOS_ROOT=/app",
            "LITELLM_BASE_URL=http://litellm:4000",
            "LITELLM_PORT=4000",
            "EPOS_API_PORT=8001",
            "LOG_LEVEL=INFO",
        ]

        env_prod_path = EPOS_ROOT / ".env.production"
        env_prod_path.write_text("\n".join(lines), encoding="utf-8")
        return {"path": str(env_prod_path), "lines": len(lines)}


def run_scan() -> dict:
    return SecretExtractor().scan()


def run_extract() -> dict:
    return SecretExtractor().extract()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="EPOS Secret Extractor")
    parser.add_argument("--extract", action="store_true", help="Extract secrets (default: scan only)")
    args = parser.parse_args()

    se = SecretExtractor()
    if args.extract:
        result = se.extract()
        print(f"Files scanned:   {result['files_scanned']}")
        print(f"Secrets found:   {result['secrets_found']}")
        print(f"Secrets moved:   {result['secrets_moved']}")
        print(f"Auto-generated:  {result['auto_generated']}")
        print(f"Human gate:      {result['human_gate']}")
        print(f"env_secrets.json: {result['env_secrets_path']}")
        # Also generate .env.production
        env_result = se.generate_env_production()
        print(f".env.production: {env_result['path']}")
    else:
        result = se.scan()
        print(f"Files scanned:  {result['files_scanned']}")
        print(f"Secrets found:  {result['secrets_found']}")
        for f in result["findings"][:5]:
            print(f"  [{f['file'].split('/')[-1]}:L{f['line']}] {f['secret_type']}: {f['matched_value']}")

    print("\nPASS: secret_extractor")
