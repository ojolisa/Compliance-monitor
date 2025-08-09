# Compliance Monitor Agent - Quick Start

## Windows Installation

### Option 1: PowerShell Installer (Recommended)
1. Extract this package to a temporary directory
2. Open PowerShell as Administrator
3. Run: `Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process`
4. Run: `.\install.ps1`
5. Follow the prompts to configure

### Option 2: Manual Installation
1. Copy `compliance-monitor-agent.exe` to `C:\Program Files\Compliance Monitor\`
2. Copy `config.env.example` to same directory and rename to `.env`
3. Edit `.env` with your server details:
   ```
   CM_ENDPOINT=https://your-server.com/api/report
   CM_API_KEY=your-api-key-here
   ```
4. Install as service:
   ```
   sc create ComplianceMonitorAgent binPath= "C:\Program Files\Compliance Monitor\compliance-monitor-agent.exe" start= auto
   ```
5. Start service: `net start ComplianceMonitorAgent`

## Configuration

Edit the `.env` file with these required settings:

- `CM_ENDPOINT`: Your server URL (e.g., https://yourserver.com/api/report)
- `CM_API_KEY`: Authentication key for your server

Optional settings:
- `CM_MIN_INTERVAL=15`: Minimum check interval (minutes)
- `CM_MAX_INTERVAL=60`: Maximum check interval (minutes)
- `CM_VERBOSE=false`: Enable debug logging

## Verification

Check service status:
```powershell
Get-Service ComplianceMonitorAgent
```

Test manually:
```powershell
cd "C:\Program Files\Compliance Monitor"
.\compliance-monitor-agent.exe
```

## Support

For issues: https://github.com/your-org/compliance-monitor/issues
