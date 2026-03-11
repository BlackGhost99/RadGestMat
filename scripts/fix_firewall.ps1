# Script pour configurer le firewall Windows pour RadGestMat
# Doit etre execute en tant qu'administrateur

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERREUR: Ce script doit etre execute en tant qu'administrateur!" -ForegroundColor Red
    Write-Host "Clic droit sur PowerShell > Executer en tant qu'administrateur" -ForegroundColor Yellow
    exit 1
}

Write-Host "Configuration du firewall pour RadGestMat..." -ForegroundColor Green

# Supprimer l'ancienne regle si elle existe
$existingRule = Get-NetFirewallRule -DisplayName "RadGestMat HTTP" -ErrorAction SilentlyContinue
if ($existingRule) {
    Remove-NetFirewallRule -DisplayName "RadGestMat HTTP" -ErrorAction SilentlyContinue
    Write-Host "Ancienne regle supprimee" -ForegroundColor Yellow
}

# Creer la nouvelle regle
try {
    # Supprimer l'ancienne regle si elle existe avec un nom different
    $oldRules = Get-NetFirewallRule | Where-Object { $_.DisplayName -like '*RadGestMat*' -or $_.DisplayName -like '*8000*' }
    foreach ($rule in $oldRules) {
        Remove-NetFirewallRule -Name $rule.Name -ErrorAction SilentlyContinue
        Write-Host "Ancienne regle supprimee: $($rule.DisplayName)" -ForegroundColor Yellow
    }
    
    New-NetFirewallRule `
        -DisplayName "RadGestMat HTTP" `
        -Name "RadGestMat_HTTP_Port_8000" `
        -Description "Autorise les connexions HTTP entrantes pour RadGestMat sur le port 8000" `
        -Direction Inbound `
        -Protocol TCP `
        -LocalPort 8000 `
        -Action Allow `
        -Profile Any `
        -Enabled True `
        -ErrorAction Stop
    
    Write-Host "Regle firewall creee avec succes!" -ForegroundColor Green
    Write-Host "Port 8000 est maintenant ouvert pour les connexions entrantes" -ForegroundColor Green
} catch {
    Write-Host "Erreur lors de la creation de la regle: $_" -ForegroundColor Red
    exit 1
}

# Afficher la regle creee
Write-Host ""
Write-Host "Regle creee:" -ForegroundColor Cyan
Get-NetFirewallRule -DisplayName "RadGestMat HTTP" | Select-Object DisplayName, Enabled, Direction, Action, Profile | Format-Table
