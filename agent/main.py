import argparse
import hashlib
import json
import os
import random
import sys
import time
from datetime import datetime, timezone

from agent.checks import collect_all_checks
from agent.state import load_last_state, save_last_state
from agent.transport import post_update
from agent.utils import get_machine_identity


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


def maybe_report(args) -> bool:
    payload = build_payload(verbose=args.verbose)

    last = load_last_state()
    current_hash = stable_hash(payload["checks"])
    last_hash = last.get("last_hash") if last else None

    if args.once or args.dry_run:
        if args.verbose:
            print(json.dumps(payload, indent=2))
        if not args.dry_run and args.endpoint and args.api_key:
            post_update(args.endpoint, args.api_key, payload, verify_tls=not args.insecure)
        return True

    if last_hash == current_hash:
        if args.verbose:
            print("No change detected; skipping report.")
        return False

    if args.endpoint and args.api_key:
        post_update(args.endpoint, args.api_key, payload, verify_tls=not args.insecure)
        save_last_state({"last_hash": current_hash, "last_payload": payload})
        if args.verbose:
            print("Reported change.")
        return True
    else:
        if args.verbose:
            print("Endpoint or API key missing; not reporting.")
        return False


def daemon_loop(args):
    # On start, always compute and possibly send if changed
    if maybe_report(args):
        pass
    while True:
        interval_min = max(1, int(args.min_interval))
        interval_max = max(interval_min, int(args.max_interval))
        sleep_minutes = random.randint(interval_min, interval_max)
        if args.verbose:
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
            maybe_report(args)
        except Exception as e:
            if args.verbose:
                print(f"Report error: {e}")


def parse_args():
    p = argparse.ArgumentParser(description="Compliance Monitor Agent")
    p.add_argument("--endpoint", help="Server report endpoint", default=os.getenv("CM_ENDPOINT"))
    p.add_argument("--api-key", help="API key for server", default=os.getenv("CM_API_KEY"))
    p.add_argument("--once", action="store_true", help="Run once and exit")
    p.add_argument("--dry-run", action="store_true", help="Do not send; print payload only")
    p.add_argument("--verbose", action="store_true", help="Verbose output")
    p.add_argument("--min-interval", type=int, default=int(os.getenv("CM_MIN_INTERVAL", "15")))
    p.add_argument("--max-interval", type=int, default=int(os.getenv("CM_MAX_INTERVAL", "60")))
    p.add_argument("--insecure", action="store_true", help="Allow insecure HTTP (no TLS)")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.once or args.dry_run:
        maybe_report(args)
    else:
        daemon_loop(args)
