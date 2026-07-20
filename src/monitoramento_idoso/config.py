from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
import yaml

_DEFAULT_CONFIG = {
    "discovery": {
        "timeout": 5,
    },
    "onvif": {
        "username": "admin",
        "password": "admin",
    },
}

_PROJECT_ROOT = Path(__file__).parent.parent.parent
_CONFIG_PATH = _PROJECT_ROOT / "config.yaml"


def load_config(path: Path | None = None) -> dict:
    load_dotenv(_PROJECT_ROOT / ".env")

    config_path = path or _CONFIG_PATH
    if config_path.exists():
        with open(config_path) as f:
            user_cfg = yaml.safe_load(f) or {}
        cfg = _deep_merge(_DEFAULT_CONFIG, user_cfg)
    else:
        cfg = _DEFAULT_CONFIG.copy()

    # Environment variables override config file
    onvif = cfg.get("onvif", {})
    if val := os.environ.get("MO_ONVIF_USER"):
        onvif["username"] = val
    if val := os.environ.get("MO_ONVIF_PASS"):
        onvif["password"] = val
    cfg["onvif"] = onvif
    return cfg


def _deep_merge(base: dict, override: dict) -> dict:
    merged = base.copy()
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged
