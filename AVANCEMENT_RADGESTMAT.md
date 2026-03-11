# Rapport d'avancement — RadGestMat

Date : 2025-12-15

## Présentation

RadGestMat est une application Web Django destinée à la gestion de matériel (assets) et des notifications/alertes associées. Le projet contient des applications principales `assets` et `users`, des templates HTML, des fichiers statiques (CSS/JS) et des scripts pour le déploiement (Docker, Nginx, Gunicorn).

## Fonctionnalités principales

- Authentification et gestion des utilisateurs (`users`).
- Gestion des matériels (`assets`) : création, modification, listes, détails, groupes.
- Attributions et suivi des matériels (check-in/check-out).
- Notifications et alertes (système d'alertes, préférences de notification).
- Génération de QR codes et exports (tests présents pour QR et pertes/dommages).
- Interface d'administration simple (parallèle à Django admin via `assets.urls_admin_ui`).

## Architecture technique

- Backend : Django (multiples settings par environnement : `radgestmat/settings/`), Python 3.11.
- Frontend : Templates Django + fichiers statiques (`static/css`, `static/js`), dépendances externes via CDN (Bootstrap, icons).
- Déploiement : Docker Compose orchestration, service `web` (Gunicorn + Django), service `nginx` en frontal, Redis, Postgres (ou SQLite configurable).
- Stockage static : `STATIC_ROOT` = `/app/staticfiles` dans le conteneur, volume Docker `static_volume` monté pour partager avec `nginx`.
- Stockage média : volume `media_volume` et répertoire `/app/media`.

## Avancement technique (état actuel)

- Code et structure : le dépôt contient les apps, templates, fichiers statiques et documentation de déploiement.
- Tests : quelques tests unitaires existent (`test_damage_loss.py`, `test_qr_generation.py`). La suite complète des tests n'a pas encore été exécutée systématiquement.
- Settings :
  - `radgestmat/settings/base.py` configure `STATIC_URL`, `STATICFILES_DIRS` et `STATIC_ROOT` correctement.
  - `radgestmat/settings/production.py` désactive `DEBUG`, utilise `ManifestStaticFilesStorage` et configure Redis.
- Déploiement Docker :
  - `Dockerfile` exécute un `collectstatic` lors du build (mais le contenu peut être masqué par le volume à runtime).
  - `docker-compose.yml` exécute `collectstatic` au démarrage du service `web` et monte `static_volume` sur `/app/staticfiles` pour que `nginx` serve les fichiers.
- Nginx : configuration présente dans `nginx.conf` servant `/static/` depuis `/app/staticfiles` et `/media/` depuis `/app/media`.

## Problèmes constatés

- Apparence non stylée (page sans CSS) sur l'instance Docker/production : causes probables identifiées :
  - Le volume Docker `static_volume` peut être vide ou masque les fichiers créés lors du build. Si le volume existe mais vide avant que l'image n'écrive, le contenu du build ne sera pas présent à l'intérieur du volume au runtime.
  - Permissions ou ownership sur `/app/staticfiles` empêchant `nginx` de lire les fichiers (chown requis si `appuser` a un UID différent).
  - Cache navigateur (moins probable mais à vérifier avec un hard-refresh/incognito).

## Actions réalisées

- Inspection des templates et vérification que les balises `{% load static %}` et `{% static 'css/custom.css' %}` sont correctement utilisées (`templates/base.html`).
- Vérification que les fichiers locaux `static/css/custom.css`, `static/css/responsive.css`, `static/js/custom.js` existent dans le repo.
- Correction temporaire pour le développement : `radgestmat/urls.py` modifié pour utiliser `staticfiles_urlpatterns()` en `DEBUG` afin d'assurer que `runserver` sert correctement les fichiers depuis `STATICFILES_DIRS`.
- Vérification que la commande `collectstatic` a été exécutée manuellement dans votre environnement Docker (commande exécutée et sortie `Exit Code: 0` dans le terminal fourni).

## Recommandations et prochaines étapes (prioritaires)

1. Vérifier le contenu du volume `static_volume` depuis le conteneur `web` :

```powershell
docker-compose exec web ls -la /app/staticfiles
```

2. Si le volume est vide, exécuter `collectstatic` dans le conteneur `web` (cela écrira dans le volume monté) :

```powershell
docker-compose exec web python manage.py collectstatic --noinput
```

3. Vérifier/permettre la lecture par `nginx` :

```powershell
docker-compose exec web chown -R 1000:1000 /app/staticfiles
docker-compose restart nginx
```

(ici `1000` est l'UID du `appuser` défini dans le `Dockerfile` — ajustez si nécessaire.)

4. Tester directement depuis le conteneur `nginx` ou depuis l'hôte que le CSS est accessible :

```powershell
# depuis l'hôte (si mappe port 80):
curl -I http://localhost/static/css/custom.css
# ou depuis le conteneur nginx:
docker-compose exec nginx ls -la /app/staticfiles
```

5. Faire un hard-refresh du navigateur (Ctrl+F5) ou tester en mode incognito pour éliminer le cache.

6. Ajouter une étape de vérification (optionnelle) dans l'entrée `web` pour lister `/app/staticfiles` et logguer si vide (utile en debug initial).

## Commandes utiles rappel

- Lancer la stack :

```powershell
docker-compose up -d --build
```

- Voir logs récents :

```powershell
docker-compose logs web --tail 200
docker-compose logs nginx --tail 200
```

- Lancer tests :

```powershell
docker-compose exec web python manage.py test
# ou
docker-compose exec web pytest -q
```

## Conclusion

Le projet est fonctionnel côté backend et présente une architecture Docker+Nginx correctement définie. Le problème d'apparence observé est très probablement lié à la chaîne de déploiement des fichiers statiques (volume Docker masquant le contenu collecté ou permissions incorrectes). Les étapes recommandées ci-dessus permettent de vérifier et corriger le flux `collectstatic -> volume -> nginx`.

Si vous le souhaitez, j'exécute immédiatement les vérifications (ls du volume, logs `web` et `nginx`, test `curl`) et j'applique les corrections (collectstatic + chown) puis je vous rends compte des résultats.
