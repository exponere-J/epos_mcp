#!/usr/bin/env python3
"""
life_os_cli.py — EPOS LifeOS Command Line Interface
=====================================================
Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles II, VIII
Mission ID: LIFEOS-CLI-001
File Location: C:/Users/Jamie/workspace/epos_mcp/life_os_cli.py

Commands:
    python life_os_cli.py projects           — Dashboard of all projects
    python life_os_cli.py project <name>     — Tasks for a project grouped by status
    python life_os_cli.py gate <name>        — Blocked tasks for a project
    python life_os_cli.py update <id> <stat> — Update a task's status
    python life_os_cli.py log <project>      — Find and show AAR for a project
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# ── Environment ──────────────────────────────────────────────────
load_dotenv(Path(__file__).resolve().parent / ".env")

DB_CONTAINER = os.getenv("DB_CONTAINER", "epos_db")
DB_USER = os.getenv("DB_USER", "epos_user")
DB_NAME = os.getenv("DB_NAME", "epos")

VALID_STATUSES = {"backlog", "todo", "in_progress", "blocked", "review", "done", "cancelled"}


# ── DB Helper ────────────────────────────────────────────────────

def db_query(sql: str) -> list[dict]:
    """Execute SQL via docker exec and return rows as list of dicts."""
    cmd = [
        "docker", "exec", DB_CONTAINER,
        "psql", "-U", DB_USER, "-d", DB_NAME,
        "-t", "-A", "-F", "\t",
        "-c", sql,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            print(f"DB ERROR: {result.stderr.strip()}")
            sys.exit(1)
        return result.stdout.strip()
    except FileNotFoundError:
        print("ERROR: docker not found. Is Docker Desktop running?")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("ERROR: DB query timed out (15s)")
        sys.exit(1)


def db_query_rows(sql: str, columns: list[str]) -> list[dict]:
    """Execute SQL and parse into list of dicts using provided column names."""
    raw = db_query(sql)
    if not raw:
        return []
    rows = []
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        row = {}
        for i, col in enumerate(columns):
            row[col] = parts[i] if i < len(parts) else ""
        rows.append(row)
    return rows


# ── Table Printer ────────────────────────────────────────────────

def print_table(rows: list[dict], columns: list[str], headers: list[str] = None):
    """Print rows as a formatted table."""
    if not rows:
        print("  (no data)")
        return
    headers = headers or columns
    widths = [len(h) for h in headers]
    for row in rows:
        for i, col in enumerate(columns):
            widths[i] = max(widths[i], len(str(row.get(col, ""))))

    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*["-" * w for w in widths]))
    for row in rows:
        vals = [str(row.get(col, "")) for col in columns]
        print(fmt.format(*vals))


# ── Commands ─────────────────────────────────────────────────────

def cmd_projects():
    """Dashboard of all projects."""
    sql = """
        SELECT p.name, p.status::text, p.priority::text,
               COUNT(t.id) as total,
               COUNT(t.id) FILTER (WHERE t.status='done') as done,
               COUNT(t.id) FILTER (WHERE t.status='in_progress') as active,
               COUNT(t.id) FILTER (WHERE t.status='blocked') as blocked,
               COUNT(t.id) FILTER (WHERE t.status='backlog') as backlog
        FROM epos.projects p
        LEFT JOIN epos.tasks t ON t.project_id = p.id
        GROUP BY p.name, p.status, p.priority
        ORDER BY p.priority DESC, p.name;
    """
    cols = ["name", "status", "priority", "total", "done", "active", "blocked", "backlog"]
    rows = db_query_rows(sql, cols)
    print("\n EPOS Projects Dashboard")
    print("=" * 70)
    print_table(rows, cols, ["Project", "Status", "Priority", "Total", "Done", "Active", "Blocked", "Backlog"])
    print()


def cmd_project(name: str):
    """Show tasks for a project grouped by status."""
    sql = f"""
        SELECT t.id::text, t.tags[1] as layer, t.title, t.owner, t.status::text
        FROM epos.tasks t
        JOIN epos.projects p ON p.id = t.project_id
        WHERE LOWER(p.name) = LOWER('{name}')
        ORDER BY
            CASE t.status
                WHEN 'in_progress' THEN 1
                WHEN 'blocked' THEN 2
                WHEN 'todo' THEN 3
                WHEN 'review' THEN 4
                WHEN 'backlog' THEN 5
                WHEN 'done' THEN 6
                WHEN 'cancelled' THEN 7
            END,
            t.priority DESC, t.title;
    """
    cols = ["id", "layer", "title", "owner", "status"]
    rows = db_query_rows(sql, cols)

    if not rows:
        print(f"\nNo tasks found for project '{name}'")
        return

    # Shorten UUIDs
    for r in rows:
        r["id"] = r["id"][:8]

    # Group by status
    print(f"\n Project: {name}")
    print("=" * 80)

    current_status = None
    status_count = {}
    for r in rows:
        s = r["status"]
        status_count[s] = status_count.get(s, 0) + 1

    for r in rows:
        if r["status"] != current_status:
            current_status = r["status"]
            count = status_count[current_status]
            print(f"\n  [{current_status.upper()}] ({count})")
            print(f"  {'ID':<10} {'Layer':<14} {'Title':<42} {'Owner':<12}")
            print(f"  {'-'*10} {'-'*14} {'-'*42} {'-'*12}")
        print(f"  {r['id']:<10} {r['layer']:<14} {r['title'][:42]:<42} {r['owner']:<12}")

    print(f"\n  Total: {len(rows)} tasks")
    for s, c in status_count.items():
        print(f"    {s}: {c}")
    print()


def cmd_gate(name: str):
    """Show blocked tasks for a project."""
    sql = f"""
        SELECT t.id::text, t.title, t.owner, t.tags::text
        FROM epos.tasks t
        JOIN epos.projects p ON p.id = t.project_id
        WHERE LOWER(p.name) = LOWER('{name}')
          AND t.status = 'blocked'
        ORDER BY t.priority DESC, t.title;
    """
    cols = ["id", "title", "owner", "tags"]
    rows = db_query_rows(sql, cols)

    if not rows:
        print(f"\n Gate clear — no blocked tasks for {name}")
        return

    print(f"\n BLOCKED tasks for {name}")
    print("=" * 70)
    for r in rows:
        r["id"] = r["id"][:8]
    print_table(rows, cols, ["ID", "Title", "Owner", "Tags"])
    print()


def cmd_update(task_id_prefix: str, status: str):
    """Update a task's status."""
    if status not in VALID_STATUSES:
        print(f"ERROR: Invalid status '{status}'. Must be one of: {', '.join(sorted(VALID_STATUSES))}")
        sys.exit(1)

    # Find and update
    sql = f"""
        UPDATE epos.tasks
        SET status = '{status}'::epos.task_status, updated_at = now()
        WHERE id::text LIKE '{task_id_prefix}%'
        RETURNING title, status::text;
    """
    raw = db_query(sql)
    if not raw:
        print(f"ERROR: No task found matching prefix '{task_id_prefix}'")
        sys.exit(1)

    parts = raw.split("\t")
    title = parts[0] if parts else "unknown"
    print(f"Updated: {title} -> {status}")


def cmd_log(project: str):
    """Find and show AAR for a project."""
    epos_root = Path(__file__).resolve().parent
    search_dirs = [
        epos_root,
        epos_root / "context_vault" / "bi_history",
    ]

    found_files = []
    for d in search_dirs:
        if d.exists():
            for f in d.rglob("*AAR*"):
                if f.is_file():
                    try:
                        content = f.read_text(encoding="utf-8", errors="ignore").lower()
                        if project.lower() in content or project.lower() in f.name.lower():
                            found_files.append(f)
                    except Exception:
                        pass

    if not found_files:
        print(f"\nNo AAR found for '{project}'. Location when created:")
        print(f"  {epos_root}/")
        return

    # Show most recent
    found_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    target = found_files[0]
    print(f"\n AAR: {target.name}")
    print(f"  Path: {target}")
    print("=" * 70)

    lines = target.read_text(encoding="utf-8", errors="ignore").splitlines()
    for line in lines[-50:]:
        print(line)
    print()


# ── Main ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="EPOS LifeOS CLI — Project and Task Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("projects", help="Dashboard of all projects")

    p_proj = sub.add_parser("project", help="Tasks for a project")
    p_proj.add_argument("name", help="Project name")

    p_gate = sub.add_parser("gate", help="Blocked tasks for a project")
    p_gate.add_argument("name", help="Project name")

    p_upd = sub.add_parser("update", help="Update task status")
    p_upd.add_argument("task_id", help="Task ID prefix (first 8 chars)")
    p_upd.add_argument("status", help="New status", choices=sorted(VALID_STATUSES))

    p_log = sub.add_parser("log", help="Show AAR for a project")
    p_log.add_argument("project", help="Project name")

    args = parser.parse_args()

    if args.command == "projects":
        cmd_projects()
    elif args.command == "project":
        cmd_project(args.name)
    elif args.command == "gate":
        cmd_gate(args.name)
    elif args.command == "update":
        cmd_update(args.task_id, args.status)
    elif args.command == "log":
        cmd_log(args.project)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
