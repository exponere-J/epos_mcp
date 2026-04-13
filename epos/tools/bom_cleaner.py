#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos/tools/bom_cleaner.py — UTF-8 BOM Sentinel
================================================
Constitutional Authority: EPOS Constitution v3.1
Directive: 20260413-03A (Sensory Organ Initialization)

Strips UTF-8 BOM (U+FEFF / b'\\xef\\xbb\\xbf') from all Python files.
BOM characters cause ast.parse() failures on non-first lines —
the silent killer of Windows-originated codebases.

Wired into epos_doctor.py as a standing health check.
"""

from pathlib import Path


def clean_bom(root: str = "/app") -> dict:
    """Strip UTF-8 BOM from all Python files under root.

    Returns:
        {"cleaned": int, "files": [str]}
    """
    cleaned = []
    for py_file in Path(root).rglob("*.py"):
        try:
            content = py_file.read_bytes()
            if content.startswith(b'\xef\xbb\xbf'):
                py_file.write_bytes(content[3:])
                cleaned.append(str(py_file))
        except Exception:
            pass
    return {"cleaned": len(cleaned), "files": cleaned}


def has_bom(file_path: str) -> bool:
    """Return True if file has a UTF-8 BOM prefix."""
    try:
        return Path(file_path).read_bytes().startswith(b'\xef\xbb\xbf')
    except Exception:
        return False


def scan_bom(root: str = "/app") -> dict:
    """Scan for BOM-infected files without modifying them.

    Returns:
        {"infected": int, "files": [str]}
    """
    infected = []
    for py_file in Path(root).rglob("*.py"):
        try:
            if py_file.read_bytes().startswith(b'\xef\xbb\xbf'):
                infected.append(str(py_file))
        except Exception:
            pass
    return {"infected": len(infected), "files": infected}


if __name__ == "__main__":
    import sys
    root = sys.argv[1] if len(sys.argv) > 1 else "/app"
    result = clean_bom(root)
    print(f"BOM Cleaner: {result['cleaned']} files cleaned")
    for f in result["files"]:
        print(f"  stripped: {f}")
