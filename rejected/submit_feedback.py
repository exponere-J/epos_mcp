import argparse, json
from pathlib import Path
from datetime import datetime

QUEUE = Path("queue/feedback")
QUEUE.mkdir(parents=True, exist_ok=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="user")
    ap.add_argument("--title", required=True)
    ap.add_argument("--body", required=True)
    ap.add_argument("--tag", action="append", default=[])
    ap.add_argument("--context", default="{}", help="JSON string")
    args = ap.parse_args()

    try:
        ctx = json.loads(args.context)
    except Exception:
        ctx = {}

    if args.tag:
        ctx["tags"] = args.tag

    payload = {
        "id": f"fb_{int(datetime.now().timestamp())}",
        "source": args.source,
        "title": args.title,
        "body": args.body,
        "context": ctx
    }

    out = QUEUE / f"{payload['id']}.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"queued: {out}")

if __name__ == "__main__":
    main()
