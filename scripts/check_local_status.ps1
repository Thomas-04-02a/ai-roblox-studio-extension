$ErrorActionPreference = 'Stop'

try {
    $bridge = Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8765/status' -TimeoutSec 5 | Select-Object -ExpandProperty Content
    Write-Host '--- Bridge ---'
    Write-Host $bridge
}
catch {
    Write-Host 'Bridge is offline on http://127.0.0.1:8765'
    Write-Host $_.Exception.Message
}

try {
    $mock = Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8767' -TimeoutSec 5 | Select-Object -ExpandProperty Content
    Write-Host '--- Mock MCP ---'
    Write-Host $mock
}
catch {
    Write-Host 'Mock MCP is offline on http://127.0.0.1:8767'
    Write-Host $_.Exception.Message
}
