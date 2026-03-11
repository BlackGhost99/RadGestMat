# Script de test de connexion - A copier sur le PC client
# Executez ce script directement dans PowerShell sur le PC client

$serverIP = "10.105.42.118"
$port = 8000

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  TEST DE CONNEXION - RADGESTMAT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Serveur: $serverIP`:$port" -ForegroundColor Yellow
Write-Host ""

# Test 1: Ping
Write-Host "1. Test Ping vers $serverIP..." -ForegroundColor Green
try {
    $pingResult = Test-Connection -ComputerName $serverIP -Count 2 -Quiet
    if ($pingResult) {
        Write-Host "   OK: Ping reussi" -ForegroundColor Green
    } else {
        Write-Host "   ECHOUE: Ping echoue" -ForegroundColor Red
        Write-Host "   Les PC ne sont pas sur le meme reseau" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "   ERREUR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 2: Port TCP
Write-Host "2. Test Port TCP $port..." -ForegroundColor Green
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $connect = $tcpClient.BeginConnect($serverIP, $port, $null, $null)
    $wait = $connect.AsyncWaitHandle.WaitOne(3000, $false)
    
    if ($wait) {
        $tcpClient.EndConnect($connect)
        Write-Host "   OK: Port $port accessible" -ForegroundColor Green
        $tcpClient.Close()
    } else {
        Write-Host "   ECHOUE: Timeout - Port $port non accessible" -ForegroundColor Red
        Write-Host "   Le port est bloque par un firewall" -ForegroundColor Yellow
        $tcpClient.Close()
        exit 1
    }
} catch {
    Write-Host "   ERREUR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Le port est probablement bloque par un firewall" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Test 3: HTTP
Write-Host "3. Test HTTP..." -ForegroundColor Green
try {
    $response = Invoke-WebRequest -Uri "http://${serverIP}:${port}" -Method GET -TimeoutSec 5 -UseBasicParsing
    Write-Host "   OK: HTTP Status $($response.StatusCode)" -ForegroundColor Green
    Write-Host "   Taille reponse: $($response.Content.Length) bytes" -ForegroundColor Gray
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  SUCCESS: L'application est accessible!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Vous pouvez maintenant ouvrir:" -ForegroundColor Yellow
    Write-Host "  http://$serverIP`:$port" -ForegroundColor Cyan
    Write-Host ""
} catch {
    Write-Host "   ERREUR: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "   Status Code: $statusCode" -ForegroundColor Yellow
        
        if ($statusCode -eq 400) {
            Write-Host "   Probablement un probleme ALLOWED_HOSTS dans Django" -ForegroundColor Yellow
        } elseif ($statusCode -eq 403) {
            Write-Host "   Acces refuse par Django" -ForegroundColor Yellow
        } elseif ($statusCode -eq 500) {
            Write-Host "   Erreur serveur Django" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   La requete n'a pas atteint le serveur" -ForegroundColor Yellow
        Write-Host "   Verifier le firewall ou la configuration reseau" -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  ECHOUE" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Cyan
    exit 1
}
