# Script simplifie pour demarrer RadGestMat
# Sans logs de debug pour eviter problemes d'encodage

$localIP = "10.105.42.118"
$projectRoot = "S:\Brice\RadGestMat"

# Variables d'environnement
$env:LOCAL_NETWORK_IP = $localIP
$env:DJANGO_SETTINGS_MODULE = "radgestmat.settings.local_network"
$env:ALLOWED_HOSTS = "$localIP,localhost,127.0.0.1"
$env:CSRF_TRUSTED_ORIGINS = "http://$localIP,http://$localIP:8000,http://localhost,http://localhost:8000"

# Chercher Python
$pythonExe = $null
$venvPaths = @(
    "$projectRoot\env_new",
    "$projectRoot\.venv",
    "$projectRoot\env"
)

foreach ($venvPath in $venvPaths) {
    $testPython = "$venvPath\Scripts\python.exe"
    if (Test-Path $testPython) {
        $pythonExe = $testPython
        break
    }
}

if (-not $pythonExe) {
    $pythonExe = "python"
}

Set-Location $projectRoot

Write-Host "IP: $localIP"
Write-Host "Python: $pythonExe"
Write-Host "URL: http://$localIP:8000"
Write-Host ""

# Verifier le port
$portInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "ATTENTION: Port 8000 deja utilise!" -ForegroundColor Red
}

# Verifier l'IP
$activeIPs = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -ne '127.0.0.1' }
$ipMatch = $activeIPs | Where-Object { $_.IPAddress -eq $localIP }
if (-not $ipMatch) {
    Write-Host "ATTENTION: IP $localIP non trouvee sur les interfaces actives!" -ForegroundColor Yellow
    Write-Host "IPs actives:" -ForegroundColor Yellow
    $activeIPs | ForEach-Object { Write-Host "  - $($_.IPAddress)" -ForegroundColor Yellow }
}

Write-Host ""
Write-Host "Demarrage du serveur Django..." -ForegroundColor Green
Write-Host ""

& $pythonExe manage.py runserver 0.0.0.0:8000
