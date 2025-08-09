$ErrorActionPreference = 'Stop'

# Run uninstaller if available
$uninstallScript = "C:\Program Files\Compliance Monitor\install.ps1"
if (Test-Path $uninstallScript) {
    & PowerShell -ExecutionPolicy Bypass -File $uninstallScript -Uninstall
}
