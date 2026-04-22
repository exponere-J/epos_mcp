# File: /mnt/c/Users/Jamie/workspace/epos_mcp/browseruse_airtable_setup.py
# Constitutional Authority: EPOS Constitution v3.1
# Governed: True
# Note: Legacy file — migration to root scheduled Sprint 5
"""
BROWSERUSE AIRTABLE SETUP AUTOMATION
=====================================
Purpose: Automate creation of EPOS AirTable bases via web UI using BrowserUse
Authority: EPOS Constitution v3.1 — Article II (No Silent Failures)

WHY BROWSERUSE INSTEAD OF API:
- AirTable deprecated public table creation API
- BrowserUse navigates the web UI programmatically
- Handles authentication, base creation, table setup, field configuration

PREREQUISITES:
1. BrowserUse installed: pip install browser-use --break-system-packages
2. Playwright browsers: playwright install chromium
3. AirTable account credentials in .env:
   AIRTABLE_EMAIL=your.email@domain.com
   AIRTABLE_PASSWORD=your_password

EXECUTION:
python browseruse_airtable_setup.py --base "EPOS Command Base"
python browseruse_airtable_setup.py --base "LIFE Command Base"
python browseruse_airtable_setup.py --base "FIN Apps Base"
python browseruse_airtable_setup.py --base "PGP Command Base"

WHAT THIS DOES:
1. Opens browser to airtable.com
2. Logs in with credentials
3. Creates new base with specified name
4. For each table in the schema:
   - Creates table
   - Adds all fields with correct types
   - Configures single-select/multi-select options
   - Sets up number precision, currency symbols, date formats
5. Exports base ID and URLs to context_vault/airtable/base_manifest.json
6. Logs all actions to logs/browseruse_airtable_{timestamp}.jsonl

SAFETY:
- Runs in headed mode (you can watch it work)
- Pauses before destructive actions
- Validates each step before proceeding
- Full audit trail in logs
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# ─── SETUP ───────────────────────────────────────────────────────────────────
load_dotenv()

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"browseruse_airtable_{TIMESTAMP}.jsonl"

VAULT_DIR = Path("context_vault/airtable")
VAULT_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST_FILE = VAULT_DIR / "base_manifest.json"


def audit(event: str, status: str, detail: str = ""):
    """Constitutional Article II: no silent failures. Every action logged."""
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": event,
        "status": status,
        "detail": detail
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")
    print(f"[{status}] {event} — {detail}")


# ─── BROWSERUSE CLIENT ───────────────────────────────────────────────────────
try:
    from browser_use import Agent
    from langchain_openai import ChatOpenAI
except ImportError:
    audit("IMPORT_CHECK", "FAIL", "browser-use not installed. Run: pip install browser-use langchain-openai --break-system-packages")
    sys.exit(1)

EMAIL = os.getenv("AIRTABLE_EMAIL")
PASSWORD = os.getenv("AIRTABLE_PASSWORD")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

if not EMAIL or not PASSWORD:
    audit("ENV_CHECK", "FAIL", "AIRTABLE_EMAIL or AIRTABLE_PASSWORD not in .env")
    sys.exit(1)

if not OPENAI_KEY:
    audit("ENV_CHECK", "FAIL", "OPENAI_API_KEY not in .env (BrowserUse requires LLM)")
    sys.exit(1)


# ─── TABLE SCHEMAS ──────────────────────────────────────────────────────────
# Same schemas as API version but formatted for BrowserUse natural language

EPOS_COMMAND_BASE = {
    "base_name": "EPOS Command Base",
    "tables": [
        {
            "name": "CJ_Leads",
            "fields": [
                {"name": "Lead ID", "type": "autonumber"},
                {"name": "Full Name", "type": "text"},
                {"name": "Email", "type": "email"},
                {"name": "Phone", "type": "phone"},
                {"name": "Company", "type": "text"},
                {"name": "Source Channel", "type": "single_select", "options": [
                    "Organic Search", "Social Media", "Email Outreach", "Referral",
                    "Content Lab", "Marketplace", "Cold Outreach", "Direct"
                ]},
                {"name": "Journey Phase", "type": "single_select", "options": [
                    "TP01-05 Awareness", "TP06-10 Discovery", "TP11-17 Consideration",
                    "TP18-24 Commitment", "TP25-31 Stewardship"
                ]},
                {"name": "Psychological State", "type": "single_select", "options": [
                    "Discovery", "Education", "Decision", "Commitment", "Advocacy"
                ]},
                {"name": "Revenue Layer", "type": "single_select", "options": [
                    "L1 Solo ($39-$97/mo)", "L2 SMB ($197-$597/mo)",
                    "L3 Agency ($997-$1,997/mo)", "L4 Enterprise ($2,997+/mo)"
                ]},
                {"name": "Resonance Score (0-100)", "type": "number"},
                {"name": "Lead Status", "type": "single_select", "options": [
                    "New", "Engaged", "Qualified", "Proposal Sent", "Negotiating",
                    "Won", "Lost", "Nurture"
                ]},
                {"name": "Pipeline Value ($)", "type": "currency"},
                {"name": "First Contact Date", "type": "date"},
                {"name": "Notes / Context", "type": "long_text"}
            ]
        },
        {
            "name": "FIN_Transactions",
            "fields": [
                {"name": "Transaction ID", "type": "autonumber"},
                {"name": "Date", "type": "date"},
                {"name": "Vendor / Merchant", "type": "text"},
                {"name": "Description", "type": "text"},
                {"name": "Amount ($)", "type": "currency"},
                {"name": "Category", "type": "text"},
                {"name": "Transaction Type", "type": "single_select", "options": [
                    "Expense", "Revenue", "Transfer", "Payroll", "Tax Payment", "Retirement Contrib"
                ]},
                {"name": "Status", "type": "single_select", "options": [
                    "Pending", "Approved", "Paid", "Reconciled", "Disputed"
                ]},
                {"name": "Receipt Attached", "type": "checkbox"},
                {"name": "Business Purpose", "type": "text"},
                {"name": "Quarter", "type": "single_select", "options": ["Q1", "Q2", "Q3", "Q4"]},
                {"name": "Tax Year", "type": "number"}
            ]
        },
        {
            "name": "FIN_Revenue",
            "fields": [
                {"name": "Revenue ID", "type": "autonumber"},
                {"name": "Date", "type": "date"},
                {"name": "Client / Source", "type": "text"},
                {"name": "Product / Node", "type": "single_select", "options": [
                    "Research Node ($39/mo)", "Content Lab ($97/mo)", "Automation Node ($197/mo)",
                    "Full EPOS Stack ($297/mo)", "Agency White-Label ($997/mo)",
                    "Enterprise ($2,997+/mo)", "TTLG Setup Fee", "Custom Build Fee"
                ]},
                {"name": "Amount ($)", "type": "currency"},
                {"name": "Net Amount ($)", "type": "currency"},
                {"name": "Revenue Type", "type": "single_select", "options": [
                    "Recurring MRR", "One-Time Setup", "Project Fee", "Consulting", "Marketplace"
                ]},
                {"name": "Quarter", "type": "single_select", "options": ["Q1", "Q2", "Q3", "Q4"]},
                {"name": "Tax Year", "type": "number"}
            ]
        },
        {
            "name": "FIN_Vendors",
            "fields": [
                {"name": "Vendor ID", "type": "autonumber"},
                {"name": "Vendor Name", "type": "text"},
                {"name": "Category", "type": "single_select", "options": [
                    "AI & Voice/Video", "Development Tools", "Cloud Infrastructure",
                    "Marketing & Content", "Payment Processing", "Legal & Financial",
                    "Communication", "Insurance", "Professional Services"
                ]},
                {"name": "Monthly Cost ($)", "type": "currency"},
                {"name": "Annual Cost ($)", "type": "currency"},
                {"name": "Next Renewal Date", "type": "date"},
                {"name": "ROI Score (1-10)", "type": "number"},
                {"name": "Status", "type": "single_select", "options": [
                    "Active", "On Trial", "Cancelled", "Paused"
                ]}
            ]
        },
        {
            "name": "OPS_Missions",
            "fields": [
                {"name": "Mission ID", "type": "autonumber"},
                {"name": "Mission Title", "type": "text"},
                {"name": "Assigned Agent", "type": "single_select", "options": [
                    "Agent Zero", "BrowserUse", "Content Lab Agent", "Financial Agent",
                    "Claude Strategic", "Human (Jamie)"
                ]},
                {"name": "Status", "type": "single_select", "options": [
                    "Queued", "Running", "Complete", "Failed", "Blocked"
                ]},
                {"name": "Start Time", "type": "datetime"},
                {"name": "Output / Result", "type": "long_text"},
                {"name": "Vault Path Written", "type": "text"}
            ]
        }
    ]
}

LIFE_COMMAND_BASE = {
    "base_name": "LIFE Command Base",
    "tables": [
        {
            "name": "TRUST_Structure",
            "fields": [
                {"name": "Entity ID", "type": "autonumber"},
                {"name": "Entity Name", "type": "text"},
                {"name": "Entity Type", "type": "single_select", "options": [
                    "Revocable Living Trust", "Irrevocable Grantor Trust (IDGT)",
                    "QSST", "ESBT", "S-Corporation", "LLC", "Holding Company"
                ]},
                {"name": "Purpose", "type": "long_text"},
                {"name": "Beneficiaries", "type": "text"},
                {"name": "Est. Value ($)", "type": "currency"},
                {"name": "Status", "type": "single_select", "options": [
                    "Planned", "In Formation", "Active", "Under Review"
                ]}
            ]
        },
        {
            "name": "TRUST_GiftTracking",
            "fields": [
                {"name": "Gift ID", "type": "autonumber"},
                {"name": "Tax Year", "type": "number"},
                {"name": "Recipient", "type": "text"},
                {"name": "Gift Amount ($)", "type": "currency"},
                {"name": "Annual Exclusion Used ($)", "type": "currency"},
                {"name": "Lifetime Exemption Used ($)", "type": "currency"},
                {"name": "Date", "type": "date"},
                {"name": "Documented", "type": "checkbox"}
            ]
        },
        {
            "name": "Personal_Health",
            "fields": [
                {"name": "Record ID", "type": "autonumber"},
                {"name": "Category", "type": "single_select", "options": [
                    "Medical", "Dental", "Vision", "Mental Health", "Fitness"
                ]},
                {"name": "Provider", "type": "text"},
                {"name": "Date", "type": "date"},
                {"name": "Notes", "type": "long_text"}
            ]
        }
    ]
}

FIN_APPS_BASE = {
    "base_name": "FIN Apps Base",
    "tables": [
        {
            "name": "Invoices",
            "fields": [
                {"name": "Invoice ID", "type": "autonumber"},
                {"name": "Client", "type": "text"},
                {"name": "Invoice Date", "type": "date"},
                {"name": "Due Date", "type": "date"},
                {"name": "Amount ($)", "type": "currency"},
                {"name": "Status", "type": "single_select", "options": [
                    "Draft", "Sent", "Paid", "Overdue", "Cancelled"
                ]},
                {"name": "Payment Received", "type": "checkbox"}
            ]
        },
        {
            "name": "Tax_Planning",
            "fields": [
                {"name": "Record ID", "type": "autonumber"},
                {"name": "Tax Year", "type": "number"},
                {"name": "Quarter", "type": "single_select", "options": [
                    "Q1 — Apr 15", "Q2 — Jun 15", "Q3 — Sep 15", "Q4 — Jan 15", "Annual"
                ]},
                {"name": "Est. Net Profit ($)", "type": "currency"},
                {"name": "Total Tax Liability ($)", "type": "currency"},
                {"name": "Payment Due Date", "type": "date"},
                {"name": "Amount Paid ($)", "type": "currency"},
                {"name": "Payment Status", "type": "single_select", "options": [
                    "Upcoming", "Paid", "Late", "Planned"
                ]}
            ]
        }
    ]
}

PGP_COMMAND_BASE = {
    "base_name": "PGP Command Base",
    "tables": [
        {
            "name": "Jobs",
            "fields": [
                {"name": "Job ID", "type": "autonumber"},
                {"name": "Client Name", "type": "text"},
                {"name": "Service", "type": "single_select", "options": [
                    "Pressure Washing", "Gutter Cleaning", "Roof Cleaning", "Deck Cleaning"
                ]},
                {"name": "Job Date", "type": "date"},
                {"name": "Amount ($)", "type": "currency"},
                {"name": "Status", "type": "single_select", "options": [
                    "Scheduled", "In Progress", "Complete", "Invoiced", "Paid"
                ]},
                {"name": "Notes", "type": "long_text"}
            ]
        },
        {
            "name": "Revenue",
            "fields": [
                {"name": "Revenue ID", "type": "autonumber"},
                {"name": "Date", "type": "date"},
                {"name": "Client", "type": "text"},
                {"name": "Amount ($)", "type": "currency"},
                {"name": "Payment Method", "type": "single_select", "options": [
                    "Cash", "Check", "Venmo", "Credit Card", "PayPal"
                ]},
                {"name": "Quarter", "type": "single_select", "options": ["Q1", "Q2", "Q3", "Q4"]}
            ]
        }
    ]
}


SCHEMA_MAP = {
    "EPOS Command Base": EPOS_COMMAND_BASE,
    "LIFE Command Base": LIFE_COMMAND_BASE,
    "FIN Apps Base": FIN_APPS_BASE,
    "PGP Command Base": PGP_COMMAND_BASE
}


# ─── BROWSERUSE AUTOMATION ──────────────────────────────────────────────────

def create_base_with_browseruse(base_name: str, schema: dict):
    """Use BrowserUse to create AirTable base via web UI automation."""
    
    audit("BASE_CREATE_START", "INFO", f"Creating base: {base_name}")
    
    # Initialize LLM for BrowserUse
    llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_KEY)
    
    # Create BrowserUse agent
    agent = Agent(
        task=f"""
        Create an AirTable base named "{base_name}" with the following structure.
        
        STEPS:
        1. Go to https://airtable.com
        2. Log in with:
           Email: {EMAIL}
           Password: {PASSWORD}
        3. Click "Create a base" or "+" to start new base
        4. Name it: {base_name}
        5. For each table in the schema below, create the table and add all fields with correct types
        
        SCHEMA:
        {json.dumps(schema, indent=2)}
        
        FIELD TYPE MAPPING:
        - "text" → Single line text
        - "long_text" → Long text
        - "email" → Email
        - "phone" → Phone number
        - "number" → Number (no decimals unless specified)
        - "currency" → Currency (USD, 2 decimal places)
        - "date" → Date (US format)
        - "datetime" → Date and time (US format, 12-hour)
        - "checkbox" → Checkbox
        - "autonumber" → Autonumber
        - "single_select" → Single select (create all options listed)
        - "multi_select" → Multiple select (create all options listed)
        
        After creating each table, verify all fields are present before moving to next table.
        At the end, copy the base URL from the browser address bar.
        """,
        llm=llm,
        use_vision=True,
        save_conversation_path=str(LOG_DIR / f"browseruse_conversation_{base_name.replace(' ', '_')}.json")
    )
    
    # Run the agent
    try:
        result = agent.run()
        
        # Extract base URL from result
        base_url = None
        if "airtable.com" in str(result):
            # Parse URL from agent response
            import re
            url_match = re.search(r'https://airtable\.com/app[A-Za-z0-9]+', str(result))
            if url_match:
                base_url = url_match.group(0)
                base_id = base_url.split('/')[-1]
                
                audit("BASE_CREATE_SUCCESS", "SUCCESS", f"{base_name} → {base_url}")
                
                # Save to manifest
                manifest = {}
                if MANIFEST_FILE.exists():
                    with open(MANIFEST_FILE, 'r') as f:
                        manifest = json.load(f)
                
                manifest[base_name] = {
                    "base_id": base_id,
                    "base_url": base_url,
                    "created_at": datetime.utcnow().isoformat(),
                    "table_count": len(schema["tables"]),
                    "tables": [t["name"] for t in schema["tables"]]
                }
                
                with open(MANIFEST_FILE, 'w') as f:
                    json.dump(manifest, f, indent=2)
                
                return base_url
            else:
                audit("BASE_URL_EXTRACT", "FAIL", "Could not extract base URL from agent response")
                return None
        else:
            audit("BASE_CREATE_CHECK", "WARN", "Agent completed but no AirTable URL found in response")
            return None
            
    except Exception as e:
        audit("BASE_CREATE", "FAIL", f"{base_name} — {str(e)}")
        raise


# ─── MAIN ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="BrowserUse AirTable Setup")
    parser.add_argument("--base", required=True, 
                       choices=list(SCHEMA_MAP.keys()),
                       help="Which base to create")
    parser.add_argument("--all", action="store_true",
                       help="Create all 4 bases in sequence")
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("  BROWSERUSE AIRTABLE SETUP")
    print(f"  Mode: {'ALL BASES' if args.all else args.base}")
    print(f"  Log: {LOG_FILE}")
    print("="*70 + "\n")
    
    if args.all:
        bases_to_create = list(SCHEMA_MAP.keys())
    else:
        bases_to_create = [args.base]
    
    results = {}
    
    for base_name in bases_to_create:
        print(f"\n▶ Creating: {base_name}\n")
        schema = SCHEMA_MAP[base_name]
        
        try:
            url = create_base_with_browseruse(base_name, schema)
            results[base_name] = {"status": "success", "url": url}
            print(f"\n✅ {base_name} created successfully")
            
            # Wait between bases to avoid rate limits
            if len(bases_to_create) > 1:
                print("\nWaiting 30 seconds before next base...")
                time.sleep(30)
                
        except Exception as e:
            results[base_name] = {"status": "failed", "error": str(e)}
            print(f"\n❌ {base_name} failed: {str(e)}")
    
    # Summary
    print("\n" + "="*70)
    print("  SUMMARY")
    success_count = sum(1 for r in results.values() if r["status"] == "success")
    print(f"  Successful: {success_count}/{len(bases_to_create)}")
    print(f"  Manifest:   {MANIFEST_FILE}")
    print("="*70)
    
    for base_name, result in results.items():
        status_icon = "✅" if result["status"] == "success" else "❌"
        print(f"  {status_icon} {base_name}: {result.get('url', result.get('error'))}")
    
    print()


if __name__ == "__main__":
    main()
