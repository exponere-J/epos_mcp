# AAR CONSTITUTIONAL AMENDMENT
## Non-Skippable After Action Review Mandate
### Amendment to EPOS Constitution v3.1
### Ratified: April 6, 2026
### Authority: Jamie Purdue, Sovereign Architect

---

## THE PROBLEM

CODE sessions produce features but skip reflection. A summary table says "we built it." An AAR says "here's what building it taught us." The difference is institutional learning versus institutional amnesia.

## THE LAW

Every CODE directive includes an AAR as its FINAL MISSION — not part of session close, not optional, not a summary table. It is its own bounded mission with acceptance criteria.

If context limits are approaching, the AAR takes PRIORITY over the last feature mission. The learning from what was built is more valuable than one more unreviewed feature.

## AAR TEMPLATE (9 Mandatory Sections)

1. **Session Identity**: Date, directive name, mission count, total duration
2. **Planned vs Actual**: For every mission — what was planned, what was delivered, delta
3. **What Went Well**: Specific successes with evidence (test results, scores, events)
4. **What Went Wrong**: At least ONE entry required. No session is perfect. If nothing went wrong, the AAR is lying.
5. **What Was Learned**: New patterns, architectural insights, process improvements discovered
6. **Doctrine Impact**: Did this session change any governance documents? Which ones? Why?
7. **Ecosystem State Delta**: Before/after for composite maturity, node count, CLI domains, event bus count
8. **Files Created/Modified**: Complete manifest of what changed in the codebase
9. **Next Session Guidance**: What the next CODE session should know before it starts

## STORAGE (Three Locations)

1. Project root: `EPOS_AAR_{date}.md` (every agent sees it)
2. Context vault: `context_vault/aar/` (searchable, FOTW/TTLG/Friday accessible)
3. Doctrine vault: `context_vault/doctrine/` (if session changed governance docs)

## DOCTOR INTEGRATION

- Check: "Most recent AAR newer than most recent code commit"
- If AAR missing: WARNING with `system.health.aar_missing` event
- Self-Healing queues reminder to Friday

## DIRECTIVE TEMPLATE BLOCK

Include this at the end of every CODE directive:

```
## FINAL MISSION: AFTER ACTION REVIEW

Write an exhaustive AAR with all 9 mandatory sections.
Store at project root AND context_vault/aar/.
This mission takes priority over the previous mission if context limits approach.

Acceptance criteria:
- All 9 sections present
- At least 1 "What Went Wrong" entry
- Ecosystem state delta with specific numbers
- Complete files manifest
- Stored in both required locations
```

---

> *"The organism that reflects on its own development is the organism that compounds."*

*1% daily. 37x annually.*
