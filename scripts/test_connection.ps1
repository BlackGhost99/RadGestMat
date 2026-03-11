# Script pour tester la connexion depuis un autre PC
# A executer depuis le PC client (pas le serveur)

param(
    [string]$ServerIP = "10.105.42.118",
    [int]$Port = 8000
)

Write-Host "Test de connexion a RadGestMat..." -ForegroundColor Cyan
Write-Host "Serveur: $ServerIP`:$Port" -ForegroundColor Yellow
Write-Host ""

# Test 1: Ping
Write-Host "1. Test Ping..." -ForegroundColor Green
$pingResult = Test-Connection -ComputerName $ServerIP -Count 2 -Quiet
if ($pingResult) {
    Write-Host "   OK: Ping reussi" -ForegroundColor Green
} else {
    Write-Host "   ERREUR: Ping echoue" -ForegroundColor Red
    exit 1
}

# Test 2: Port ouvert
Write-Host "2. Test Port $Port..." -ForegroundColor Green
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $connect = $tcpClient.BeginConnect($ServerIP, $Port, $null, $null)
    $wait = $connect.AsyncWaitHandle.WaitOne(3000, $false)
    if ($wait) {
        $tcpClient.EndConnect($connect)
        Write-Host "   OK: Port $Port accessible" -ForegroundColor Green
        $tcpClient.Close()
    } else {
        Write-Host "   ERREUR: Timeout - Port $Port non accessible" -ForegroundColor Red
        $tcpClient.Close()
        exit 1
    }
} catch {
    Write-Host "   ERREUR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 3: HTTP
Write-Host "3. Test HTTP..." -ForegroundColor Green
try {
    $response = Invoke-WebRequest -Uri "http://${ServerIP}:${Port}" -Method GET -TimeoutSec 5 -UseBasicParsing
    Write-Host "   OK: HTTP Status $($response.StatusCode)" -ForegroundColor Green
    Write-Host "   Taille reponse: $($response.Content.Length) bytes" -ForegroundColor Gray
} catch {
    Write-Host "   ERREUR: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        Write-Host "   Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Yellow
    }
    exit 1
}

Write-Host ""
Write-Host "Tous les tests sont passes!" -ForegroundColor Green
Write-Host "L application est accessible depuis ce PC" -ForegroundColor Green
