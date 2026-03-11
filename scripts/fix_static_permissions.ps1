# Script de correction des fichiers statiques pour RadGestMat
Write-Host "Diagnostic et correction des fichiers statiques..." -ForegroundColor Cyan

# 1. Vérifier si le conteneur web tourne
$webContainer = docker-compose ps -q web
if (-not $webContainer) {
    Write-Host "Le conteneur web n'est pas démarré. Tentative de démarrage..." -ForegroundColor Yellow
    docker-compose up -d web
}

# 2. Forcer collectstatic
Write-Host "Exécution de collectstatic..." -ForegroundColor Cyan
docker-compose exec -T web python manage.py collectstatic --noinput
if ($LASTEXITCODE -eq 0) {
    Write-Host "Collectstatic réussi." -ForegroundColor Green
} else {
    Write-Host "Erreur lors de collectstatic." -ForegroundColor Red
    exit 1
}

# 3. Corriger les permissions (User 1000:1000 souvent utilisé par l'image python non-root)
Write-Host "Correction des permissions sur /app/staticfiles..." -ForegroundColor Cyan
# On utilise root pour changer les perms
docker-compose exec -u root -T web chown -R 1000:1000 /app/staticfiles

# 4. Vérifier le contenu
Write-Host "Vérification du contenu du dossier static..." -ForegroundColor Cyan
docker-compose exec -T web ls -la /app/staticfiles/css

# 5. Redémarrer Nginx pour s'assurer qu'il voit les fichiers
Write-Host "Redémarrage de Nginx..." -ForegroundColor Cyan
docker-compose restart nginx

# 6. Test final avec Curl
Write-Host "Test d'accès au fichier CSS via Nginx..." -ForegroundColor Cyan
# On teste via localhost sur le port 80 (ou celui mappé)
try {
    $response = Invoke-WebRequest -Uri "http://localhost:80/static/css/custom.css" -Method Head -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "SUCCÈS : Le fichier CSS est accessible !" -ForegroundColor Green
    } else {
        Write-Host "ATTENTION : Code retour $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "ERREUR : Impossible d'accéder au fichier CSS via http://localhost/static/css/custom.css" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host "Opération terminée." -ForegroundColor Cyan
