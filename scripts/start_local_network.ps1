# ============================================



# Demarrage RadGestMat - Reseau Local Admin



# ============================================



# 



# Script de demarrage pour hebergement local sur PC Windows



# - Detecte automatiquement l'IP locale



# - Configure le firewall Windows



# - Demarre Django sur 0.0.0.0:8000



# - Affiche les URLs d'acces







param(



    [switch]$SkipFirewall = $false,



    [switch]$Verbose = $false



)







Write-Host "================================================" -ForegroundColor Cyan



Write-Host "  RADGESTMAT - HEBERGEMENT RESEAU LOCAL" -ForegroundColor Cyan



Write-Host "================================================" -ForegroundColor Cyan



Write-Host ""







# ====================



# 1. CONFIGURATION IP



# ====================



Write-Host '1. Configuration de l IP...' -ForegroundColor Green











# IP fixe du serveur (reseau admin Ethernet)



$localIP = "10.105.42.118"







# Option: Detection automatique si IP non specifiee



$envIP = $env:LOCAL_NETWORK_IP



if ($envIP -and $envIP -ne "") {



    $localIP = $envIP



    Write-Host "   i  IP depuis variable d'environnement: $localIP" -ForegroundColor Cyan



} else {



    Write-Host "    IP fixe configuree: $localIP" -ForegroundColor Green



}







Write-Host ""







# ====================



# 2. CONFIGURATION FIREWALL



# ====================



$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path







if ($SkipFirewall) {



    Write-Host "2. Configuration firewall ignoree (SkipFirewall)" -ForegroundColor Yellow



    Write-Host ""



} else {



    Write-Host "2. Configuration du firewall Windows..." -ForegroundColor Green



    



    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)



    



    if ($isAdmin) {



        $firewallScript = Join-Path $scriptPath "configure_firewall.ps1"



        if (Test-Path $firewallScript) {



            & $firewallScript -Port 8000 -RuleName "RadGestMat HTTP"



            Write-Host ""



        } else {



            Write-Host "   Script configure_firewall.ps1 non trouve" -ForegroundColor Yellow



        }



    } else {



        Write-Host "   Droits administrateur requis pour configurer le firewall" -ForegroundColor Yellow



        Write-Host "   Vous pouvez le faire manuellement ou relancer en admin" -ForegroundColor Yellow



        Write-Host ""



    }



}







# ====================



# 3. VERIFICATION ENVIRONNEMENT



# ====================



Write-Host '3. Verification de l environnement Python...' -ForegroundColor Green











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



        Write-Host "    Environnement trouve: $venvPath" -ForegroundColor Green



        break



    }



}







if (-not $pythonExe) {



    # Essayer avec python global



    try {



        $pythonVersion = python --version 2>&1



        if ($LASTEXITCODE -eq 0) {



            $pythonExe = "python"



            Write-Host "    Python global trouve: $pythonVersion" -ForegroundColor Green



        }



    } catch {



        Write-Host "    Python non trouve!" -ForegroundColor Red



        Write-Host "   Installez Python ou creez un environnement virtuel" -ForegroundColor Yellow



        exit 1



    }



}







# Verifier manage.py



$managePy = Join-Path $projectRoot "manage.py"



if (-not (Test-Path $managePy)) {



    Write-Host " manage.py non trouve dans $projectRoot" -ForegroundColor Red



    exit 1



}







Write-Host ""







# ====================



# 4. CONFIGURATION VARIABLES D'ENVIRONNEMENT



# ====================



Write-Host "  4. Configuration des variables d'environnement..." -ForegroundColor Green







# Definir l'IP locale pour Django



$env:LOCAL_NETWORK_IP = $localIP



$env:DJANGO_SETTINGS_MODULE = "radgestmat.settings.local_network"



$env:PYTHONIOENCODING = "utf-8"







# ALLOWED_HOSTS avec IP locale



$env:ALLOWED_HOSTS = "$localIP,localhost,127.0.0.1"







# CSRF_TRUSTED_ORIGINS



$env:CSRF_TRUSTED_ORIGINS = "http://$localIP,http://$localIP:8000,http://localhost,http://localhost:8000"







# QR_DOMAIN



$env:QR_DOMAIN = "http://$localIP:8000"







Write-Host "    Variables configurees" -ForegroundColor Green



Write-Host "   - LOCAL_NETWORK_IP: $localIP" -ForegroundColor Gray



Write-Host "   - DJANGO_SETTINGS_MODULE: radgestmat.settings.local_network" -ForegroundColor Gray



Write-Host ""







# ====================



# 5. APPLIQUER MIGRATIONS (si necessaire)



# ====================



Write-Host '5. Verification des migrations...' -ForegroundColor Green











Set-Location $projectRoot







try {



    & $pythonExe manage.py migrate --check --noinput 2>&1 | Out-Null



    if ($LASTEXITCODE -ne 0) {



        Write-Host "     Migrations en attente, application..." -ForegroundColor Yellow



        & $pythonExe manage.py migrate --noinput



        Write-Host "    Migrations appliquees" -ForegroundColor Green



    } else {



        Write-Host "    Base de donnees a jour" -ForegroundColor Green



    }



} catch {



    Write-Host "    Impossible de verifier les migrations: $_" -ForegroundColor Yellow







}







Write-Host ""







# ====================



# 6. COLLECTER FICHIERS STATIQUES (si necessaire)



# ====================



Write-Host '6. Verification des fichiers statiques...' -ForegroundColor Green











$staticRoot = Join-Path $projectRoot "staticfiles"



if (-not (Test-Path $staticRoot) -or (Get-ChildItem $staticRoot -ErrorAction SilentlyContinue | Measure-Object).Count -eq 0) {



    Write-Host "     Fichiers statiques manquants, collecte..." -ForegroundColor Yellow



    & $pythonExe manage.py collectstatic --noinput



    Write-Host "    Fichiers statiques collectes" -ForegroundColor Green



} else {



    Write-Host "    Fichiers statiques presents" -ForegroundColor Green



}







Write-Host ""







# ====================



# 7. AFFICHER INFORMATIONS D'ACCES



# ====================



Write-Host "================================================" -ForegroundColor Cyan



Write-Host "   PRET A DEMARRER" -ForegroundColor Green



Write-Host "================================================" -ForegroundColor Cyan



Write-Host ""



Write-Host 'Informations d acces:' -ForegroundColor Yellow







Write-Host ""



Write-Host '   Depuis ce PC:' -ForegroundColor White







Write-Host "      http://localhost:8000" -ForegroundColor Cyan



Write-Host ""



Write-Host '   Depuis autres PC (reseau admin Ethernet):' -ForegroundColor White







Write-Host "      http://$localIP:8000" -ForegroundColor Cyan



Write-Host ""



Write-Host '   Interface Admin:' -ForegroundColor White







Write-Host "      http://$localIP:8000/admin/" -ForegroundColor Cyan



Write-Host ""



Write-Host "IMPORTANT:" -ForegroundColor Yellow



Write-Host "   - Acces uniquement depuis PC connectes en Ethernet au reseau admin" -ForegroundColor Yellow



Write-Host "   - Les smartphones ne peuvent pas acceder (pas de WiFi admin)" -ForegroundColor Yellow



Write-Host "   - IP fixe: $localIP" -ForegroundColor Yellow



Write-Host ""



Write-Host "Pour arreter: Ctrl+C" -ForegroundColor Red



Write-Host ""



Write-Host "================================================" -ForegroundColor Cyan



Write-Host ""







# ====================



# 8. DEMARRER SERVEUR DJANGO



# ====================



Write-Host 'Demarrage du serveur Django...' -ForegroundColor Green







Write-Host ""







# #region agent log



$logPath = Join-Path $projectRoot '.cursor\debug.log'



$logData = @{



    sessionId = 'debug-session'



    runId = 'run1'



    hypothesisId = 'A'



    location = 'start_local_network.ps1:210'



    message = 'Before starting Django server'



    data = @{



        pythonExe = $pythonExe



        localIP = $localIP



        bindAddress = '0.0.0.0:8000'



        projectRoot = $projectRoot



    }



    timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()



} | ConvertTo-Json -Compress



Add-Content -Path $logPath -Value $logData -ErrorAction SilentlyContinue



# #endregion







# Verifier si le port est deja utilise



$portInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue



if ($portInUse) {



    Write-Host 'ATTENTION: Le port 8000 est deja utilise!' -ForegroundColor Red



    Write-Host ('   Processus: ' + $portInUse.OwningProcess) -ForegroundColor Yellow



    



    # #region agent log



    $logData = @{



        sessionId = 'debug-session'



        runId = 'run1'



        hypothesisId = 'B'



        location = 'start_local_network.ps1:225'



        message = 'Port 8000 already in use'



        data = @{



            owningProcess = $portInUse.OwningProcess



            state = $portInUse.State



        }



        timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()



    } | ConvertTo-Json -Compress



    Add-Content -Path $logPath -Value $logData -ErrorAction SilentlyContinue



    # #endregion



}







# Verifier l IP de l interface reseau active



$activeIPs = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -ne "127.0.0.1" -and $_.InterfaceAlias -notlike "*Loopback*" }



$ipMatch = $activeIPs | Where-Object { $_.IPAddress -eq $localIP }







# #region agent log



$logData = @{



    sessionId = 'debug-session'



    runId = 'run1'



    hypothesisId = 'D'



    location = 'start_local_network.ps1:245'



    message = 'Network interface check'



    data = @{



        configuredIP = $localIP



        activeIPs = @($activeIPs.IPAddress)



        ipMatchFound = ($ipMatch -ne $null)



    }



    timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()



} | ConvertTo-Json -Compress



Add-Content -Path $logPath -Value $logData -ErrorAction SilentlyContinue



# #endregion







if (-not $ipMatch) {



    Write-Host ('ATTENTION: L IP ' + $localIP + ' n est pas trouvee sur les interfaces reseau actives!') -ForegroundColor Yellow



    $activeIPsList = ($activeIPs.IPAddress) -join ', '



    Write-Host ('   IPs actives: ' + $activeIPsList) -ForegroundColor Yellow



}







# Verifier le firewall



$firewallRule = Get-NetFirewallRule -DisplayName 'RadGestMat HTTP' -ErrorAction SilentlyContinue



# #region agent log



$logData = @{



    sessionId = 'debug-session'



    runId = 'run1'



    hypothesisId = 'C'



    location = 'start_local_network.ps1:260'



    message = 'Firewall rule check'



    data = @{



        ruleExists = ($firewallRule -ne $null)



        ruleEnabled = if ($firewallRule) { $firewallRule.Enabled } else { $false }



    }



    timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()



} | ConvertTo-Json -Compress



Add-Content -Path $logPath -Value $logData -ErrorAction SilentlyContinue



# #endregion







Write-Host ""







# #region agent log



$cmdStr = $pythonExe + ' manage.py runserver 0.0.0.0:8000'



$logData = @{



    sessionId = 'debug-session'



    runId = 'run1'



    hypothesisId = 'E'



    location = 'start_local_network.ps1:270'



    message = 'About to execute Django runserver'



    data = @{



        command = $cmdStr



    }



    timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()



} | ConvertTo-Json -Compress



Add-Content -Path $logPath -Value $logData -ErrorAction SilentlyContinue



# #endregion







try {



    & $pythonExe manage.py runserver 0.0.0.0:8000



    



    # #region agent log



    $logData = @{



        sessionId = 'debug-session'



        runId = 'run1'



        hypothesisId = 'E'



        location = 'start_local_network.ps1:280'



        message = 'Django server process exited'



        data = @{



            exitCode = $LASTEXITCODE



        }



        timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()



    } | ConvertTo-Json -Compress



    Add-Content -Path $logPath -Value $logData -ErrorAction SilentlyContinue



    # #endregion



} catch {



    # #region agent log



    $errorMsg = $_.Exception.Message



    $stackTrace = $_.ScriptStackTrace



    $logData = @{



        sessionId = 'debug-session'



        runId = 'run1'



        hypothesisId = 'E'



        location = 'start_local_network.ps1:290'



        message = 'Django server startup error'



        data = @{



            error = $errorMsg



            stackTrace = $stackTrace



        }



        timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()



    } | ConvertTo-Json -Compress



    Add-Content -Path $logPath -Value $logData -ErrorAction SilentlyContinue



    # #endregion



    



    $errorMsg = $_.Exception.Message



    Write-Host ('Erreur lors du demarrage: ' + $errorMsg) -ForegroundColor Red



    throw



}



