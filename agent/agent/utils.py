import json
import platform
import socket
import subprocess
import sys
from typing import Dict, Optional

import psutil


def run_cmd(cmd: list[str], timeout: int = 15) -> tuple[int, str, str]:
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = p.communicate(timeout=timeout)
        return p.returncode, out or "", err or ""
    except Exception as e:
        return 1, "", str(e)


# Machine identity

def _windows_machine_guid() -> Optional[str]:
    try:
        import winreg

        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography")
        val, _ = winreg.QueryValueEx(key, "MachineGuid")
        return str(val)
    except Exception:
        return None


def _macos_platform_uuid() -> Optional[str]:
    code, out, _ = run_cmd(["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"])
    if code == 0 and "IOPlatformUUID" in out:
        for line in out.splitlines():
            if "IOPlatformUUID" in line:
                parts = line.split("\"")
                if len(parts) >= 4:
                    return parts[3]
    return None


def _linux_machine_id() -> Optional[str]:
    for path in ["/etc/machine-id", "/var/lib/dbus/machine-id"]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                mid = f.read().strip()
                if mid:
                    return mid
        except Exception:
            continue
    return None


def get_machine_identity() -> Dict[str, str]:
    os_name = platform.system()
    hostname = socket.gethostname()
    mid = None
    if os_name == "Windows":
        mid = _windows_machine_guid()
    elif os_name == "Darwin":
        mid = _macos_platform_uuid()
    elif os_name == "Linux":
        mid = _linux_machine_id()

    if not mid:
        # Fallback to MAC addresses + hostname
        macs = sorted([nic.address for nic in psutil.net_if_addrs().get("Ethernet", [])])
        mid = f"{hostname}-{platform.platform()}"
    return {"machine_id": mid, "hostname": hostname, "os": os_name}
