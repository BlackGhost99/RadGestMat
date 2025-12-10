# ============================================
# Script de Déploiement Production - Windows
# RadGestMat - Gestion de Matériel
# ============================================

param(
    [string]$ServerIP = "192.168.1.100",
    [string]$ProjectPath = "C:\RadGestMat",
    [switch]$UsePostgreSQL = $false,
    [switch]$InstallService = $true
)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  DÉPLOIEMENT RADGESTMAT EN PRODUCTION" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier les privilèges admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "⚠️  Ce script nécessite les droits administrateur!" -ForegroundColor Red
    Write-Host "   Relancez PowerShell en tant qu'administrateur" -ForegroundColor Yellow
    exit 1
}

# ====================
# 1. CONFIGURATION
# ====================
Write-Host "📋 1. Configuration..." -ForegroundColor Green

$EnvPath = Join-Path $ProjectPath "RadGestMat\env_prod"
$ManagePath = Join-Path $ProjectPath "RadGestMat\manage.py"
$PythonExe = Join-Path $EnvPath "Scripts\python.exe"

Write-Host "   📁 Projet : $ProjectPath"
Write-Host "   🐍 Python : $PythonExe"
Write-Host "   🌐 IP Serveur : $ServerIP"

# Vérifier que le projet existe
if (-not (Test-Path $ManagePath)) {
    Write-Host "❌ manage.py non trouvé dans $ProjectPath\RadGestMat" -ForegroundColor Red
    exit 1
}

# ====================
# 2. CRÉER ENVIRONNEMENT VIRTUEL
# ====================
Write-Host ""
Write-Host "🐍 2. Création environnement virtuel production..." -ForegroundColor Green

if (-not (Test-Path $EnvPath)) {
    python -m venv $EnvPath
    Write-Host "   ✅ Environnement créé"
} else {
    Write-Host "   ℹ️  Environnement existant"
}

# Activer l'environnement
$ActivateScript = Join-Path $EnvPath "Scripts\Activate.ps1"
& $ActivateScript

# ====================
# 3. INSTALLER DÉPENDANCES
# ====================
Write-Host ""
Write-Host "📦 3. Installation des dépendances..." -ForegroundColor Green

Set-Location (Join-Path $ProjectPath "RadGestMat")

& $PythonExe -m pip install --upgrade pip setuptools wheel
& $PythonExe -m pip install -r requirements.txt

if ($UsePostgreSQL) {
    Write-Host "   📊 Installation psycopg2 pour PostgreSQL..."
    & $PythonExe -m pip install psycopg2-binary
}

Write-Host "   ✅ Dépendances installées"

# ====================
# 4. CONFIGURATION ENVIRONNEMENT
# ====================
Write-Host ""
Write-Host "⚙️  4. Configuration variables d'environnement..." -ForegroundColor Green

$EnvFile = Join-Path $ProjectPath "RadGestMat\.env.production"

# Générer SECRET_KEY si n'existe pas
if (-not (Test-Path $EnvFile)) {
    $SecretKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 50 | ForEach-Object {[char]$_})
    
    $EnvContent = @"
# Configuration Production RadGestMat
DJANGO_SETTINGS_MODULE=radgestmat.settings.production
SECRET_KEY=$SecretKey
ALLOWED_HOSTS=$ServerIP,localhost,127.0.0.1
DEBUG=False

# Base de données (décommenter si PostgreSQL)
# USE_POSTGRESQL=true
# DB_NAME=radgestmat
# DB_USER=radgestmat_user
# DB_PASSWORD=VotreMotDePasseSecurise
# DB_HOST=localhost
# DB_PORT=5432

# Email (Gmail ou SMTP entreprise)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=votre.email@entreprise.com
EMAIL_HOST_PASSWORD=mot_de_passe_application

# WhatsApp Twilio (optionnel)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
"@
    
    Set-Content -Path $EnvFile -Value $EnvContent
    Write-Host "   ✅ Fichier .env.production créé"
    Write-Host "   ⚠️  IMPORTANT : Éditer $EnvFile avec vos paramètres" -ForegroundColor Yellow
} else {
    Write-Host "   ℹ️  Fichier .env.production existant"
}

# Charger les variables
Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.+)$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim()
        [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

# ====================
# 5. MIGRATIONS ET STATIC
# ====================
Write-Host ""
Write-Host "🗄️  5. Migrations et fichiers statiques..." -ForegroundColor Green

$env:DJANGO_SETTINGS_MODULE = "radgestmat.settings.production"

& $PythonExe manage.py migrate --noinput
Write-Host "   ✅ Migrations appliquées"

& $PythonExe manage.py collectstatic --noinput
Write-Host "   ✅ Fichiers statiques collectés"

# ====================
# 6. CRÉER SUPERUSER
# ====================
Write-Host ""
Write-Host "👤 6. Création superuser..." -ForegroundColor Green

$CreateSuperuser = Read-Host "   Créer un compte superuser ? (O/N)"
if ($CreateSuperuser -eq "O" -or $CreateSuperuser -eq "o") {
    & $PythonExe manage.py createsuperuser
}

# ====================
# 7. CONFIGURATION PARE-FEU
# ====================
Write-Host ""
Write-Host "🔥 7. Configuration pare-feu..." -ForegroundColor Green

try {
    New-NetFirewallRule -DisplayName "RadGestMat HTTP" -Direction Inbound -LocalPort 80 -Protocol TCP -Action Allow -ErrorAction SilentlyContinue
    New-NetFirewallRule -DisplayName "RadGestMat Django" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow -ErrorAction SilentlyContinue
    Write-Host "   ✅ Règles pare-feu créées (ports 80, 8000)"
} catch {
    Write-Host "   ⚠️  Impossible de créer les règles pare-feu" -ForegroundColor Yellow
}

# ====================
# 8. INSTALLER SERVICE WINDOWS (NSSM)
# ====================
if ($InstallService) {
    Write-Host ""
    Write-Host "🔧 8. Installation du service Windows..." -ForegroundColor Green
    
    $NSSMPath = "C:\nssm\nssm.exe"
    
    if (Test-Path $NSSMPath) {
        # Service Django
        & $NSSMPath install RadGestMat $PythonExe
        & $NSSMPath set RadGestMat AppParameters "manage.py runserver 0.0.0.0:8000"
        & $NSSMPath set RadGestMat AppDirectory (Join-Path $ProjectPath "RadGestMat")
        & $NSSMPath set RadGestMat AppEnvironmentExtra "DJANGO_SETTINGS_MODULE=radgestmat.settings.production"
        & $NSSMPath set RadGestMat DisplayName "RadGestMat - Gestion Matériel"
        & $NSSMPath set RadGestMat Description "Système de gestion de matériel RadGestMat"
        & $NSSMPath set RadGestMat Start SERVICE_AUTO_START
        
        # Service Scheduler
        & $NSSMPath install RadGestMatScheduler $PythonExe
        & $NSSMPath set RadGestMatScheduler AppParameters "manage.py run_scheduler"
        & $NSSMPath set RadGestMatScheduler AppDirectory (Join-Path $ProjectPath "RadGestMat")
        & $NSSMPath set RadGestMatScheduler AppEnvironmentExtra "DJANGO_SETTINGS_MODULE=radgestmat.settings.production"
        & $NSSMPath set RadGestMatScheduler DisplayName "RadGestMat - Scheduler"
        & $NSSMPath set RadGestMatScheduler Start SERVICE_AUTO_START
        
        Write-Host "   ✅ Services Windows créés"
        Write-Host "   ℹ️  Pour démarrer : nssm start RadGestMat"
        
        $StartNow = Read-Host "   Démarrer les services maintenant ? (O/N)"
        if ($StartNow -eq "O" -or $StartNow -eq "o") {
            & $NSSMPath start RadGestMat
            & $NSSMPath start RadGestMatScheduler
            Write-Host "   ✅ Services démarrés"
        }
    } else {
        Write-Host "   ⚠️  NSSM non trouvé dans C:\nssm\" -ForegroundColor Yellow
        Write-Host "   📥 Télécharger depuis : https://nssm.cc/download" -ForegroundColor Cyan
    }
}

# ====================
# 9. BACKUP AUTOMATIQUE
# ====================
Write-Host ""
Write-Host "💾 9. Configuration backup automatique..." -ForegroundColor Green

$BackupDir = Join-Path $ProjectPath "RadGestMat\backups"
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
}

$BackupScript = @"
# Script de backup automatique
`$BackupDir = "$BackupDir"
`$Date = Get-Date -Format "yyyyMMdd_HHmm"

# Backup SQLite
Copy-Item "$ProjectPath\RadGestMat\db.sqlite3" "`$BackupDir\db_`$Date.sqlite3"

# Cleanup (garder 7 jours)
Get-ChildItem `$BackupDir -Filter "db_*.sqlite3" | Where-Object {`$_.LastWriteTime -lt (Get-Date).AddDays(-7)} | Remove-Item

Write-Host "Backup effectué : `$Date"
"@

$BackupScriptPath = Join-Path $ProjectPath "RadGestMat\scripts\backup_prod.ps1"
Set-Content -Path $BackupScriptPath -Value $BackupScript

# Créer tâche planifiée
try {
    $Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File $BackupScriptPath"
    $Trigger = New-ScheduledTaskTrigger -Daily -At "02:00AM"
    Register-ScheduledTask -TaskName "RadGestMat Backup" -Action $Action -Trigger $Trigger -Force | Out-Null
    Write-Host "   ✅ Tâche de backup planifiée (tous les jours à 2h)"
} catch {
    Write-Host "   ⚠️  Impossible de créer la tâche planifiée" -ForegroundColor Yellow
}

# ====================
# 10. RÉSUMÉ
# ====================
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  ✅ DÉPLOIEMENT TERMINÉ" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 Informations d'accès :" -ForegroundColor Yellow
Write-Host "   🌐 URL : http://$ServerIP" -ForegroundColor White
Write-Host "   🌐 Local : http://localhost:8000" -ForegroundColor White
Write-Host "   👤 Admin : http://$ServerIP/admin/" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Gestion des services :" -ForegroundColor Yellow
Write-Host "   Démarrer : nssm start RadGestMat"
Write-Host "   Arrêter  : nssm stop RadGestMat"
Write-Host "   Statut   : nssm status RadGestMat"
Write-Host ""
Write-Host "📝 Prochaines étapes :" -ForegroundColor Yellow
Write-Host "   1. Éditer .env.production avec vos paramètres Email/WhatsApp"
Write-Host "   2. Configurer une IP fixe pour ce serveur"
Write-Host "   3. Tester l'accès depuis un autre PC : http://$ServerIP"
Write-Host "   4. Tester depuis smartphone (WiFi entreprise)"
Write-Host ""
Write-Host "📚 Documentation complète : DEPLOIEMENT_PRODUCTION_INTERNE.md" -ForegroundColor Cyan
Write-Host ""
Write-Host "🎉 RadGestMat est prêt pour la production !" -ForegroundColor Green
Write-Host ""
