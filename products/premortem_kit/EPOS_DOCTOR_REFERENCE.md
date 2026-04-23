# EPOS Doctor — Reference Guide

## The enforcement layer for the Pre-Mortem Framework

---

## What the Doctor does

`epos_doctor.py` is a runnable script that checks a codebase against
the rules laid down in the five constitutional documents. It refuses to
return a "green" verdict if any of the following are true:

- A Path Clarity Rule is violated (e.g. code mixes Windows and POSIX
  paths, or hard-codes an absolute path outside of configuration).
- A hard-boundary from the Constitution is violated (e.g. a file writes
  outside the project root, or an agent attempts an operation outside
  its capability scope).
- A Failure Scenario signature is present (e.g. silent file I/O, stub
  code masquerading as implementation, "status lies" — reporting success
  when the operation didn't actually succeed).
- The Environment Spec contract is broken (e.g. code requires an
  environment variable that isn't declared in the spec).

## When to run it

**Always before a deploy.** That's the minimum.

Other high-value moments:
- After a large refactor
- Before merging a feature branch into main
- When onboarding a new contributor (they run the Doctor on their
  first PR to see if the environment is set up right)
- Periodically (weekly) — the Doctor catches drift

## How to invoke

The script ships in the main EPOS codebase. A stripped-down reference
version is included with this kit.

### Full scan

```bash
python3 epos_doctor.py
```

Returns:
- `doctor: green` — no violations, safe to proceed
- `doctor: yellow` — non-blocking warnings; review before proceeding
- `doctor: red` — blocking violations; do not proceed until fixed

### Scoped scan

```bash
python3 epos_doctor.py --scope engine/
python3 epos_doctor.py --scope recent       # only files changed since last commit
python3 epos_doctor.py --check path_clarity # only the Path Clarity Rule checks
```

### Pre-commit hook

Install as a pre-commit hook:

```bash
cp epos_doctor.py .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

Every commit now runs the Doctor. A red verdict aborts the commit.

## What the Doctor checks (default check-set)

| Check | Rule source | What it catches |
|---|---|---|
| `path_clarity.no_mixed_separators` | Doc 03 | Windows `C:\` paths mixed with POSIX `/` paths in the same file |
| `path_clarity.no_hardcoded_absolute` | Doc 03 | Absolute paths hard-coded outside configuration |
| `path_clarity.wsl_canonical` | Doc 03 + Article XIV | Paths that aren't WSL-canonical when WSL discipline applies |
| `failure.status_lies` | Doc 02 | Code that reports "success" without actually verifying |
| `failure.silent_io` | Doc 02 | File-I/O operations wrapped in bare `except: pass` |
| `failure.stub_code` | Doc 02 | Functions that return placeholder values (`TODO`, `NotImplemented`, `pass`) in code claimed operational |
| `env.required_vars_declared` | Doc 05 | `os.getenv` calls for vars not declared in Environment Spec |
| `env.no_drive_letters` | Doc 05 + Article XIV | Drive letters (`C:/`, `D:/`) in code (not docstrings) |
| `constitution.write_scope` | Doc 01 Article II | Writes attempted outside project root |
| `constitution.no_delete_without_gate` | Doc 01 Article V | Deletions not passing through a deletion gate |

## How to extend the Doctor

The Doctor is designed for extension. Add your own check in three steps:

### Step 1 — Write a checker function

```python
# my_checks.py
def check_no_print_in_library(path: str, src: str) -> list[dict]:
    """Return a list of violations (one dict per violation)."""
    violations = []
    for i, line in enumerate(src.splitlines(), 1):
        if "print(" in line and "lib/" in path:
            violations.append({
                "rule": "no_print_in_library",
                "severity": "yellow",
                "file": path, "line": i,
                "message": "print() in library code — use logger instead",
            })
    return violations
```

### Step 2 — Register with the Doctor

```python
# in epos_doctor.py or a plugin:
from my_checks import check_no_print_in_library
DOCTOR.register(check_no_print_in_library)
```

### Step 3 — Run

```bash
python3 epos_doctor.py --check no_print_in_library
```

## Reading the verdict

```
[doctor] scanning 47 files in engine/
[doctor] check path_clarity.no_mixed_separators  ... green
[doctor] check failure.status_lies               ... yellow (2)
  - engine/foo.py:145  — return {"status": "ok"} with no verification
  - engine/bar.py:12   — print("success") inside except: pass
[doctor] check failure.silent_io                 ... red (1)
  - engine/baz.py:89   — try: write(); except: pass

doctor: red
```

Green = go. Yellow = review. Red = stop.

## What the Doctor does NOT do

- It doesn't run your tests. Run those separately (`pytest`, `go test`,
  etc.). Doctor is for constitutional rules; tests are for behavior.
- It doesn't catch business-logic bugs. "The total is wrong" is not
  detectable by static analysis; only behavior tests catch that.
- It doesn't replace code review. It makes code review more productive
  by catching the mechanical issues before a human looks.

## The compound effect, again

Every rule the Doctor enforces is a failure class you can't repeat.
Add one rule a month. In a year, you have 12 entire categories of
failures the system prevents automatically. That's what makes the
framework compound.

---

*See `constitutional/02_Failure_Scenarios.md` for the catalog of
failure patterns the Doctor's default checks cover.*
