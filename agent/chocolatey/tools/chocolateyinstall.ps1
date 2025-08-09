$ErrorActionPreference = 'Stop'

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
