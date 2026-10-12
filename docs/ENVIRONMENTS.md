# Environnements RadGestMat

## Developpement Windows

Le developpement local utilise :

- `radgestmat.settings.development`
- `db.dev.sqlite3`
- les emails dans la console
- le serveur Django sur le port `8001`

Depuis la racine du projet :

```powershell
.\scripts\start_dev.ps1
```

Cette commande applique les migrations uniquement sur `db.dev.sqlite3`. Elle ne lit pas la base de production et ne doit pas etre utilisee pour demarrer le serveur Ubuntu.

Pour lancer les tests sur l'environnement dev :

```powershell
$env:ENVIRONMENT = 'development'
$env:DJANGO_SETTINGS_MODULE = 'radgestmat.settings.development'
$env:DB_NAME = (Join-Path (Get-Location) 'db.dev.sqlite3')
python manage.py test
```

## Production Ubuntu

La production utilise Docker Compose, `radgestmat.settings.production` et le fichier `.env` present uniquement sur le serveur. La base SQLite persistante est montee dans `/app/db_data/db.sqlite3`.

Apres validation locale et transfert du code :

```bash
git pull origin main
docker compose build
docker compose up -d
docker compose exec -T web python manage.py migrate
docker compose exec -T web python manage.py collectstatic --noinput
docker compose ps
```

Avant toute migration en production, faire une sauvegarde de la base persistante et verifier les logs :

```bash
docker compose exec -T web python manage.py check --deploy
docker compose logs --tail 100 web
```

Ne jamais copier `db.dev.sqlite3` vers la production et ne jamais executer `scripts/start_dev.ps1` sur Ubuntu.
