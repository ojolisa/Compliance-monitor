# Compliance Monitor

A comprehensive system monitoring solution that tracks security compliance across Windows, macOS, and Linux endpoints. The system consists of a lightweight agent that performs periodic compliance checks and a web-based server for centralized monitoring and reporting.

## 🚀 Features

### Agent Capabilities
- **Disk Encryption Monitoring**: Tracks BitLocker (Windows), FileVault (macOS), and LUKS (Linux) status
- **OS Update Status**: Monitors pending and available system updates
- **Antivirus Protection**: Checks antivirus software installation and status
- **Sleep Policy Compliance**: Validates power management settings
- **Flexible Scheduling**: Configurable check intervals with randomization
- **Secure Communication**: TLS-encrypted data transmission with API key authentication
- **Cross-Platform**: Supports Windows, macOS, and Linux environments

### Server Features
- **RESTful API**: Secure endpoint for agent data collection
- **Web Dashboard**: Real-time compliance monitoring interface
- **Data Persistence**: JSON-based database with automatic backups
- **Filtering & Search**: Advanced filtering by OS, compliance status, and machine details
- **Statistics**: Overview of fleet compliance status
- **Export Capabilities**: JSON data export for further analysis

## 📋 System Requirements

### Agent
- **Windows**: Windows 10/11, Windows Server 2016+
- **macOS**: macOS 10.14+ (Mojave)
- **Linux**: Modern distributions with systemd
- **Python**: 3.8+ (for source installation)
- **Disk Space**: 50MB minimum
- **Network**: HTTPS connectivity to compliance server

### Server
- **Node.js**: 16.0+
- **RAM**: 512MB minimum
- **Disk Space**: 1GB minimum (for data storage)
- **Network**: Inbound HTTPS/HTTP capability

## 🛠 Installation

### Quick Start - Agent (Windows)

**Option 1: Pre-built Executable**
1. Download the latest release from the releases page
2. Extract `compliance-monitor-agent.exe` to a directory
3. Run PowerShell as Administrator
4. Execute the installer:
   ```powershell
   powershell -ExecutionPolicy Bypass -File install.ps1
   ```

**Option 2: Chocolatey Package Manager**
```powershell
choco install compliance-monitor-agent
```

### Agent Configuration

Create a `.env` file or set environment variables:

```env
# Required for production use
CM_ENDPOINT=https://your-compliance-server.com/api/report
CM_API_KEY=your-secure-api-key

# Optional configuration
CM_MIN_INTERVAL=15          # Minimum check interval (minutes)
CM_MAX_INTERVAL=60          # Maximum check interval (minutes)
CM_VERBOSE=false            # Enable verbose logging
CM_INSECURE=false           # Disable TLS verification (not recommended)

# Testing modes
CM_ONCE=false               # Run once and exit
CM_DRY_RUN=false           # Test mode without sending data
```

### Server Installation

1. **Install Node.js dependencies:**
   ```bash
   cd server
   npm install
   ```

2. **Configure environment:**
   ```env
   PORT=3000
   API_KEY=your-secure-api-key
   DB_PATH=./data/db.json
   ```

3. **Start the server:**
   ```bash
   npm start
   ```

4. **Access the dashboard:**
   Open `http://localhost:3000/admin` in your browser

## 🔧 Configuration

### Agent Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CM_ENDPOINT` | - | **Required** Server API endpoint URL |
| `CM_API_KEY` | - | **Required** Authentication key |
| `CM_MIN_INTERVAL` | 15 | Minimum check interval (minutes) |
| `CM_MAX_INTERVAL` | 60 | Maximum check interval (minutes) |
| `CM_ONCE` | false | Run once and exit |
| `CM_DRY_RUN` | false | Test mode (no data transmission) |
| `CM_VERBOSE` | false | Enable detailed logging |
| `CM_INSECURE` | false | Disable TLS certificate verification |

### Server Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 3000 | HTTP server port |
| `API_KEY` | dev_local | Agent authentication key |
| `DB_PATH` | ./data/db.json | Database file location |

## 📊 Compliance Checks

### Disk Encryption
- **Windows**: BitLocker status and encryption percentage
- **macOS**: FileVault status
- **Linux**: LUKS encryption detection

### OS Updates
- **Windows**: Windows Update status via PowerShell
- **macOS**: Software Update availability
- **Linux**: Package manager update checks (apt, yum, dnf)

### Antivirus Protection
- **Windows**: Windows Defender and third-party AV detection
- **macOS**: Built-in security features and third-party solutions
- **Linux**: ClamAV and other security software

### Sleep Policy
- **Windows**: Power management settings validation
- **macOS**: Energy Saver preferences
- **Linux**: systemd power management

## 🌐 API Reference

### POST /api/report

Submit compliance data from agent.

**Headers:**
```
X-API-Key: your-api-key
Content-Type: application/json
```

**Request Body:**
```json
{
  "machine_id": "unique-machine-identifier",
  "hostname": "DESKTOP-ABC123",
  "os": "Windows",
  "timestamp": 1692454800,
  "checks": {
    "disk_encryption": {
      "ok": true,
      "summary": "BitLocker enabled",
      "data": {"percentage_encrypted": 100}
    },
    "os_updates": {
      "ok": false,
      "summary": "5 updates pending",
      "data": {"pending_count": 5}
    }
  }
}
```

### GET /api/reports

Retrieve compliance reports (authentication required).

**Query Parameters:**
- `os`: Filter by operating system
- `limit`: Number of records to return
- `offset`: Pagination offset

## 🖥 Web Dashboard

The web dashboard provides:

- **Fleet Overview**: Total machines, compliance percentages, recent activity
- **Machine List**: Sortable table with all monitored endpoints
- **Filtering**: By OS, compliance status, hostname, or machine ID
- **Detailed Views**: Click any machine for detailed compliance information
- **Export**: Download compliance data as JSON

### Dashboard Access

Navigate to `http://your-server:3000/admin` to access the monitoring interface.

## 🔧 Development

### Building the Agent

**Windows Executable:**
```powershell
cd agent
python build.py
```

**Cross-Platform Package:**
```bash
cd agent
python -m pip install -r requirements-build.txt
python -m PyInstaller compliance-monitor-agent.spec
```

### Running Tests

**Agent Tests:**
```powershell
cd agent
powershell -File test-agent.ps1
```

**Simple Functionality Test:**
```powershell
cd agent
powershell -File test-simple.ps1
```

### Project Structure

```
compliance-monitor/
├── agent/                          # Compliance monitoring agent
│   ├── agent/                      # Core agent modules
│   │   ├── checks.py              # Compliance check implementations
│   │   ├── state.py               # State management
│   │   ├── transport.py           # Network communication
│   │   └── utils.py               # Utility functions
│   ├── main.py                    # Agent entry point
│   ├── requirements.txt           # Python dependencies
│   ├── install.ps1               # Windows installer script
│   └── build.py                  # Build automation
├── server/                        # Compliance monitoring server
│   ├── index.js                  # Express.js server
│   ├── package.json              # Node.js dependencies
│   ├── data/                     # Database storage
│   └── public/admin/             # Web dashboard
└── chocolatey/                   # Chocolatey package files
```

## 🚨 Security Considerations

### Agent Security
- Uses TLS 1.2+ for all communications
- API key authentication for server access
- No sensitive data stored locally
- Runs with minimal required privileges

### Server Security
- API key authentication for all endpoints
- Input validation and sanitization
- Rate limiting recommended for production
- HTTPS strongly recommended

### Best Practices
1. Use strong, unique API keys
2. Deploy server behind a reverse proxy with HTTPS
3. Regularly rotate API keys
4. Monitor server logs for suspicious activity
5. Keep both agent and server updated

## 📝 Logging

### Agent Logs
- **Windows**: Event Viewer (Application log)
- **Location**: `%ProgramData%\Compliance Monitor\logs\`
- **Verbose Mode**: Set `CM_VERBOSE=true` for detailed output

### Server Logs
- **Console Output**: Standard Node.js logging
- **Access Logs**: HTTP request/response logging
- **Error Logs**: Detailed error information

## 🆘 Troubleshooting

### Common Agent Issues

**Agent not starting:**
1. Check Windows Service status: `Get-Service ComplianceMonitorAgent`
2. Verify configuration in `.env` file
3. Check firewall settings for outbound HTTPS

**Connection errors:**
1. Verify `CM_ENDPOINT` URL is accessible
2. Check `CM_API_KEY` matches server configuration
3. Test network connectivity: `Test-NetConnection your-server -Port 443`

**Permission errors:**
1. Ensure agent runs as Local System or Administrator
2. Check UAC settings on Windows
3. Verify disk encryption tools are accessible

### Common Server Issues

**Server won't start:**
1. Check port availability: `netstat -an | findstr :3000`
2. Verify Node.js version compatibility
3. Check database file permissions

**Agent authentication failures:**
1. Verify `API_KEY` environment variable
2. Check agent configuration matches server
3. Review server logs for authentication attempts