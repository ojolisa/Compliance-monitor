import json
import os
import platform
import re
import shutil
import subprocess
from typing import Any, Dict, Optional

from .utils import run_cmd


def _bool_to_status(ok: Optional[bool]) -> str:
    if ok is True:
        return "ok"
    if ok is False:
        return "issue"
    return "unknown"


def check_disk_encryption() -> Dict[str, Any]:
    os_name = platform.system()
    result: Dict[str, Any] = {"ok": None, "summary": "", "data": {}}
    try:
        if os_name == "Windows":
            # Use manage-bde for system drive C:
            code, out, err = run_cmd(["manage-bde", "-status", "C:"])
            if code == 0:
                enc = False
                pct = None
                for line in out.splitlines():
                    if "Conversion Status" in line and ":" in line:
                        status = line.split(":", 1)[1].strip()
                        if status.lower().startswith("fully"):
                            enc = True
                    if "Percentage Encrypted" in line and ":" in line:
                        m = re.search(r"(\d+)%", line)
                        if m:
                            pct = int(m.group(1))
                            if pct >= 99:
                                enc = True
                result["ok"] = enc
                result["summary"] = f"BitLocker {'enabled' if enc else 'disabled'}"
                result["data"] = {"percentage_encrypted": pct}
            else:
                result["summary"] = f"manage-bde failed: {err.strip()}"
        elif os_name == "Darwin":
            code, out, err = run_cmd(["fdesetup", "status"])
            if code == 0:
                on = "On." in out or "On" in out
                result["ok"] = on
                result["summary"] = f"FileVault {'enabled' if on else 'disabled'}"
            else:
                result["summary"] = f"fdesetup failed: {err.strip()}"
        elif os_name == "Linux":
            # Heuristics: check for any dm-crypt/crypt device via lsblk
            if shutil.which("lsblk"):
                code, out, err = run_cmd(["lsblk", "-o", "NAME,TYPE"])
                if code == 0:
                    has_crypt = any("crypt" in line for line in out.lower().splitlines())
                    result["ok"] = has_crypt
                    result["summary"] = "LUKS/dm-crypt present" if has_crypt else "No dm-crypt mapping detected"
                else:
                    result["summary"] = f"lsblk failed: {err.strip()}"
            else:
                result["summary"] = "lsblk not available"
        else:
            result["summary"] = f"Unsupported OS: {os_name}"
    except Exception as e:
        result["summary"] = f"error: {e}"
    result["status"] = _bool_to_status(result["ok"])  # normalize
    return result


def check_os_updates(timeout: int = 45) -> Dict[str, Any]:
    os_name = platform.system()
    result: Dict[str, Any] = {"ok": None, "summary": "", "data": {}}
    try:
        if os_name == "Windows":
            # Check for pending reboot as minimal signal
            try:
                import winreg

                key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired"
                try:
                    winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                    pending = True
                except FileNotFoundError:
                    pending = False
                result["ok"] = not pending
                result["summary"] = "No pending reboot" if not pending else "Pending reboot detected"
                result["data"] = {"pending_reboot": pending, "pending_updates": None}
            except Exception as e:
                result["summary"] = f"Update status unknown: {e}"
        elif os_name == "Darwin":
            code, out, err = run_cmd(["softwareupdate", "-l"], timeout=timeout)
            if code == 0:
                has_updates = "No new software available." not in out
                result["ok"] = not has_updates
                result["summary"] = "Up to date" if not has_updates else "Updates available"
            else:
                result["summary"] = f"softwareupdate failed: {err.strip()}"
        elif os_name == "Linux":
            # Try apt
            if shutil.which("apt-get"):
                code, out, err = run_cmd(["apt-get", "-s", "upgrade"], timeout=timeout)
                if code == 0:
                    m = re.search(r"(\d+) upgraded, (\d+) newly installed, (\d+) to remove, (\d+) not upgraded", out)
                    has_updates = False
                    if m:
                        has_updates = any(int(m.group(i)) > 0 for i in range(1, 5))
                    result["ok"] = not has_updates
                    result["summary"] = "Up to date" if not has_updates else "Updates available"
                else:
                    result["summary"] = f"apt-get failed: {err.strip()}"
            elif shutil.which("dnf") or shutil.which("yum"):
                tool = "dnf" if shutil.which("dnf") else "yum"
                code, out, err = run_cmd([tool, "-q", "check-update"], timeout=timeout)
                # For yum/dnf, exit code 100 means updates available, 0 means none
                if code == 100:
                    result["ok"] = False
                    result["summary"] = "Updates available"
                elif code == 0:
                    result["ok"] = True
                    result["summary"] = "Up to date"
                else:
                    result["summary"] = f"{tool} check-update failed (code {code})"
            else:
                result["summary"] = "No known package manager found"
        else:
            result["summary"] = f"Unsupported OS: {os_name}"
    except Exception as e:
        result["summary"] = f"error: {e}"
    result["status"] = _bool_to_status(result["ok"])  # normalize
    return result


def check_antivirus() -> Dict[str, Any]:
    os_name = platform.system()
    result: Dict[str, Any] = {"ok": None, "summary": "", "data": {}}
    try:
        if os_name == "Windows":
            # Try Windows Defender
            code, out, err = run_cmd(["powershell", "-NoProfile", "-Command", "Get-MpComputerStatus | ConvertTo-Json -Compress"], timeout=20)
            if code == 0 and out.strip():
                try:
                    data = json.loads(out)
                    am_enabled = bool(data.get("AntivirusEnabled", False)) or bool(data.get("RealTimeProtectionEnabled", False))
                    result["ok"] = am_enabled
                    result["summary"] = "Defender active" if am_enabled else "Defender not active"
                    result["data"] = {"defender": data}
                    result["status"] = _bool_to_status(result["ok"])  # early return
                    return result
                except Exception:
                    pass
            # Fallback: query SecurityCenter2 for any AV products
            ps = (
                "Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntivirusProduct | "
                "Select-Object -Property displayName,productState | ConvertTo-Json -Compress"
            )
            code, out, err = run_cmd(["powershell", "-NoProfile", "-Command", ps], timeout=20)
            if code == 0 and out.strip():
                try:
                    data = json.loads(out)
                    if isinstance(data, dict):
                        data = [data]
                    ok = len(data) > 0
                    result["ok"] = ok
                    names = ", ".join([d.get("displayName", "?") for d in data]) if ok else "none"
                    result["summary"] = f"AV products: {names}" if ok else "No antivirus detected"
                    result["data"] = {"products": data}
                except Exception as e:
                    result["summary"] = f"Parse error: {e}"
            else:
                result["summary"] = "Unable to determine antivirus status"
        elif os_name == "Darwin":
            # Heuristic: list known AV daemons/processes
            known = ["symantec", "sophos", "sentinel", "carbonblack", "crowdstrike", "malwarebytes", "clamd"]
            code, out, err = run_cmd(["ps", "-A", "-o", "comm="])
            if code == 0:
                procs = out.lower()
                present = [k for k in known if k in procs]
                ok = len(present) > 0
                result["ok"] = ok
                result["summary"] = f"AV present: {', '.join(present)}" if ok else "No known AV detected"
            else:
                result["summary"] = "ps failed"
        elif os_name == "Linux":
            # Heuristic: detect common AV services
            known = ["clamd", "freshclam", "sophos", "savd", "csagent", "falcon-sensor", "sentinel-agent"]
            if shutil.which("ps"):
                code, out, err = run_cmd(["ps", "-eo", "comm="])
                if code == 0:
                    procs = out.lower()
                    present = [k for k in known if k in procs]
                    ok = len(present) > 0
                    result["ok"] = ok
                    result["summary"] = f"AV present: {', '.join(present)}" if ok else "No known AV detected"
                else:
                    result["summary"] = "ps failed"
            else:
                result["summary"] = "ps not available"
        else:
            result["summary"] = f"Unsupported OS: {os_name}"
    except Exception as e:
        result["summary"] = f"error: {e}"
    result["status"] = _bool_to_status(result["ok"])  # normalize
    return result


def check_sleep_settings() -> Dict[str, Any]:
    os_name = platform.system()
    result: Dict[str, Any] = {"ok": None, "summary": "", "data": {}}
    policy_minutes = 10
    try:
        if os_name == "Windows":
            # Parse powercfg -q for "Sleep after" settings (AC/DC)
            code, out, err = run_cmd(["powercfg", "-q"], timeout=20)
            if code == 0:
                ac = None
                dc = None
                # We look for a block containing "Sleep after" then lines with AC/DC indices
                lines = out.splitlines()
                for i, line in enumerate(lines):
                    if "Sleep after" in line:
                        # Next lines often contain AC/DC values in minutes
                        for j in range(i + 1, min(i + 6, len(lines))):
                            l = lines[j].strip()
                            m = re.search(r"AC Power Setting Index: (\d+)", l)
                            if m:
                                ac = int(m.group(1))
                            m = re.search(r"DC Power Setting Index: (\d+)", l)
                            if m:
                                dc = int(m.group(1))
                        break
                ok_vals = []
                if ac is not None:
                    ok_vals.append(ac <= policy_minutes and ac != 0)
                if dc is not None:
                    ok_vals.append(dc <= policy_minutes and dc != 0)
                ok = None if not ok_vals else all(ok_vals)
                result["ok"] = ok
                result["summary"] = f"Sleep AC={ac} DC={dc} minutes"
                result["data"] = {"sleep_ac": ac, "sleep_dc": dc, "policy": policy_minutes}
            else:
                result["summary"] = f"powercfg failed: {err.strip()}"
        elif os_name == "Darwin":
            code, out, err = run_cmd(["pmset", "-g", "custom"], timeout=15)
            if code != 0:
                # fallback simple
                code, out, err = run_cmd(["pmset", "-g"], timeout=15)
            if code == 0:
                displaysleep = None
                sleep = None
                m = re.search(r"displaysleep\s+(\d+)", out)
                if m:
                    displaysleep = int(m.group(1))
                m = re.search(r"sleep\s+(\d+)", out)
                if m:
                    sleep = int(m.group(1))
                # 0 means never
                vals = [v for v in [displaysleep, sleep] if v is not None]
                ok = None if not vals else all((v != 0 and v <= policy_minutes) for v in vals)
                result["ok"] = ok
                result["summary"] = f"pmset displaysleep={displaysleep} sleep={sleep}"
                result["data"] = {"displaysleep": displaysleep, "sleep": sleep, "policy": policy_minutes}
            else:
                result["summary"] = f"pmset failed: {err.strip()}"
        elif os_name == "Linux":
            # Heuristics: try gsettings for GNOME
            if shutil.which("gsettings"):
                # AC
                code1, out1, _ = run_cmd(["gsettings", "get", "org.gnome.settings-daemon.plugins.power", "sleep-inactive-ac-timeout"], timeout=10)
                # Battery
                code2, out2, _ = run_cmd(["gsettings", "get", "org.gnome.settings-daemon.plugins.power", "sleep-inactive-battery-timeout"], timeout=10)
                def parse_val(s: str) -> Optional[int]:
                    s = s.strip()
                    try:
                        return int(s)
                    except Exception:
                        m = re.search(r"(\d+)", s)
                        return int(m.group(1)) if m else None
                ac = parse_val(out1) if code1 == 0 else None
                dc = parse_val(out2) if code2 == 0 else None
                vals = [v for v in [ac, dc] if v is not None]
                ok = None if not vals else all((v != 0 and v <= policy_minutes * 60) for v in vals)  # gsettings returns seconds
                result["ok"] = ok
                result["summary"] = f"GNOME sleep AC={ac}s DC={dc}s"
                result["data"] = {"sleep_ac_s": ac, "sleep_dc_s": dc, "policy_minutes": policy_minutes}
            else:
                result["summary"] = "Unknown desktop; sleep policy unknown"
        else:
            result["summary"] = f"Unsupported OS: {os_name}"
    except Exception as e:
        result["summary"] = f"error: {e}"
    result["status"] = _bool_to_status(result["ok"])  # normalize
    return result


def collect_all_checks(verbose: bool = False) -> Dict[str, Any]:
    checks = {
        "disk_encryption": check_disk_encryption(),
        "os_updates": check_os_updates(),
        "antivirus": check_antivirus(),
        "sleep_policy": check_sleep_settings(),
    }
    if verbose:
        # Truncate verbose data to summaries
        pass
    return checks
