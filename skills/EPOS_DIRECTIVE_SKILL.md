# EPOS Directive Interpretation Skill

## When to use
Apply when receiving a CODE directive from Jamie.

## Rules
1. Read the ENTIRE directive before writing any code
2. Execute the Scenario Projection Block FIRST — verify environment assumptions
3. Execute missions in ORDER — do not skip ahead
4. Run Doctor between each mission
5. If a mission fails, debug it before proceeding
6. If context limits approach, prioritize AAR over last feature mission
7. Print the AAR to terminal before closing
8. A file is not a feature. Nothing is done until it runs.

## The Mission Lifecycle
For every mission:
1. **Plan** — read the spec, identify dependencies, anticipate failures
2. **Build** — write the minimum code to satisfy the spec
3. **Run** — execute the code, capture output
4. **Verify** — assert expected behavior, run Doctor check
5. **Observe** — confirm Event Bus entry or log entry
6. **Mark complete** — only after all 5 steps pass

## The Acceptance Test (5 questions)
Before marking ANY mission complete, ask:
1. Does the code EXIST? (file created)
2. Is the code IMPORTED by at least one other EPOS module? (integrated)
3. Does the code RUN successfully when invoked? (deployed)
4. Is the result VERIFIED by a test or Doctor check? (verified)
5. Is there an Event Bus entry or log confirming the operation? (observable)

If ANY answer is "no", the mission is INCOMPLETE.

## Pre-mortem discipline
Before writing the first line of code for any mission:
- What environmental assumption could be wrong?
- What dependency might not be installed?
- What import path might fail?
- What permission or network could block this?
- What does graceful degradation look like?

## When BrowserUse / Agent Zero / external services are involved
- Verify the service is reachable BEFORE building the integration
- Provide a fallback (staging, manual, or queue) when the service is unavailable
- Never assume — always check

## When context limits approach
Constitutional priority order:
1. AAR (always — cannot be skipped)
2. Verification of completed missions
3. Doctor check
4. Last feature mission (deferred to next session if needed)

The learning from what was built > one more unverified feature.

*1% daily. 37x annually.*
