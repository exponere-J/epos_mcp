# REJECTION RECEIPT: epos_intelligence.py

**Generated:** 2026-02-19T07:25:55.353968
**Constitutional Authority:** EPOS_CONSTITUTION_v3.1.md

---

## Violations

### ERR-ENTRYPOINT-001

**Article:** II.3
**Severity:** CRITICAL
**Description:** Entrypoint does not call epos_doctor.py pre-flight check

**Required Fix:**
```
Add pre-flight validation: from engine.epos_doctor import EPOSDoctor; EPOSDoctor().run()
```

---

## Next Steps

1. Review the violations above
2. Fix each issue in your code
3. Re-submit to `inbox/`
4. Run `python governance_gate.py` to re-validate

## Resources

- `EPOS_CONSTITUTION_v3.1.md` - Full constitutional rules
- `PATH_CLARITY_RULES.md` - Path handling specification
- `PRE_FLIGHT_CHECKLIST.md` - Validation checklist
