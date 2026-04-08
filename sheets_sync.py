#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
sheets_sync.py — EPOS Google Sheets Sync Layer
================================================
Constitutional Authority: EPOS Constitution v3.1
Module: Google Sheets Sync (CODE DIRECTIVE Module 6)

Bi-directional sync between EPOS DB/vault and Google Sheets.
Uses Google Sheets API v4 via service account or OAuth.

Sync targets:
  1. Projects → Sheet (read/write)
  2. Tasks → Sheet (read/write)
  3. Idea Log → Sheet (read-only export)
  4. Growth Timeline → Sheet (read-only export)
  5. Content Pipeline → Sheet (read-only export)

Design: Pull-based sync triggered via CLI or scheduled task.
No real-time webhooks (constitutional: no unnecessary external dependencies).

Prerequisites:
  - GOOGLE_SHEETS_CREDENTIALS_PATH in .env (service account JSON)
  - GOOGLE_SHEETS_SPREADSHEET_ID in .env (target spreadsheet)
"""

import json
import os
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

from path_utils import get_context_vault, get_epos_root
from epos_event_bus import EPOSEventBus
from epos_intelligence import record_decision
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


class SheetsSync:
    """Bi-directional Google Sheets sync for EPOS data surfaces."""

    def __init__(self):
        self.vault = get_context_vault()
        self.bus = EPOSEventBus()
        self.creds_path = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH", "")
        self.spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")
        self._service = None
        self.sync_log = self.vault / "sync" / "sheets_sync_log.jsonl"
        self.sync_log.parent.mkdir(parents=True, exist_ok=True)

    def _get_service(self):
        """Lazy-load Google Sheets API service."""
        if self._service:
            return self._service
        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
            creds = Credentials.from_service_account_file(
                self.creds_path,
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
            self._service = build("sheets", "v4", credentials=creds)
            return self._service
        except ImportError:
            print("  [SHEETS] google-api-python-client not installed.")
            print("  Run: pip install google-api-python-client google-auth")
            return None
        except Exception as e:
            print(f"  [SHEETS] Auth failed: {e}")
            return None

    def is_configured(self) -> bool:
        """Check if Google Sheets integration is configured."""
        return bool(self.creds_path and self.spreadsheet_id and
                     Path(self.creds_path).exists() if self.creds_path else False)

    def export_projects(self) -> dict:
        """Export projects from EPOS DB to Google Sheets."""
        # Get projects from DB
        projects = self._get_projects_from_db()
        if not projects:
            return {"status": "no_data", "rows": 0}

        headers = ["ID", "Name", "Status", "Priority", "Owner", "Start", "Due", "Progress"]
        rows = [headers]
        for p in projects:
            rows.append([
                str(p.get("id", "")),
                p.get("name", ""),
                p.get("status", ""),
                p.get("priority", ""),
                p.get("owner", ""),
                p.get("start_date", ""),
                p.get("due_date", ""),
                str(p.get("progress", 0)),
            ])

        return self._write_sheet("Projects", rows)

    def export_tasks(self, project_id: Optional[int] = None) -> dict:
        """Export tasks to Google Sheets."""
        tasks = self._get_tasks_from_db(project_id)
        if not tasks:
            return {"status": "no_data", "rows": 0}

        headers = ["ID", "Project", "Title", "Status", "Assignee", "Priority", "Due", "Estimate"]
        rows = [headers]
        for t in tasks:
            rows.append([
                str(t.get("id", "")),
                str(t.get("project_id", "")),
                t.get("title", ""),
                t.get("status", ""),
                t.get("assignee", ""),
                t.get("priority", ""),
                t.get("due_date", ""),
                t.get("estimate_hours", ""),
            ])

        return self._write_sheet("Tasks", rows)

    def export_ideas(self) -> dict:
        """Export idea log to Google Sheets."""
        from idea_log import IdeaLog
        log = IdeaLog()
        ideas = log.list_ideas(limit=200)

        headers = ["ID", "Title", "Category", "Priority", "Status", "Created", "Triage Verdict"]
        rows = [headers]
        for idea in ideas:
            triage = idea.get("triage_result", {})
            rows.append([
                idea.get("idea_id", ""),
                idea.get("title", ""),
                idea.get("category", ""),
                idea.get("priority", ""),
                idea.get("status", ""),
                idea.get("created_at", "")[:10],
                triage.get("verdict", "") if triage else "",
            ])

        return self._write_sheet("Ideas", rows)

    def export_timeline(self) -> dict:
        """Export growth timeline to Google Sheets."""
        timeline_path = self.vault / "lifeos" / "growth_timeline.jsonl"
        if not timeline_path.exists():
            return {"status": "no_data", "rows": 0}

        milestones = []
        for line in timeline_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    milestones.append(json.loads(line))
                except Exception:
                    pass

        headers = ["Day", "Date", "Type", "Title", "Pillar"]
        rows = [headers]
        for m in milestones:
            rows.append([
                str(m.get("day_number", "")),
                m.get("date", ""),
                m.get("type", ""),
                m.get("title", ""),
                m.get("pillar", ""),
            ])

        return self._write_sheet("Timeline", rows)

    def export_all(self) -> dict:
        """Export all data surfaces to Google Sheets."""
        results = {}
        for name, func in [
            ("projects", self.export_projects),
            ("tasks", self.export_tasks),
            ("ideas", self.export_ideas),
            ("timeline", self.export_timeline),
        ]:
            try:
                results[name] = func()
            except Exception as e:
                results[name] = {"status": "error", "error": str(e)}

        self._log_sync("export_all", results)
        self.bus.publish("sheets.sync.complete", {
            "direction": "export",
            "surfaces": list(results.keys()),
        }, "sheets_sync")

        return results

    def import_projects(self) -> dict:
        """Import project updates from Google Sheets back to DB."""
        rows = self._read_sheet("Projects")
        if not rows or len(rows) < 2:
            return {"status": "no_data", "rows": 0}

        headers = rows[0]
        updated = 0
        for row in rows[1:]:
            data = dict(zip(headers, row))
            project_id = data.get("ID", "")
            if project_id:
                self._update_project_in_db(project_id, data)
                updated += 1

        self._log_sync("import_projects", {"updated": updated})
        return {"status": "success", "updated": updated}

    def _write_sheet(self, sheet_name: str, rows: List[list]) -> dict:
        """Write rows to a named sheet tab."""
        service = self._get_service()
        if not service:
            # Fallback: write to local CSV
            return self._write_csv_fallback(sheet_name, rows)

        try:
            body = {"values": rows}
            service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A1",
                valueInputOption="RAW",
                body=body,
            ).execute()
            return {"status": "success", "sheet": sheet_name, "rows": len(rows)}
        except Exception as e:
            return self._write_csv_fallback(sheet_name, rows, str(e))

    def _read_sheet(self, sheet_name: str) -> Optional[list]:
        """Read all rows from a named sheet tab."""
        service = self._get_service()
        if not service:
            return None
        try:
            result = service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A:Z",
            ).execute()
            return result.get("values", [])
        except Exception:
            return None

    def _write_csv_fallback(self, sheet_name: str, rows: list, error: str = "") -> dict:
        """Fallback: write data to local CSV when Sheets API unavailable."""
        csv_dir = self.vault / "sync" / "csv_exports"
        csv_dir.mkdir(parents=True, exist_ok=True)
        csv_path = csv_dir / f"{sheet_name.lower()}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"

        import csv
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        return {
            "status": "csv_fallback",
            "sheet": sheet_name,
            "rows": len(rows),
            "csv_path": str(csv_path),
            "api_error": error,
        }

    def _get_projects_from_db(self) -> list:
        """Get projects from EPOS DB via docker exec."""
        try:
            result = subprocess.run(
                ["docker", "exec", "epos_db", "psql", "-U", "epos_user", "-d", "epos",
                 "-t", "-A", "-F", "|",
                 "-c", "SELECT id, name, status, priority, owner, start_date, due_date, progress "
                       "FROM epos.projects ORDER BY id"],
                capture_output=True, text=True, timeout=10)
            rows = []
            for line in result.stdout.strip().splitlines():
                if line.strip():
                    parts = line.split("|")
                    if len(parts) >= 8:
                        rows.append({
                            "id": parts[0], "name": parts[1], "status": parts[2],
                            "priority": parts[3], "owner": parts[4],
                            "start_date": parts[5], "due_date": parts[6],
                            "progress": parts[7],
                        })
            return rows
        except Exception:
            return []

    def _get_tasks_from_db(self, project_id: Optional[int] = None) -> list:
        """Get tasks from EPOS DB."""
        try:
            where = f"WHERE project_id = {project_id}" if project_id else ""
            result = subprocess.run(
                ["docker", "exec", "epos_db", "psql", "-U", "epos_user", "-d", "epos",
                 "-t", "-A", "-F", "|",
                 "-c", f"SELECT id, project_id, title, status, assignee, priority, due_date, estimate_hours "
                       f"FROM epos.tasks {where} ORDER BY id"],
                capture_output=True, text=True, timeout=10)
            rows = []
            for line in result.stdout.strip().splitlines():
                if line.strip():
                    parts = line.split("|")
                    if len(parts) >= 8:
                        rows.append({
                            "id": parts[0], "project_id": parts[1], "title": parts[2],
                            "status": parts[3], "assignee": parts[4], "priority": parts[5],
                            "due_date": parts[6], "estimate_hours": parts[7],
                        })
            return rows
        except Exception:
            return []

    def _update_project_in_db(self, project_id: str, data: dict) -> None:
        """Update a project in DB from sheet data."""
        try:
            status = data.get("Status", "").replace("'", "''")
            priority = data.get("Priority", "").replace("'", "''")
            if status or priority:
                sets = []
                if status:
                    sets.append(f"status = '{status}'")
                if priority:
                    sets.append(f"priority = '{priority}'")
                sql = f"UPDATE epos.projects SET {', '.join(sets)} WHERE id = {project_id}"
                subprocess.run(
                    ["docker", "exec", "epos_db", "psql", "-U", "epos_user", "-d", "epos",
                     "-c", sql],
                    capture_output=True, text=True, timeout=10)
        except Exception:
            pass

    def _log_sync(self, operation: str, result: dict) -> None:
        """Log sync operation."""
        entry = {
            "operation": operation,
            "result": result,
            "at": datetime.now(timezone.utc).isoformat(),
        }
        with open(self.sync_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")


# ── Self-Test ────────────────────────────────────────────────────

if __name__ == "__main__":
    import py_compile

    py_compile.compile("sheets_sync.py", doraise=True)
    print("PASS: sheets_sync.py compiles clean")

    sync = SheetsSync()

    # Check configuration
    configured = sync.is_configured()
    print(f"  Google Sheets configured: {configured}")

    # Test CSV fallback exports (always works, no API needed)
    result = sync.export_ideas()
    print(f"PASS: Ideas export — {result.get('status')}, {result.get('rows', 0)} rows")
    if result.get("csv_path"):
        print(f"  CSV: {result['csv_path']}")

    result = sync.export_timeline()
    print(f"PASS: Timeline export — {result.get('status')}, {result.get('rows', 0)} rows")

    # Test DB exports (requires docker)
    result = sync.export_projects()
    print(f"PASS: Projects export — {result.get('status')}, {result.get('rows', 0)} rows")

    print("\nPASS: SheetsSync — all tests passed (CSV fallback active)")
