from dataclasses import dataclass

@dataclass
class Intent:
    category: str
    confidence: float
    notes: str

def analyze_intent(task: str, extra_context: str = "") -> Intent:
    """
    Minimal deterministic intent analyzer.
    Expand later with Phi-3 / Phi-4 collaboration.
    """
    task_lower = task.lower()

    if any(k in task_lower for k in ["create", "add", "scaffold", "generate"]):
        category = "code_creation"
    elif any(k in task_lower for k in ["fix", "bug", "error", "crash"]):
        category = "bug_fix"
    elif any(k in task_lower for k in ["refactor", "cleanup", "optimize"]):
        category = "refactor"
    elif any(k in task_lower for k in ["test", "validate", "check"]):
        category = "testing"
    else:
        category = "general_engineering"

    return Intent(
        category=category,
        confidence=0.85,
        notes="Rule-based intent classification (v1)."
    )
