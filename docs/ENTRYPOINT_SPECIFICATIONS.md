# ENTRYPOINT SPECIFICATIONS

**Exact CLI Signatures and JSON Schemas for Friday ↔ Claude Code Communication**

---

## OVERVIEW

Friday calls four entrypoints on Claude Code. These must be built exactly as specified so that Friday's decisions result in predictable, testable code execution.

**Entrypoints are not optional.** They are the interface between the decision agent (Friday) and the implementation agent (Claude Code).

---

## ENTRYPOINT 1: `ttlg_systems_light_scout`

### Purpose
Quick architectural scan of EPOS (subset of full Phase 1). Used when:
- Brittle points are medium/low severity
- Time is limited (< 2 hour window)
- Only specific modules need review

### CLI Signature
```bash
ttlg_systems_light_scout \
  --targets "governance_gate,context_vault" \
  --scan-id "scan_20260228_140000" \
  --intensity "light" \
  --timeout-minutes 60 \
  --output-format "json" \
  --output-path "./context_vault/scans/light_scout_output.json"
```

### Parameters (All Required)

| Parameter | Type | Values | Description |
|-----------|------|--------|-------------|
| `--targets` | string (comma-separated) | Module names | Which parts of EPOS to scan |
| `--scan-id` | string | ISO timestamp format | Unique identifier for this scan |
| `--intensity` | enum | "light", "normal", "aggressive" | Scanning thoroughness |
| `--timeout-minutes` | integer | 30-120 | Max execution time |
| `--output-format` | enum | "json", "jsonl", "md" | Output structure |
| `--output-path` | string | File path | Where to save results |

### Input JSON Schema
```json
{
  "entrypoint": "ttlg_systems_light_scout",
  "version": "1.0",
  "trigger": {
    "type": "friday_decision",
    "decision_id": "FRI-DEC-2026-02-28-T14-00-00Z",
    "reasoning": "Medium severity issues detected; quick verification"
  },
  "parameters": {
    "targets": ["governance_gate", "context_vault"],
    "scan_id": "scan_20260228_140000",
    "intensity": "light",
    "timeout_minutes": 60,
    "scope": {
      "max_files": 20,
      "max_dependencies": 100,
      "focus_areas": ["paths", "coupling", "governance"]
    }
  },
  "governance": {
    "approved": true,
    "approval_timestamp": "2026-02-28T13:55:00Z",
    "constitutional_check_passed": true
  }
}
```

### Output JSON Schema
```json
{
  "scan_id": "scan_20260228_140000",
  "entrypoint": "ttlg_systems_light_scout",
  "timestamp_completed": "2026-02-28T14:30:00Z",
  "duration_seconds": 1800,
  "scan_summary": {
    "files_scanned": 12,
    "dependencies_mapped": 45,
    "brittle_points_found": 2
  },
  "brittle_points": [
    {
      "id": "BP-001",
      "severity": "high",
      "category": "hardcoded_paths",
      "file": "governance.py:42",
      "description": "Hardcoded path breaks when EPOS_ROOT changes"
    }
  ],
  "governance": {
    "logged_to_audit_trail": true,
    "audit_log_id": "GOVLOG-2026-02-28-T14-30-00Z"
  },
  "status": "success",
  "ready_for_phase_2": true
}
```

### Success Criteria
- ✅ Completes within `--timeout-minutes`
- ✅ Files scanned = number of target modules
- ✅ Output written to `--output-path`
- ✅ All findings logged to audit trail
- ✅ Valid JSON output (no parsing errors)

### Failure Modes
- ❌ Timeout exceeded → Graceful halt, return partial results
- ❌ Target not found → Error message, abort scan
- ❌ Governance check failed → Do not proceed, log failure
- ❌ Output path unwritable → Log error, return JSON to stdout

---

## ENTRYPOINT 2: `ttlg_market_light_scout`

### Purpose
Quick market listening (subset of full Phase 1 Market). Used when:
- Market signal is growing but not yet critical
- Time is limited
- Testing new markets

### CLI Signature
```bash
ttlg_market_light_scout \
  --domain "agentic_web_browsing_security" \
  --sample-size 50 \
  --scan-id "market_scan_20260228_140000" \
  --sources "reddit,twitter" \
  --output-path "./context_vault/market_scans/light_scout.json"
```

### Parameters (All Required)

| Parameter | Type | Values | Description |
|-----------|------|--------|-------------|
| `--domain` | string | Domain name | Market domain to listen to |
| `--sample-size` | integer | 10-100 | Posts/mentions to analyze |
| `--scan-id` | string | ISO timestamp format | Unique scan identifier |
| `--sources` | string (comma-separated) | "reddit", "twitter", "discord", "github" | Platforms to sample |
| `--output-path` | string | File path | Where to save results |

### Input JSON Schema
```json
{
  "entrypoint": "ttlg_market_light_scout",
  "version": "1.0",
  "trigger": {
    "type": "friday_decision",
    "decision_id": "FRI-DEC-2026-02-28-T14-15-00Z",
    "reasoning": "Market signal for domain is growing; test concept resonance"
  },
  "parameters": {
    "domain": "agentic_web_browsing_security",
    "sample_size": 50,
    "scan_id": "market_scan_20260228_140000",
    "sources": ["reddit", "twitter"],
    "lookback_days": 7,
    "personas_filter": ["dev", "founder", "security"]
  },
  "governance": {
    "approved": true,
    "constitutional_check_passed": true
  }
}
```

### Output JSON Schema
```json
{
  "scan_id": "market_scan_20260228_140000",
  "entrypoint": "ttlg_market_light_scout",
  "domain": "agentic_web_browsing_security",
  "timestamp_completed": "2026-02-28T14:40:00Z",
  "duration_seconds": 600,
  "scan_summary": {
    "total_mentions_found": 45,
    "personas_identified": 3,
    "sentiment_distribution": {
      "positive": 5,
      "neutral": 12,
      "negative": 28
    }
  },
  "top_pains_identified": [
    {
      "pain": "Session context leakage between browser tabs",
      "mentions": 12,
      "sentiment": "strongly_negative",
      "personas": ["dev", "security"]
    }
  ],
  "signal_analysis": {
    "signal_strength": "rising",
    "trend_confidence": 0.87,
    "recommendation": "Increase market listening; strong pain signal"
  },
  "governance": {
    "logged_to_audit_trail": true
  },
  "status": "success",
  "ready_for_phase_2": true
}
```

### Success Criteria
- ✅ Sample size achieved (or logged if partial)
- ✅ Sentiment correctly classified
- ✅ Top pains identified and quoted
- ✅ Output written to path
- ✅ All data logged to audit trail

---

## ENTRYPOINT 3: `friday_vault_summary`

### Purpose
Friday needs to understand recent TTLG artifacts (scans, AARs, patterns). This entrypoint generates a summary for Friday's decision-making.

### CLI Signature
```bash
friday_vault_summary \
  --lookback-days 7 \
  --artifact-types "scan,aar,pattern" \
  --summarize-for "friday_decision" \
  --output-format "json"
```

### Parameters (All Required)

| Parameter | Type | Values | Description |
|-----------|------|--------|-------------|
| `--lookback-days` | integer | 1-90 | How far back to summarize |
| `--artifact-types` | string (comma-separated) | "scan", "aar", "pattern", "decision" | What to include |
| `--summarize-for` | enum | "friday_decision", "jamie_report", "technical_audit" | Audience |
| `--output-format` | enum | "json", "md", "html" | Format preference |

### Input JSON Schema
```json
{
  "entrypoint": "friday_vault_summary",
  "version": "1.0",
  "trigger": {
    "type": "friday_request",
    "timing": "pre_decision",
    "reason": "Friday needs context before deciding which workflow to run"
  },
  "parameters": {
    "lookback_days": 7,
    "artifact_types": ["scan", "aar", "pattern"],
    "summarize_for": "friday_decision",
    "include_metrics": true,
    "include_patterns": true,
    "include_confidence_scores": true
  }
}
```

### Output JSON Schema
```json
{
  "summary_id": "VAULT-SUM-2026-02-28-T14-50-00Z",
  "generated_at": "2026-02-28T14:50:00Z",
  "lookback_days": 7,
  "summary": {
    "recent_scans": 3,
    "recent_aars": 3,
    "patterns_discovered": 2
  },
  "systems_cycle_status": {
    "last_scan": {
      "scan_id": "scan_20260227_020000",
      "timestamp": "2026-02-27T02:30:00Z",
      "brittle_points_found": 2,
      "severity_distribution": {
        "critical": 0,
        "high": 1,
        "medium": 1,
        "low": 0
      },
      "fix_success_rate": 0.92
    },
    "trend": "Improving (fix_success_rate up 5% in past 3 scans)"
  },
  "market_cycle_status": {
    "domains_monitored": 2,
    "active_domains": [
      {
        "domain": "agentic_web_browsing_security",
        "signal_strength": "rising",
        "sentiment": "strongly_negative",
        "recommendation": "Increase listening cadence"
      }
    ],
    "solution_concepts_under_test": 3
  },
  "patterns_and_learning": {
    "high_confidence_patterns": [
      {
        "pattern": "PAT-aggressive-full-cycle",
        "confidence": 0.89,
        "uses": 4,
        "success_rate": 0.92
      }
    ],
    "recently_updated_patterns": 2
  },
  "friday_decision_recommendation": {
    "recommended_workflow": "ttlg_systems_full_cycle",
    "reasoning": "High severity issues detected; success rate supports aggressive approach",
    "confidence": 0.87
  },
  "governance": {
    "logged": true
  }
}
```

### Success Criteria
- ✅ All recent artifacts included
- ✅ Confidence scores present
- ✅ Trend analysis included
- ✅ Recommendations clear
- ✅ Output usable by Friday for decisions

---

## ENTRYPOINT 4: `friday_check_ttlg_health`

### Purpose
Friday periodically checks that both TTLG cycles (systems + market) are running, logging, and healthy. This is a diagnostics entrypoint.

### CLI Signature
```bash
friday_check_ttlg_health \
  --check-systems true \
  --check-market true \
  --check-logging true \
  --output-format "json"
```

### Parameters (All Required)

| Parameter | Type | Values | Description |
|-----------|------|--------|-------------|
| `--check-systems` | boolean | true/false | Verify systems cycle health |
| `--check-market` | boolean | true/false | Verify market cycle health |
| `--check-logging` | boolean | true/false | Verify audit trail integrity |
| `--output-format` | enum | "json", "text" | Response format |

### Input JSON Schema
```json
{
  "entrypoint": "friday_check_ttlg_health",
  "version": "1.0",
  "trigger": {
    "type": "friday_cron",
    "schedule": "hourly",
    "purpose": "Health check, diagnostic only"
  },
  "parameters": {
    "check_systems": true,
    "check_market": true,
    "check_logging": true,
    "alert_on_failures": true,
    "include_detailed_diagnostics": true
  }
}
```

### Output JSON Schema
```json
{
  "health_check_id": "HEALTH-2026-02-28-T14-55-00Z",
  "timestamp": "2026-02-28T14:55:00Z",
  "overall_status": "healthy",
  "systems_cycle": {
    "status": "healthy",
    "last_scan": "2026-02-27T02:30:00Z",
    "hours_since_last_scan": 36.5,
    "next_scheduled_scan": "2026-02-28T02:00:00Z",
    "issues_detected": 0,
    "audit_trail_valid": true
  },
  "market_cycle": {
    "status": "healthy",
    "active_domains": 2,
    "last_scout": "2026-02-28T14:30:00Z",
    "minutes_since_last_scout": 25,
    "issues_detected": 0,
    "audit_trail_valid": true
  },
  "logging_health": {
    "audit_log_status": "operational",
    "log_file_size_mb": 15.3,
    "entries_today": 47,
    "immutability_verified": true,
    "corruption_detected": false
  },
  "alerts": [],
  "recommendations": {
    "next_action": "Continue normal operations",
    "governance_status": "compliant"
  },
  "governance": {
    "logged": true,
    "health_check_logged": true
  }
}
```

### Success Criteria
- ✅ All systems operational
- ✅ Logging intact and immutable
- ✅ Audit trail valid
- ✅ No corruption or failures
- ✅ Output clear and actionable

---

## ENTRYPOINT ORCHESTRATION (How Friday Calls Them)

### Daily Workflow
```
06:00 AM: friday_check_ttlg_health (diagnostic)
          ↓ (if healthy, proceed)
06:05 AM: friday_vault_summary (get context)
          ↓ (read summary, make decision)
06:10 AM: IF (high severity detected)
            THEN ttlg_systems_light_scout
          ELSE (continue monitoring)
          ↓
06:30 AM: ttlg_market_light_scout (daily market check)
          ↓
14:00 PM: friday_check_ttlg_health (afternoon health check)
          ↓
20:00 PM: friday_vault_summary (evening summary for Jamie's report)
```

### Entrypoint Interdependencies

```
friday_check_ttlg_health (prerequisite)
    ↓ (must be healthy)
friday_vault_summary (context gathering)
    ↓ (read summary)
ttlg_systems_light_scout OR full_cycle (decision)
    ↓
ttlg_market_light_scout (parallel market listening)
    ↓
friday_vault_summary (post-decision summary)
```

---

## IMPLEMENTATION REQUIREMENTS FOR CLAUDE CODE

Claude Code must deliver all four entrypoints with:

- ✅ **Exact CLI signature** (matches above)
- ✅ **JSON input/output schemas** (validation required)
- ✅ **Error handling** (graceful failures, logged)
- ✅ **Governance compliance** (all logged, all auditable)
- ✅ **Testing** (unit tests for each entrypoint)
- ✅ **Documentation** (README for each)

### Checklist for Claude Code
- [ ] Implement `ttlg_systems_light_scout` CLI
- [ ] Implement `ttlg_market_light_scout` CLI
- [ ] Implement `friday_vault_summary` CLI
- [ ] Implement `friday_check_ttlg_health` CLI
- [ ] Validate all input JSON against schemas
- [ ] Write output JSON to correct paths
- [ ] Log all calls to audit trail
- [ ] Pass governance compliance checks
- [ ] Write unit tests for each entrypoint
- [ ] Create README with examples
- [ ] Test end-to-end: Friday calls → Claude Code responds → Friday reads output

---

## EXAMPLE: FRIDAY CALLING `ttlg_systems_light_scout`

### Friday's Decision
```json
{
  "decision_id": "FRI-DEC-2026-02-28-T14-00-00Z",
  "decision": "run_light_scout",
  "reasoning": "Governance module changed; quick verification needed"
}
```

### Friday's Call to Claude Code
```bash
bash scripts/ttlg_systems_light_scout.sh \
  --targets "governance_gate" \
  --scan-id "scan_20260228_140000" \
  --intensity "light" \
  --timeout-minutes 60 \
  --output-path "./context_vault/scans/scan_20260228_140000/scout_output.json"
```

### Claude Code's Response (Logged to JSON)
```json
{
  "scan_id": "scan_20260228_140000",
  "status": "success",
  "files_scanned": 5,
  "brittle_points_found": 1,
  "governance": {
    "logged": true,
    "audit_log_id": "GOVLOG-2026-02-28-T14-30-00Z"
  }
}
```

### Friday Reads Output and Logs Decision
```json
{
  "friday_decision_execution": "completed",
  "entrypoint_called": "ttlg_systems_light_scout",
  "entrypoint_response": "success",
  "findings": 1,
  "next_action": "Proceed to Phase 2 evaluation",
  "logged": true
}
```

---

**Status:** 🟢 SPECIFICATIONS COMPLETE  
**For Claude Code:** Implement these 4 entrypoints exactly as specified  
**For Friday:** Call these entrypoints in the orchestration flow above
