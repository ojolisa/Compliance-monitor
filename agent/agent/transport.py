import json
from typing import Any, Dict

import requests

DEFAULT_TIMEOUT = 15


def post_update(endpoint: str, api_key: str, payload: Dict[str, Any], verify_tls: bool = True) -> None:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-API-Key": api_key,
    }
    resp = requests.post(endpoint, data=json.dumps(payload), headers=headers, timeout=DEFAULT_TIMEOUT, verify=verify_tls)
    resp.raise_for_status()
