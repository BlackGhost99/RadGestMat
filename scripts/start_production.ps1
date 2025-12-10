# ============================================
# Démarrage Rapide Production - RadGestMat
# ============================================

Write-Host "🚀 Démarrage RadGestMat en mode Production..." -ForegroundColor Cyan
Write-Host ""

# Trouver l'IP locale
$IP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*"}).IPAddress
if (-not $IP) {
    $IP = "localhost"
}

Write-Host "📍 IP du serveur : $IP" -ForegroundColor Green
Write-Host ""

# Configuration environnement
$env:DJANGO_SETTINGS_MODULE = "radgestmat.settings.production"
$env:PYTHONIOENCODING = "utf-8"

# Charger .env.production si existe
$EnvFile = ".\.env.production"
if (Test-Path $EnvFile) {
    Write-Host "⚙️  Chargement configuration production..." -ForegroundColor Yellow
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.+)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
} else {
    Write-Host "⚠️  Fichier .env.production non trouvé" -ForegroundColor Yellow
    Write-Host "   Utilisation de la configuration par défaut" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  RADGESTMAT - MODE PRODUCTION" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Accès depuis :" -ForegroundColor Yellow
Write-Host "   PC (local)  : http://localhost:8000" -ForegroundColor White
Write-Host "   PC (réseau) : http://$IP:8000" -ForegroundColor White
Write-Host "   Smartphone  : http://$IP:8000" -ForegroundColor White
Write-Host ""
Write-Host "👤 Admin : http://$IP:8000/admin/" -ForegroundColor Cyan
Write-Host ""
Write-Host "📱 Pour smartphone : Connecter au WiFi puis ouvrir l'URL ci-dessus" -ForegroundColor Yellow
Write-Host ""
Write-Host "🛑 Pour arrêter : Ctrl+C" -ForegroundColor Red
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Démarrer le serveur
Write-Host "🔄 Démarrage du serveur Django..." -ForegroundColor Green
Write-Host ""

.\env_new\Scripts\python.exe manage.py runserver 0.0.0.0:8000
