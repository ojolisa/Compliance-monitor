#!/usr/bin/env python3
"""
Build script for creating cross-platform executables of the Compliance Monitor Agent
"""
import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return success status"""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
        if result.stdout.strip():
            print(f"✓ Success: {result.stdout.strip()}")
        else:
            print("✓ Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error (code {e.returncode}): {e.stderr.strip() if e.stderr else 'Unknown error'}")
        if e.stdout:
            print(f"Output: {e.stdout.strip()}")
        return False
    except Exception as e:
        print(f"✗ Exception: {str(e)}")
        return False

def install_build_dependencies():
    """Install PyInstaller and other build dependencies"""
    print("Installing build dependencies...")
    return run_command([sys.executable, "-m", "pip", "install", "pyinstaller"])

def clean_build_dirs():
    """Clean previous build artifacts"""
    print("Cleaning build directories...")
    dirs_to_clean = ["build", "dist", "__pycache__"]
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"Removed {dir_name}/")
            except Exception as e:
                print(f"Warning: Could not remove {dir_name}/: {e}")
    
    # Also clean .spec files
    for spec_file in ["compliance-monitor-agent.spec"]:
        if os.path.exists(spec_file):
            try:
                os.remove(spec_file)
                print(f"Removed {spec_file}")
            except Exception as e:
                print(f"Warning: Could not remove {spec_file}: {e}")
    
    return True

def create_pyinstaller_spec():
    """Create PyInstaller spec file for the agent"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'agent.checks',
        'agent.state', 
        'agent.transport',
        'agent.utils'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='compliance-monitor-agent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
    
    try:
        with open("compliance-monitor-agent.spec", "w") as f:
            f.write(spec_content)
        print("Created PyInstaller spec file")
        return True
    except Exception as e:
        print(f"Failed to create spec file: {e}")
        return False

def build_executable():
    """Build the executable using PyInstaller"""
    print("Building executable...")
    return run_command([
        sys.executable, "-m", "PyInstaller", 
        "--clean",
        "compliance-monitor-agent.spec"
    ])

def create_distribution_package():
    """Create a distribution package with executable and config files"""
    os_name = platform.system().lower()
    arch = platform.machine().lower()
    
    # Create distribution directory
    dist_name = f"compliance-monitor-agent-{os_name}-{arch}"
    dist_dir = Path("dist") / dist_name
    
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    dist_dir.mkdir(parents=True)
    
    # Copy executable
    exe_name = "compliance-monitor-agent"
    if os_name == "windows":
        exe_name += ".exe"
    
    exe_path = Path("dist") / exe_name
    if exe_path.exists():
        shutil.copy2(exe_path, dist_dir / exe_name)
        print(f"Copied executable to {dist_dir}")
    
    # Create sample config file
    config_content = '''# Compliance Monitor Agent Configuration
# Copy this file to .env and configure for your environment

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
'''
    
    with open(dist_dir / "config.env.example", "w") as f:
        f.write(config_content)
    
    # Create installation instructions
    if os_name == "windows":
        create_windows_installer(dist_dir)
    elif os_name == "darwin":
        create_macos_installer(dist_dir)
    else:
        create_linux_installer(dist_dir)
    
    # Create archive
    archive_name = f"{dist_name}.zip"
    shutil.make_archive(str(Path("dist") / dist_name), 'zip', str(dist_dir))
    print(f"Created distribution package: dist/{archive_name}")
    
    return True

def create_windows_installer(dist_dir):
    """Create Windows installation script"""
    install_script = '''@echo off
echo Installing Compliance Monitor Agent...

REM Create installation directory
set INSTALL_DIR=C:\\Program Files\\Compliance Monitor
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Copy executable
copy compliance-monitor-agent.exe "%INSTALL_DIR%\\"

REM Copy config template
copy config.env.example "%INSTALL_DIR%\\"

REM Create Windows service using sc command
echo Creating Windows service...
sc create ComplianceMonitorAgent binPath= "\"%INSTALL_DIR%\\compliance-monitor-agent.exe\"" start= auto
sc description ComplianceMonitorAgent "Compliance Monitor Agent - System Health Monitoring"

echo.
echo Installation complete!
echo.
echo Next steps:
echo 1. Edit %INSTALL_DIR%\\config.env.example and save as .env
echo 2. Start the service: net start ComplianceMonitorAgent
echo.
pause
'''
    
    with open(dist_dir / "install.bat", "w") as f:
        f.write(install_script)
    
    uninstall_script = '''@echo off
echo Uninstalling Compliance Monitor Agent...

REM Stop and remove service
net stop ComplianceMonitorAgent
sc delete ComplianceMonitorAgent

REM Remove installation directory
set INSTALL_DIR=C:\\Program Files\\Compliance Monitor
if exist "%INSTALL_DIR%" rmdir /s /q "%INSTALL_DIR%"

echo Uninstallation complete!
pause
'''
    
    with open(dist_dir / "uninstall.bat", "w") as f:
        f.write(uninstall_script)

def create_macos_installer(dist_dir):
    """Create macOS installation script"""
    install_script = '''#!/bin/bash
set -e

echo "Installing Compliance Monitor Agent..."

# Create installation directory
INSTALL_DIR="/usr/local/bin"
CONFIG_DIR="$HOME/.compliance-monitor"

# Copy executable
sudo cp compliance-monitor-agent "$INSTALL_DIR/"
sudo chmod +x "$INSTALL_DIR/compliance-monitor-agent"

# Create config directory
mkdir -p "$CONFIG_DIR"
cp config.env.example "$CONFIG_DIR/"

# Create launchd plist for daemon
PLIST_PATH="$HOME/Library/LaunchAgents/com.compliancemonitor.agent.plist"
cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.compliancemonitor.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>$INSTALL_DIR/compliance-monitor-agent</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$CONFIG_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$CONFIG_DIR/agent.log</string>
    <key>StandardErrorPath</key>
    <string>$CONFIG_DIR/agent.error.log</string>
</dict>
</plist>
EOF

echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Edit $CONFIG_DIR/config.env.example and save as .env"
echo "2. Load the daemon: launchctl load $PLIST_PATH"
echo "3. Start the daemon: launchctl start com.compliancemonitor.agent"
'''
    
    with open(dist_dir / "install.sh", "w") as f:
        f.write(install_script)
    
    os.chmod(dist_dir / "install.sh", 0o755)

def create_linux_installer(dist_dir):
    """Create Linux installation script"""
    install_script = '''#!/bin/bash
set -e

echo "Installing Compliance Monitor Agent..."

# Create installation directory
INSTALL_DIR="/usr/local/bin"
CONFIG_DIR="/etc/compliance-monitor"

# Copy executable
sudo cp compliance-monitor-agent "$INSTALL_DIR/"
sudo chmod +x "$INSTALL_DIR/compliance-monitor-agent"

# Create config directory
sudo mkdir -p "$CONFIG_DIR"
sudo cp config.env.example "$CONFIG_DIR/"

# Create systemd service
sudo tee /etc/systemd/system/compliance-monitor-agent.service > /dev/null << EOF
[Unit]
Description=Compliance Monitor Agent
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=1
User=root
WorkingDirectory=$CONFIG_DIR
ExecStart=$INSTALL_DIR/compliance-monitor-agent

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable compliance-monitor-agent

echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Edit $CONFIG_DIR/config.env.example and save as .env"
echo "2. Start the service: sudo systemctl start compliance-monitor-agent"
echo "3. Check status: sudo systemctl status compliance-monitor-agent"
'''
    
    with open(dist_dir / "install.sh", "w") as f:
        f.write(install_script)
    
    os.chmod(dist_dir / "install.sh", 0o755)

def main():
    """Main build process"""
    print("=== Compliance Monitor Agent Build Process ===")
    print(f"Platform: {platform.system()} {platform.machine()}")
    print()
    
    # Check if we're in the right directory
    if not os.path.exists("main.py"):
        print("Error: main.py not found. Please run this script from the agent directory.")
        return False
    
    steps = [
        ("Installing build dependencies", install_build_dependencies),
        ("Cleaning build directories", clean_build_dirs),
        ("Creating PyInstaller spec", create_pyinstaller_spec),
        ("Building executable", build_executable),
        ("Creating distribution package", create_distribution_package),
    ]
    
    for step_name, step_func in steps:
        print(f"\n--- {step_name} ---")
        if not step_func():
            print(f"Build failed at step: {step_name}")
            return False
    
    print("\n=== Build Complete! ===")
    print("Distribution packages created in dist/ directory")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
