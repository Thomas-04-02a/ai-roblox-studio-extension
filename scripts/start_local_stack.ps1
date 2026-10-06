$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root '.venv\Scripts\python.exe'

if (-not (Test-Path $python)) {
    throw "Python venv not found at $python"
}

$bridgeCmd = "cd '$root'; & '$python' scripts\start_bridge.py"
$mockCmd = "cd '$root'; & '$python' bridge\mock_roblox_server.py"

Start-Process powershell -ArgumentList '-NoExit', '-Command', $bridgeCmd
Start-Process powershell -ArgumentList '-NoExit', '-Command', $mockCmd

Start-Sleep -Seconds 2

try {
    $bridge = Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8765/status' -TimeoutSec 5 | Select-Object -ExpandProperty Content
    $mock = Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8767' -TimeoutSec 5 | Select-Object -ExpandProperty Content
    Write-Host '--- Bridge status ---'
    Write-Host $bridge
    Write-Host '--- Mock server status ---'
    Write-Host $mock
}
catch {
    Write-Host 'Local stack is still starting or not reachable yet.'
    Write-Host $_.Exception.Message
}

Write-Host ''
Write-Host 'Both local terminals were launched in separate PowerShell windows.'
Write-Host 'Leave them open while testing the extension.'
