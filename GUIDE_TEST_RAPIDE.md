# ⚡ Test Rapide - Diagnostic Connexion

## Test depuis le PC Client

### Option 1 : Script Complet

Copiez le contenu du fichier `TEST_CONNEXION_CLIENT.ps1` et exécutez-le dans PowerShell sur le PC client.

### Option 2 : Commandes Directes

Exécutez ces commandes directement dans PowerShell **depuis le PC client** (pas le serveur) :

```powershell
$serverIP = "10.105.42.118"
$port = 8000

Write-Host "Test de connexion a RadGestMat" -ForegroundColor Cyan
Write-Host "Serveur: $serverIP`:$port" -ForegroundColor Yellow
Write-Host ""

# Test 1: Ping
Write-Host "1. Ping..." -ForegroundColor Green
$ping = Test-Connection -ComputerName $serverIP -Count 2 -Quiet
if ($ping) {
    Write-Host "   OK" -ForegroundColor Green
} else {
    Write-Host "   ECHOUE" -ForegroundColor Red
    exit
}

# Test 2: Port TCP
Write-Host "2. Port TCP $port..." -ForegroundColor Green
try {
    $tcp = New-Object System.Net.Sockets.TcpClient
    $tcp.Connect($serverIP, $port)
    Write-Host "   OK - Port accessible" -ForegroundColor Green
    $tcp.Close()
} catch {
    Write-Host "   ECHOUE - $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Le port est bloque par un firewall" -ForegroundColor Yellow
    exit
}

# Test 3: HTTP
Write-Host "3. HTTP..." -ForegroundColor Green
try {
    $response = Invoke-WebRequest -Uri "http://${serverIP}:${port}" -UseBasicParsing -TimeoutSec 5
    Write-Host "   OK - Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host ""
    Write-Host "SUCCESS: L application est accessible!" -ForegroundColor Green
} catch {
    Write-Host "   ECHOUE - $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        Write-Host "   Status: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Yellow
    }
}
```

## Résultats Possibles

### Cas 1 : Ping OK, Port ECHOUE
**Problème** : Firewall bloque le port 8000  
**Solution** : Configurer le firewall sur le serveur avec `.\scripts\fix_firewall.ps1` (en admin)

### Cas 2 : Ping OK, Port OK, HTTP ECHOUE
**Problème** : Django rejette la connexion (ALLOWED_HOSTS)  
**Solution** : Vérifier ALLOWED_HOSTS dans les settings

### Cas 3 : Ping ECHOUE
**Problème** : Les PC ne sont pas sur le même réseau  
**Solution** : Vérifier les adresses IP et le masque de sous-réseau

## Solution Temporaire pour Tester

Si vous voulez tester rapidement si c'est ALLOWED_HOSTS, modifiez temporairement :

```python
# Dans radgestmat/settings/local_network.py
ALLOWED_HOSTS = ['*']  # TEMPORAIRE - pour tester uniquement
```

**⚠️ Ne pas laisser '*' en production !**
