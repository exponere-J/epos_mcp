import os
import sys
import subprocess
from datetime import datetime

try:
    import questionary
    from rich.console import Console
    from rich.panel import Panel
except ImportError:
    # Fallback to plain prints if deps missing
    questionary = None
    Console = None
    Panel = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # tools/
PROJECT_ROOT = os.path.dirname(ROOT)

console = Console() if Console else None

def _print_header():
    title = "NEXT STEPS\u2122 TOOLBOX\nUniversal Chassis v1.0\n  EPOS / Exponere"
    if console and Panel:
        console.print(Panel.fit(title, style="bold cyan"))
    else:
        print("=" * 40)
        print("NEXT STEPS(TM) TOOLBOX")
        print("Universal Chassis v1.0")
        print("EPOS / Exponere")
        print("=" * 40)

def _run(cmd: list[str]) -> int:
    if console:
        console.print(f"[dim]$ {' '.join(cmd)}[/dim]")
    else:
        print(f"$ {' '.join(cmd)}")
    return subprocess.call(cmd)

def a1_available() -> bool:
    a1_path = os.path.join(PROJECT_ROOT, "tools", "next_steps", "a1_extractor", "src", "extract.py")
    return os.path.isfile(a1_path)

def run_a1():
    """Run A1 Context Extractor via menu."""
    if not a1_available():
        print("A1 extractor not found in tools/next_steps/a1_extractor/src/extract.py")
        input("Press Enter to return to menu...")
        return

    if questionary:
        url = questionary.text("Paste chat URL:").ask()
        platform = questionary.select(
            "Platform:",
            choices=["chatgpt", "perplexity", "claude"]
        ).ask()
        headless = questionary.confirm("Run headless?", default=True).ask()
    else:
        url = input("Paste chat URL: ").strip()
        platform = input("Platform [chatgpt/claude/perplexity]: ").strip() or "chatgpt"
        headless = True

    if not url:
        print("No URL supplied.")
        return

    a1_path = os.path.join(PROJECT_ROOT, "tools", "next_steps", "a1_extractor", "src", "extract.py")
    cmd = [sys.executable, a1_path, url, "--platform", platform]
    if headless:
        cmd.append("--headless")
    _run(cmd)
    input("A1 run complete. Press Enter to return to menu...")

def open_exports():
    exports_dir = os.path.join(PROJECT_ROOT, "exports")
    os.makedirs(exports_dir, exist_ok=True)
    if os.name == "nt":
        os.startfile(exports_dir)  # type: ignore[attr-defined]
    else:
        subprocess.call(["open" if sys.platform == "darwin" else "xdg-open", exports_dir])

def main():
    while True:
        _print_header()

        # Build dynamic choices based on what exists
        choices = []
        if a1_available():
            choices.append("A1: Context Extractor")
        else:
            choices.append("[A1 not installed]")

        # B1 placeholder – we’ll wire this next
        choices.append("[B1 not installed]")
        choices.append("Open Exports Folder")
        choices.append("Exit")

        if questionary:
            choice = questionary.select(
                "What do you want to do? (Use arrow keys)",
                choices=choices
            ).ask()
        else:
            # crude fallback
            for idx, c in enumerate(choices, start=1):
                print(f"{idx}. {c}")
            raw = input("Select option: ").strip()
            try:
                choice = choices[int(raw) - 1]
            except Exception:
                choice = "Exit"

        if choice.startswith("A1"):
            run_a1()
        elif choice.startswith("Open Exports"):
            open_exports()
        elif choice.startswith("Exit"):
            break
        else:
            # not installed placeholders
            if questionary:
                questionary.print("Module not installed yet.", style="fg:red")
            else:
                print("Module not installed yet.")
            input("Press Enter to return to menu...")

if __name__ == "__main__":
    main()
