#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
payment_gateway.py — EPOS Payment Gateway (Stripe Integration)
================================================================
Constitutional Authority: EPOS Constitution v3.1
Sovereign Node — Payment Links, Webhooks, Revenue Tracking

Bridges Stripe to EPOS financial operations:
  - Generate payment links for TTLG engagements and subscriptions
  - Process webhook events (payment_intent.succeeded, invoice.paid)
  - Record all transactions in sovereign vault journal
  - Publish events to EPOS bus for downstream intelligence

Requires: STRIPE_SECRET_KEY in .env
Degrades gracefully: generates invoice stubs without Stripe.
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

try:
    from epos_event_bus import EPOSEventBus
    _BUS = EPOSEventBus()
except Exception:
    _BUS = None

try:
    from epos_intelligence import record_decision
except ImportError:
    def record_decision(**kw): pass


# ── Configuration ───────────────────────────────────────────

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
EPOS_ROOT = Path(os.getenv("EPOS_ROOT", "C:/Users/Jamie/workspace/epos_mcp"))
PAYMENT_VAULT = EPOS_ROOT / "context_vault" / "financial" / "payments"

# Service catalog — maps EPOS offerings to Stripe-compatible line items
SERVICE_CATALOG = {
    "ttlg_audit": {
        "name": "TTLG Sovereign Alignment Audit",
        "price": 497_00,  # cents
        "currency": "usd",
        "type": "one_time",
    },
    "ttlg_blueprint": {
        "name": "TTLG Full Blueprint (Layers 1-15)",
        "price": 4997_00,
        "currency": "usd",
        "type": "one_time",
    },
    "ttlg_enterprise": {
        "name": "TTLG Enterprise Build (Layers 1-20)",
        "price": 9997_00,
        "currency": "usd",
        "type": "one_time",
    },
    "content_engine_monthly": {
        "name": "Sovereign Content Engine — Monthly",
        "price": 1500_00,
        "currency": "usd",
        "type": "recurring",
        "interval": "month",
    },
    "epos_solo": {
        "name": "EPOS Solo Node Bundle",
        "price": 49_00,
        "currency": "usd",
        "type": "recurring",
        "interval": "month",
    },
    "epos_workflow": {
        "name": "EPOS Workflow Bundle",
        "price": 149_00,
        "currency": "usd",
        "type": "recurring",
        "interval": "month",
    },
    "epos_department": {
        "name": "EPOS Department Bundle",
        "price": 297_00,
        "currency": "usd",
        "type": "recurring",
        "interval": "month",
    },
}


class PaymentGateway:
    """
    Sovereign payment processing node.
    Uses Stripe when available, generates invoice stubs when not.
    """

    def __init__(self, vault_path: Path = None):
        self.vault = vault_path or PAYMENT_VAULT
        self.vault.mkdir(parents=True, exist_ok=True)
        self._stripe = None
        if STRIPE_SECRET_KEY:
            try:
                import stripe
                stripe.api_key = STRIPE_SECRET_KEY
                self._stripe = stripe
            except ImportError:
                pass

    @property
    def stripe_available(self) -> bool:
        return self._stripe is not None

    # ── Payment Link Generation ─────────────────────────────

    def create_payment_link(self, service_id: str, client_id: str,
                            client_email: str = None) -> dict:
        """Create a Stripe payment link or generate a manual invoice stub."""
        service = SERVICE_CATALOG.get(service_id)
        if not service:
            return {"error": f"Unknown service: {service_id}",
                    "available": list(SERVICE_CATALOG.keys())}

        if self.stripe_available:
            return self._create_stripe_link(service, service_id, client_id, client_email)
        else:
            return self._create_invoice_stub(service, service_id, client_id)

    def _create_stripe_link(self, service: dict, service_id: str,
                            client_id: str, email: str = None) -> dict:
        """Create actual Stripe payment link."""
        stripe = self._stripe

        if service["type"] == "one_time":
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": service["currency"],
                        "product_data": {"name": service["name"]},
                        "unit_amount": service["price"],
                    },
                    "quantity": 1,
                }],
                mode="payment",
                customer_email=email,
                metadata={"client_id": client_id, "service_id": service_id},
            )
        else:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": service["currency"],
                        "product_data": {"name": service["name"]},
                        "unit_amount": service["price"],
                        "recurring": {"interval": service["interval"]},
                    },
                    "quantity": 1,
                }],
                mode="subscription",
                customer_email=email,
                metadata={"client_id": client_id, "service_id": service_id},
            )

        result = {
            "payment_url": session.url,
            "session_id": session.id,
            "service_id": service_id,
            "client_id": client_id,
            "amount": service["price"] / 100,
            "currency": service["currency"],
            "type": service["type"],
            "provider": "stripe",
        }

        self._journal_transaction("payment_link.created", result)
        self._publish("payment.link.created", result)
        return result

    def _create_invoice_stub(self, service: dict, service_id: str,
                             client_id: str) -> dict:
        """Generate manual invoice stub when Stripe isn't configured."""
        stub_id = f"STUB-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{hashlib.md5(client_id.encode()).hexdigest()[:6]}"
        result = {
            "stub_id": stub_id,
            "service_id": service_id,
            "service_name": service["name"],
            "client_id": client_id,
            "amount": service["price"] / 100,
            "currency": service["currency"],
            "type": service["type"],
            "provider": "manual",
            "instructions": "Send invoice manually. Configure STRIPE_SECRET_KEY for automated links.",
        }

        self._journal_transaction("invoice_stub.created", result)
        self._publish("payment.stub.created", result)
        return result

    # ── Webhook Processing ──────────────────────────────────

    def process_webhook(self, payload: dict, signature: str = None) -> dict:
        """Process incoming Stripe webhook event."""
        event_type = payload.get("type", "")
        data = payload.get("data", {}).get("object", {})

        if event_type == "checkout.session.completed":
            return self._handle_checkout_complete(data)
        elif event_type == "invoice.paid":
            return self._handle_invoice_paid(data)
        elif event_type == "customer.subscription.created":
            return self._handle_subscription_created(data)
        elif event_type == "payment_intent.succeeded":
            return self._handle_payment_succeeded(data)
        else:
            return {"status": "ignored", "event_type": event_type}

    def _handle_checkout_complete(self, data: dict) -> dict:
        result = {
            "event": "checkout.completed",
            "session_id": data.get("id"),
            "client_id": data.get("metadata", {}).get("client_id"),
            "service_id": data.get("metadata", {}).get("service_id"),
            "amount": data.get("amount_total", 0) / 100,
            "payment_status": data.get("payment_status"),
        }
        self._journal_transaction("payment.received", result)
        self._publish("payment.received", result)
        return result

    def _handle_invoice_paid(self, data: dict) -> dict:
        result = {
            "event": "invoice.paid",
            "invoice_id": data.get("id"),
            "amount": data.get("amount_paid", 0) / 100,
            "customer": data.get("customer"),
        }
        self._journal_transaction("subscription.payment", result)
        self._publish("subscription.payment.received", result)
        return result

    def _handle_subscription_created(self, data: dict) -> dict:
        result = {
            "event": "subscription.created",
            "subscription_id": data.get("id"),
            "customer": data.get("customer"),
            "status": data.get("status"),
        }
        self._journal_transaction("subscription.created", result)
        self._publish("subscription.created", result)
        return result

    def _handle_payment_succeeded(self, data: dict) -> dict:
        result = {
            "event": "payment.succeeded",
            "payment_intent": data.get("id"),
            "amount": data.get("amount", 0) / 100,
        }
        self._journal_transaction("payment.succeeded", result)
        self._publish("payment.succeeded", result)
        return result

    # ── Service Catalog ─────────────────────────────────────

    def list_services(self) -> list:
        """List all available services with pricing."""
        return [
            {"id": sid, "name": s["name"],
             "price": f"${s['price']/100:.2f}",
             "type": s["type"]}
            for sid, s in SERVICE_CATALOG.items()
        ]

    # ── Revenue Tracking ────────────────────────────────────

    def get_revenue_summary(self) -> dict:
        """Summarize revenue from payment journal."""
        journal_path = self.vault / "transactions.jsonl"
        if not journal_path.exists():
            return {"total_revenue": 0, "transaction_count": 0, "by_type": {}}

        total = 0
        count = 0
        by_type = {}
        for line in journal_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                if entry.get("event_type") in ("payment.received", "payment.succeeded",
                                                 "subscription.payment"):
                    amount = entry.get("payload", {}).get("amount", 0)
                    total += amount
                    count += 1
                    stype = entry.get("payload", {}).get("service_id", "unknown")
                    by_type[stype] = by_type.get(stype, 0) + amount
            except Exception:
                pass

        return {"total_revenue": total, "transaction_count": count, "by_type": by_type}

    # ── Journal & Events ────────────────────────────────────

    def _journal_transaction(self, event_type: str, payload: dict):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "payload": payload,
        }
        journal_path = self.vault / "transactions.jsonl"
        with open(journal_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def _publish(self, event_type: str, payload: dict):
        if _BUS:
            try:
                _BUS.publish(event_type, payload, source_module="payment_gateway")
            except Exception:
                pass
        record_decision(
            decision_type=event_type,
            description=f"Payment: {event_type}",
            agent_id="payment_gateway",
            outcome="success",
            context=payload,
        )

    def get_journal(self, limit: int = 50) -> list:
        journal_path = self.vault / "transactions.jsonl"
        if not journal_path.exists():
            return []
        lines = journal_path.read_text(encoding="utf-8").splitlines()
        entries = []
        for line in lines[-limit:]:
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except Exception:
                    pass
        return entries


# ── Self-Test ───────────────────────────────────────────────

if __name__ == "__main__":
    passed = 0
    gw = PaymentGateway()

    # Test 1: Instantiation
    assert hasattr(gw, "create_payment_link"), "Missing create_payment_link"
    assert hasattr(gw, "process_webhook"), "Missing process_webhook"
    assert hasattr(gw, "list_services"), "Missing list_services"
    passed += 1

    # Test 2: Service catalog
    services = gw.list_services()
    assert len(services) >= 7, f"Expected 7+ services, got {len(services)}"
    passed += 1

    # Test 3: Invoice stub (no Stripe key)
    result = gw.create_payment_link("ttlg_audit", "test-client")
    assert result.get("amount") == 497.0, f"Expected 497, got {result.get('amount')}"
    assert result.get("provider") in ("stripe", "manual"), "Invalid provider"
    passed += 1

    # Test 4: Journal written
    journal = gw.get_journal(limit=5)
    assert len(journal) > 0, "Journal should have entries"
    passed += 1

    # Test 5: Revenue summary
    summary = gw.get_revenue_summary()
    assert "total_revenue" in summary, "Missing total_revenue"
    passed += 1

    # Test 6: Webhook processing
    webhook_result = gw.process_webhook({"type": "checkout.session.completed",
        "data": {"object": {"id": "cs_test", "amount_total": 49700,
                             "payment_status": "paid",
                             "metadata": {"client_id": "test", "service_id": "ttlg_audit"}}}})
    assert webhook_result.get("event") == "checkout.completed", "Webhook processing failed"
    passed += 1

    stripe_status = "LIVE" if gw.stripe_available else "STUB MODE (set STRIPE_SECRET_KEY)"
    print(f"PASS: payment_gateway ({passed} assertions)")
    print(f"Stripe: {stripe_status}")
    print(f"Services: {len(services)} configured")
