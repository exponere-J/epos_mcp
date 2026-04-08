import json
import os
from typing import Dict, Tuple

# Keep config in kernel/state so it survives repo moves
STATE_FILE = os.path.join("kernel", "state", "epos_console_config.json")

TIER_KEYS = {
    "FREE": 1,
    "RESEARCHER-19": 1,
    "OPERATOR-49": 2,
    "SOVEREIGN-97": 3,
}

MODULE_KEYS = {
    "TOOL-A2-FLY": "A2_FLYWALL",
    # future:
    # "TOOL-C1-COMP": "C1_COMPILER",
}

DEFAULT_CONFIG = {
    "tier_level": 1,
    "user_name": "Sovereign",
    "features": []
}

def _atomic_write(path: str, data: str) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(data)
    os.replace(tmp, path)

def load_config() -> Dict:
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    if not os.path.exists(STATE_FILE):
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        if "features" not in cfg:
            cfg["features"] = []
        if "tier_level" not in cfg:
            cfg["tier_level"] = 1
        if "user_name" not in cfg:
            cfg["user_name"] = "Sovereign"
        return cfg
    except:
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)

def save_config(cfg: Dict) -> None:
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    _atomic_write(STATE_FILE, json.dumps(cfg, indent=2))

def unlock_feature(key_code: str) -> Tuple[bool, str]:
    key = (key_code or "").strip().upper()
    cfg = load_config()

    # Tier upgrades
    if key in TIER_KEYS:
        new_level = TIER_KEYS[key]
        if new_level > cfg["tier_level"]:
            cfg["tier_level"] = new_level
            # Tier-3 includes all known modules
            if cfg["tier_level"] >= 3:
                cfg["features"] = sorted(list(set(cfg["features"] + list(MODULE_KEYS.values()))))
            save_config(cfg)
            return True, f"Tier upgraded to Level {cfg['tier_level']}."
        return False, "Tier already active."

    # Individual module unlocks (Side Door)
    if key in MODULE_KEYS:
        feat = MODULE_KEYS[key]
        if feat not in cfg["features"]:
            cfg["features"].append(feat)
            cfg["features"] = sorted(list(set(cfg["features"])))
            save_config(cfg)
            return True, f"Module unlocked: {feat}."
        return False, "Module already installed."

    return False, "Invalid key."
