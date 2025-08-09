# Simple test script for the Compliance Monitor Agent
param(
    [switch]$Verbose
)

Write-Host "Compliance Monitor Agent - Simple Test" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Find the executable
$exePaths = @(
    ".\dist\compliance-monitor-agent.exe",
    ".\release\compliance-monitor-agent.exe"
)

$exeFound = $null
foreach ($path in $exePaths) {
    if (Test-Path $path) {
        $exeFound = $path
        break
    }
}

if (-not $exeFound) {
    Write-Host "Error: Agent executable not found" -ForegroundColor Red
    Write-Host "Please build the agent first using: .\build-windows.bat" -ForegroundColor Yellow
    exit 1
}

Write-Host "Found executable: $exeFound" -ForegroundColor Green

# Test the agent in dry-run mode
Write-Host "`nTesting agent in dry-run mode..." -ForegroundColor Yellow

$env:CM_DRY_RUN = "true"
$env:CM_VERBOSE = "true"
$env:CM_ONCE = "true"
$env:CM_ENDPOINT = "https://test.example.com/api/report"
$env:CM_API_KEY = "test-key"

try {
    $result = & $exeFound
    $exitCode = $LASTEXITCODE
    
    Write-Host "`nExit Code: $exitCode" -ForegroundColor $(if ($exitCode -eq 0) { "Green" } else { "Red" })
    
    if ($Verbose -and $result) {
        Write-Host "`nAgent Output:" -ForegroundColor Gray
        $result | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
    }
    
    if ($exitCode -eq 0) {
        Write-Host "`n SUCCESS: Agent is working correctly!" -ForegroundColor Green
    } else {
        Write-Host "`n FAILED: Agent returned error code $exitCode" -ForegroundColor Red
    }
    
} catch {
    Write-Host "`n FAILED: Exception occurred - $($_.Exception.Message)" -ForegroundColor Red
} finally {
    # Clean up environment variables
    Remove-Item env:CM_DRY_RUN -ErrorAction SilentlyContinue
    Remove-Item env:CM_VERBOSE -ErrorAction SilentlyContinue
    Remove-Item env:CM_ONCE -ErrorAction SilentlyContinue
    Remove-Item env:CM_ENDPOINT -ErrorAction SilentlyContinue
    Remove-Item env:CM_API_KEY -ErrorAction SilentlyContinue
}

Write-Host "`nTest complete!" -ForegroundColor Cyan
