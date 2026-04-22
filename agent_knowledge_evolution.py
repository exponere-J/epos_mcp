#!/usr/bin/env python3
"""
agent_knowledge_evolution.py — Agent Knowledge Evolution System
================================================================
Constitutional Authority: EPOS Constitution v3.1
File: /mnt/c/Users/Jamie/workspace/epos_mcp/agent_knowledge_evolution.py
# EPOS GOVERNANCE WATERMARK

The living knowledge base for every agent in the EPOS ecosystem.
Grows through five channels: domain expertise, strategic frameworks,
interaction learnings, failure cases, and weekly synthesis.
Queried at reasoning time to enrich prompts beyond static system prompts.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from path_utils import get_context_vault
from epos_intelligence import record_decision


class AgentKnowledgeBase:
    """
    The living knowledge base for a single agent.
    Grows through five channels simultaneously.
    Queried at reasoning time to provide context
    beyond the static system prompt.
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.base_path = get_context_vault() / "agent_knowledge" / agent_id
        self.base_path.mkdir(parents=True, exist_ok=True)
        for fname in [
            "domain_expertise.jsonl",
            "strategic_frameworks.jsonl",
            "interaction_learnings.jsonl",
            "failure_cases.jsonl",
            "growth_log.jsonl",
        ]:
            (self.base_path / fname).touch()

    def record_interaction_learning(
        self, situation: str, action_taken: str,
        outcome: str, insight: str, outcome_score: float
    ) -> None:
        """Record an interaction learning. outcome_score: 0-1 scale."""
        entry = {
            "learning_id": uuid.uuid4().hex[:8],
            "agent_id": self.agent_id,
            "situation": situation,
            "action_taken": action_taken,
            "outcome": outcome,
            "insight": insight,
            "outcome_score": outcome_score,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        self._append("interaction_learnings.jsonl", entry)
        self._log_growth("interaction_learning", insight)

    def record_failure_case(
        self, situation: str, action_taken: str,
        what_went_wrong: str, root_cause: str, correction: str
    ) -> None:
        """Record a failure case — the most valuable intelligence."""
        entry = {
            "failure_id": uuid.uuid4().hex[:8],
            "agent_id": self.agent_id,
            "situation": situation,
            "action_taken": action_taken,
            "what_went_wrong": what_went_wrong,
            "root_cause": root_cause,
            "correction": correction,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        self._append("failure_cases.jsonl", entry)
        self._log_growth("failure_case", root_cause)

    def add_domain_expertise(
        self, topic: str, expertise: str,
        source: str, confidence: float = 0.7
    ) -> None:
        """Add domain knowledge to the agent's base."""
        entry = {
            "expertise_id": uuid.uuid4().hex[:8],
            "agent_id": self.agent_id,
            "topic": topic,
            "expertise": expertise,
            "source": source,
            "confidence": confidence,
            "added_at": datetime.now(timezone.utc).isoformat(),
        }
        self._append("domain_expertise.jsonl", entry)
        self._log_growth("domain_expertise", topic)

    def add_strategic_framework(
        self, framework_name: str, description: str,
        when_to_apply: str, source: str
    ) -> None:
        """Add a strategic framework — a mental model for a class of situations."""
        entry = {
            "framework_id": uuid.uuid4().hex[:8],
            "agent_id": self.agent_id,
            "framework_name": framework_name,
            "description": description,
            "when_to_apply": when_to_apply,
            "source": source,
            "added_at": datetime.now(timezone.utc).isoformat(),
        }
        self._append("strategic_frameworks.jsonl", entry)
        self._log_growth("strategic_framework", framework_name)

    def query_relevant_knowledge(self, situation: str, top_k: int = 5) -> dict:
        """
        Query knowledge base for entries relevant to the current situation.
        Keyword matching for speed. Future: semantic search via embeddings.
        """
        situation_words = set(situation.lower().split())
        results = {}
        for category in [
            "domain_expertise", "strategic_frameworks",
            "interaction_learnings", "failure_cases",
        ]:
            entries = self._read_all(f"{category}.jsonl")
            scored = []
            for entry in entries:
                text = json.dumps(entry).lower()
                overlap = len(situation_words & set(text.split()))
                if overlap > 0:
                    scored.append((overlap, entry))
            scored.sort(key=lambda x: x[0], reverse=True)
            results[category] = [e for _, e in scored[:top_k]]
        return results

    def build_enriched_prompt(self, base_system_prompt: str,
                               current_situation: str) -> str:
        """
        The key method. Takes a static system prompt and enriches it
        with relevant knowledge. Every call may be richer than the last.
        """
        knowledge = self.query_relevant_knowledge(current_situation, top_k=3)
        additions = []

        if knowledge["domain_expertise"]:
            additions.append(
                "RELEVANT DOMAIN EXPERTISE:\n" +
                "\n".join([f"- [{e['topic']}]: {e['expertise']}"
                           for e in knowledge["domain_expertise"]])
            )
        if knowledge["strategic_frameworks"]:
            additions.append(
                "APPLICABLE FRAMEWORKS:\n" +
                "\n".join([f"- [{e['framework_name']}]: {e['description']} "
                           f"(apply when: {e['when_to_apply']})"
                           for e in knowledge["strategic_frameworks"]])
            )
        if knowledge["interaction_learnings"]:
            high_score = [e for e in knowledge["interaction_learnings"]
                          if e.get("outcome_score", 0) > 0.7]
            if high_score:
                additions.append(
                    "WHAT WORKED IN SIMILAR SITUATIONS:\n" +
                    "\n".join([f"- {e['insight']}" for e in high_score[:2]])
                )
        if knowledge["failure_cases"]:
            additions.append(
                "WATCH OUT FOR:\n" +
                "\n".join([f"- {e['root_cause']}: {e['correction']}"
                           for e in knowledge["failure_cases"][:2]])
            )

        if not additions:
            return base_system_prompt
        return (base_system_prompt +
                "\n\n--- ACCUMULATED KNOWLEDGE ---\n" +
                "\n\n".join(additions))

    def get_growth_summary(self) -> dict:
        """How much has this agent grown?"""
        counts = {}
        total = 0
        for c in ["domain_expertise", "strategic_frameworks",
                   "interaction_learnings", "failure_cases"]:
            n = len(self._read_all(f"{c}.jsonl"))
            counts[f"{c}_count"] = n
            total += n
        return {"agent_id": self.agent_id, **counts,
                "total_knowledge_entries": total}

    def _append(self, filename: str, entry: dict) -> None:
        path = self.base_path / filename
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _read_all(self, filename: str) -> list:
        path = self.base_path / filename
        if not path.exists() or path.stat().st_size == 0:
            return []
        return [json.loads(l) for l in
                path.read_text(encoding="utf-8").strip().splitlines()
                if l.strip()]

    def _log_growth(self, growth_type: str, detail: str) -> None:
        self._append("growth_log.jsonl", {
            "growth_type": growth_type,
            "detail": detail[:200],
            "logged_at": datetime.now(timezone.utc).isoformat(),
        })


class AgentKnowledgeEvolution:
    """
    The system that grows every agent's knowledge base.
    Triggered by outcome events and weekly EVL1 synthesis.
    """

    AGENT_REGISTRY = [
        "an1_analyst", "a1_architect", "ttlg_diagnostic",
        "m1_marshall", "consumer_journey", "v1_validation",
        "r1_radar", "echoes_research",
    ]

    def seed_initial_knowledge(self) -> None:
        """Seed each agent with foundational domain knowledge."""
        seed_topics = {
            "an1_analyst": [
                ("ERI prediction accuracy",
                 "Hook type accounts for 35% of ERI variance, competitive density inverse 25%, posting velocity 20%, thumbnail quality 20%. List hooks outperform question hooks in affiliate niches by 18%.",
                 "content_lab_constitution"),
                ("ERI failure modes",
                 "ERI predictions fail when: new hook format lacks historical data, platform algorithm shifts mid-campaign, competitive density spikes from viral competitor. Flag for human calibration.",
                 "failure_analysis"),
            ],
            "a1_architect": [
                ("Triple-Threat scripting",
                 "Every topic has three angles: Challenger disrupts beliefs, Architect reveals structural logic, Closer drives action. Best scripts serve one angle completely. Mixing reduces conversion by 23%.",
                 "content_lab_constitution"),
                ("Hook mechanics",
                 "First 3 seconds determine 60% of watch time. Hook must create knowledge gap. Questions create weak gaps. Surprising statements create strong gaps. Demonstrations create strongest gaps.",
                 "platform_intelligence"),
            ],
            "ttlg_diagnostic": [
                ("Agency diagnostic pattern",
                 "Agencies suffer three simultaneous bottlenecks: delivery capacity, production speed, BI blindness. Highest-leverage fix: Content Lab + FOTW combination addresses all three.",
                 "niche_intelligence_agency"),
                ("Resistance pattern",
                 "Businesses with existing automation resist diagnosis. Don't challenge the stack — audit what falls between tools: unmeasured handoffs where data disappears and decisions become opinions.",
                 "client_interaction_learnings"),
            ],
            "consumer_journey": [
                ("Conversion timing",
                 "Leads convert at intersection of: just experienced failure with current approach, seen evidence alternative works, path to alternative is short and clear. Journey creates all three sequentially.",
                 "journey_map_v3"),
                ("Trust mechanics",
                 "Trust builds through consistency (same voice every time), specificity (details only experts know), proof (verifiable outcomes). Generic content destroys trust faster than no content.",
                 "consumer_psychology"),
            ],
        }

        for agent_id, topics in seed_topics.items():
            kb = AgentKnowledgeBase(agent_id)
            for topic, expertise, source in topics:
                kb.add_domain_expertise(topic, expertise, source)
            print(f"  Seeded: {agent_id} -- {len(topics)} knowledge entries")

    def process_outcome_event(self, event_type: str,
                               event_payload: dict) -> None:
        """Route an outcome event to relevant agents' knowledge bases."""
        if event_type == "content.eri_actual":
            self._learn_from_eri_outcome(event_payload)
        elif event_type == "governance.validation.fail":
            self._learn_from_validation_failure(event_payload)
        elif event_type == "crm.lead.converted":
            self._learn_from_conversion(event_payload)

    def _learn_from_eri_outcome(self, payload: dict) -> None:
        """When ERI actual comes in, AN1 and A1 both learn."""
        an1_kb = AgentKnowledgeBase("an1_analyst")
        a1_kb = AgentKnowledgeBase("a1_architect")

        eri_actual = payload.get("eri_actual", 0)
        eri_predicted = payload.get("eri_predicted", 0)
        hook_type = payload.get("hook_type", "unknown")
        angle_type = payload.get("angle_type", "unknown")
        niche_id = payload.get("niche_id", "unknown")

        delta = eri_actual - eri_predicted
        outcome_score = max(0, 1.0 - (abs(delta) / max(eri_predicted, 1)))

        an1_kb.record_interaction_learning(
            situation=f"ERI prediction for {hook_type} hook in {niche_id}",
            action_taken=f"Predicted {eri_predicted:.1f}",
            outcome=f"Actual {eri_actual:.1f} (delta {delta:+.1f})",
            insight=(f"{hook_type} hooks in {niche_id} "
                     f"{'outperformed' if delta > 0 else 'underperformed'} "
                     f"predictions by {abs(delta):.1f} points"),
            outcome_score=outcome_score,
        )

        if eri_actual > 60:
            a1_kb.record_interaction_learning(
                situation=f"Script production for {niche_id}",
                action_taken=f"Used {angle_type} angle with {hook_type} hook",
                outcome=f"ERI {eri_actual:.1f} -- strong performance",
                insight=(f"{angle_type} angle with {hook_type} hook "
                         f"delivers strong ERI ({eri_actual:.1f}) in {niche_id}"),
                outcome_score=min(eri_actual / 100, 1.0),
            )
        elif eri_actual < 35:
            a1_kb.record_failure_case(
                situation=f"Script production for {niche_id}",
                action_taken=f"Used {angle_type} angle with {hook_type} hook",
                what_went_wrong=f"ERI {eri_actual:.1f} -- below break-even",
                root_cause=f"{angle_type}/{hook_type} underperforms in {niche_id}",
                correction=f"Reduce {angle_type}/{hook_type} allocation. Test alternatives.",
            )

    def _learn_from_validation_failure(self, payload: dict) -> None:
        """When V1 validation fails, V1 and A1 both learn."""
        v1_kb = AgentKnowledgeBase("v1_validation")
        a1_kb = AgentKnowledgeBase("a1_architect")

        for check in payload.get("failed_checks", []):
            excerpt = payload.get("script_excerpt", "")[:100]
            v1_kb.record_interaction_learning(
                situation="Script validation",
                action_taken=f"Ran {check} check", outcome="FAIL",
                insight=f"{check} failures cluster around: {excerpt}",
                outcome_score=0.0,
            )
            a1_kb.record_failure_case(
                situation="Script production",
                action_taken="Generated script",
                what_went_wrong=f"Failed {check} validation",
                root_cause=f"Script triggered {check} violation",
                correction=f"Review {check} rules before generating in this style",
            )

    def _learn_from_conversion(self, payload: dict) -> None:
        """When a lead converts, consumer_journey learns the sequence."""
        journey_kb = AgentKnowledgeBase("consumer_journey")
        segment = payload.get("segment_id", "unknown")
        touchpoints = payload.get("touchpoint_sequence", [])
        days = payload.get("days_to_convert", 0)
        tier = payload.get("tier", "unknown")

        journey_kb.record_interaction_learning(
            situation=f"Lead conversion -- {segment} segment",
            action_taken=f"Journey: {' -> '.join(touchpoints[-5:])}",
            outcome=f"Converted to {tier} in {days} days",
            insight=(f"{segment} leads convert via "
                     f"{'short' if days < 7 else 'long'} journeys. "
                     f"Key touchpoints: {', '.join(touchpoints[-3:])}"),
            outcome_score=1.0,
        )

    def run_weekly_knowledge_synthesis(self) -> dict:
        """Called by EVL1 weekly. Reviews learnings, synthesizes patterns."""
        from groq_router import GroqRouter
        router = GroqRouter()

        report = {
            "synthesized_at": datetime.now(timezone.utc).isoformat(),
            "agents_reviewed": [],
            "frameworks_added": 0,
        }

        for agent_id in self.AGENT_REGISTRY:
            kb = AgentKnowledgeBase(agent_id)
            summary = kb.get_growth_summary()
            report["agents_reviewed"].append(summary)

            recent = [l for l in kb._read_all("interaction_learnings.jsonl")
                      if l.get("recorded_at", "") > datetime.now(timezone.utc).isoformat()[:10]]

            if len(recent) >= 3:
                prompt = (
                    f"Analyze these {agent_id} learnings. "
                    f"Return JSON: {{\"framework_name\":\"\",\"framework_description\":\"\","
                    f"\"when_to_apply\":\"\"}}\n\n"
                    f"{json.dumps(recent[:10], indent=2)[:2000]}"
                )
                try:
                    raw = router.route("reasoning", prompt, max_tokens=500, temperature=0.3)
                    # Extract JSON from response
                    start = raw.find("{")
                    end = raw.rfind("}") + 1
                    if start >= 0 and end > start:
                        framework = json.loads(raw[start:end])
                        kb.add_strategic_framework(
                            framework_name=framework["framework_name"],
                            description=framework["framework_description"],
                            when_to_apply=framework["when_to_apply"],
                            source="evl1_weekly_synthesis",
                        )
                        report["frameworks_added"] += 1
                except Exception:
                    pass

        record_decision(
            decision_type="agent_knowledge.weekly_synthesis",
            description=f"Weekly synthesis: {report['frameworks_added']} frameworks added",
            agent_id="agent_knowledge_evolution",
            outcome="complete", context=report,
        )
        return report


if __name__ == "__main__":
    evolution = AgentKnowledgeEvolution()

    # Test 1: Seed initial knowledge
    print("  Seeding initial knowledge bases...")
    evolution.seed_initial_knowledge()

    # Test 2: Record ERI outcome — verify agents learn
    print("  Testing ERI outcome learning...")
    evolution.process_outcome_event("content.eri_actual", {
        "brief_id": "CB-LEGO-001", "eri_actual": 72.0,
        "eri_predicted": 58.0, "hook_type": "list",
        "angle_type": "architect", "niche_id": "lego_affiliate",
    })
    an1_kb = AgentKnowledgeBase("an1_analyst")
    learnings = an1_kb._read_all("interaction_learnings.jsonl")
    assert len(learnings) >= 1
    print(f"  AN1 learnings: {len(learnings)} entries")

    # Test 3: Build enriched prompt
    a1_kb = AgentKnowledgeBase("a1_architect")
    base_prompt = "You are A1 Architect. Write a script."
    enriched = a1_kb.build_enriched_prompt(
        base_prompt, "Writing a LEGO affiliate script with list hook")
    print(f"  Enriched prompt: {len(enriched)} chars (was {len(base_prompt)})")
    assert len(enriched) > len(base_prompt)

    # Test 4: Growth summary
    summary = an1_kb.get_growth_summary()
    assert summary["total_knowledge_entries"] >= 1
    print(f"  AN1 growth: {summary['total_knowledge_entries']} total entries")

    # Test 5: A1 growth
    a1_summary = a1_kb.get_growth_summary()
    print(f"  A1 growth: {a1_summary['total_knowledge_entries']} total entries")

    print("\nPASS: AgentKnowledgeEvolution -- agents are growing")
    print("Every interaction makes every agent better.")
