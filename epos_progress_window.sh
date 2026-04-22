#!/bin/bash
# EPOS PROGRESS WINDOW v1.0
# Real-time visualization of codebase build state
# Location: /mnt/c/Users/Jamie/workspace/epos_mcp/epos_progress_window.sh

set -e

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

EPOS_ROOT="${EPOS_ROOT:-.}"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# =============================================================================
# PROGRESS WINDOW HEADER
# =============================================================================

clear
cat << "EOF"
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    🏛️  EPOS CODEBASE PROGRESS WINDOW                         ║
║                   Autonomous Dev Crew Status Dashboard                       ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
EOF

echo ""
echo -e "${CYAN}[$(date '+%H:%M:%S')]${NC} Scanning codebase state..."
echo ""

# =============================================================================
# SECTION 1: CONSTITUTIONAL FRAMEWORK
# =============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}1. CONSTITUTIONAL FRAMEWORK${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

check_file() {
    local file=$1
    local label=$2
    if [ -f "$EPOS_ROOT/$file" ]; then
        echo -e "${GREEN}✅${NC} $label"
        return 0
    else
        echo -e "${RED}❌${NC} $label (MISSING: $file)"
        return 1
    fi
}

CONST_PASS=0
CONST_TOTAL=0

declare -a CONST_FILES=(
    "EPOS_CONSTITUTION_v3.1.md:Constitution v3.1"
    "ARTICLE_XIV_ENFORCEMENT.md:Article XIV Enforcement"
    "IMAGINATIVE_PROJECTION_PROTOCOL.md:IPP Protocol"
    "PATH_VALIDATION_RULES.md:Path Validation Rules"
)

for file_entry in "${CONST_FILES[@]}"; do
    file="${file_entry%:*}"
    label="${file_entry#*:}"
    ((CONST_TOTAL++))
    if check_file "$file" "$label"; then
        ((CONST_PASS++))
    fi
done

echo ""
echo -e "Constitutional Files: ${GREEN}$CONST_PASS/$CONST_TOTAL${NC}"
echo ""

# =============================================================================
# SECTION 2: GOVERNANCE GLUE LAYER
# =============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}2. GOVERNANCE GLUE LAYER (MISSING = CRITICAL)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

GLUE_PASS=0
GLUE_TOTAL=0

declare -a GLUE_FILES=(
    "docs/governance/IPP_TEMPLATE.md:IPP Submission Template"
    "docs/governance/AAR_TEMPLATE.md:After-Action Review Template"
    "docs/governance/SQUAD_COMMUNICATION_PROTOCOL.md:Squad Communication Protocol"
    "docs/governance/GOVERNANCE_GATE_CHARTER.md:Governance Gate Charter"
    "docs/governance/SCALING_PROTOCOL.md:Scaling Protocol"
)

for file_entry in "${GLUE_FILES[@]}"; do
    file="${file_entry%:*}"
    label="${file_entry#*:}"
    ((GLUE_TOTAL++))
    if check_file "$file" "$label"; then
        ((GLUE_PASS++))
    fi
done

echo ""
echo -e "Governance Glue Files: ${YELLOW}$GLUE_PASS/$GLUE_TOTAL${NC}"
if [ $GLUE_PASS -lt $GLUE_TOTAL ]; then
    echo -e "${RED}⚠️  CRITICAL: Missing governance glue files will break agent autonomy${NC}"
fi
echo ""

# =============================================================================
# SECTION 3: INFRASTRUCTURE & AGENTS
# =============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}3. INFRASTRUCTURE & AGENTS${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

INFRA_PASS=0
INFRA_TOTAL=0

declare -a INFRA_FILES=(
    "tools/governance_gate_audit.py:Governance Gate Audit (Article XIV Enforcement)"
    "tools/litellm_client.py:LiteLLM Client (Mono-Sovereign Gemini Router)"
    "api/epos_api.py:EPOS API Entrypoint"
    "friday_orchestrator/FRIDAY_ORCHESTRATION_CHARTER.md:Friday Orchestration Charter"
    "friday_orchestrator/FRIDAY_LEARNING_FRAMEWORK.md:Friday Learning Framework"
)

for file_entry in "${INFRA_FILES[@]}"; do
    file="${file_entry%:*}"
    label="${file_entry#*:}"
    ((INFRA_TOTAL++))
    if check_file "$file" "$label"; then
        ((INFRA_PASS++))
    fi
done

echo ""
echo -e "Infrastructure: ${GREEN}$INFRA_PASS/$INFRA_TOTAL${NC}"
echo ""

# =============================================================================
# SECTION 4: TTLG DIAGNOSTICS (PENDING)
# =============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}4. TTLG DIAGNOSTICS ENTRYPOINTS (PENDING GENERATION)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

TTLG_PASS=0
TTLG_TOTAL=0

declare -a TTLG_FILES=(
    "api/ttlg_systems_light_scout.py:Systems Scout (Phase 1)"
    "api/ttlg_market_light_scout.py:Market Scout (Phase 1)"
    "api/friday_vault_summary.py:Friday Vault Summary"
    "api/friday_check_ttlg_health.py:Friday TTLG Health Check"
    "scripts/ttlg_systems_light_scout.sh:Systems Scout CLI Wrapper"
    "scripts/ttlg_market_light_scout.sh:Market Scout CLI Wrapper"
    "scripts/friday_vault_summary.sh:Friday Vault Summary CLI Wrapper"
    "scripts/friday_check_ttlg_health.sh:Friday Health Check CLI Wrapper"
)

for file_entry in "${TTLG_FILES[@]}"; do
    file="${file_entry%:*}"
    label="${file_entry#*:}"
    ((TTLG_TOTAL++))
    if check_file "$file" "$label"; then
        ((TTLG_PASS++))
    fi
done

echo ""
echo -e "TTLG Entrypoints: ${YELLOW}$TTLG_PASS/$TTLG_TOTAL${NC} (Ready for Claude Code generation)"
echo ""

# =============================================================================
# SECTION 5: CONTEXT VAULT STRUCTURE
# =============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}5. CONTEXT VAULT STRUCTURE${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

VAULT_PASS=0
VAULT_TOTAL=0

declare -a VAULT_DIRS=(
    "context_vault/scans:Scan Results"
    "context_vault/agent_logs/fotw_captures:FOTW Captures"
    "context_vault/mission_data:Mission Data"
    "context_vault/events:System Events"
    "friday_orchestrator/logs:Friday Logs"
    "logs:Diagnostic Logs"
)

for dir_entry in "${VAULT_DIRS[@]}"; do
    dir="${dir_entry%:*}"
    label="${dir_entry#*:}"
    ((VAULT_TOTAL++))
    if [ -d "$EPOS_ROOT/$dir" ]; then
        echo -e "${GREEN}✅${NC} $label ($dir)"
        ((VAULT_PASS++))
    else
        echo -e "${YELLOW}⚠️ ${NC} $label (Directory not created: $dir)"
    fi
done

echo ""
echo -e "Context Vault Directories: ${YELLOW}$VAULT_PASS/$VAULT_TOTAL${NC}"
echo ""

# =============================================================================
# SECTION 6: ENVIRONMENT CONFIGURATION
# =============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}6. ENVIRONMENT CONFIGURATION${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

ENV_PASS=0
ENV_TOTAL=0

if [ -f "$EPOS_ROOT/.env" ]; then
    echo -e "${GREEN}✅${NC} .env file exists"
    ((ENV_PASS++))
    
    # Check for critical env vars
    declare -a ENV_VARS=(
        "OPENROUTER_API_KEY"
        "TTLG_SCOUT_MODEL_ALIAS"
        "FRIDAY_ORCHESTRATOR_MODEL_ALIAS"
    )
    
    for var in "${ENV_VARS[@]}"; do
        if grep -q "^${var}=" "$EPOS_ROOT/.env" 2>/dev/null; then
            echo -e "  ${GREEN}✓${NC} $var configured"
        else
            echo -e "  ${YELLOW}◯${NC} $var not configured"
        fi
    done
else
    echo -e "${RED}❌${NC} .env file missing"
fi

((ENV_TOTAL++))
echo ""

# =============================================================================
# SECTION 7: BUILD STATUS SUMMARY
# =============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}BUILD STATUS SUMMARY${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

TOTAL_PASS=$((CONST_PASS + GLUE_PASS + INFRA_PASS + TTLG_PASS + VAULT_PASS + ENV_PASS))
TOTAL_COUNT=$((CONST_TOTAL + GLUE_TOTAL + INFRA_TOTAL + TTLG_TOTAL + VAULT_TOTAL + ENV_TOTAL))

PERCENT=$((TOTAL_PASS * 100 / TOTAL_COUNT))

echo ""
echo -e "Constitutional Framework:  ${GREEN}$CONST_PASS/$CONST_TOTAL${NC}"
echo -e "Governance Glue:           ${YELLOW}$GLUE_PASS/$GLUE_TOTAL${NC}  ← CRITICAL IF NOT 5/5"
echo -e "Infrastructure:            ${GREEN}$INFRA_PASS/$INFRA_TOTAL${NC}"
echo -e "TTLG Entrypoints:          ${YELLOW}$TTLG_PASS/$TTLG_TOTAL${NC}  ← Pending Claude Code"
echo -e "Context Vault:             ${YELLOW}$VAULT_PASS/$VAULT_TOTAL${NC}"
echo -e "Environment Config:        ${GREEN}$ENV_PASS/$ENV_TOTAL${NC}"
echo ""
echo -e "Overall Build Progress: ${YELLOW}$TOTAL_PASS/$TOTAL_COUNT${NC} components ($PERCENT%)"
echo ""

# =============================================================================
# NEXT STEPS
# =============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}NEXT STEPS${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ $GLUE_PASS -lt 5 ]; then
    echo -e "${RED}🚨 PRIORITY 1:${NC} Generate governance glue files (5 markdown files)"
    echo "   Command: claude (in Claude Code)"
    echo "   Files to generate:"
    for file_entry in "${GLUE_FILES[@]}"; do
        label="${file_entry#*:}"
        echo "     - $label"
    done
    echo ""
fi

if [ $TTLG_PASS -lt 8 ]; then
    echo -e "${YELLOW}🎯 PRIORITY 2:${NC} Generate TTLG entrypoints (after governance glue complete)"
    echo "   Command: Activate Claude Code with FROZEN_EVENT_AND_ARTIFACT_CONTRACT.md"
    echo "   Outputs: 4 Python entrypoints + 4 CLI wrappers"
    echo ""
fi

echo -e "${GREEN}📊 PROGRESS SAVED:${NC} Review this window regularly to track build state"
echo ""

# =============================================================================
# FOOTER
# =============================================================================

echo -e "${CYAN}[$(date '+%H:%M:%S')]${NC} Progress window updated"
echo ""
echo "Run this script again with: bash epos_progress_window.sh"
echo ""
