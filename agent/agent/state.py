import json
import os
from typing import Any, Dict, Optional

from platformdirs import user_data_dir

APP_NAME = "compliance_monitor"
APP_AUTHOR = "cm"
STATE_FILENAME = "agent_state.json"


def _state_path() -> str:
    data_dir = user_data_dir(APP_NAME, APP_AUTHOR)
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, STATE_FILENAME)


def load_last_state() -> Optional[Dict[str, Any]]:
    path = _state_path()
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_last_state(state: Dict[str, Any]) -> None:
    path = _state_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f)
    except Exception:
        pass
