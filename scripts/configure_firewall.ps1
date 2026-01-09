# ============================================
# Configuration Firewall Windows
# RadGestMat - Port 8000
# ============================================
# 
# Crée une règle Windows Firewall pour autoriser
# les connexions entrantes sur le port 8000
# depuis le réseau local uniquement

param(
    [int]$Port = 8000,
    [string]$RuleName = "RadGestMat HTTP",
    [switch]$Remove = $false
)

# Vérifier les privilèges administrateur
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "⚠️  Ce script nécessite les droits administrateur!" -ForegroundColor Red
    Write-Host "   Relancez PowerShell en tant qu'administrateur" -ForegroundColor Yellow
    exit 1
}

# Fonction pour supprimer la règle
function Remove-FirewallRule {
    param([string]$Name)
    
    try {
        $existingRule = Get-NetFirewallRule -DisplayName $Name -ErrorAction SilentlyContinue
        if ($existingRule) {
            Remove-NetFirewallRule -DisplayName $Name -ErrorAction Stop
            Write-Host "✅ Règle '$Name' supprimée" -ForegroundColor Green
            return $true
        } else {
            Write-Host "ℹ️  Règle '$Name' n'existe pas" -ForegroundColor Yellow
            return $false
        }
    } catch {
        Write-Host "❌ Erreur lors de la suppression: $_" -ForegroundColor Red
        return $false
    }
}

# Fonction pour créer la règle
function New-FirewallRule {
    param(
        [string]$Name,
        [int]$PortNumber
    )
    
    try {
        # Vérifier si la règle existe déjà
        $existingRule = Get-NetFirewallRule -DisplayName $Name -ErrorAction SilentlyContinue
        if ($existingRule) {
            Write-Host "ℹ️  Règle '$Name' existe déjà" -ForegroundColor Yellow
            Write-Host "   Pour la recréer, utilisez: .\configure_firewall.ps1 -Remove puis relancez" -ForegroundColor Cyan
            return $true
        }
        
        # Créer la règle pour le port TCP
        New-NetFirewallRule `
            -DisplayName $Name `
            -Name "RadGestMat_HTTP_Port_$PortNumber" `
            -Description "Autorise les connexions HTTP entrantes pour RadGestMat sur le port $PortNumber" `
            -Direction Inbound `
            -Protocol TCP `
            -LocalPort $PortNumber `
            -Action Allow `
            -Profile Domain,Private `
            -Enabled True `
            -ErrorAction Stop
        
        Write-Host "✅ Règle firewall créée: '$Name' (Port $PortNumber)" -ForegroundColor Green
        Write-Host "   Direction: Inbound" -ForegroundColor Gray
        Write-Host "   Protocole: TCP" -ForegroundColor Gray
        Write-Host "   Profil: Domain, Private" -ForegroundColor Gray
        return $true
        
    } catch {
        Write-Host "❌ Erreur lors de la création de la règle: $_" -ForegroundColor Red
        return $false
    }
}

# ====================
# EXÉCUTION
# ====================

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  CONFIGURATION FIREWALL - RADGESTMAT" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

if ($Remove) {
    Write-Host "🗑️  Suppression de la règle firewall..." -ForegroundColor Yellow
    Remove-FirewallRule -Name $RuleName
} else {
    Write-Host "🔥 Création de la règle firewall..." -ForegroundColor Green
    Write-Host "   Port: $Port" -ForegroundColor Gray
    Write-Host "   Nom: $RuleName" -ForegroundColor Gray
    Write-Host ""
    
    $success = New-FirewallRule -Name $RuleName -PortNumber $Port
    
    if ($success) {
        Write-Host ""
        Write-Host "✅ Configuration firewall terminée" -ForegroundColor Green
        Write-Host ""
        Write-Host "📝 Pour vérifier la règle:" -ForegroundColor Cyan
        Write-Host "   Get-NetFirewallRule -DisplayName '$RuleName'" -ForegroundColor White
        Write-Host ""
        Write-Host "📝 Pour supprimer la règle:" -ForegroundColor Cyan
        Write-Host "   .\configure_firewall.ps1 -Remove" -ForegroundColor White
    } else {
        Write-Host ""
        Write-Host "❌ Échec de la configuration firewall" -ForegroundColor Red
        exit 1
    }
}
