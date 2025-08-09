# Compliance Monitor Agent (Python)

Cross-platform agent that performs compliance checks and reports to the backend.

Features

- Disk encryption check
- OS updates pending
- Antivirus presence/status
- Inactivity sleep policy (<= 10 minutes)
- Background daemon (15–60 min by default) that reports only on change

Usage

- One-shot run (verbose, dry-run):

```powershell
python main.py --once --verbose --dry-run
```

- Report to server:

```powershell
python main.py --endpoint http://localhost:3000/api/v1/report --api-key dev_local --once --verbose
```

- Daemon mode:

```powershell
python main.py --endpoint http://localhost:3000/api/v1/report --api-key dev_local --min-interval 15 --max-interval 60 --verbose
```

Service install

- Windows: use Task Scheduler or NSSM to wrap the command above.
- macOS: use launchd (see `launchctl` example in this README later).
- Linux: use systemd service.

Data & privacy

- Machine ID derived from OS-specific stable ID (Windows MachineGuid, macOS IOPlatformUUID, Linux /etc/machine-id). Only the check results are sent.
- Local state file stored under platform-specific user data dir to avoid redundant reports.
