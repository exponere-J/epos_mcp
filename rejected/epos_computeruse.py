import subprocess
import pyautogui
from pynput.keyboard import Key, Controller as KeyboardController
from pynput.mouse import Button, Controller as MouseController
from pathlib import Path
import time
import json

keyboard = KeyboardController()
mouse = MouseController()

LOG_DIR = Path("local_arm/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "computeruse.log"

def log_event(event: str):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(event + "\n")

def exec_shell(cmd: str):
    log_event(f"[SHELL] {cmd}")
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    out = (proc.stdout or "") + (proc.stderr or "")
    log_event(f"[OUTPUT]\\n{out}\\n")
    return out

def type_text(text: str):
    log_event(f"[TYPE] {text}")
    keyboard.type(text)
    time.sleep(0.2)

def press_key(key: str):
    log_event(f"[KEY] {key}")
    keyboard.press(key)
    keyboard.release(key)
    time.sleep(0.1)

def move_mouse(x: int, y: int):
    log_event(f"[MOVE] {x},{y}")
    mouse.position = (x, y)
    time.sleep(0.1)

def click_mouse(button: str = "left"):
    log_event(f"[CLICK] {button}")
    if button == "left":
        mouse.click(Button.left)
    elif button == "right":
        mouse.click(Button.right)
    time.sleep(0.1)

def screenshot(path: str):
    log_event(f"[SCREENSHOT] {path}")
    img = pyautogui.screenshot()
    img.save(path)

def run_action(action: dict):
    a = action.get("action")

    if a == "shell":
        return exec_shell(action["command"])
    elif a == "type":
        return type_text(action["text"])
    elif a == "key":
        return press_key(action["key"])
    elif a == "mouse_move":
        return move_mouse(action["x"], action["y"])
    elif a == "mouse_click":
        return click_mouse(action.get("button", "left"))
    elif a == "screenshot":
        return screenshot(action["path"])
    else:
        return log_event(f"[UNKNOWN ACTION] {a}")

def execute_plan(plan: list[dict]):
    for step in plan:
        log_event(f"[STEP] {json.dumps(step)}")
        print(f"Executing: {step.get('action')}")
        run_action(step)
        print("Done.")
