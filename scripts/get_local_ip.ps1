# ============================================
# Script de Détection IP Locale
# RadGestMat - Réseau Admin
# ============================================
# 
# Détecte l'IP IPv4 du réseau admin (exclut loopback)
# Retourne la première IP valide trouvée

param(
    [switch]$Verbose = $false
)

function Get-LocalNetworkIP {
    <#
    .SYNOPSIS
    Détecte l'IP IPv4 locale du réseau admin.
    
    .DESCRIPTION
    Essaie plusieurs méthodes pour trouver l'IP active:
    1. Interface réseau avec connexion active (priorité)
    2. Interface avec passerelle par défaut
    3. Première interface IPv4 non-loopback
    
    .OUTPUTS
    String - Adresse IP IPv4 ou "127.0.0.1" si aucune trouvée
    #>
    
    $ipAddresses = @()
    
    # Méthode 1: Interfaces avec connexion active et passerelle
    try {
        $adapters = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | 
            Where-Object { 
                $_.IPAddress -ne '127.0.0.1' -and 
                $_.InterfaceAlias -notlike '*Loopback*' -and
                $_.InterfaceAlias -notlike '*isatap*' -and
                $_.InterfaceAlias -notlike '*Teredo*'
            }
        
        foreach ($adapter in $adapters) {
            $interface = Get-NetAdapter -InterfaceIndex $adapter.InterfaceIndex -ErrorAction SilentlyContinue
            if ($interface -and $interface.Status -eq 'Up') {
                # Vérifier si l'interface a une passerelle (réseau actif)
                $route = Get-NetRoute -InterfaceIndex $adapter.InterfaceIndex -DestinationPrefix "0.0.0.0/0" -ErrorAction SilentlyContinue
                if ($route) {
                    $ipAddresses += $adapter.IPAddress
                    if ($Verbose) {
                        Write-Host "  ✓ Interface active avec passerelle: $($adapter.InterfaceAlias) - $($adapter.IPAddress)" -ForegroundColor Green
                    }
                }
            }
        }
    } catch {
        if ($Verbose) {
            Write-Host "  ⚠ Erreur lors de la détection des interfaces: $_" -ForegroundColor Yellow
        }
    }
    
    # Si aucune IP trouvée avec passerelle, prendre la première interface active
    if ($ipAddresses.Count -eq 0) {
        try {
            $adapters = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | 
                Where-Object { 
                    $_.IPAddress -ne '127.0.0.1' -and 
                    $_.InterfaceAlias -notlike '*Loopback*' -and
                    $_.InterfaceAlias -notlike '*isatap*' -and
                    $_.InterfaceAlias -notlike '*Teredo*'
                } |
                Sort-Object InterfaceIndex
            
            foreach ($adapter in $adapters) {
                $interface = Get-NetAdapter -InterfaceIndex $adapter.InterfaceIndex -ErrorAction SilentlyContinue
                if ($interface -and $interface.Status -eq 'Up') {
                    $ipAddresses += $adapter.IPAddress
                    if ($Verbose) {
                        Write-Host "  ✓ Interface active: $($adapter.InterfaceAlias) - $($adapter.IPAddress)" -ForegroundColor Green
                    }
                    break  # Prendre la première
                }
            }
        } catch {
            if ($Verbose) {
                Write-Host "  ⚠ Erreur lors de la détection des interfaces: $_" -ForegroundColor Yellow
            }
        }
    }
    
    # Retourner la première IP trouvée
    if ($ipAddresses.Count -gt 0) {
        $selectedIP = $ipAddresses[0]
        if ($Verbose) {
            Write-Host "  → IP sélectionnée: $selectedIP" -ForegroundColor Cyan
        }
        return $selectedIP
    }
    
    # Fallback: localhost
    if ($Verbose) {
        Write-Host "  ⚠ Aucune IP réseau trouvée, utilisation de localhost" -ForegroundColor Yellow
    }
    return "127.0.0.1"
}

# Exécuter la fonction
$localIP = Get-LocalNetworkIP

# Afficher le résultat
if ($Verbose) {
    Write-Host ""
    Write-Host "IP Locale Détectée: $localIP" -ForegroundColor Cyan
}

# Retourner l'IP (pour utilisation dans autres scripts)
return $localIP
