#!/usr/bin/env python3
"""
Deployment script for Compliance Monitor Agent
This script creates production-ready packages for all supported platforms
"""

import os
import sys
import shutil
import subprocess
import zipfile
from pathlib import Path
import json

def create_release_package():
    """Create a complete release package with all files"""
    print("Creating release package...")
    
    # Ensure we have the built executable
    exe_path = Path("dist/compliance-monitor-agent.exe")
    if not exe_path.exists():
        print("Error: Built executable not found. Run build.py first.")
        return False
    
    # Create release directory
    release_dir = Path("release")
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir()
    
    # Copy main files
    files_to_copy = [
        ("dist/compliance-monitor-agent.exe", "compliance-monitor-agent.exe"),
        ("config.env.example", "config.env.example"),
        ("install.ps1", "install.ps1"),
        ("README.md", "README.md"),
        ("requirements.txt", "requirements.txt"),
    ]
    
    for src, dst in files_to_copy:
        if Path(src).exists():
            shutil.copy2(src, release_dir / dst)
            print(f"Copied {src} -> {dst}")
    
    # Create quick start guide
    quickstart_content = r'''# Compliance Monitor Agent - Quick Start

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
'''
    
    with open(release_dir / "QUICKSTART.md", "w") as f:
        f.write(quickstart_content)
    
    # Create version info
    version_info = {
        "version": "1.0.0",
        "build_date": "2025-08-09",
        "platform": "windows-amd64",
        "features": [
            "Disk encryption monitoring",
            "OS update checking", 
            "Antivirus detection",
            "Sleep policy compliance",
            "Windows service integration"
        ]
    }
    
    with open(release_dir / "version.json", "w") as f:
        json.dump(version_info, f, indent=2)
    
    # Create final ZIP package
    zip_path = Path("compliance-monitor-agent-v1.0.0-windows.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in release_dir.rglob("*"):
            if file_path.is_file():
                zipf.write(file_path, file_path.relative_to(release_dir))
    
    print(f"Created release package: {zip_path}")
    print(f"Package size: {zip_path.stat().st_size / 1024 / 1024:.1f} MB")
    
    return True

def create_chocolatey_package():
    """Create a Chocolatey package for Windows distribution"""
    choco_dir = Path("chocolatey")
    if choco_dir.exists():
        shutil.rmtree(choco_dir)
    choco_dir.mkdir()
    
    # Create nuspec file
    nuspec_content = '''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://schemas.microsoft.com/packaging/2015/06/nuspec.xsd">
  <metadata>
    <id>compliance-monitor-agent</id>
    <version>1.0.0</version>
    <packageSourceUrl>https://github.com/your-org/compliance-monitor</packageSourceUrl>
    <owners>YourOrg</owners>
    <title>Compliance Monitor Agent</title>
    <authors>YourOrg</authors>
    <projectUrl>https://github.com/your-org/compliance-monitor</projectUrl>
    <iconUrl>https://github.com/your-org/compliance-monitor/raw/main/icon.png</iconUrl>
    <copyright>2025 YourOrg</copyright>
    <licenseUrl>https://github.com/your-org/compliance-monitor/blob/main/LICENSE</licenseUrl>
    <requireLicenseAcceptance>false</requireLicenseAcceptance>
    <projectSourceUrl>https://github.com/your-org/compliance-monitor</projectSourceUrl>
    <docsUrl>https://github.com/your-org/compliance-monitor/wiki</docsUrl>
    <bugTrackerUrl>https://github.com/your-org/compliance-monitor/issues</bugTrackerUrl>
    <tags>compliance monitoring security admin</tags>
    <summary>Cross-platform system compliance monitoring agent</summary>
    <description>
Compliance Monitor Agent is a lightweight utility that monitors system compliance including:
- Disk encryption status (BitLocker, FileVault, LUKS)
- OS update status
- Antivirus presence and status  
- Sleep/screen lock policies
- Automated reporting to central dashboard
    </description>
    <releaseNotes>Initial release with Windows support</releaseNotes>
  </metadata>
  <files>
    <file src="tools\\**" target="tools" />
  </files>
</package>'''
    
    with open(choco_dir / "compliance-monitor-agent.nuspec", "w") as f:
        f.write(nuspec_content)
    
    # Create tools directory and install script
    tools_dir = choco_dir / "tools"
    tools_dir.mkdir()
    
    install_script = '''$ErrorActionPreference = 'Stop'

$packageName = 'compliance-monitor-agent'
$url64 = 'https://github.com/your-org/compliance-monitor/releases/download/v1.0.0/compliance-monitor-agent-v1.0.0-windows.zip'
$checksum64 = 'YOUR_CHECKSUM_HERE'

$packageArgs = @{
  packageName   = $packageName
  unzipLocation = $toolsDir
  url64bit      = $url64
  checksum64    = $checksum64
  checksumType64= 'sha256'
}

Install-ChocolateyZipPackage @packageArgs

# Run installer
$installScript = Join-Path $toolsDir 'install.ps1'
if (Test-Path $installScript) {
    & PowerShell -ExecutionPolicy Bypass -File $installScript
}
'''
    
    with open(tools_dir / "chocolateyinstall.ps1", "w") as f:
        f.write(install_script)
    
    uninstall_script = '''$ErrorActionPreference = 'Stop'

# Run uninstaller if available
$uninstallScript = "C:\\Program Files\\Compliance Monitor\\install.ps1"
if (Test-Path $uninstallScript) {
    & PowerShell -ExecutionPolicy Bypass -File $uninstallScript -Uninstall
}
'''
    
    with open(tools_dir / "chocolateyuninstall.ps1", "w") as f:
        f.write(uninstall_script)
    
    print("Created Chocolatey package structure in chocolatey/")
    print("To build: Run 'choco pack' in the chocolatey directory")
    
    return True  # Make sure to return True for success

def main():
    """Main deployment process"""
    print("=== Compliance Monitor Agent Deployment ===")
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("Error: main.py not found. Please run this script from the agent directory.")
        return False
    
    # Check if executable exists
    if not Path("dist/compliance-monitor-agent.exe").exists():
        print("Error: No built executable found. Please run build.py first.")
        return False
    
    steps = [
        ("Creating release package", create_release_package),
        ("Creating Chocolatey package", create_chocolatey_package),
    ]
    
    for step_name, step_func in steps:
        print(f"\n--- {step_name} ---")
        if not step_func():
            print(f"Deployment failed at step: {step_name}")
            return False
    
    print("\n=== Deployment Complete! ===")
    print("Created packages:")
    print("- compliance-monitor-agent-v1.0.0-windows.zip (Complete release)")
    print("- chocolatey/ (Chocolatey package)")
    print("- release/ (Unpacked release files)")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
