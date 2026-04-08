from engine.feedback_flywheel import process_queue_once, build_daily_digest

def main():
    n = process_queue_once()
    digest = build_daily_digest()
    print(f"[feedback_worker] processed={n} digest={digest}")

if __name__ == "__main__":
    main()
