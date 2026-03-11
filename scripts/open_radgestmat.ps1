param(
    [Parameter(Mandatory = $true)]
    [string]$SharePath,
    [string]$FileName = 'radgestmat_ip.txt',
    [int]$Port = 8000,
    [int]$Retries = 5,
    [int]$DelaySeconds = 2,
    [switch]$ShowOutput
)

$ipFile = Join-Path $SharePath $FileName
$ip = ''

for ($i = 0; $i -lt $Retries; $i++) {
    if (Test-Path $ipFile) {
        $ip = (Get-Content $ipFile -TotalCount 1).Trim()
        if ($ip) {
            break
        }
    }
    Start-Sleep -Seconds $DelaySeconds
}

if (-not $ip) {
    Write-Host ('IP file not found or empty: ' + $ipFile) -ForegroundColor Red
    exit 1
}

$url = 'http://' + $ip + ':' + $Port
if ($ShowOutput) {
    Write-Host ('Opening ' + $url) -ForegroundColor Green
}

Start-Process $url
