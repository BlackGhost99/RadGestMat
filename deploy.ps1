# Script de deploiement automatise pour RadGestMat - Windows
# Utilisation: .\deploy.ps1

Write-Host ">>> Deploiement de RadGestMat sur 10.105.42.118" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Verifier les prerequis
Write-Host "[1/7] Verification des prerequis..." -ForegroundColor Yellow
$docker = docker --version 2>$null
$compose = docker-compose --version 2>$null

if ($docker -and $compose) {
    Write-Host "OK Docker et Docker Compose trouves`n" -ForegroundColor Green
}
else {
    Write-Host "ERREUR Docker n'est pas installe ou pas dans le PATH" -ForegroundColor Red
    exit 1
}

# Verifier le fichier .env
Write-Host "[2/7] Verification de la configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "ERREUR Fichier .env manquant" -ForegroundColor Red
    Write-Host "Creer le a partir de .env.example"
    exit 1
}
Write-Host "OK Fichier .env detecte`n" -ForegroundColor Green

# Arreter les services existants
Write-Host "[3/7] Arret des services existants..." -ForegroundColor Yellow
docker-compose down --remove-orphans 2>$null
Write-Host "OK Services arretes`n" -ForegroundColor Green

# Construire l'image
Write-Host "[4/7] Construction de l'image Docker..." -ForegroundColor Yellow
docker-compose build
Write-Host "OK Image construite`n" -ForegroundColor Green

# Demarrer les services
Write-Host "[5/7] Demarrage des services..." -ForegroundColor Yellow
docker-compose up -d
Write-Host "OK Services demarres`n" -ForegroundColor Green

# Attendre que Django soit pret
Write-Host "[6/7] Initialisation de la base de donnees..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

$maxAttempts = 30

Write-Host "Etat actuel des containers (docker-compose ps) :" -ForegroundColor Cyan
docker-compose ps

for ($attempt = 0; $attempt -lt $maxAttempts; $attempt++) {
    Write-Host "Tentative de migration ($($attempt + 1)/$maxAttempts)..." -ForegroundColor Yellow
    # Exécute la migration en affichant la sortie pour faciliter le debug
    $migrateOutput = docker-compose exec -T web python manage.py migrate 2>&1
    $exit = $LASTEXITCODE
    if ($exit -eq 0) {
        Write-Host "OK Migrations appliquees." -ForegroundColor Green
        break
    } else {
        Write-Host "Migration echouee (code $exit). Sortie de la commande:" -ForegroundColor Red
        Write-Host $migrateOutput
    }

    if ($attempt -lt ($maxAttempts - 1)) {
        Write-Host "Attente du service web... ($($attempt + 1)/$maxAttempts)" -ForegroundColor Yellow
        Start-Sleep -Seconds 5
    }
}

if ($exit -ne 0) {
    Write-Host "ERREUR Timeout: Django ne repond pas ou migrations ont echoue" -ForegroundColor Red
    Write-Host "---- Logs web (dernieres lignes) ----" -ForegroundColor Cyan
    docker-compose logs web --tail 200
    exit 1
}

# Collecter les static files
Write-Host "[7/7] Collecte des fichiers statiques..." -ForegroundColor Yellow
docker-compose exec -T web python manage.py collectstatic --noinput
Write-Host "OK Fichiers statiques collectes`n" -ForegroundColor Green

# Fix permissions for media/static volumes so Django can write uploads (QR codes etc.)
Write-Host "[8/8] Correction des permissions sur les volumes (media/staticfiles)..." -ForegroundColor Yellow
try {
    Write-Host "Tentative d'ajustement des permissions dans le conteneur web..." -ForegroundColor Yellow
    $permOutput = docker-compose exec -u 0 web bash -lc "mkdir -p /app/media/qr_codes /app/media && chown -R 1000:1000 /app/media /app/staticfiles" 2>&1
    $permExit = $LASTEXITCODE
    if ($permExit -eq 0) {
        Write-Host "OK Permissions positionnees`n" -ForegroundColor Green
    } else {
        Write-Host "WARN Ajustement des permissions a retourne le code $permExit. Sortie:" -ForegroundColor Yellow
        Write-Host $permOutput
        Write-Host "Veuillez executer manuellement: docker-compose exec -u 0 web chown -R 1000:1000 /app/media /app/staticfiles" -ForegroundColor Yellow
    }
} catch {
    Write-Host "WARN Exception lors de l'ajustement des permissions: $_" -ForegroundColor Yellow
    Write-Host "Veuillez executer manuellement: docker-compose exec -u 0 web chown -R 1000:1000 /app/media /app/staticfiles" -ForegroundColor Yellow
}

# Resume final
Write-Host "SUCCES Deploiement reussi!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

Write-Host "`nServices deployes:"
Write-Host "  - Django (Gunicorn): http://10.105.42.118:8000"
Write-Host "  - Nginx (Reverse Proxy): http://10.105.42.118"
Write-Host "  - Redis (Cache): localhost:6379"

Write-Host "`nProchaines etapes:"
Write-Host "  1. Creer un superutilisateur:"
Write-Host "     docker-compose exec web python manage.py createsuperuser"
Write-Host ""
Write-Host "  2. Acceder a l'admin:"
Write-Host "     http://10.105.42.118/admin/"
Write-Host ""
Write-Host "  3. Voir les logs:"
Write-Host "     docker-compose logs -f web"

Write-Host "`n================================================" -ForegroundColor Green
