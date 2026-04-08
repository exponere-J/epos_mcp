#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos_financial.py — EPOS Financial Operations
================================================
Constitutional Authority: EPOS Constitution v3.1

Billing, invoicing, payment tracking, revenue recognition.
Constitutional pricing: never sell below 1.3x cost.
"""

import json
import uuid
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta, date
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from epos_intelligence import record_decision
from epos_event_bus import EPOSEventBus

PRICING_CONSTITUTION = {
    "margin_floor": 1.3,
    "bundle_discount_max": 0.30,
    "enterprise_minimum": 2997,
    "payment_terms_default": "net_30",
    "trial_period_days": 14,
    "late_fee_pct": 0.015,
}


@dataclass
class Invoice:
    invoice_id: str
    client_id: str
    line_items: list
    subtotal: float
    discount: float
    tax: float
    total: float
    status: str = "draft"
    due_date: str = ""
    issued_at: str = ""
    paid_at: Optional[str] = None
    payment_method: Optional[str] = None


class EPOSFinancialOps:
    """Billing, invoicing, and constitutional pricing enforcement."""

    def __init__(self):
        self.bus = EPOSEventBus()

    def _psql(self, sql: str) -> str:
        import os
        result = subprocess.run(
            ["docker", "exec", os.getenv("DB_CONTAINER", "epos_db"),
             "psql", "-U", os.getenv("DB_USER", "epos_user"),
             "-d", os.getenv("DB_NAME", "epos"), "-t", "-A", "-c", sql],
            capture_output=True, text=True, timeout=15)
        return result.stdout.strip()

    def enforce_pricing_constitution(self, proposed_price: float, cost: float) -> dict:
        """Block any price below 1.3x cost."""
        floor = cost * PRICING_CONSTITUTION["margin_floor"]
        if proposed_price < floor:
            return {"valid": False, "corrected_price": floor,
                    "reason": f"Price {proposed_price} below margin floor {floor:.2f} (1.3x cost {cost})"}
        return {"valid": True, "corrected_price": proposed_price, "reason": "within constitution"}

    def generate_invoice(self, client_id: str, line_items: list,
                         discount_pct: float = 0, tax_pct: float = 0) -> Invoice:
        """Generate constitutionally valid invoice."""
        subtotal = sum(item.get("total", item.get("unit_price", 0) * item.get("quantity", 1))
                       for item in line_items)

        # Enforce discount cap
        actual_discount = min(discount_pct, PRICING_CONSTITUTION["bundle_discount_max"])
        discount = subtotal * actual_discount
        taxable = subtotal - discount
        tax = taxable * tax_pct
        total = taxable + tax

        # Enforce margin floor on each line item
        for item in line_items:
            cost = item.get("cost", 0)
            if cost > 0:
                check = self.enforce_pricing_constitution(item.get("unit_price", 0), cost)
                if not check["valid"]:
                    item["unit_price"] = check["corrected_price"]
                    item["margin_corrected"] = True

        due_date = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")
        invoice_id = f"INV-{datetime.now().strftime('%Y%m')}-{uuid.uuid4().hex[:6]}"

        invoice = Invoice(
            invoice_id=invoice_id, client_id=client_id, line_items=line_items,
            subtotal=round(subtotal, 2), discount=round(discount, 2),
            tax=round(tax, 2), total=round(total, 2),
            due_date=due_date, issued_at=datetime.now(timezone.utc).isoformat())

        # Write to DB
        self._psql(f"""
            INSERT INTO epos.invoices (contact_id, line_items, subtotal, discount, tax, total, status, due_date)
            SELECT id, '{json.dumps(line_items)}'::jsonb, {invoice.subtotal}, {invoice.discount},
                   {invoice.tax}, {invoice.total}, 'draft', '{due_date}'::date
            FROM epos.contacts WHERE id::text LIKE '{client_id}%' OR name LIKE '%{client_id}%' LIMIT 1;
        """)

        record_decision(decision_type="billing.invoice.generated",
                        description=f"Invoice {invoice_id}: ${invoice.total:.2f}",
                        agent_id="fin_ops", outcome="draft",
                        context={"invoice_id": invoice_id, "total": invoice.total})

        try:
            self.bus.publish("billing.invoice.generated",
                             {"invoice_id": invoice_id, "total": invoice.total}, "epos_financial")
        except Exception:
            pass
        return invoice

    def record_payment(self, invoice_id: str, amount: float, method: str = "stripe") -> dict:
        now = datetime.now(timezone.utc).isoformat()
        self._psql(f"""
            UPDATE epos.invoices SET status = 'paid', paid_at = NOW(), payment_method = '{method}'
            WHERE id::text LIKE '%{invoice_id}%';
        """)
        record_decision(decision_type="billing.payment.received",
                        description=f"Payment ${amount:.2f} via {method}",
                        agent_id="fin_ops", outcome="paid",
                        context={"invoice_id": invoice_id, "amount": amount})
        try:
            self.bus.publish("billing.payment.received",
                             {"invoice_id": invoice_id, "amount": amount}, "epos_financial")
        except Exception:
            pass
        return {"invoice_id": invoice_id, "amount": amount, "paid_at": now}

    def check_overdue(self) -> list:
        raw = self._psql("""
            SELECT id::text, total, due_date::text,
                   CURRENT_DATE - due_date as days_overdue
            FROM epos.invoices
            WHERE status NOT IN ('paid', 'cancelled')
              AND due_date < CURRENT_DATE;
        """)
        overdue = []
        for line in raw.split("\n"):
            if "|" in line:
                parts = line.split("|")
                overdue.append({"invoice_id": parts[0].strip(), "total": parts[1].strip(),
                                "due_date": parts[2].strip(), "days_overdue": parts[3].strip()})
        if overdue:
            try:
                self.bus.publish("billing.overdue.flagged",
                                 {"count": len(overdue)}, "epos_financial")
            except Exception:
                pass
        return overdue

    def get_revenue_summary(self) -> dict:
        raw = self._psql("""
            SELECT COALESCE(SUM(total), 0) as total_revenue,
                   COUNT(*) as invoice_count,
                   COUNT(*) FILTER (WHERE status='paid') as paid,
                   COUNT(*) FILTER (WHERE status='draft') as draft,
                   COUNT(*) FILTER (WHERE due_date < CURRENT_DATE AND status NOT IN ('paid','cancelled')) as overdue
            FROM epos.invoices;
        """)
        parts = raw.split("|") if raw else ["0", "0", "0", "0", "0"]
        return {
            "total_revenue": float(parts[0].strip() or 0),
            "invoice_count": int(parts[1].strip() or 0),
            "paid": int(parts[2].strip() or 0),
            "draft": int(parts[3].strip() or 0),
            "overdue": int(parts[4].strip() or 0),
        }


if __name__ == "__main__":
    fin = EPOSFinancialOps()

    # Test constitutional pricing
    check = fin.enforce_pricing_constitution(100, 90)
    assert not check["valid"]  # 100 < 90 * 1.3 = 117
    print(f"  Pricing check: {check}")

    check2 = fin.enforce_pricing_constitution(200, 90)
    assert check2["valid"]
    print(f"  Pricing check 2: {check2}")

    summary = fin.get_revenue_summary()
    print(f"  Revenue summary: {summary}")
    print("PASS: EPOSFinancialOps operational")
