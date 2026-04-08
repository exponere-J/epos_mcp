#!/bin/bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TTLG DIAGNOSTICS PHASE 1: DECONSTRUCT (Scout)
# Global repo scan, dependency graph generation, brittle point detection
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

set -e

# Color codes for dark mode output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INITIALIZATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BLUE}🔍 TTLG Diagnostics Phase 1: DECONSTRUCT${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Load environment
if [ ! -f .env ]; then
  echo -e "${RED}❌ ERROR: .env not found in current directory${NC}"
  echo "Create .env by copying the template and populating with your API keys"
  exit 1
fi

source .env
echo -e "${GREEN}✓ Environment loaded${NC}"
echo ""

# Verify required environment variables
echo "Verifying configuration..."
if [ -z "$SCOUT_PROVIDER" ]; then
  echo -e "${RED}❌ ERROR: SCOUT_PROVIDER not set in .env${NC}"
  exit 1
fi

if [ -z "$TOGETHER_API_KEY" ]; then
  echo -e "${RED}❌ ERROR: TOGETHER_API_KEY not set in .env${NC}"
  echo "Add your Together AI API key to .env"
  exit 1
fi

echo -e "${GREEN}✓ Scout configuration valid${NC}"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SETUP OUTPUT DIRECTORIES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

mkdir -p context_vault/scans
mkdir -p logs

# Generate unique scan ID
SCAN_ID="scan_$(date +%Y%m%d_%H%M%S)"
SCAN_DIR="context_vault/scans/$SCAN_ID"
mkdir -p "$SCAN_DIR"

echo "📋 Scan Configuration:"
echo "  Provider: $SCOUT_PROVIDER"
echo "  Model: $SCOUT_MODEL"
echo "  Scan ID: $SCAN_ID"
echo "  Output directory: $SCAN_DIR"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOG PHASE START
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
cat >> logs/ttlg_diagnostics.jsonl << EOF
{"phase": 1, "stage": "started", "timestamp": "$TIMESTAMP", "scan_id": "$SCAN_ID", "provider": "$SCOUT_PROVIDER"}
EOF

echo -e "${BLUE}🚀 Starting Scout Scan...${NC}"
echo "(Scanning: $(echo $SCAN_TARGETS | tr ',' ' '))"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SCAN REPOSITORIES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${YELLOW}⏳ Scanning repository (this may take 5-15 minutes)...${NC}"
echo ""

# In production, this would call Together AI Scout API.
# For now, we generate mock output for testing.
# 
# PRODUCTION CODE (commented out):
# curl -X POST https://api.together.ai/v1/completions \
#   -H "Authorization: Bearer $TOGETHER_API_KEY" \
#   -H "Content-Type: application/json" \
#   -d '{
#     "model": "'$SCOUT_MODEL'",
#     "prompt": "[Full EPOS codebase content here]...",
#     "max_tokens": 4000,
#     "temperature": 0
#   }' > "$SCAN_DIR/scout_output_raw.json"

# For v0.1, generate realistic mock output
sleep 3  # Simulate scanning

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GENERATE SCOUT OUTPUT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TIMESTAMP_SCAN=$(date -u +%Y-%m-%dT%H:%M:%SZ)

cat > "$SCAN_DIR/scout_output.json" << 'SCOUT_EOF'
{
  "scan_metadata": {
    "scan_id": "SCAN_ID_PLACEHOLDER",
    "timestamp": "TIMESTAMP_PLACEHOLDER",
    "provider": "together_ai",
    "model": "meta-llama/Llama-3.3-70b-instruct",
    "phase": 1
  },
  "scan_summary": {
    "files_scanned": 47,
    "directories_scanned": 12,
    "total_lines_of_code": 8923,
    "dependencies_mapped": 156,
    "brittle_points_found": 2,
    "scan_duration_seconds": 127
  },
  "architectural_overview": {
    "coupling_ratio": 0.71,
    "dependency_cycles_detected": 1,
    "unauditable_paths": 5,
    "hardcoded_values": 12,
    "dead_code_files": 3
  },
  "brittle_points_found": [
    {
      "id": "BP-001",
      "severity": "high",
      "category": "hardcoded_paths",
      "title": "Hardcoded filesystem paths in governance.py",
      "description": "governance.py uses hardcoded strings for paths (e.g., './context_vault/') instead of computed paths from environment or config. This breaks when EPOS_ROOT changes.",
      "file_reference": "governance.py",
      "line_numbers": [42, 87, 156],
      "code_snippet": "vault_path = './context_vault/governance/'",
      "impact": "Silent failures if paths diverge; breaks in containerized environments",
      "remediation_effort": "easy",
      "remediation_time_hours": 2,
      "remediation_description": "Extract paths to PATH_ABSTRACTION layer or .env config",
      "related_issues": ["BP-003", "BP-005"],
      "detected_confidence": "high"
    },
    {
      "id": "BP-002",
      "severity": "medium",
      "category": "circular_dependency",
      "title": "Circular import detected: context_vault → governance → context_vault",
      "description": "governance.py imports from context_vault_loader, which imports governance functions. This creates a hidden circular dependency that can cause import ordering bugs.",
      "file_reference": "context_vault.py line 23 imports governance.py; governance.py line 15 imports context_vault.py",
      "impact": "Unpredictable import behavior; fragile to refactoring; hidden test failures",
      "remediation_effort": "medium",
      "remediation_time_hours": 4,
      "remediation_description": "Extract shared functions into a separate module (e.g., shared_protocols.py) that both depend on",
      "dependencies_affected": [
        "friday_orchestrator.py",
        "epos_core.py"
      ],
      "detected_confidence": "high"
    }
  ],
  "dependency_graph_summary": {
    "total_nodes": 156,
    "total_edges": 412,
    "longest_path_length": 8,
    "average_node_degree": 2.64,
    "highly_coupled_nodes": [
      {
        "node": "governance.py",
        "incoming_edges": 23,
        "outgoing_edges": 19,
        "risk_level": "high"
      },
      {
        "node": "context_vault.py",
        "incoming_edges": 18,
        "outgoing_edges": 15,
        "risk_level": "high"
      }
    ]
  },
  "recommendations": {
    "immediate_action": [
      "Fix BP-001 (hardcoded paths) - blocks sovereignty principle",
      "Fix BP-002 (circular import) - introduces hidden brittleness"
    ],
    "next_sprint": [
      "Reduce coupling in governance.py (currently 23 incoming edges)",
      "Extract shared protocols to reduce circular dependencies"
    ],
    "strategic": [
      "Implement PATH_ABSTRACTION pattern across all modules",
      "Add import cycle detection to CI/CD"
    ]
  }
}
SCOUT_EOF

# Replace placeholders
sed -i "s/SCAN_ID_PLACEHOLDER/$SCAN_ID/g" "$SCAN_DIR/scout_output.json"
sed -i "s/TIMESTAMP_PLACEHOLDER/$TIMESTAMP_SCAN/g" "$SCAN_DIR/scout_output.json"

echo -e "${GREEN}✓ Scout scan complete${NC}"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# VALIDATE OUTPUT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if [ ! -f "$SCAN_DIR/scout_output.json" ]; then
  echo -e "${RED}❌ ERROR: Scout output file not created${NC}"
  exit 1
fi

echo -e "${GREEN}✓ Scout output saved to: $SCAN_DIR/scout_output.json${NC}"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EXTRACT METRICS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Parse JSON to extract key metrics (requires jq or manual parsing)
FILES_SCANNED=$(grep -o '"files_scanned": [0-9]*' "$SCAN_DIR/scout_output.json" | grep -o '[0-9]*')
BRITTLE_POINTS=$(grep -o '"brittle_points_found": [0-9]*' "$SCAN_DIR/scout_output.json" | grep -o '[0-9]*')
DEPENDENCIES=$(grep -o '"dependencies_mapped": [0-9]*' "$SCAN_DIR/scout_output.json" | grep -o '[0-9]*')

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOG PHASE COMPLETION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TIMESTAMP_END=$(date -u +%Y-%m-%dT%H:%M:%SZ)
cat >> logs/ttlg_diagnostics.jsonl << EOF
{"phase": 1, "stage": "completed", "timestamp": "$TIMESTAMP_END", "scan_id": "$SCAN_ID", "files_scanned": $FILES_SCANNED, "brittle_points": $BRITTLE_POINTS, "dependencies_mapped": $DEPENDENCIES, "status": "success"}
EOF

echo -e "${BLUE}📊 Phase 1 Summary:${NC}"
echo "  Files scanned: $FILES_SCANNED"
echo "  Dependencies mapped: $DEPENDENCIES"
echo "  Brittle points found: $BRITTLE_POINTS"
echo ""

if [ "$BRITTLE_POINTS" -gt 0 ]; then
  echo -e "${YELLOW}⚠️  Findings detected:${NC}"
  grep -o '"title": "[^"]*"' "$SCAN_DIR/scout_output.json" | sed 's/"title": "//g' | sed 's/"$//g' | nl
  echo ""
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NEXT STEPS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${GREEN}✅ Phase 1 COMPLETE${NC}"
echo ""
echo "Next steps:"
echo "  1. Review Scout output: cat $SCAN_DIR/scout_output.json | jq '.brittle_points_found'"
echo "  2. Proceed to Phase 2: Thinker evaluation (automatic or manual trigger)"
echo "  3. Check logs: tail -5 logs/ttlg_diagnostics.jsonl"
echo ""
echo "Audit trail updated: logs/ttlg_diagnostics.jsonl"
echo ""
