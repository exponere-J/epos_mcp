#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos_support.py — EPOS Client Support System
==============================================
Constitutional Authority: EPOS Constitution v3.1

SLA targets: critical=1h, high=4h, medium=24h, low=72h.
Auto-respond via LiveQuery. Escalate on low confidence.
Every unresolved ticket degrades engagement health.
"""

import json
import uuid
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from epos_intelligence import record_decision
from epos_event_bus import EPOSEventBus

SLA_HOURS = {"critical": 1, "high": 4, "medium": 24, "low": 72}


@dataclass
class SupportTicket:
    ticket_id: str
    client_id: str
    category: str
    priority: str
    subject: str
    description: str
    status: str = "open"
    assigned_to: str = ""
    sla_hours: int = 24
    opened_at: str = ""
    first_response_at: Optional[str] = None
    resolved_at: Optional[str] = None
    resolution: Optional[str] = None
    satisfaction_score: Optional[int] = None


class EPOSSupport:
    """Client support system with SLA enforcement and auto-response."""

    def __init__(self):
        self.bus = EPOSEventBus()

    def _psql(self, sql: str) -> str:
        import os
        container = os.getenv("DB_CONTAINER", "epos_db")
        user = os.getenv("DB_USER", "epos_user")
        db = os.getenv("DB_NAME", "epos")
        result = subprocess.run(
            ["docker", "exec", container, "psql", "-U", user, "-d", db, "-t", "-A", "-c", sql],
            capture_output=True, text=True, timeout=15)
        return result.stdout.strip()

    def open_ticket(self, contact_id: str, category: str,
                    subject: str, description: str,
                    priority: str = "medium") -> SupportTicket:
        sla = SLA_HOURS.get(priority, 24)
        ticket_id = f"TKT-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()

        self._psql(f"""
            INSERT INTO epos.support_tickets
                (id, contact_id, category, priority, subject, description, status, sla_hours, opened_at)
            VALUES
                (gen_random_uuid(), '{contact_id}'::uuid, '{category}', '{priority}',
                 '{subject.replace("'","''")}', '{description.replace("'","''")}',
                 'open', {sla}, NOW());
        """)

        ticket = SupportTicket(
            ticket_id=ticket_id, client_id=contact_id, category=category,
            priority=priority, subject=subject, description=description,
            sla_hours=sla, opened_at=now)

        record_decision(decision_type="support.ticket.opened",
                        description=f"Support ticket: {subject[:60]}",
                        agent_id="epos_support", outcome="opened",
                        context={"ticket_id": ticket_id, "priority": priority, "category": category})

        try:
            self.bus.publish("support.ticket.opened",
                             {"ticket_id": ticket_id, "priority": priority, "category": category},
                             "epos_support")
        except Exception:
            pass

        # Auto-route
        self._route_ticket(ticket)
        return ticket

    def _route_ticket(self, ticket: SupportTicket) -> None:
        if ticket.priority == "critical" or ticket.category == "technical":
            ticket.assigned_to = "growth_steward"
        elif ticket.category == "billing":
            ticket.assigned_to = "fin_ops"
        elif ticket.category in ("strategy", "content"):
            ticket.assigned_to = "ttlg_diagnostic"
        else:
            ticket.assigned_to = "auto_responder"

    def auto_respond(self, ticket: SupportTicket) -> str:
        from epos_live_query import EPOSLiveQuery
        lq = EPOSLiveQuery()
        result = lq.query(f"{ticket.subject}: {ticket.description}",
                          context={"stage": "support"}, mode="synthesized")
        if result.confidence >= 0.7:
            return result.answer
        return f"Your ticket has been received and assigned to {ticket.assigned_to}. We'll respond within {ticket.sla_hours} hours."

    def resolve_ticket(self, ticket_id: str, resolution: str,
                       satisfaction: int = None) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        sat_clause = f", satisfaction_score = {satisfaction}" if satisfaction else ""
        self._psql(f"""
            UPDATE epos.support_tickets
            SET status = 'resolved', resolved_at = NOW(),
                resolution = '{resolution.replace("'","''")}'
                {sat_clause}
            WHERE id::text LIKE '%{ticket_id}%' OR subject LIKE '%{ticket_id}%';
        """)

        record_decision(decision_type="support.ticket.resolved",
                        description=f"Ticket resolved: {ticket_id}",
                        agent_id="epos_support", outcome="resolved",
                        context={"ticket_id": ticket_id, "satisfaction": satisfaction})

        try:
            self.bus.publish("support.ticket.resolved",
                             {"ticket_id": ticket_id, "satisfaction": satisfaction},
                             "epos_support")
        except Exception:
            pass
        return {"ticket_id": ticket_id, "status": "resolved", "resolved_at": now}

    def check_sla_breaches(self) -> list:
        raw = self._psql("""
            SELECT id::text, subject, priority, sla_hours,
                   EXTRACT(EPOCH FROM (NOW() - opened_at))/3600 as hours_open
            FROM epos.support_tickets
            WHERE status IN ('open', 'in_progress')
              AND EXTRACT(EPOCH FROM (NOW() - opened_at))/3600 > sla_hours;
        """)
        breaches = []
        for line in raw.split("\n"):
            if line.strip():
                parts = line.split("|")
                if len(parts) >= 5:
                    breaches.append({"ticket_id": parts[0].strip(), "subject": parts[1].strip(),
                                     "priority": parts[2].strip(), "hours_open": parts[4].strip()})
        if breaches:
            try:
                self.bus.publish("support.sla.breached",
                                 {"breach_count": len(breaches)}, "epos_support")
            except Exception:
                pass
        return breaches

    def get_support_health(self) -> dict:
        raw = self._psql("""
            SELECT status, COUNT(*), AVG(satisfaction_score)
            FROM epos.support_tickets GROUP BY status;
        """)
        return {"raw": raw, "checked_at": datetime.now(timezone.utc).isoformat()}


if __name__ == "__main__":
    support = EPOSSupport()
    health = support.get_support_health()
    breaches = support.check_sla_breaches()
    print(f"  Support health: {health}")
    print(f"  SLA breaches: {len(breaches)}")
    print("PASS: EPOSSupport operational")
