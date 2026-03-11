# ============================================
# Demarrage Rapide Production - RadGestMat
# ============================================

Write-Host "Demarrage RadGestMat en mode Production..." -ForegroundColor Cyan
Write-Host ""

# Trouver l'IP locale
$IPs = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*"}).IPAddress
if ($IPs -is [array]) {
    $IP = $IPs[0]
} elseif ($IPs) {
    $IP = $IPs
} else {
    $IP = "localhost"
}
Write-Host "IP du serveur : $IP" -ForegroundColor Green
Write-Host ""

# Configuration environnement
$env:ENVIRONMENT = "production"
$env:PYTHONIOENCODING = "utf-8"

# Charger .env si existe (utilise python-decouple)
$EnvFile = ".\.env"
if (Test-Path $EnvFile) {
    Write-Host "[*] Chargement configuration depuis .env..." -ForegroundColor Yellow
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.+)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
} else {
    Write-Host "[!] Fichier .env non trouve" -ForegroundColor Yellow
    Write-Host "    Utilisation de la configuration par defaut" -ForegroundColor Yellow
    Write-Host "    Creez .env a partir de .env.example" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  RADGESTMAT - MODE PRODUCTION" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Verifier le firewall
$firewallRule = Get-NetFirewallRule -DisplayName "RadGestMat HTTP" -ErrorAction SilentlyContinue
if (-not $firewallRule -or -not $firewallRule.Enabled) {
    Write-Host "[!] ATTENTION: Regle firewall pour le port 8000 non configuree" -ForegroundColor Yellow
    Write-Host "    Pour configurer le firewall, executez en tant qu'administrateur:" -ForegroundColor Yellow
    Write-Host "    .\scripts\configure_firewall.ps1" -ForegroundColor White
    Write-Host ""
}

Write-Host "Acces depuis :" -ForegroundColor Yellow
Write-Host "   PC (local)  : http://localhost:8000" -ForegroundColor White
if ($IP -and $IP -ne "localhost") {
    Write-Host "   PC (reseau) : http://$IP:8000" -ForegroundColor White
    Write-Host "   Smartphone  : http://$IP:8000" -ForegroundColor White
    Write-Host ""
    Write-Host "Admin : http://$IP:8000/admin/" -ForegroundColor Cyan
} else {
    Write-Host "   PC (reseau) : http://localhost:8000" -ForegroundColor White
    Write-Host "   Smartphone  : http://localhost:8000" -ForegroundColor White
    Write-Host ""
    Write-Host "Admin : http://localhost:8000/admin/" -ForegroundColor Cyan
}
Write-Host ""
Write-Host "Pour smartphone : Connecter au WiFi puis ouvrir l'URL ci-dessus" -ForegroundColor Yellow
Write-Host ""
Write-Host "Pour arreter : Ctrl+C" -ForegroundColor Red
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Demarrer le serveur
Write-Host "[*] Demarrage du serveur Django..." -ForegroundColor Green
Write-Host ""

# Detectar l'environnement Python
$PythonExe = $null
$envPaths = @(".\env_new\Scripts\python.exe", ".\venv\Scripts\python.exe", ".\env\Scripts\python.exe", ".\env_prod\Scripts\python.exe")
foreach ($path in $envPaths) {
    if (Test-Path $path) {
        $PythonExe = $path
        Write-Host "[*] Utilisation de l'environnement virtuel: $path" -ForegroundColor Gray
        break
    }
}

if (-not $PythonExe) {
    # Utiliser python du PATH
    $PythonExe = "python"
    Write-Host "[*] Utilisation de Python du PATH" -ForegroundColor Gray
    Write-Host "[!] Attention: Assurez-vous que Python et les dependances sont installees" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[*] Demarrage avec Waitress (serveur WSGI compatible Windows)..." -ForegroundColor Green
Write-Host ""

# Utiliser waitress au lieu de runserver pour production
& $PythonExe -m waitress --listen=0.0.0.0:8000 radgestmat.wsgi:application
