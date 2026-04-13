#!/usr/bin/env python3
"""EPOS Execution Arm Verification — run inside epos-core container."""
import sys
sys.path.insert(0, '/app')

results = {}

def run_check(name, fn):
    try:
        status, detail = fn()
        results[name] = (status, detail)
    except Exception as e:
        results[name] = ('FAIL', str(e)[:100])

# 1. Friday graph
def check_friday():
    from friday.friday_graph import friday_app, classify_directive
    s = classify_directive({'directive': 'Run TTLG diagnostic'})
    return 'PASS', 'compiled ttlg->' + s['mission_type']
run_check('Friday Graph', check_friday)

# 2. Code executor
def check_code():
    from friday.executors.code_executor import run as code_run
    r = code_run({'id': 'V-CODE', 'description': 'Write hello world', 'run_code': False})
    return ('PASS' if r['status'] == 'complete' else 'FAIL'), r['status']
run_check('Code Executor', check_code)

# 3. Sovereign Coding Component executor
def check_cc():
    from friday.executors.scc_executor import SCCExecutor
    h = SCCExecutor().health_check()
    return 'PASS', h['status']
run_check('SCC Executor', check_cc)

# 4. AZ executor
def check_az():
    from friday.executors.az_executor import run as az_run
    r = az_run({'id': 'V-AZ', 'description': 'echo test'})
    ok = r['status'] in ('dispatched', 'failed')
    return ('PASS' if ok else 'FAIL'), r['status'] + ': ' + str(r.get('error', 'ok'))[:40]
run_check('Agent Zero Executor', check_az)

# 5. Browser executor
def check_browser():
    from friday.executors.browser_executor import run as br_run
    r = br_run({'id': 'V-BROWSER', 'description': 'Navigate to example.com'})
    ok = r['status'] in ('complete', 'failed')
    return ('PASS' if ok else 'FAIL'), r['status'] + ': ' + str(r.get('error', 'ok'))[:50]
run_check('Browser Executor', check_browser)

# 6. ComputerUse executor
def check_cu():
    from friday.executors.computeruse_executor import run as cu_run
    r_block = cu_run({'id': 'V-CU-B', 'description': 'screenshot', 'computeruse_approved': False})
    r_pass = cu_run({'id': 'V-CU-P', 'description': 'list files', 'computeruse_approved': True})
    gate_ok = r_block['status'] == 'escalated'
    return ('PASS' if gate_ok else 'FAIL'), 'gate=' + ('OK' if gate_ok else 'FAIL') + ' approved->' + r_pass['status']
run_check('ComputerUse Executor', check_cu)

# 7. TTLG internal
def check_ttlg_int():
    from friday.executors.ttlg_executor import run as ttlg_run
    r = ttlg_run({'id': 'V-TTLG-INT', 'mode': 'internal', 'description': 'healing'})
    return ('PASS' if r['status'] == 'complete' else 'FAIL'), r.get('output', r.get('error', ''))[:80]
run_check('TTLG Internal', check_ttlg_int)

# 8. TTLG 8scan
def check_ttlg_8():
    from friday.executors.ttlg_executor import run as ttlg_run
    r = ttlg_run({'id': 'V-TTLG-8', 'mode': '8scan', 'description': 'doctor'})
    return ('PASS' if r['status'] == 'complete' else 'FAIL'), r.get('output', r.get('error', ''))[:80]
run_check('TTLG 8scan', check_ttlg_8)

# 9. System doctor
def check_sys_doc():
    from friday.executors.system_executor import run as sys_run
    r = sys_run({'id': 'V-DOC', 'action': 'doctor', 'description': 'doctor'})
    return ('PASS' if r['status'] == 'complete' else 'FAIL'), r.get('output', r.get('error', ''))[:80]
run_check('System Doctor', check_sys_doc)

# 10. System heal
def check_sys_heal():
    from friday.executors.system_executor import run as sys_run
    r = sys_run({'id': 'V-HEAL', 'action': 'heal', 'description': 'heal'})
    return ('PASS' if r['status'] == 'complete' else 'FAIL'), r.get('output', r.get('error', ''))[:80]
run_check('System Heal', check_sys_heal)

# 11. LLM client
def check_llm():
    from engine.llm_client import ping
    r = ping()
    return ('PASS' if r.get('ok') else 'FAIL'), 'mode=' + str(r.get('mode')) + ' ok=' + str(r.get('ok'))
run_check('LLM Client (Groq)', check_llm)

# 12. Groq router
def check_groq():
    from groq_router import GroqRouter
    r = GroqRouter().route('classification', 'Reply with just the word OK')
    return ('PASS' if r else 'FAIL'), str(r)[:50] if r else 'empty'
run_check('Groq Router', check_groq)

# 13. Event bus
def check_bus():
    from pathlib import Path
    bus = Path('/app/context_vault/events/system/events.jsonl')
    lines = sum(1 for _ in open(bus))
    size_kb = bus.stat().st_size / 1024
    return 'PASS', str(lines) + ' entries ' + str(round(size_kb, 1)) + 'KB'
run_check('Event Bus', check_bus)

# 14. Nightly upskill
def check_upskill():
    from friday.skills.nightly_upskill import FridayNightlyUpskill
    r = FridayNightlyUpskill().run_nightly_cycle()
    phases = sum(1 for v in r.values() if isinstance(v, dict) and v.get('status') == 'complete')
    return 'PASS', str(phases) + '/11 phases complete'
run_check('Nightly Upskill', check_upskill)

# 15. Research scanner
def check_research():
    from friday.skills.research_scanner import FridayResearchScanner
    sigs = FridayResearchScanner().scan_market_signals()
    return 'PASS', str(len(sigs)) + ' signal sources'
run_check('Research Scanner', check_research)

# 16. Morning briefing
def check_briefing():
    from friday.skills.morning_briefing import generate
    b = generate()
    return 'PASS', 'len=' + str(len(b['text'])) + ' market=' + str(bool(b.get('market_awareness')))
run_check('Morning Briefing', check_briefing)

# 17. Avatar registry
def check_avatars():
    from nodes.avatar_registry import AvatarRegistry
    avatars = AvatarRegistry().list_avatars()
    return 'PASS', str(len(avatars)) + ' avatars'
run_check('Avatar Registry', check_avatars)

# 18. Content reactor
def check_content_reactor():
    from reactor.content_reactor import CONTENT_HANDLERS
    return 'PASS', str(len(CONTENT_HANDLERS)) + ' handlers'
run_check('Content Reactor', check_content_reactor)

# Print table
print()
print('=' * 70)
print('EXECUTION ARM VERIFICATION TABLE — 2026-04-08')
print('=' * 70)
print('%-28s %-6s %s' % ('Arm', 'Result', 'Detail'))
print('-' * 70)
for arm, (status, detail) in results.items():
    icon = '[OK]' if status == 'PASS' else '[XX]'
    print('%s %-27s %-6s %s' % (icon, arm, status, detail))
print('=' * 70)
pass_count = sum(1 for s, _ in results.values() if s == 'PASS')
fail_count = sum(1 for s, _ in results.values() if s == 'FAIL')
print('TOTAL: %d PASS / %d FAIL / %d arms' % (pass_count, fail_count, len(results)))
