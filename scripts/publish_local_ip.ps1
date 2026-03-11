param(
    [Parameter(Mandatory = $true)]
    [string]$SharePath,
    [string]$FileName = 'radgestmat_ip.txt',
    [switch]$ShowOutput
)

$ipCandidates = Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
    $_.IPAddress -ne '127.0.0.1' -and
    $_.InterfaceAlias -notlike '*Loopback*' -and
    $_.AddressState -eq 'Preferred'
}

$ip = $null
$dhcp = $ipCandidates | Where-Object { $_.PrefixOrigin -eq 'Dhcp' } | Select-Object -First 1
if ($dhcp) {
    $ip = $dhcp.IPAddress
} else {
    $ip = ($ipCandidates | Select-Object -First 1).IPAddress
}

if (-not $ip) {
    Write-Host 'No IPv4 address found.' -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $SharePath)) {
    Write-Host ('SharePath not reachable: ' + $SharePath) -ForegroundColor Red
    exit 1
}

$ipFile = Join-Path $SharePath $FileName
$ip | Out-File -FilePath $ipFile -Encoding ascii -Force

if ($ShowOutput) {
    Write-Host ('Wrote ' + $ip + ' to ' + $ipFile) -ForegroundColor Green
}
