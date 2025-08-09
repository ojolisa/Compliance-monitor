import hashlib
import json
import os
import random
import sys
import time
from datetime import datetime, timezone

from dotenv import load_dotenv

from agent.checks import collect_all_checks
from agent.state import load_last_state, save_last_state
from agent.transport import post_update
from agent.utils import get_machine_identity


class Config:
    """Configuration loaded from environment variables and .env file"""
    
    def __init__(self):
        # Load .env file if it exists
        load_dotenv()
        
        # Load configuration from environment variables
        self.endpoint = os.getenv("CM_ENDPOINT")
        self.api_key = os.getenv("CM_API_KEY")
        self.min_interval = int(os.getenv("CM_MIN_INTERVAL", "15"))
        self.max_interval = int(os.getenv("CM_MAX_INTERVAL", "60"))
        self.once = os.getenv("CM_ONCE", "false").lower() == "true"
        self.dry_run = os.getenv("CM_DRY_RUN", "false").lower() == "true"
        self.verbose = os.getenv("CM_VERBOSE", "false").lower() == "true"
        self.insecure = os.getenv("CM_INSECURE", "false").lower() == "true"
    
    def validate(self):
        """Validate required configuration"""
        if not self.once and not self.dry_run:
            if not self.endpoint:
                raise ValueError("CM_ENDPOINT is required when not running in once or dry-run mode")
            if not self.api_key:
                raise ValueError("CM_API_KEY is required when not running in once or dry-run mode")


def now_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def stable_hash(obj) -> str:
    data = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def build_payload(verbose: bool = False):
    identity = get_machine_identity()
    checks = collect_all_checks(verbose=verbose)
    payload = {
        "machine_id": identity["machine_id"],
        "hostname": identity["hostname"],
        "os": identity["os"],
        "timestamp": now_ts(),
        "checks": checks,
    }
    return payload


def maybe_report(config: Config) -> bool:
    payload = build_payload(verbose=config.verbose)

    last = load_last_state()
    current_hash = stable_hash(payload["checks"])
    last_hash = last.get("last_hash") if last else None

    if config.once or config.dry_run:
        if config.verbose:
            print(json.dumps(payload, indent=2))
        if not config.dry_run and config.endpoint and config.api_key:
            post_update(config.endpoint, config.api_key, payload, verify_tls=not config.insecure)
        return True

    if last_hash == current_hash:
        if config.verbose:
            print("No change detected; skipping report.")
        return False

    if config.endpoint and config.api_key:
        post_update(config.endpoint, config.api_key, payload, verify_tls=not config.insecure)
        save_last_state({"last_hash": current_hash, "last_payload": payload})
        if config.verbose:
            print("Reported change.")
        return True
    else:
        if config.verbose:
            print("Endpoint or API key missing; not reporting.")
        return False


def daemon_loop(config: Config):
    # On start, always compute and possibly send if changed
    if maybe_report(config):
        pass
    while True:
        interval_min = max(1, int(config.min_interval))
        interval_max = max(interval_min, int(config.max_interval))
        sleep_minutes = random.randint(interval_min, interval_max)
        if config.verbose:
            print(f"Sleeping for {sleep_minutes} minutes...")
        try:
            time.sleep(sleep_minutes * 60)
        except KeyboardInterrupt:
            print("Exiting daemon loop.")
            sys.exit(0)
        except Exception:
            # Ensure we continue running even if sleep is interrupted
            pass
        try:
            maybe_report(config)
        except Exception as e:
            if config.verbose:
                print(f"Report error: {e}")


if __name__ == "__main__":
    try:
        config = Config()
        config.validate()
        
        if config.verbose:
            print("Compliance Monitor Agent starting...")
            print(f"Endpoint: {config.endpoint}")
            print(f"Min interval: {config.min_interval} minutes")
            print(f"Max interval: {config.max_interval} minutes")
            print(f"Once mode: {config.once}")
            print(f"Dry run: {config.dry_run}")
            print(f"Insecure: {config.insecure}")
        
        if config.once or config.dry_run:
            maybe_report(config)
        else:
            daemon_loop(config)
            
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please check your .env file or environment variables.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
