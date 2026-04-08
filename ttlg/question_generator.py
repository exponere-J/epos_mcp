#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
question_generator.py — TTLG Dynamic Question Generator (Mission 2)
=====================================================================
Constitutional Authority: EPOS Constitution v3.1

Generates phase-specific diagnostic questions from TTLGProps.
Replaces hardcoded questions with domain-aware, scope-driven generation.
Backward compatible: when no props loaded, returns default question set.
"""

import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ttlg.props.schema import TTLGProps


# ── Scope-to-Question Templates ─────────────────────────────

SCOUT_TEMPLATES = {
    # Business tracks
    "marketing": {
        "quick": [
            "What is your primary customer acquisition channel?",
            "How much of your content production is systematized vs manual?",
        ],
        "standard": [
            "What is your primary customer acquisition channel?",
            "How much of your content production is systematized vs manual?",
            "If your top marketing person quit tomorrow, would content production stop?",
        ],
        "detailed": [
            "What is your primary customer acquisition channel and what is its cost per acquisition?",
            "How much of your content production is systematized vs manual?",
            "If your top marketing person quit tomorrow, would content production stop?",
            "What percentage of your content gets repurposed across multiple platforms?",
            "How do you measure content ROI beyond vanity metrics?",
        ],
    },
    "sales": {
        "quick": [
            "Walk me through what happens when someone expresses interest in working with you.",
            "What is your close rate on qualified conversations?",
        ],
        "standard": [
            "Walk me through what happens when someone expresses interest in working with you.",
            "How do you know which leads are worth your time vs just browsing?",
            "What is your close rate on qualified conversations?",
        ],
        "detailed": [
            "Walk me through what happens when someone expresses interest in working with you.",
            "How do you know which leads are worth your time vs just browsing?",
            "What is your close rate on qualified conversations?",
            "How long is your average sales cycle from first touch to signed contract?",
            "Do you have documented objection handling for your top 5 objections?",
        ],
    },
    "service": {
        "quick": [
            "After a client signs, what does the first 30 days look like?",
            "What is your biggest operational bottleneck right now?",
        ],
        "standard": [
            "After a client signs, what does the first 30 days look like?",
            "How do you measure whether a client is getting value from your work?",
            "What is your biggest operational bottleneck right now?",
        ],
        "detailed": [
            "After a client signs, what does the first 30 days look like?",
            "How do you measure whether a client is getting value from your work?",
            "What is your biggest operational bottleneck right now?",
            "How do you handle client escalations and what is your average resolution time?",
            "What percentage of clients renew or expand their engagement?",
        ],
    },
    "governance": {
        "quick": [
            "If you had to hand operations to someone for a month, how long would handoff take?",
            "What happens when something breaks at 2am?",
        ],
        "standard": [
            "If you had to hand operations to someone for a month, how long would handoff take?",
            "Where does your critical business data live? One place or scattered?",
            "What happens when something breaks at 2am — is there a process, or is it you?",
        ],
        "detailed": [
            "If you had to hand operations to someone for a month, how long would handoff take?",
            "Where does your critical business data live? One place or scattered?",
            "What happens when something breaks at 2am — is there a process, or is it you?",
            "How many critical processes exist only in one person's head?",
            "When was the last time you audited your tool stack for redundancy?",
        ],
    },
    # EPOS internal tracks
    "intelligence": {
        "standard": [
            "How many intelligence nodes are at 100% sovereignty?",
            "What is the CCP parse accuracy on the last 10 sessions?",
            "Are FOTW expressions being routed to all downstream consumers?",
        ],
    },
    "communication": {
        "standard": [
            "What is the event bus throughput over the last 24 hours?",
            "Are all nodes publishing events as expected?",
            "How many orphaned events exist (published but not consumed)?",
        ],
    },
    "memory": {
        "standard": [
            "What is the Context Vault size and growth rate?",
            "Are all JSONL journals being written to within their freshness window?",
            "How many vault paths are missing or empty?",
        ],
    },
    "orchestration": {
        "standard": [
            "Is Friday responding to steward signals within SLA?",
            "How many pending signals are in the queue?",
            "Are daily anchors being executed consistently?",
        ],
    },
    "diagnostic": {
        "standard": [
            "What is the average TTLG diagnostic completion rate?",
            "How many conversational sessions are in progress vs complete?",
            "Is the cost heuristic database current?",
        ],
    },
    "research": {
        "standard": [
            "How many research briefs were generated this week?",
            "What is the RS1 brief generation success rate?",
            "How many unconverted sparks are sitting in the vault?",
        ],
    },
    "content": {
        "standard": [
            "How many scripts were generated vs published this week?",
            "What is the spark-to-brief conversion rate?",
            "Are all multimodal providers responsive?",
        ],
    },
    "execution": {
        "standard": [
            "How many Paperclip missions were executed this week?",
            "What is the mission success rate?",
            "Are there any unresolved Tier 2 escalations?",
        ],
    },
    "financial": {
        "standard": [
            "What is total revenue this period?",
            "How many invoices are overdue?",
            "Is the payment gateway operational?",
        ],
    },
    "interface": {
        "standard": [
            "How many CLI domains are operational?",
            "Is the dashboard engine returning current data?",
            "How many unique commands were executed today?",
        ],
    },
    # Competitive tracks
    "product_capabilities": {
        "standard": [
            "What core features does the competitor offer that we don't?",
            "Where do we have feature parity or superiority?",
            "What is their product release velocity?",
        ],
    },
    "pricing_model": {
        "standard": [
            "What is the competitor's pricing structure?",
            "How does their per-seat/per-unit cost compare to ours?",
            "Do they offer a free tier or trial?",
        ],
    },
    "market_reach": {
        "standard": [
            "What is their estimated market share in our target segments?",
            "Which geographic or vertical markets do they dominate?",
            "What is their content publishing velocity and engagement?",
        ],
    },
    "technology_stack": {
        "standard": [
            "What technology infrastructure does the competitor use?",
            "Do they have any proprietary technology moats?",
            "How dependent are they on third-party APIs?",
        ],
    },
    "customer_experience": {
        "standard": [
            "What do customer reviews say about their strengths?",
            "What are the top complaints in their reviews?",
            "What is their average customer tenure?",
        ],
    },
    # Market signals
    "competitive_landscape": {
        "standard": [
            "Which competitors have made moves in the last 14 days?",
            "Have any new entrants appeared in our market segment?",
            "Which competitor weaknesses have become exploitable?",
        ],
    },
    "market_signals": {
        "standard": [
            "What technology releases in the last 14 days affect our positioning?",
            "Have any regulatory changes occurred that create opportunities?",
            "What customer sentiment shifts have been detected?",
        ],
    },
}

# ── Thinker Question Templates ──────────────────────────────

THINKER_TEMPLATES = {
    "market_forward": [
        "Which of these findings represent defensible competitive moats?",
        "Where has the market moved that the target has not followed?",
        "What thought leadership angles emerge from these gaps?",
        "Which gaps have the highest revenue potential if closed?",
        "What is the 90-day window of opportunity before competitors catch up?",
    ],
    "internal_health": [
        "Which findings indicate production blockers that reduce output?",
        "Where is the support burden highest relative to value delivered?",
        "What technical debt is accumulating and what is its compounding cost?",
        "Which processes depend on a single person and what is the bus factor risk?",
        "Where is revenue leaking due to operational inefficiency?",
    ],
    "competitive": [
        "Which advantages are truly defensible vs easily copied?",
        "What competitor blind spots can be exploited in the next 90 days?",
        "Where is the target most vulnerable to competitive disruption?",
        "What positioning statement accurately captures the differentiation?",
        "Which competitive dimensions should be de-emphasized vs amplified?",
    ],
}


class TTLGQuestionGenerator:
    """
    Generates phase-specific diagnostic questions from TTLGProps.
    Domain-aware, scope-driven, depth-configurable.
    """

    def __init__(self, props: TTLGProps = None):
        self.props = props or TTLGProps()

    def generate_scout_questions(self) -> dict:
        """Generate scout questions based on props scope and depth."""
        depth = self.props.phases.scout.depth
        questions = {}

        for scope_item in self.props.phases.scout.scope:
            templates = SCOUT_TEMPLATES.get(scope_item, {})
            # Try requested depth, fall back to standard, then quick
            q_list = templates.get(depth) or templates.get("standard") or templates.get("quick")
            if q_list:
                questions[scope_item] = q_list
            else:
                # Generic fallback for unknown scope items
                questions[scope_item] = [
                    f"What is the current state of {scope_item.replace('_', ' ')}?",
                    f"What are the top 3 challenges in {scope_item.replace('_', ' ')}?",
                    f"Where is {scope_item.replace('_', ' ')} relative to industry benchmarks?",
                ]

        return questions

    def generate_thinker_questions(self) -> list:
        """Generate thinker analysis questions based on weighting model."""
        model = self.props.phases.thinker.weighting_model
        return THINKER_TEMPLATES.get(model, THINKER_TEMPLATES["market_forward"])

    def generate_full_questionnaire(self) -> dict:
        """Generate complete questionnaire for all phases."""
        scout = self.generate_scout_questions()
        thinker = self.generate_thinker_questions()

        total_scout = sum(len(qs) for qs in scout.values())

        return {
            "props_name": self.props.name,
            "target": self.props.target,
            "depth": self.props.phases.scout.depth,
            "weighting_model": self.props.phases.thinker.weighting_model,
            "scout_questions": scout,
            "scout_question_count": total_scout,
            "thinker_questions": thinker,
            "thinker_question_count": len(thinker),
            "total_questions": total_scout + len(thinker),
        }


# ── Self-Test ───────────────────────────────────────────────

if __name__ == "__main__":
    from ttlg.props.schema import load_props

    passed = 0

    # Test 1: Default props generate questions
    gen = TTLGQuestionGenerator()
    q = gen.generate_full_questionnaire()
    assert q["total_questions"] > 0
    print(f"Default: {q['total_questions']} questions across {len(q['scout_questions'])} scopes")
    passed += 1

    # Test 2: Ecosystem architecture props
    eco_props = load_props("ecosystem_architecture")
    gen2 = TTLGQuestionGenerator(eco_props)
    q2 = gen2.generate_full_questionnaire()
    assert q2["total_questions"] > q["total_questions"], "Ecosystem should have more questions (12 scopes)"
    assert "intelligence" in q2["scout_questions"]
    assert "execution" in q2["scout_questions"]
    print(f"Ecosystem: {q2['total_questions']} questions across {len(q2['scout_questions'])} scopes")
    passed += 1

    # Test 3: Client ecosystem props
    client_props = load_props("client_ecosystem")
    gen3 = TTLGQuestionGenerator(client_props)
    q3 = gen3.generate_full_questionnaire()
    assert q3["weighting_model"] == "internal_health"
    assert "marketing" in q3["scout_questions"]
    print(f"Client: {q3['total_questions']} questions, weighting={q3['weighting_model']}")
    passed += 1

    # Test 4: Competitive props produce different thinker questions
    comp_props = load_props("competitive_positioning")
    gen4 = TTLGQuestionGenerator(comp_props)
    q4 = gen4.generate_full_questionnaire()
    assert q4["thinker_questions"] != q3["thinker_questions"], "Different models should produce different questions"
    print(f"Competitive: {q4['total_questions']} questions, weighting={q4['weighting_model']}")
    passed += 1

    # Test 5: Unknown scope item gets generic fallback
    custom = TTLGProps(phases={"scout": {"scope": ["quantum_computing"]}})
    gen5 = TTLGQuestionGenerator(custom)
    q5 = gen5.generate_scout_questions()
    assert "quantum_computing" in q5
    assert len(q5["quantum_computing"]) >= 2
    print(f"Unknown scope fallback: {len(q5['quantum_computing'])} generic questions")
    passed += 1

    print(f"\nPASS: question_generator ({passed} assertions)")
