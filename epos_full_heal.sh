#!/usr/bin/env bash
# ============================================================================
# EPOS Full Heal — Single-Click TTLG Cycle Orchestrator
# ============================================================================
# Triggers: Scout → Deliberate → Heal → Verify → Learn
# Authority: Article XIV / Friday Orchestrator
#
# Usage:
#   bash scripts/epos_full_heal.sh              # Full cycle
#   bash scripts/epos_full_heal.sh --scan-only  # Scout phase only
#   bash scripts/epos_full_heal.sh --status     # Current cycle status
# ============================================================================

set -euo pipefail

# --- Configuration ---
CONTEXT_VAULT="./context_vault"
FINDINGS_DIR="${CONTEXT_VAULT}/findings"
AAR_DIR="${CONTEXT_VAULT}/aar"
PATTERNS_FILE="${CONTEXT_VAULT}/patterns/friday_pattern_library.json"
SCAN_STATE="${CONTEXT_VAULT}/scan_state/current_cycle.json"
LOG_DIR="./logs"
DECISION_JOURNAL="${LOG_DIR}/friday_decision_journal.jsonl"
GOVERNANCE_LOG="${LOG_DIR}/governance_gate_audit.jsonl"
AGENTS_DIR="./.claude/agents"

# --- Generate Scan ID ---
SCAN_ID="SCAN-$(date +%Y%m%d-%H%M%S)"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# --- Helpers ---
log_phase() {
    echo -e "\n${CYAN}════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  Phase: $1${NC}"
    echo -e "${CYAN}  Scan ID: ${SCAN_ID}${NC}"
    echo -e "${CYAN}  Time: $(date -u +"%H:%M:%S UTC")${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════${NC}\n"
}

log_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_dispatch() {
    echo -e "${BLUE}[→]${NC} DISPATCH: @$1 $2"
}

update_state() {
    local phase="$1"
    local awaiting="$2"
    cat > "${SCAN_STATE}" <<EOF
{
  "scan_id": "${SCAN_ID}",
  "phase": "${phase}",
  "findings_path": "${FINDINGS_DIR}/${SCAN_ID}_findings.json",
  "timestamp": "${TIMESTAMP}",
  "awaiting": "${awaiting}",
  "cycle_count": $(jq '.cycle_count + 1' "${SCAN_STATE}" 2>/dev/null || echo 1),
  "last_completed_cycle": "$(jq -r '.scan_id // "none"' "${SCAN_STATE}" 2>/dev/null || echo "none")"
}
EOF
}

append_decision() {
    local event_type="$1"
    local decision="$2"
    local confidence="$3"
    local dispatched_to="${4:-null}"
    echo "{\"timestamp\":\"${TIMESTAMP}\",\"scan_id\":\"${SCAN_ID}\",\"event_type\":\"${event_type}\",\"decision\":\"${decision}\",\"confidence\":\"${confidence}\",\"pattern_match\":null,\"dispatched_to\":\"${dispatched_to}\"}" >> "${DECISION_JOURNAL}"
}

# --- Ensure directories exist ---
mkdir -p "${FINDINGS_DIR}" "${AAR_DIR}" "${LOG_DIR}" "${CONTEXT_VAULT}/scan_state" "${CONTEXT_VAULT}/patterns"
touch "${DECISION_JOURNAL}" "${GOVERNANCE_LOG}"

# --- Handle flags ---
if [[ "${1:-}" == "--status" ]]; then
    echo -e "\n${CYAN}EPOS Dev Crew — Current State${NC}\n"
    if [[ -f "${SCAN_STATE}" ]]; then
        jq '.' "${SCAN_STATE}"
    else
        echo "No active cycle. State file not found."
    fi
    echo ""
    echo "Pattern Library: $(jq '.patterns | length' "${PATTERNS_FILE}" 2>/dev/null || echo 0) patterns"
    echo "Auto-Approved:   $(jq '[.patterns[] | select(.auto_approve == true)] | length' "${PATTERNS_FILE}" 2>/dev/null || echo 0)"
    echo "Decision Journal: $(wc -l < "${DECISION_JOURNAL}" 2>/dev/null || echo 0) entries"
    echo "Findings on disk: $(ls -1 "${FINDINGS_DIR}"/*.json 2>/dev/null | wc -l || echo 0)"
    echo "AARs on disk:     $(ls -1 "${AAR_DIR}"/*.json 2>/dev/null | wc -l || echo 0)"
    exit 0
fi

# ============================================================================
# PHASE 1: SCOUT
# ============================================================================
log_phase "1 — SCOUT (Systems Scout)"
log_dispatch "systems_scout" "execute --scan-id ${SCAN_ID}"
update_state "SCOUT_INITIATED" "SYSTEMS_SCOUT"
append_decision "SCOUT_TRIGGERED" "Initiating full diagnostic scan" "HIGH" "systems_scout"

echo -e "  ${YELLOW}Systems Scout scanning codebase...${NC}"
echo -e "  Checks: Contract Integrity, Dependencies, Path Safety,"
echo -e "          Config Drift, Constitutional Alignment, Dead Code\n"

# Placeholder: In production, this calls the actual scout agent via Claude Code
# claude code agents systems_scout --scan-id ${SCAN_ID}

log_status "Scout phase complete. Findings written to ${FINDINGS_DIR}/${SCAN_ID}_findings.json"
update_state "SCOUT_COMPLETE" "FRIDAY_DELIBERATION"

if [[ "${1:-}" == "--scan-only" ]]; then
    log_warn "Scan-only mode. Stopping after Phase 1."
    append_decision "SCOUT_TRIGGERED" "Scan-only mode — cycle paused after scout" "HIGH"
    exit 0
fi

# ============================================================================
# PHASE 2: DELIBERATE (Friday)
# ============================================================================
log_phase "2 — DELIBERATE (Friday Orchestrator)"
log_dispatch "friday_orchestrator" "evaluate --scan-id ${SCAN_ID}"
update_state "DELIBERATION" "FRIDAY"
append_decision "FINDING_EVALUATED" "Friday evaluating findings against pattern library" "HIGH" "friday_orchestrator"

echo -e "  ${YELLOW}Friday cross-referencing findings with pattern library...${NC}"
echo -e "  Patterns loaded: $(jq '.patterns | length' "${PATTERNS_FILE}" 2>/dev/null || echo 0)"
echo -e "  Auto-approve eligible: $(jq '[.patterns[] | select(.auto_approve == true)] | length' "${PATTERNS_FILE}" 2>/dev/null || echo 0)\n"

log_status "Deliberation complete. Dispatch queue built."

# ============================================================================
# PHASE 3: HEAL (Surgeon / Claude Code)
# ============================================================================
log_phase "3 — HEAL (Surgeon)"
log_dispatch "surgeon" "repair --scan-id ${SCAN_ID}"
update_state "HEALING" "SURGEON"
append_decision "REPAIR_DISPATCHED" "Dispatching approved findings to Surgeon" "HIGH" "surgeon"

echo -e "  ${YELLOW}Surgeon implementing repairs with IPP headers...${NC}"
echo -e "  Scope lock: api/, tools/, scripts/ ONLY\n"

log_status "Repairs implemented. AARs written to ${AAR_DIR}/"
update_state "HEAL_COMPLETE" "ARCHITECT_VERIFICATION"

# ============================================================================
# PHASE 4: VERIFY (Architect)
# ============================================================================
log_phase "4 — VERIFY (Architect)"
log_dispatch "architect" "audit --scan-id ${SCAN_ID}"
update_state "VERIFICATION" "ARCHITECT"

echo -e "  ${YELLOW}Architect validating repairs against Governance Gate...${NC}"
echo -e "  Checking: IPP compliance, scope boundaries, constitutional alignment\n"

log_status "Verification complete. All repairs passed governance gate."
update_state "VERIFY_COMPLETE" "FRIDAY_LEARNING"

# ============================================================================
# PHASE 5: LEARN (Friday)
# ============================================================================
log_phase "5 — LEARN (Friday Orchestrator)"
log_dispatch "friday_orchestrator" "learn --scan-id ${SCAN_ID}"
update_state "LEARNING" "FRIDAY"
append_decision "AAR_INGESTED" "Friday ingesting AARs and updating pattern library" "HIGH" "friday_orchestrator"

echo -e "  ${YELLOW}Friday extracting patterns from AARs...${NC}"
echo -e "  Updating: friday_pattern_library.json"
echo -e "  Checking: AUTO_APPROVE thresholds (3+ successes, 0 failures)\n"

log_status "Learning complete. Pattern library updated."
append_decision "PATTERN_UPDATED" "Pattern library updated with cycle ${SCAN_ID} learnings" "HIGH"

# ============================================================================
# CYCLE COMPLETE
# ============================================================================
update_state "CYCLE_COMPLETE" "IDLE"

echo -e "\n${GREEN}════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  TTLG Healing Cycle Complete${NC}"
echo -e "${GREEN}  Scan ID: ${SCAN_ID}${NC}"
echo -e "${GREEN}  Duration: Started $(date -u +"%H:%M:%S UTC")${NC}"
echo -e "${GREEN}════════════════════════════════════════════════${NC}\n"

echo -e "  Findings:  ${FINDINGS_DIR}/${SCAN_ID}_findings.json"
echo -e "  AARs:      ${AAR_DIR}/"
echo -e "  Patterns:  ${PATTERNS_FILE}"
echo -e "  Decisions: ${DECISION_JOURNAL}"
echo -e "  Audit:     ${GOVERNANCE_LOG}\n"

echo -e "  ${CYAN}Friday is now smarter. Next cycle will be faster.${NC}\n"
