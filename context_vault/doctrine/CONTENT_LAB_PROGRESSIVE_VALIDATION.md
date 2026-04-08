<!-- EPOS GOVERNANCE WATERMARK -->
+++# CONTENT LAB PROGRESSIVE VALIDATION SUITE
## Prove Each Layer Before Stacking the Next
### Hell Week — Pre-Constellation Deployment

> "The human mind plays out scenarios before executing. EPOS must do the same."

---

## TEST PHILOSOPHY

We do NOT deploy the full constellation and hope it works.
We prove 7 layers in sequence. Each layer must pass before the next begins.
If a layer fails, we fix it at that layer — not three layers up where the symptom appears.

---

## LAYER 1: ISOLATED ENGINE VALIDATION
**Objective:** Prove each Python module works standalone, with zero dependencies on other modules.
**Permission Gate:** AUTONOMOUS

### Test 1.1 — Echolocation Algorithm (Standalone)
```powershell
cd C:\Users\Jamie\workspace\epos_mcp
python content\lab\tributaries\echolocation_algorithm.py
```

**Expected Output:**
```json
{
  "content_id": "TEST_001",
  "score": [60-100 range],
  "action": "expand" or "promote",
  "transformations": [non-empty list],
  "reasoning": [non-empty string]
}
```

**Pass Criteria:**
- [ ] No import errors
- [ ] Score is a number between 0 and 100
- [ ] Action is one of: expand, promote, hold, kill
- [ ] Transformations list is non-empty for scores above 60
- [ ] Health check returns status: healthy

**If Fails:** Fix the module in isolation. Do not proceed.

---

### Test 1.2 — Cascade Optimizer (Standalone)
```powershell
python content\lab\cascades\cascade_optimizer.py
```

**Expected Output:**
```json
{
  "source_id": "YT_TEST_001",
  "total_derivatives": [5 or more],
  "stabilization_ok": true,
  "derivatives": [non-empty array]
}
```

**Pass Criteria:**
- [ ] No import errors
- [ ] total_derivatives >= 5
- [ ] stabilization_ok is true (test data published > 24hr ago)
- [ ] Each derivative has: derivative_id, type, format, source_attribution
- [ ] Health check returns status: healthy

**If Fails:** Fix the module in isolation. Do not proceed.

---

### Test 1.3 — Brand Validator (Standalone)
```powershell
python content\lab\validation\brand_validator.py
```

**Expected Output:**
```json
{
  "content_id": "DERIV_TEST_001",
  "passed": true,
  "score": [70-100],
  "requires_human_review": false
}
```

**Pass Criteria:**
- [ ] No import errors
- [ ] Compliant content returns passed: true
- [ ] Score is a number between 0 and 100
- [ ] All check names present (voice_tone, prohibited_words, platform_format, hashtag_limit, cta_present, source_attribution, flagged_content)
- [ ] Health check returns status: healthy

**If Fails:** Fix the module in isolation. Do not proceed.

---

## LAYER 2: CROSS-MODULE INTEGRATION
**Objective:** Prove modules can import each other and data flows between them.
**Permission Gate:** AUTONOMOUS

### Test 2.1 — Tributary Worker Imports
```powershell
python -c "from content.lab.automation.tributary_worker import TributaryWorker; print('IMPORT OK')"
```

**Pass Criteria:**
- [ ] Prints "IMPORT OK" with no errors
- [ ] No ModuleNotFoundError or ImportError

**If Fails:** Check sys.path configuration and __init__.py files. Fix before proceeding.

---

### Test 2.2 — Cascade Worker Imports
```powershell
python -c "from content.lab.automation.cascade_worker import CascadeWorker; print('IMPORT OK')"
```

**Pass Criteria:**
- [ ] Prints "IMPORT OK" with no errors

---

### Test 2.3 — Publish Orchestrator Imports
```powershell
python -c "from content.lab.automation.publish_orchestrator import PublishOrchestrator; print('IMPORT OK')"
```

**Pass Criteria:**
- [ ] Prints "IMPORT OK" with no errors

---

## LAYER 3: CONTEXT VAULT INTEGRATION
**Objective:** Prove all modules can read from and write to the Context Vault.
**Permission Gate:** AUTONOMOUS

### Test 3.1 — Decision Logging
```powershell
python -c "
from content.lab.tributaries.echolocation_algorithm import EcholocationAlgorithm
algo = EcholocationAlgorithm()
result = algo.analyze({
    'content_id': 'VAULT_TEST_001',
    'platform': 'x',
    'text': 'Sovereignty test',
    'likes': 100, 'shares': 30, 'comments': 15, 'saves': 8,
    'impressions': 2000, 'hours_live': 2.0,
    'follower_count': 1000, 'verified_engagers': 1,
})
print(f'Score: {result[\"score\"]}')
"
```

Then verify the log was written:
```powershell
Get-Content context_vault\bi_history\echolocation_decisions.jsonl | Select-Object -Last 1
```

**Pass Criteria:**
- [ ] Score returned without error
- [ ] echolocation_decisions.jsonl exists and contains the VAULT_TEST_001 entry
- [ ] system_events.jsonl contains a corresponding event

---

### Test 3.2 — Cascade Decision Logging
```powershell
python -c "
from content.lab.cascades.cascade_optimizer import CascadeOptimizer
opt = CascadeOptimizer()
result = opt.generate_derivatives({
    'source_id': 'VAULT_CAS_TEST', 'source_type': 'youtube',
    'title': 'Vault Test', 'transcript': 'Step 1: Test sovereignty.',
    'published_at': '2026-02-10T10:00:00Z',
})
print(f'Derivatives: {result[\"total_derivatives\"]}')
"
```

Then verify:
```powershell
Get-Content context_vault\bi_history\cascade_decisions.jsonl | Select-Object -Last 1
```

**Pass Criteria:**
- [ ] Derivatives generated
- [ ] cascade_decisions.jsonl contains the VAULT_CAS_TEST entry
- [ ] system_events.jsonl contains cascade.generated event

---

## LAYER 4: FULL PIPELINE FLOW (TRIBUTARY)
**Objective:** Prove the complete bottom-up pipeline: capture → score → route → validate.
**Permission Gate:** AUTONOMOUS (no external publishing)

### Test 4.1 — Seed and Process
Create 3 test tweets in the captured directory:

```powershell
# Create captured directory if needed
New-Item -ItemType Directory -Force -Path content\lab\tributaries\x\captured

# Seed high-performer
@'
{"content_id": "PIPE_HIGH_001", "text": "Your AI strategy is a subscription to a cage. EPOS gives you the title to the land. Sovereignty is survival. #EPOS", "likes": 280, "shares": 95, "comments": 42, "saves": 31, "impressions": 8500, "hours_live": 6.0, "follower_count": 2400, "verified_engagers": 5}
'@ | Set-Content content\lab\tributaries\x\captured\pipe_high_001.json

# Seed medium-performer
@'
{"content_id": "PIPE_MED_002", "text": "Built a content engine. 200 pieces a month. Zero employees. 12 sovereign AI nodes.", "likes": 45, "shares": 12, "comments": 8, "saves": 3, "impressions": 1200, "hours_live": 12.0, "follower_count": 2400, "verified_engagers": 1}
'@ | Set-Content content\lab\tributaries\x\captured\pipe_med_002.json

# Seed low-performer (should be killed)
@'
{"content_id": "PIPE_LOW_003", "text": "Nice weather today", "likes": 2, "shares": 0, "comments": 0, "saves": 0, "impressions": 50, "hours_live": 48.0, "follower_count": 2400, "verified_engagers": 0}
'@ | Set-Content content\lab\tributaries\x\captured\pipe_low_003.json
```

Then run the worker:
```powershell
python content\lab\automation\tributary_worker.py
```

**Pass Criteria:**
- [ ] PIPE_HIGH_001 → expansion_queue/ (score > 85) OR production/ (score > 60)
- [ ] PIPE_MED_002 → production/ (score 40-85) OR left in place (hold)
- [ ] PIPE_LOW_003 → archive/ (score < 25)
- [ ] captured/ directory is empty after processing (all files routed)
- [ ] Events logged to system_events.jsonl
- [ ] Summary JSON returned with correct counts

---

## LAYER 5: FULL PIPELINE FLOW (CASCADE)
**Objective:** Prove the complete top-down pipeline: source → derivatives → validate → queue.
**Permission Gate:** AUTONOMOUS (no external publishing)

### Test 5.1 — YouTube Source Processing
```powershell
# Create source directory
New-Item -ItemType Directory -Force -Path content\lab\cascades\youtube\sources

# Seed a YouTube source
@'
{"source_id": "YT_PIPE_001", "title": "Why Sovereign AI Wins", "transcript": "Step 1: Stop renting intelligence. Step 2: Build sovereign nodes. Step 3: Deploy constitutional governance. The key insight is that data sovereignty is the entire business model. The bottom line is if your AI cannot run offline, you do not own it.", "url": "https://youtube.com/watch?v=test001", "published_at": "2026-02-12T10:00:00Z", "metrics": {"likes": 340, "shares": 89, "comments": 45, "impressions": 12000}}
'@ | Set-Content content\lab\cascades\youtube\sources\yt_pipe_001.json
```

Then run:
```powershell
python content\lab\automation\cascade_worker.py
```

**Pass Criteria:**
- [ ] Source processed (moved to sources/processed/)
- [ ] 5+ derivatives generated in cascades/derivatives/
- [ ] Each derivative has a derivative_id, type, format, and source_attribution
- [ ] Brand validation results attached to each derivative (_validation field)
- [ ] Validation failures (if any) in validation_failures/
- [ ] Events logged

---

## LAYER 6: PUBLISH ORCHESTRATOR (DRY RUN)
**Objective:** Prove the publish orchestrator routes content correctly WITHOUT sending anything external.
**Permission Gate:** AUTONOMOUS (generates ready-to-post files only)

### Test 6.1 — Process Publish Queue
First, manually move one validated derivative into the publish queue:
```powershell
# Take the first derivative and copy to publish queue
$firstDeriv = (Get-ChildItem content\lab\cascades\derivatives\*.json | Select-Object -First 1)
Copy-Item $firstDeriv.FullName content\lab\publish_queue\
```

Then run:
```powershell
python content\lab\automation\publish_orchestrator.py
```

**Pass Criteria:**
- [ ] File moved from publish_queue/ to published/
- [ ] ready_to_post/{platform}/ contains the formatted post
- [ ] Post file includes: content_id, platform, text, cta_token, scheduled_time
- [ ] permission_status field is either "approved" or "AWAITING_HUMAN_APPROVAL"
- [ ] publish_schedule.jsonl updated
- [ ] No external API calls made (this is a dry run)

---

## LAYER 7: HEALTH ENDPOINT INTEGRATION
**Objective:** Prove the Content Lab health check reports accurate status through the Meta Orchestrator.
**Permission Gate:** AUTONOMOUS

### Test 7.1 — Component Health Roll-Up
```powershell
python -c "
from content.lab.tributaries.echolocation_algorithm import health_check as echo_h
from content.lab.cascades.cascade_optimizer import health_check as cascade_h
from content.lab.validation.brand_validator import health_check as brand_h
from content.lab.automation.tributary_worker import health_check as trib_h
from content.lab.automation.cascade_worker import health_check as cas_h
from content.lab.automation.publish_orchestrator import health_check as pub_h
import json

health = {
    'C10_CONTENT_LAB': {
        'echolocation': echo_h(),
        'cascade': cascade_h(),
        'brand_validator': brand_h(),
        'tributary_worker': trib_h(),
        'cascade_worker': cas_h(),
        'publish_orchestrator': pub_h(),
    }
}

all_healthy = all(
    v['status'] == 'healthy'
    for v in health['C10_CONTENT_LAB'].values()
)
health['C10_CONTENT_LAB']['overall'] = 'healthy' if all_healthy else 'degraded'
print(json.dumps(health, indent=2))
"
```

**Pass Criteria:**
- [ ] All 6 components report "healthy"
- [ ] Overall status is "healthy"
- [ ] No import or runtime errors

---

## GRADUATION: FULL CONSTELLATION COMMAND

**Only issue this command after ALL 7 layers pass.**

> "EPOS, as META + C10: The Content Lab has passed all 7 validation layers. Execute CONTENT_LAB_ATTACHMENT_V1:
>
> 1. Register C10 in the Component Interaction Matrix with dependencies C01, C05, C09; failure modes FS-CL01 through FS-CL03; health endpoint /content/lab/health.
>
> 2. Add Content Lab endpoints to meta_orchestrator.py: GET /content/lab/health, POST /content/lab/analyze-tributary, POST /content/lab/generate-cascade.
>
> 3. Update stasis.py with Content Lab checks: tributary_active, cascade_active, validation_passing, publication_flowing.
>
> 4. Run the full mission pack (content_lab_mission_pack.json) missions 001 through 005 in sequence.
>
> 5. Confirm health endpoint returns all-green via: curl http://127.0.0.1:8001/content/lab/health
>
> 6. Report status: which missions passed, which failed, and any Governance Gate rejections.
>
> Content Lab is now operational. Begin the I.I.D.E.A.T.E. loop: Immersion cycle 1."

---

## FAILURE RECOVERY

If any layer fails, DO NOT proceed to the next layer. Instead:

| Layer | Common Failure | Fix |
|-------|---------------|-----|
| 1 | ImportError | Check Python 3.11.x, check pathlib imports, verify no 3.13 ABI issues |
| 2 | ModuleNotFoundError | Add __init__.py files, check sys.path, verify directory structure |
| 3 | FileNotFoundError on Vault | Run setup_content_lab.py, verify EPOS_ROOT env var |
| 4 | Files not moving between dirs | Check file permissions, verify Path operations, check OS path separator |
| 5 | Zero derivatives generated | Check extraction regex patterns, verify test transcript has parseable content |
| 6 | No ready-to-post output | Check publish_queue has files, verify platform inference logic |
| 7 | Health reports degraded | Run individual health checks to find the failing component |

---

> "Go slow to go fast. Prove each layer. Then let lil Essa walk."
