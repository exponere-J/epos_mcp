#!/usr/bin/env python3
"""
roles.py — EPOS Agent Role Definitions
========================================
Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X
Mission ID: EPOS Core Heal — Module 3 of 9
File Location: C:/Users/Jamie/workspace/epos_mcp/roles.py

Single responsibility: Define all agent roles, capabilities, and constraints
as structured data. No business logic — this is a registry.

Other modules import from here to know what agents exist, what they can do,
and what constitutional boundaries apply to each.

Dependencies: path_utils (Module 1)
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Any
from pathlib import Path

from path_utils import get_epos_root


# ── Enums ────────────────────────────────────────────────────────

class AgentId(str, Enum):
    """Canonical agent identifiers used across all EPOS modules."""
    ALPHA = "alpha"          # Constitutional Arbiter
    SIGMA = "sigma"          # Context Librarian
    OMEGA = "omega"          # Flywheel Analyst
    ORCHESTRATOR = "orchestrator"  # Agent Orchestrator
    BRIDGE = "bridge"        # Agent Zero Bridge
    FRIDAY = "friday"        # Friday UI / CLI
    CLAUDE_CODE = "claude_code"  # Claude Code (external)
    TTLG = "ttlg"            # Talk To the Looking Glass


class Capability(str, Enum):
    """Actions an agent is permitted to perform."""
    READ_VAULT = "read_vault"
    WRITE_VAULT = "write_vault"
    READ_ENGINE = "read_engine"
    WRITE_ENGINE = "write_engine"
    EXECUTE_MISSION = "execute_mission"
    GOVERNANCE_AUDIT = "governance_audit"
    GOVERNANCE_ENFORCE = "governance_enforce"
    BI_READ = "bi_read"
    BI_WRITE = "bi_write"
    PROPOSE_AMENDMENT = "propose_amendment"
    MANAGE_AGENTS = "manage_agents"
    EXTERNAL_API = "external_api"
    FILE_SYSTEM = "file_system"


class ConstitutionalBoundary(str, Enum):
    """Hard limits that agents cannot cross."""
    NO_WRITE_OUTSIDE_EPOS = "no_write_outside_epos_root"
    NO_DELETE_ENGINE = "no_delete_engine_files"
    NO_BYPASS_GATE = "no_bypass_governance_gate"
    NO_DIRECT_DB_WRITE = "no_direct_db_write_without_receipt"
    NO_UNLOGGED_DECISION = "no_unlogged_bi_decision"
    REQUIRE_STASIS_CHECK = "require_stasis_before_mission"


# ── Role Definition ──────────────────────────────────────────────

@dataclass(frozen=True)
class AgentRole:
    """
    Immutable definition of an agent's identity, purpose, and constraints.

    This is a data class, not a runtime actor. Agents import their role
    to know what they are allowed to do. The orchestrator uses this
    registry to validate mission assignments.
    """
    agent_id: AgentId
    name: str
    codename: str
    description: str
    constitutional_articles: List[str]
    capabilities: List[Capability]
    boundaries: List[ConstitutionalBoundary]
    log_dir_name: str
    monetization: Optional[str] = None
    depends_on: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for JSON logging and BI."""
        d = asdict(self)
        d["agent_id"] = self.agent_id.value
        d["capabilities"] = [c.value for c in self.capabilities]
        d["boundaries"] = [b.value for b in self.boundaries]
        return d

    @property
    def log_dir(self) -> Path:
        """Absolute path to this agent's log directory."""
        return get_epos_root() / "ops" / "logs" / self.log_dir_name


# ── Role Registry ────────────────────────────────────────────────

ROLE_ALPHA = AgentRole(
    agent_id=AgentId.ALPHA,
    name="Constitutional Arbiter",
    codename="Alpha",
    description="Enforces EPOS Constitution on all code changes. "
                "Pre-flight PR scans, merge gate, sprint boundary audits.",
    constitutional_articles=["II", "III", "IV", "XIV"],
    capabilities=[
        Capability.GOVERNANCE_AUDIT,
        Capability.GOVERNANCE_ENFORCE,
        Capability.READ_ENGINE,
        Capability.READ_VAULT,
        Capability.BI_WRITE,
    ],
    boundaries=[
        ConstitutionalBoundary.NO_WRITE_OUTSIDE_EPOS,
        ConstitutionalBoundary.NO_UNLOGGED_DECISION,
    ],
    log_dir_name="arbiter",
    monetization="$297/mo per repository (Governance-as-a-Service)",
)

ROLE_SIGMA = AgentRole(
    agent_id=AgentId.SIGMA,
    name="Context Librarian",
    codename="Sigma",
    description="Custodian of Context Vault. Ingests large artifacts, "
                "maintains symbolic search indices, never dumps raw content.",
    constitutional_articles=["VII"],
    capabilities=[
        Capability.READ_VAULT,
        Capability.WRITE_VAULT,
        Capability.BI_WRITE,
    ],
    boundaries=[
        ConstitutionalBoundary.NO_WRITE_OUTSIDE_EPOS,
        ConstitutionalBoundary.NO_DELETE_ENGINE,
    ],
    log_dir_name="librarian",
    monetization="$497/mo (Enterprise Data Sovereignty Engine)",
)

ROLE_OMEGA = AgentRole(
    agent_id=AgentId.OMEGA,
    name="Flywheel Analyst",
    codename="Omega",
    description="Turns BI logs into strategic intelligence. Detects failure "
                "patterns, tracks 4 flywheel metrics, proposes amendments.",
    constitutional_articles=["VIII"],
    capabilities=[
        Capability.BI_READ,
        Capability.BI_WRITE,
        Capability.READ_VAULT,
        Capability.PROPOSE_AMENDMENT,
    ],
    boundaries=[
        ConstitutionalBoundary.NO_WRITE_OUTSIDE_EPOS,
        ConstitutionalBoundary.NO_DELETE_ENGINE,
        ConstitutionalBoundary.NO_BYPASS_GATE,
    ],
    log_dir_name="analyst",
    monetization="$149/mo (Governance-aware BI Dashboard)",
)

ROLE_ORCHESTRATOR = AgentRole(
    agent_id=AgentId.ORCHESTRATOR,
    name="Agent Orchestrator",
    codename="Conductor",
    description="Coordinates governance agents and integrates with Agent Zero. "
                "Routes missions, validates assignments, tracks execution.",
    constitutional_articles=["V", "X"],
    capabilities=[
        Capability.MANAGE_AGENTS,
        Capability.EXECUTE_MISSION,
        Capability.READ_VAULT,
        Capability.BI_WRITE,
    ],
    boundaries=[
        ConstitutionalBoundary.REQUIRE_STASIS_CHECK,
        ConstitutionalBoundary.NO_UNLOGGED_DECISION,
    ],
    log_dir_name="orchestrator",
    depends_on=["alpha", "sigma", "omega"],
)

ROLE_BRIDGE = AgentRole(
    agent_id=AgentId.BRIDGE,
    name="Agent Zero Bridge",
    codename="Bridge",
    description="Mission execution interface to Agent Zero. Translates EPOS "
                "mission briefs into AZ-compatible prompts and monitors execution.",
    constitutional_articles=["II", "III", "VII", "X"],
    capabilities=[
        Capability.EXECUTE_MISSION,
        Capability.FILE_SYSTEM,
        Capability.EXTERNAL_API,
        Capability.BI_WRITE,
    ],
    boundaries=[
        ConstitutionalBoundary.REQUIRE_STASIS_CHECK,
        ConstitutionalBoundary.NO_UNLOGGED_DECISION,
        ConstitutionalBoundary.NO_DIRECT_DB_WRITE,
    ],
    log_dir_name="bridge",
    depends_on=["orchestrator"],
)

ROLE_FRIDAY = AgentRole(
    agent_id=AgentId.FRIDAY,
    name="Friday",
    codename="Friday",
    description="User-facing orchestration layer. Streamlit UI and CLI for "
                "mission briefing, status monitoring, and REPL interaction.",
    constitutional_articles=["V", "VII"],
    capabilities=[
        Capability.READ_VAULT,
        Capability.EXECUTE_MISSION,
        Capability.EXTERNAL_API,
    ],
    boundaries=[
        ConstitutionalBoundary.NO_WRITE_OUTSIDE_EPOS,
        ConstitutionalBoundary.NO_DELETE_ENGINE,
        ConstitutionalBoundary.NO_BYPASS_GATE,
    ],
    log_dir_name="friday",
)

ROLE_TTLG = AgentRole(
    agent_id=AgentId.TTLG,
    name="Talk To the Looking Glass",
    codename="TTLG",
    description="Six-phase diagnostic pipeline. Scans codebase health, "
                "alignment, and generates strategic recommendations.",
    constitutional_articles=["V", "VI", "VIII"],
    capabilities=[
        Capability.READ_ENGINE,
        Capability.READ_VAULT,
        Capability.BI_READ,
        Capability.BI_WRITE,
        Capability.GOVERNANCE_AUDIT,
    ],
    boundaries=[
        ConstitutionalBoundary.NO_WRITE_OUTSIDE_EPOS,
        ConstitutionalBoundary.NO_DELETE_ENGINE,
    ],
    log_dir_name="ttlg",
)


# ── Registry Access ──────────────────────────────────────────────

ROLES: Dict[AgentId, AgentRole] = {
    AgentId.ALPHA: ROLE_ALPHA,
    AgentId.SIGMA: ROLE_SIGMA,
    AgentId.OMEGA: ROLE_OMEGA,
    AgentId.ORCHESTRATOR: ROLE_ORCHESTRATOR,
    AgentId.BRIDGE: ROLE_BRIDGE,
    AgentId.FRIDAY: ROLE_FRIDAY,
    AgentId.TTLG: ROLE_TTLG,
}


def get_role(agent_id: str) -> AgentRole:
    """
    Look up an agent role by string ID.

    Args:
        agent_id: String like "alpha", "sigma", "omega", etc.

    Returns:
        AgentRole for the given agent.

    Raises:
        KeyError: If agent_id is not registered.
    """
    try:
        key = AgentId(agent_id)
    except ValueError:
        raise KeyError(
            f"Unknown agent '{agent_id}'. "
            f"Valid agents: {', '.join(a.value for a in AgentId)}"
        )
    return ROLES[key]


def get_all_roles() -> Dict[str, AgentRole]:
    """Return all roles keyed by string ID."""
    return {k.value: v for k, v in ROLES.items()}


def get_agents_with_capability(capability: Capability) -> List[AgentRole]:
    """Find all agents that have a specific capability."""
    return [role for role in ROLES.values() if capability in role.capabilities]


def validate_assignment(agent_id: str, capability: str) -> bool:
    """
    Check if an agent is permitted to perform an action.

    Args:
        agent_id: Agent string ID
        capability: Capability string value

    Returns:
        True if the agent has this capability, False otherwise.
    """
    try:
        role = get_role(agent_id)
        cap = Capability(capability)
        return cap in role.capabilities
    except (KeyError, ValueError):
        return False


# ── Self-test ────────────────────────────────────────────────────

if __name__ == "__main__":
    print("EPOS Agent Role Registry")
    print("=" * 60)

    for agent_id, role in ROLES.items():
        print(f"\n  [{role.codename}] {role.name}")
        print(f"    ID: {agent_id.value}")
        print(f"    Articles: {', '.join(role.constitutional_articles)}")
        print(f"    Capabilities: {len(role.capabilities)}")
        print(f"    Boundaries: {len(role.boundaries)}")
        if role.monetization:
            print(f"    Monetization: {role.monetization}")
        if role.depends_on:
            print(f"    Depends on: {', '.join(role.depends_on)}")

    print(f"\n  Total agents: {len(ROLES)}")
    print(f"  Total capabilities defined: {len(Capability)}")
    print(f"  Total boundaries defined: {len(ConstitutionalBoundary)}")

    # Validate
    assert get_role("alpha").name == "Constitutional Arbiter"
    assert validate_assignment("alpha", "governance_audit") is True
    assert validate_assignment("sigma", "governance_enforce") is False
    assert len(get_agents_with_capability(Capability.BI_WRITE)) >= 3

    print("\n  All assertions passed.")
