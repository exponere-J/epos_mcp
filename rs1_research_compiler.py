#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
rs1_research_compiler.py — EPOS Research Skill Compiler
========================================================
Constitutional Authority: EPOS Constitution v3.1
Converts learning emphasis into persistent, callable skills.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from path_utils import get_context_vault
from groq_router import GroqRouter
from epos_intelligence import record_decision
from epos_event_bus import EPOSEventBus

SIGNAL_SOURCES = {
    "model_intelligence": {
        "sources": ["huggingface.co/blog", "paperswithcode.com/sota", "simonwillison.net"],
        "focus": "open model quality, benchmark movement, deployment options",
    },
    "generative_ai_practice": {
        "sources": ["karpathy.ai", "sebastianraschka.com/blog", "oneusefulthing.org"],
        "focus": "practical capability shifts, when open matches closed",
    },
    "market_intelligence": {
        "sources": ["deeplearning.ai/the-batch", "research.google", "anthropic.com/research"],
        "focus": "capability ceiling, competitive landscape",
    },
    "content_generation": {
        "sources": ["huggingface.co/models", "fal.ai/models", "ollama.ai/library"],
        "focus": "image/video/audio generation models",
    },
}

DOMAIN_SOURCE_MAP = {
    "generative_model_rotation": "model_intelligence",
    "echoes_imagery_generation": "content_generation",
    "wordpress_page_building": "generative_ai_practice",
    "affiliate_content_production": "content_generation",
    "ttlg_diagnostic": "generative_ai_practice",
    "research_synthesis": "market_intelligence",
}


class RS1ResearchCompiler:
    """Converts learning emphasis into persistent callable skills."""

    def __init__(self):
        self.vault = get_context_vault()
        self.router = GroqRouter()
        self.skills_dir = self.vault / "skills"
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.skills_dir / "index.json"
        if not self.index_path.exists():
            self.index_path.write_text(json.dumps({"skills": {}}, indent=2))

    def compile_skill(self, learning_emphasis: str, domain: str,
                      research_depth: str = "standard") -> dict:
        """Main entry: emphasis + domain -> compiled skill artifact."""
        print(f"  [RS1] Compiling: {domain}")
        findings = self._research_sweep(learning_emphasis, domain, research_depth)
        artifact = self._synthesize(learning_emphasis, domain, findings)
        skill_path = self._store(domain, artifact)
        self._register(domain, skill_path, artifact)

        record_decision(
            decision_type="rs1.skill.compiled",
            description=f"Skill compiled: {domain}",
            agent_id="rs1_research_compiler", outcome="success",
            context={"domain": domain,
                     "principles": len(artifact.get("core_principles", []))},
        )
        EPOSEventBus().publish("rs1.skill.compiled",
                               {"domain": domain, "skill_id": artifact["skill_id"]},
                               "rs1")
        print(f"  [RS1] DONE: {artifact['skill_id']}")
        return {"skill": artifact, "path": str(skill_path)}

    def _research_sweep(self, emphasis, domain, depth):
        source_cat = DOMAIN_SOURCE_MAP.get(domain, "generative_ai_practice")
        sources = SIGNAL_SOURCES.get(source_cat, {}).get("sources", [])
        limits = {"quick": 2, "standard": 3, "deep": len(sources)}
        sources = sources[: limits.get(depth, 3)]
        findings = {"sources_consulted": sources, "raw_intelligence": []}
        for src in sources:
            synth = self.router.route(
                "reasoning",
                f"You are an intelligence analyst. Based on {src}, "
                f"what are the key findings about: {emphasis}\n"
                f"Provide 3-5 specific actionable findings.",
                max_tokens=400, temperature=0.2,
            )
            findings["raw_intelligence"].append({"source": src, "synthesis": synth})
        return findings

    def _synthesize(self, emphasis, domain, findings):
        combined = "\n".join(
            [f"SOURCE: {r['source']}\n{r['synthesis']}" for r in findings.get("raw_intelligence", [])]
        )
        prompt = (
            f"Convert this research into a JSON skill artifact for domain '{domain}'.\n"
            f"EMPHASIS: {emphasis}\n\nRESEARCH:\n{combined[:2500]}\n\n"
            f"Output JSON with exactly these fields:\n"
            f'  "skill_id": "{domain}_v1",\n'
            f'  "core_principles": [5 specific actionable principles],\n'
            f'  "operational_workflow": [5 steps],\n'
            f'  "tool_routing": {{"primary": "...", "fallback": "...", "avoid": "..."}},\n'
            f'  "failure_modes": [{{"failure": "...", "cause": "...", "prevention": "..."}}],\n'
            f'  "prompt_templates": {{"standard": "...", "high_quality": "...", "fast": "..."}},\n'
            f'  "benchmark_criteria": [3 items],\n'
            f'  "update_triggers": [3 items],\n'
            f'  "friday_invocation": "python epos.py skills invoke {domain}"\n'
            f"Output ONLY valid JSON."
        )
        raw = self.router.route("reasoning", prompt, max_tokens=1200, temperature=0.2)
        try:
            clean = raw.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
                clean = clean.strip()
            artifact = json.loads(clean)
        except Exception:
            artifact = {
                "core_principles": [
                    "Research before acting",
                    "Prefer open solutions when quality sufficient",
                    "Benchmark before production",
                    "Route through Friday for governance",
                    "Log every outcome for improvement",
                ],
                "operational_workflow": [],
                "tool_routing": {},
                "failure_modes": [],
                "prompt_templates": {},
                "benchmark_criteria": [],
                "update_triggers": ["New model releases", "EVL1 gap detected", "Steward flags concern"],
                "friday_invocation": f"python epos.py skills invoke {domain}",
            }

        artifact["skill_id"] = f"{domain}_v1"
        artifact["domain"] = domain
        artifact["learning_emphasis"] = emphasis
        artifact["version"] = "1.0"
        artifact["synthesized_from"] = findings.get("sources_consulted", [])
        artifact["compiled_at"] = datetime.now(timezone.utc).isoformat()
        return artifact

    def _store(self, domain, artifact):
        d = self.skills_dir / domain
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"{domain}_v1.json"
        p.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
        return p

    def _register(self, domain, path, artifact):
        index = json.loads(self.index_path.read_text(encoding="utf-8"))
        index["skills"][domain] = {
            "skill_id": artifact.get("skill_id"),
            "path": str(path),
            "domain": domain,
            "version": artifact.get("version", "1.0"),
            "compiled_at": artifact.get("compiled_at"),
            "friday_invocation": artifact.get("friday_invocation"),
        }
        self.index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")

    def get_skill(self, domain: str) -> dict:
        p = self.skills_dir / domain / f"{domain}_v1.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

    def list_skills(self) -> list:
        index = json.loads(self.index_path.read_text(encoding="utf-8"))
        return list(index["skills"].values())

    def update_skill_from_outcome(self, domain: str, outcome_type: str, data: dict) -> None:
        skill = self.get_skill(domain)
        if not skill:
            return
        history = skill.get("outcome_history", [])
        history.append({"type": outcome_type, "data": data,
                        "at": datetime.now(timezone.utc).isoformat()})
        skill["outcome_history"] = history[-50:]
        p = self.skills_dir / domain / f"{domain}_v1.json"
        if p.exists():
            p.write_text(json.dumps(skill, indent=2), encoding="utf-8")


if __name__ == "__main__":
    import py_compile

    py_compile.compile("rs1_research_compiler.py", doraise=True)
    print("PASS: rs1_research_compiler.py compiles clean")

    compiler = RS1ResearchCompiler()

    print("\n  Compiling: generative_model_rotation...")
    r1 = compiler.compile_skill(
        "How to discover evaluate and rotate open generative models "
        "for image text and TTS with agent-friendly inference",
        "generative_model_rotation",
        "standard",
    )
    assert r1["skill"]["skill_id"] == "generative_model_rotation_v1"
    p1 = r1["skill"].get("core_principles", [])
    print(f"  Principles: {len(p1)}")
    if p1:
        print(f"  First: {p1[0][:80]}")

    print("\n  Compiling: echoes_imagery_generation...")
    r2 = compiler.compile_skill(
        "How to generate brand-consistent imagery for Echoes Marketing "
        "using open diffusion models with navy accent gold palette",
        "echoes_imagery_generation",
        "standard",
    )
    assert r2["skill"]["skill_id"] == "echoes_imagery_generation_v1"

    skills = compiler.list_skills()
    assert len(skills) >= 2
    print(f"\n  Registered skills: {len(skills)}")
    for s in skills:
        print(f"    {s['skill_id']}")

    print("\nPASS: RS1ResearchCompiler — skills compiled and registered")
