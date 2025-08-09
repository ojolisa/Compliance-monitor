#!/usr/bin/env python3
"""
Cross-platform build helper for Compliance Monitor Agent
Usage: python make.py [command]

Commands:
  install-deps  - Install build dependencies
  clean        - Clean build artifacts
  build        - Build executable for current platform
  package      - Create distribution package
  all          - Run clean, build, and package
"""

import sys
import subprocess
import os
from pathlib import Path

def run_python_script(script_name, *args):
    """Run a Python script with arguments"""
    cmd = [sys.executable, script_name] + list(args)
    return subprocess.run(cmd).returncode == 0

def install_deps():
    """Install runtime and build dependencies"""
    print("Installing runtime dependencies...")
    if not run_python_script("-m", "pip", "install", "-r", "requirements.txt"):
        return False
    
    print("Installing build dependencies...")
    if not run_python_script("-m", "pip", "install", "-r", "requirements-build.txt"):
        return False
    
    return True

def main():
    if len(sys.argv) < 2:
        command = "all"
    else:
        command = sys.argv[1]
    
    if command == "install-deps":
        success = install_deps()
    elif command == "clean" or command == "build" or command == "package" or command == "all":
        if command == "all":
            # Install deps first for convenience
            if not install_deps():
                print("Failed to install dependencies")
                sys.exit(1)
        
        # Run the main build script
        success = run_python_script("build.py")
    else:
        print(__doc__)
        sys.exit(1)
    
    if not success:
        print(f"Command '{command}' failed")
        sys.exit(1)
    else:
        print(f"Command '{command}' completed successfully")

if __name__ == "__main__":
    main()
