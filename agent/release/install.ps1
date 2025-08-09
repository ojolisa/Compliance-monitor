# Compliance Monitor Agent - Windows PowerShell Installer
# Run as Administrator: powershell -ExecutionPolicy Bypass -File install.ps1

param(
    [switch]$Uninstall,
    [string]$InstallPath = "$env:ProgramFiles\Compliance Monitor",
    [string]$ServiceName = "ComplianceMonitorAgent"
)

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Install-Agent {
    Write-Host "Installing Compliance Monitor Agent..." -ForegroundColor Green
    
    # Check if running as administrator
    if (-not (Test-Administrator)) {
        Write-Error "This script must be run as Administrator"
        exit 1
    }
    
    # Create installation directory
    if (-not (Test-Path $InstallPath)) {
        New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
        Write-Host "Created directory: $InstallPath"
    }
    
    # Copy executable
    if (Test-Path "compliance-monitor-agent.exe") {
        Copy-Item "compliance-monitor-agent.exe" "$InstallPath\" -Force
        Write-Host "Copied executable to $InstallPath"
    } else {
        Write-Error "compliance-monitor-agent.exe not found in current directory"
        exit 1
    }
    
    # Copy config template
    if (Test-Path "config.env.example") {
        Copy-Item "config.env.example" "$InstallPath\" -Force
        Write-Host "Copied configuration template"
    }
    
    # Create Windows service
    try {
        $servicePath = "`"$InstallPath\compliance-monitor-agent.exe`""
        
        # Remove existing service if it exists
        $existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if ($existingService) {
            Write-Host "Stopping existing service..."
            Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
            sc.exe delete $ServiceName | Out-Null
            Start-Sleep -Seconds 2
        }
        
        # Create new service
        Write-Host "Creating Windows service..."
        $result = sc.exe create $ServiceName binPath= $servicePath start= auto
        if ($LASTEXITCODE -eq 0) {
            sc.exe description $ServiceName "Compliance Monitor Agent - System Health Monitoring" | Out-Null
            Write-Host "Service created successfully" -ForegroundColor Green
        } else {
            Write-Error "Failed to create service: $result"
            exit 1
        }
        
    } catch {
        Write-Error "Failed to create service: $($_.Exception.Message)"
        exit 1
    }
    
    # Create Start Menu shortcuts
    try {
        $startMenuPath = "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\Compliance Monitor"
        if (-not (Test-Path $startMenuPath)) {
            New-Item -ItemType Directory -Path $startMenuPath -Force | Out-Null
        }
        
        $WshShell = New-Object -ComObject WScript.Shell
        
        # Agent shortcut
        $agentShortcut = $WshShell.CreateShortcut("$startMenuPath\Compliance Monitor Agent.lnk")
        $agentShortcut.TargetPath = "$InstallPath\compliance-monitor-agent.exe"
        $agentShortcut.WorkingDirectory = $InstallPath
        $agentShortcut.Description = "Compliance Monitor Agent"
        $agentShortcut.Save()
        
        # Uninstall shortcut
        $uninstallShortcut = $WshShell.CreateShortcut("$startMenuPath\Uninstall Compliance Monitor.lnk")
        $uninstallShortcut.TargetPath = "powershell.exe"
        $uninstallShortcut.Arguments = "-ExecutionPolicy Bypass -File `"$InstallPath\install.ps1`" -Uninstall"
        $uninstallShortcut.WorkingDirectory = $InstallPath
        $uninstallShortcut.Description = "Uninstall Compliance Monitor Agent"
        $uninstallShortcut.Save()
        
        Write-Host "Created Start Menu shortcuts"
        
    } catch {
        Write-Warning "Failed to create Start Menu shortcuts: $($_.Exception.Message)"
    }
    
    # Copy this installer script to installation directory for uninstall
    Copy-Item $PSCommandPath "$InstallPath\install.ps1" -Force -ErrorAction SilentlyContinue
    
    Write-Host ""
    Write-Host "Installation completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Edit the configuration file:"
    Write-Host "   $InstallPath\config.env.example"
    Write-Host "   Save it as .env with your server details"
    Write-Host ""
    Write-Host "2. Start the service:"
    Write-Host "   net start $ServiceName"
    Write-Host "   or"
    Write-Host "   Start-Service -Name $ServiceName"
    Write-Host ""
    Write-Host "3. Check service status:"
    Write-Host "   Get-Service -Name $ServiceName"
    Write-Host ""
}

function Uninstall-Agent {
    Write-Host "Uninstalling Compliance Monitor Agent..." -ForegroundColor Red
    
    # Check if running as administrator
    if (-not (Test-Administrator)) {
        Write-Error "This script must be run as Administrator"
        exit 1
    }
    
    # Stop and remove service
    try {
        $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if ($service) {
            Write-Host "Stopping service..."
            Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
            
            Write-Host "Removing service..."
            sc.exe delete $ServiceName | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Service removed successfully"
            }
        } else {
            Write-Host "Service not found"
        }
    } catch {
        Write-Warning "Error removing service: $($_.Exception.Message)"
    }
    
    # Remove Start Menu shortcuts
    try {
        $startMenuPath = "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\Compliance Monitor"
        if (Test-Path $startMenuPath) {
            Remove-Item $startMenuPath -Recurse -Force
            Write-Host "Removed Start Menu shortcuts"
        }
    } catch {
        Write-Warning "Failed to remove Start Menu shortcuts: $($_.Exception.Message)"
    }
    
    # Remove installation directory
    try {
        if (Test-Path $InstallPath) {
            # Ask for confirmation before removing config
            $configExists = Test-Path "$InstallPath\.env"
            if ($configExists) {
                $response = Read-Host "Remove configuration file? (y/N)"
                if ($response -eq 'y' -or $response -eq 'Y') {
                    Remove-Item $InstallPath -Recurse -Force
                    Write-Host "Removed installation directory and configuration"
                } else {
                    # Remove everything except .env
                    Get-ChildItem $InstallPath | Where-Object { $_.Name -ne '.env' } | Remove-Item -Recurse -Force
                    Write-Host "Removed installation files (kept configuration)"
                }
            } else {
                Remove-Item $InstallPath -Recurse -Force
                Write-Host "Removed installation directory"
            }
        }
    } catch {
        Write-Warning "Failed to remove installation directory: $($_.Exception.Message)"
    }
    
    Write-Host ""
    Write-Host "Uninstallation completed!" -ForegroundColor Green
}

function Show-ServiceStatus {
    try {
        $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if ($service) {
            Write-Host ""
            Write-Host "Service Status:" -ForegroundColor Cyan
            Write-Host "Name: $($service.Name)"
            Write-Host "Status: $($service.Status)"
            Write-Host "Start Type: $($service.StartType)"
            
            if ($service.Status -eq 'Running') {
                Write-Host "Service is running correctly!" -ForegroundColor Green
            } elseif ($service.Status -eq 'Stopped') {
                Write-Host "Service is stopped. Start with: Start-Service -Name $ServiceName" -ForegroundColor Yellow
            }
        } else {
            Write-Host "Service not found. Please run installation first." -ForegroundColor Red
        }
    } catch {
        Write-Error "Error checking service status: $($_.Exception.Message)"
    }
}

# Main execution
try {
    Write-Host "Compliance Monitor Agent Installer" -ForegroundColor Cyan
    Write-Host "=================================" -ForegroundColor Cyan
    
    if ($Uninstall) {
        Uninstall-Agent
    } else {
        Install-Agent
        Show-ServiceStatus
    }
    
} catch {
    Write-Error "Installation failed: $($_.Exception.Message)"
    exit 1
}

Write-Host ""
Write-Host "For support, visit: https://github.com/your-org/compliance-monitor" -ForegroundColor Gray
