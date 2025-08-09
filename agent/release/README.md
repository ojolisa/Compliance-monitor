# Compliance Monitor Agent

A cross-platform system compliance monitoring utility that checks disk encryption, OS updates, antivirus status, and sleep settings.

## Quick Start

### Option 1: Download Pre-built Packages
Download the latest release for your platform from the releases page and follow the platform-specific installation instructions.

### Option 2: Build from Source
See the [Building from Source](#building-from-source) section below.

## Installation

### Windows

#### Method 1: Windows Installer (Recommended)
1. Download `compliance-monitor-agent-installer.exe`
2. Run as Administrator
3. Follow the installation wizard
4. The service will be automatically configured

#### Method 2: Manual Installation
1. Download and extract `compliance-monitor-agent-windows-*.zip`
2. Run `install.bat` as Administrator
3. Edit `C:\Program Files\Compliance Monitor\.env` with your configuration
4. Start the service: `net start ComplianceMonitorAgent`

### macOS

1. Download and extract `compliance-monitor-agent-darwin-*.zip`
2. Run: `chmod +x install.sh && ./install.sh`
3. Edit `~/.compliance-monitor/.env` with your configuration
4. Load the daemon: `launchctl load ~/Library/LaunchAgents/com.compliancemonitor.agent.plist`
5. Start the daemon: `launchctl start com.compliancemonitor.agent`

### Linux

#### Ubuntu/Debian
1. Download and extract `compliance-monitor-agent-linux-*.zip`
2. Run: `chmod +x install.sh && ./install.sh`
3. Edit `/etc/compliance-monitor/.env` with your configuration
4. Start the service: `sudo systemctl start compliance-monitor-agent`
5. Enable auto-start: `sudo systemctl enable compliance-monitor-agent`

#### RHEL/CentOS/Fedora
Same as Ubuntu/Debian - the installer detects the distribution automatically.

## Configuration

Create a `.env` file in the installation directory with the following settings:

```bash
# Required: Server endpoint and API key
CM_ENDPOINT=https://your-server.com/api/report
CM_API_KEY=your-api-key-here

# Optional: Check intervals (minutes)
CM_MIN_INTERVAL=15
CM_MAX_INTERVAL=60

# Optional: Debug and testing
CM_VERBOSE=false
CM_DRY_RUN=false
CM_ONCE=false
CM_INSECURE=false
```

### Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `CM_ENDPOINT` | Server API endpoint URL | Required |
| `CM_API_KEY` | Authentication key | Required |
| `CM_MIN_INTERVAL` | Minimum check interval (minutes) | 15 |
| `CM_MAX_INTERVAL` | Maximum check interval (minutes) | 60 |
| `CM_VERBOSE` | Enable verbose logging | false |
| `CM_DRY_RUN` | Test mode - don't send data | false |
| `CM_ONCE` | Run once and exit | false |
| `CM_INSECURE` | Skip TLS certificate verification | false |

## System Requirements

### Windows
- Windows 10/11 or Windows Server 2016+
- Administrator privileges for service installation
- PowerShell 5.0+ (for some compliance checks)

### macOS
- macOS 10.14+ (Mojave or later)
- Administrator privileges for daemon installation

### Linux
- Most modern distributions (Ubuntu 18.04+, CentOS 7+, etc.)
- Root privileges for service installation
- systemd (for service management)

## Compliance Checks

The agent performs the following checks:

### 1. Disk Encryption
- **Windows**: BitLocker status via `manage-bde`
- **macOS**: FileVault status via `fdesetup`
- **Linux**: LUKS/dm-crypt detection via `lsblk`

### 2. OS Updates
- **Windows**: Pending reboot detection via registry
- **macOS**: Available updates via `softwareupdate`
- **Linux**: Package manager checks (apt/dnf/yum)

### 3. Antivirus
- **Windows**: Windows Defender + SecurityCenter2 query
- **macOS**: Process detection of known AV software
- **Linux**: Process detection of common AV daemons

### 4. Sleep Policy
- **Windows**: Power configuration via `powercfg`
- **macOS**: Power management via `pmset`
- **Linux**: GNOME settings via `gsettings`

Policy: Sleep/screen lock should be ≤ 10 minutes for compliance.

## Building from Source

### Prerequisites

1. **Python 3.8+** with pip
2. **Git** for cloning the repository
3. **Platform-specific tools** (optional):
   - Windows: NSIS for advanced installer
   - macOS: Xcode command line tools
   - Linux: Standard build tools

### Build Process

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/compliance-monitor.git
   cd compliance-monitor/agent
   ```

2. **Install dependencies**:
   ```bash
   python make.py install-deps
   ```
   
   Or manually:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-build.txt
   ```

3. **Build executable**:
   ```bash
   python make.py all
   ```
   
   Or step-by-step:
   ```bash
   python make.py clean
   python make.py build
   python make.py package
   ```

4. **Find built packages** in `dist/` directory

### Advanced Windows Installer

To create a professional Windows installer with NSIS:

1. **Install NSIS**: Download from https://nsis.sourceforge.io/
2. **Build the executable** first: `python make.py build`
3. **Compile installer**: Right-click `installer.nsi` → "Compile NSIS Script"

### Build Outputs

The build process creates:
- **Executable**: `dist/compliance-monitor-agent` (or `.exe` on Windows)
- **Distribution package**: `dist/compliance-monitor-agent-{os}-{arch}.zip`
- **Installation scripts**: Platform-specific installers included in package

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Windows: Run as Administrator
   - macOS/Linux: Use `sudo` for system-wide installation

2. **Service Won't Start**
   - Check configuration in `.env` file
   - Verify network connectivity to server
   - Check service logs

3. **Build Failures**
   - Ensure all dependencies are installed
   - Check Python version (3.8+ required)
   - Clear build cache: `python make.py clean`

### Log Locations

- **Windows Service**: Event Viewer → Windows Logs → Application
- **macOS Daemon**: `~/.compliance-monitor/agent.log`
- **Linux Service**: `journalctl -u compliance-monitor-agent`

### Manual Testing

Run the agent manually for testing:

```bash
# Test configuration
CM_ONCE=true CM_VERBOSE=true ./compliance-monitor-agent

# Dry run (don't send data)
CM_DRY_RUN=true CM_VERBOSE=true ./compliance-monitor-agent
```

## Development

### Project Structure

```
agent/
├── main.py              # Entry point
├── agent/
│   ├── checks.py        # Compliance check implementations
│   ├── state.py         # State management
│   ├── transport.py     # HTTP communication
│   └── utils.py         # Utility functions
├── build.py             # Build script
├── make.py              # Build helper
├── installer.nsi        # Windows NSIS installer
└── requirements*.txt    # Dependencies
```

### Adding New Checks

1. Add check function to `agent/checks.py`
2. Return dict with `ok`, `status`, `summary`, and `data` fields
3. Add to `collect_all_checks()` function
4. Test across platforms

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure cross-platform compatibility
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- GitHub Issues: https://github.com/your-org/compliance-monitor/issues
- Documentation: https://your-org.github.io/compliance-monitor/
