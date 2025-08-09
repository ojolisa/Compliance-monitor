# Compliance Monitor Agent - Test Script
# This script tests the built agent executable

param(
    [switch]$DryRun,
    [switch]$Verbose,
    [switch]$Once
)

function Test-Agent {
    param(
        [string]$ExePath,
        [hashtable]$TestEnv
    )
    
    Write-Host "Testing agent executable..." -ForegroundColor Cyan
    
    if (-not (Test-Path $ExePath)) {
        Write-Error "Agent executable not found: $ExePath"
        return $false
    }
    
    Write-Host "Executable found: $ExePath" -ForegroundColor Green
    Write-Host "File size: $([math]::Round((Get-Item $ExePath).Length / 1MB, 2)) MB" -ForegroundColor Gray
    
    # Test dry run
    Write-Host "`nTesting dry run mode..." -ForegroundColor Yellow
    
    try {
        $env:CM_DRY_RUN = "true"
        $env:CM_VERBOSE = "true" 
        $env:CM_ONCE = "true"
        
        # Apply test environment variables
        foreach ($key in $TestEnv.Keys) {
            Set-Item -Path "env:$key" -Value $TestEnv[$key]
        }
        
        $output = & $ExePath 2>&1
        $exitCode = $LASTEXITCODE
        
        Write-Host "Exit code: $exitCode" -ForegroundColor $(if ($exitCode -eq 0) { "Green" } else { "Red" })
        
        if ($Verbose) {
            Write-Host "`nAgent output:" -ForegroundColor Gray
            Write-Host $output -ForegroundColor Gray
        }
        
        # Check for expected output patterns
        $outputText = $output -join "`n"
        $checks = @(
            @{ Pattern = "disk_encryption"; Description = "Disk encryption check" },
            @{ Pattern = "os_updates"; Description = "OS updates check" },
            @{ Pattern = "antivirus"; Description = "Antivirus check" },
            @{ Pattern = "sleep_policy"; Description = "Sleep policy check" }
        )
        
        Write-Host "`nChecking compliance tests:" -ForegroundColor Cyan
        foreach ($check in $checks) {
            if ($outputText -match $check.Pattern) {
                Write-Host "✓ $($check.Description)" -ForegroundColor Green
            } else {
                Write-Host "✗ $($check.Description)" -ForegroundColor Red
            }
        }
        
        return $exitCode -eq 0
        
    }
    catch {
        Write-Error "Failed to run agent: $($_.Exception.Message)"
        return $false
    }
    finally {
        # Clean up environment variables
        Remove-Item env:CM_DRY_RUN -ErrorAction SilentlyContinue
        Remove-Item env:CM_VERBOSE -ErrorAction SilentlyContinue
        Remove-Item env:CM_ONCE -ErrorAction SilentlyContinue
        foreach ($key in $TestEnv.Keys) {
            Remove-Item "env:$key" -ErrorAction SilentlyContinue
        }
    }
}

function Test-ServiceInstallation {
    Write-Host "`nTesting service installation (simulation)..." -ForegroundColor Cyan
    
    $serviceName = "ComplianceMonitorAgent"
    $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
    
    if ($service) {
        Write-Host "Service '$serviceName' exists:" -ForegroundColor Yellow
        Write-Host "  Status: $($service.Status)" -ForegroundColor Gray
        Write-Host "  Start Type: $($service.StartType)" -ForegroundColor Gray
        
        if ($service.Status -eq 'Running') {
            Write-Host "✓ Service is running correctly" -ForegroundColor Green
        } else {
            Write-Host "⚠ Service is not running" -ForegroundColor Yellow
        }
    } else {
        Write-Host "Service '$serviceName' not installed (expected for test)" -ForegroundColor Gray
    }
}

function Test-ConfigFile {
    param([string]$ConfigPath)
    
    Write-Host "`nTesting configuration..." -ForegroundColor Cyan
    
    if (Test-Path $ConfigPath) {
        Write-Host "✓ Config template found: $ConfigPath" -ForegroundColor Green
        
        $content = Get-Content $ConfigPath
        $requiredKeys = @("CM_ENDPOINT", "CM_API_KEY")
        
        foreach ($key in $requiredKeys) {
            if ($content -match "^#?\s*$key=") {
                Write-Host "✓ $key configuration present" -ForegroundColor Green
            } else {
                Write-Host "✗ $key configuration missing" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "✗ Config template not found: $ConfigPath" -ForegroundColor Red
    }
}

# Main test execution
Write-Host "Compliance Monitor Agent - Test Suite" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Test environment variables
$testEnv = @{
    "CM_ENDPOINT" = "https://test-server.example.com/api/report"
    "CM_API_KEY" = "test-api-key-12345"
}

# Test different executable locations
$exePaths = @(
    ".\dist\compliance-monitor-agent.exe",
    ".\release\compliance-monitor-agent.exe"
)

$testPassed = $false

foreach ($exePath in $exePaths) {
    if (Test-Path $exePath) {
        Write-Host "`nTesting executable: $exePath" -ForegroundColor White
        Write-Host "=" * 50
        
        $result = Test-Agent -ExePath $exePath -TestEnv $testEnv
        if ($result) {
            $testPassed = $true
            Write-Host "`n✓ Agent test PASSED" -ForegroundColor Green
            
            # Test configuration
            $configPath = Join-Path (Split-Path $exePath) "config.env.example"
            Test-ConfigFile -ConfigPath $configPath
            
            break
        } else {
            Write-Host "`n✗ Agent test FAILED" -ForegroundColor Red
        }
    }
}

if (-not $testPassed) {
    Write-Host "`nNo working executable found. Please build the agent first." -ForegroundColor Red
    Write-Host "Run: .\build-windows.bat" -ForegroundColor Yellow
    exit 1
}

# Test service installation capabilities
Test-ServiceInstallation

# Summary
Write-Host "`n" + "=" * 50
if ($testPassed) {
    Write-Host "Overall Test Result: PASSED" -ForegroundColor Green
    Write-Host "`nThe agent executable is working correctly!" -ForegroundColor Green
    Write-Host "`nNext steps for deployment:" -ForegroundColor Yellow
    Write-Host "1. Configure .env file with real server details"
    Write-Host "2. Run installer as Administrator: .\install.ps1"
    Write-Host "3. Start the service: Start-Service ComplianceMonitorAgent"
} else {
    Write-Host "Overall Test Result: FAILED" -ForegroundColor Red
    Write-Host "`nPlease check the build and try again." -ForegroundColor Red
}

Write-Host "`nPress any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
