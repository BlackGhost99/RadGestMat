# ============================================
# Démarrage RadGestMat - Réseau Local Admin
# ============================================
# 
# Script de démarrage pour hébergement local sur PC Windows
# - Détecte automatiquement l'IP locale
# - Configure le firewall Windows
# - Démarre Django sur 0.0.0.0:8000
# - Affiche les URLs d'accès

param(
    [switch]$SkipFirewall = $false,
    [switch]$Verbose = $false
)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  RADGESTMAT - HÉBERGEMENT RÉSEAU LOCAL" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# ====================
# 1. DÉTECTION IP LOCALE
# ====================
Write-Host "🔍 1. Détection de l'IP locale..." -ForegroundColor Green

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$getIPScript = Join-Path $scriptPath "get_local_ip.ps1"

if (-not (Test-Path $getIPScript)) {
    Write-Host "❌ Script get_local_ip.ps1 non trouvé!" -ForegroundColor Red
    exit 1
}

$localIP = & $getIPScript -Verbose:$Verbose

if (-not $localIP -or $localIP -eq "127.0.0.1") {
    Write-Host "⚠️  Avertissement: IP locale non détectée, utilisation de localhost" -ForegroundColor Yellow
    Write-Host "   L'application ne sera accessible que depuis ce PC" -ForegroundColor Yellow
}

Write-Host "   ✅ IP détectée: $localIP" -ForegroundColor Green
Write-Host ""

# ====================
# 2. CONFIGURATION FIREWALL
# ====================
if (-not $SkipFirewall) {
    Write-Host "🔥 2. Configuration du firewall Windows..." -ForegroundColor Green
    
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    
    if ($isAdmin) {
        $firewallScript = Join-Path $scriptPath "configure_firewall.ps1"
        if (Test-Path $firewallScript) {
            & $firewallScript -Port 8000 -RuleName "RadGestMat HTTP"
            Write-Host ""
        } else {
            Write-Host "   ⚠️  Script configure_firewall.ps1 non trouvé" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ⚠️  Droits administrateur requis pour configurer le firewall" -ForegroundColor Yellow
        Write-Host "   Vous pouvez le faire manuellement ou relancer en admin" -ForegroundColor Yellow
        Write-Host ""
    }
} else {
    Write-Host "⏭️  2. Configuration firewall ignorée (SkipFirewall)" -ForegroundColor Yellow
    Write-Host ""
}

# ====================
# 3. VÉRIFICATION ENVIRONNEMENT
# ====================
Write-Host "🐍 3. Vérification de l'environnement Python..." -ForegroundColor Green

# Chercher l'environnement virtuel
$projectRoot = Split-Path -Parent $scriptPath
$venvPaths = @(
    Join-Path $projectRoot "env_new",
    Join-Path $projectRoot ".venv",
    Join-Path $projectRoot "env",
    Join-Path $projectRoot "venv"
)

$pythonExe = $null
foreach ($venvPath in $venvPaths) {
    $testPython = Join-Path $venvPath "Scripts\python.exe"
    if (Test-Path $testPython) {
        $pythonExe = $testPython
        Write-Host "   ✅ Environnement trouvé: $venvPath" -ForegroundColor Green
        break
    }
}

if (-not $pythonExe) {
    # Essayer avec python global
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $pythonExe = "python"
            Write-Host "   ✅ Python global trouvé: $pythonVersion" -ForegroundColor Green
        }
    } catch {
        Write-Host "   ❌ Python non trouvé!" -ForegroundColor Red
        Write-Host "   Installez Python ou créez un environnement virtuel" -ForegroundColor Yellow
        exit 1
    }
}

# Vérifier manage.py
$managePy = Join-Path $projectRoot "manage.py"
if (-not (Test-Path $managePy)) {
    Write-Host "❌ manage.py non trouvé dans $projectRoot" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ====================
# 4. CONFIGURATION VARIABLES D'ENVIRONNEMENT
# ====================
Write-Host "⚙️  4. Configuration des variables d'environnement..." -ForegroundColor Green

# Définir l'IP locale pour Django
$env:LOCAL_NETWORK_IP = $localIP
$env:DJANGO_SETTINGS_MODULE = "radgestmat.settings.local_network"
$env:PYTHONIOENCODING = "utf-8"

# ALLOWED_HOSTS avec IP locale
$env:ALLOWED_HOSTS = "$localIP,localhost,127.0.0.1"

# CSRF_TRUSTED_ORIGINS
$env:CSRF_TRUSTED_ORIGINS = "http://$localIP,http://$localIP:8000,http://localhost,http://localhost:8000"

# QR_DOMAIN
$env:QR_DOMAIN = "http://$localIP:8000"

Write-Host "   ✅ Variables configurées" -ForegroundColor Green
Write-Host "   - LOCAL_NETWORK_IP: $localIP" -ForegroundColor Gray
Write-Host "   - DJANGO_SETTINGS_MODULE: radgestmat.settings.local_network" -ForegroundColor Gray
Write-Host ""

# ====================
# 5. APPLIQUER MIGRATIONS (si nécessaire)
# ====================
Write-Host "🗄️  5. Vérification des migrations..." -ForegroundColor Green

Set-Location $projectRoot

try {
    & $pythonExe manage.py migrate --check --noinput 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   ⚠️  Migrations en attente, application..." -ForegroundColor Yellow
        & $pythonExe manage.py migrate --noinput
        Write-Host "   ✅ Migrations appliquées" -ForegroundColor Green
    } else {
        Write-Host "   ✅ Base de données à jour" -ForegroundColor Green
    }
} catch {
    Write-Host "   ⚠️  Impossible de vérifier les migrations: $_" -ForegroundColor Yellow
}

Write-Host ""

# ====================
# 6. COLLECTER FICHIERS STATIQUES (si nécessaire)
# ====================
Write-Host "📦 6. Vérification des fichiers statiques..." -ForegroundColor Green

$staticRoot = Join-Path $projectRoot "staticfiles"
if (-not (Test-Path $staticRoot) -or (Get-ChildItem $staticRoot -ErrorAction SilentlyContinue | Measure-Object).Count -eq 0) {
    Write-Host "   ⚠️  Fichiers statiques manquants, collecte..." -ForegroundColor Yellow
    & $pythonExe manage.py collectstatic --noinput
    Write-Host "   ✅ Fichiers statiques collectés" -ForegroundColor Green
} else {
    Write-Host "   ✅ Fichiers statiques présents" -ForegroundColor Green
}

Write-Host ""

# ====================
# 7. AFFICHER INFORMATIONS D'ACCÈS
# ====================
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  ✅ PRÊT À DÉMARRER" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 Informations d'accès:" -ForegroundColor Yellow
Write-Host ""
Write-Host "   🌐 Depuis ce PC:" -ForegroundColor White
Write-Host "      http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "   🌐 Depuis autres PC (réseau admin):" -ForegroundColor White
Write-Host "      http://$localIP:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "   📱 Depuis smartphone (réseau admin):" -ForegroundColor White
Write-Host "      http://$localIP:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "   👤 Interface Admin:" -ForegroundColor White
Write-Host "      http://$localIP:8000/admin/" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  IMPORTANT:" -ForegroundColor Yellow
Write-Host "   - Les smartphones doivent être sur le réseau ADMIN (pas WiFi client)" -ForegroundColor Yellow
Write-Host "   - Si l'IP change (DHCP), redémarrer ce script" -ForegroundColor Yellow
Write-Host ""
Write-Host "🛑 Pour arrêter: Ctrl+C" -ForegroundColor Red
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# ====================
# 8. DÉMARRER SERVEUR DJANGO
# ====================
Write-Host "🚀 Démarrage du serveur Django..." -ForegroundColor Green
Write-Host ""

& $pythonExe manage.py runserver 0.0.0.0:8000
