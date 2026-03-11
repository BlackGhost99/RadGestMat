# 🔧 Commandes Essentielles - RadGestMat Production

## 📋 Index rapide

- [Démarrage/Arrêt](#démarragearrêt)
- [Logs & Monitoring](#logs--monitoring)
- [Base de données](#base-de-données)
- [Utilisateurs](#utilisateurs)
- [Static files](#static-files)
- [Maintenance](#maintenance)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Démarrage/Arrêt

### Démarrer tous les services
```bash
cd /opt/radgestmat
docker-compose up -d
```

### Arrêter tous les services
```bash
docker-compose down
```

### Arrêter ET supprimer tout (⚠️ attention!)
```bash
docker-compose down -v  # Supprime aussi les volumes
```

### Redémarrer tous les services
```bash
docker-compose restart
```

### Redémarrer un service spécifique
```bash
docker-compose restart web      # Django
docker-compose restart nginx    # Reverse proxy
docker-compose restart redis    # Cache
```

### Voir l'état des services
```bash
docker-compose ps
# Output:
# NAME                    STATUS
# radgestmat_nginx        Up 2 days
# radgestmat_web          Up 2 days
# radgestmat_redis        Up 2 days
```

---

## 📊 Logs & Monitoring

### Logs en temps réel (live)
```bash
docker-compose logs -f web      # Django
docker-compose logs -f nginx    # Nginx
docker-compose logs -f redis    # Redis
docker-compose logs -f          # Tous
```

### Voir les 50 dernières lignes
```bash
docker-compose logs --tail=50 web
```

### Logs avec timestamps
```bash
docker-compose logs --timestamps web
```

### Logs d'un moment spécifique
```bash
docker-compose logs --since 1h web   # Dernière heure
docker-compose logs --until 1h web   # Avant une heure
```

### Entrer dans le container (shell)
```bash
docker-compose exec web bash          # Django
docker-compose exec redis sh          # Redis
docker-compose exec web python manage.py shell  # Django shell
```

### Vérifier la santé
```bash
# Via HTTP
curl http://10.105.42.118/health/
# Output JSON:
# {"status": "healthy", "database": "ok", "cache": "ok", "timestamp": "..."}

# Via Docker
docker-compose exec web redis-cli -h redis ping
# Output: PONG
```

---

## 🗂️ Base de données

### Accéder à Django shell
```bash
docker-compose exec web python manage.py shell

# Exemple: Compter les matériels
>>> from assets.models import Materiel
>>> Materiel.objects.count()
42
>>> exit()
```

### Appliquer les migrations
```bash
docker-compose exec web python manage.py migrate
```

### Créer une migration pour changements de modèle
```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

### Sauvegarder la BD
```bash
# Copier db.sqlite3 du container vers serveur
docker cp radgestmat_web:/app/db.sqlite3 ./backup/db_$(date +%Y%m%d_%H%M%S).sqlite3

# Ou via le shell
docker-compose exec web cp db.sqlite3 /backup/db_backup.sqlite3
```

### Restaurer la BD
```bash
# Copier le fichier de backup vers le container
docker cp ./backup/db_backup.sqlite3 radgestmat_web:/app/db.sqlite3

# Redémarrer Django
docker-compose restart web
```

### Vérifier la taille BD
```bash
docker-compose exec web du -h db.sqlite3
# Exemple output: 5.3M db.sqlite3
```

---

## 👤 Utilisateurs

### Créer un superutilisateur
```bash
docker-compose exec web python manage.py createsuperuser
# Entrer email, password à la demande
```

### Créer un utilisateur normal (Django shell)
```bash
docker-compose exec web python manage.py shell

>>> from django.contrib.auth.models import User
>>> user = User.objects.create_user('john', 'john@example.com', 'password123')
>>> user.save()
>>> exit()
```

### Lister les utilisateurs
```bash
docker-compose exec web python manage.py shell

>>> from django.contrib.auth.models import User
>>> for u in User.objects.all():
...     print(f"{u.username} - {u.email}")
>>> exit()
```

### Réinitialiser mot de passe
```bash
docker-compose exec web python manage.py changepassword username
```

### Supprimer un utilisateur
```bash
docker-compose exec web python manage.py shell

>>> from django.contrib.auth.models import User
>>> User.objects.get(username='john').delete()
>>> exit()
```

---

## 📦 Static files

### Collecter les static files
```bash
docker-compose exec web python manage.py collectstatic --noinput
```

### Nettoyer les old static files
```bash
docker-compose exec web python manage.py collectstatic --clear --noinput
```

### Vérifier les fichiers static
```bash
docker-compose exec web ls -lah staticfiles/
```

---

## 🔧 Maintenance

### Vérifier les dépendances Python
```bash
docker-compose exec web pip list
```

### Mettre à jour les dépendances
```bash
# Modifier requirements.txt
# Puis rebuild l'image:
docker-compose build --no-cache
docker-compose down
docker-compose up -d
```

### Exécuter la commande manage.py custom
```bash
docker-compose exec web python manage.py <commande>

# Exemples:
docker-compose exec web python manage.py check                    # Vérifier config
docker-compose exec web python manage.py dumpdata > backup.json   # Exporter données
docker-compose exec web python manage.py loaddata backup.json     # Importer données
```

### Nettoyer le cache
```bash
docker-compose exec web python manage.py clear_cache  # Si implémenté

# Ou via Redis:
docker-compose exec redis redis-cli FLUSHDB  # Vider cache Redis
```

### Vérifier l'espace disque
```bash
docker-compose exec web df -h
docker-compose exec redis df -h
```

### Vérifier l'utilisation RAM/CPU
```bash
docker stats

# Output:
# CONTAINER                  CPU %   MEM USAGE
# radgestmat_web             2.3%    145 MB
# radgestmat_nginx           0.1%    12 MB
# radgestmat_redis           0.2%    8 MB
```

---

## 🚨 Troubleshooting

### Port déjà utilisé
```bash
# Identifier le processus
netstat -ano | findstr :80      # Windows
lsof -i :80                      # Linux/Mac

# Arrêter le processus
docker-compose down
docker ps  # Vérifier que tout est arrêté
```

### Container qui crash immédiatement
```bash
# Voir les logs
docker-compose logs web

# Vérifier la configuration Django
docker-compose exec web python manage.py check
```

### Permissions fichiers
```bash
# Reset permissions
docker-compose exec web chmod -R 755 /app/db.sqlite3
docker-compose exec web chown -R appuser:appuser /app/media /app/logs
```

### Redis non accessible
```bash
# Vérifier connexion
docker-compose exec web redis-cli -h redis ping
# Doit retourner: PONG

# Redémarrer Redis
docker-compose restart redis
```

### Static files non affichés
```bash
# Collecter à nouveau
docker-compose exec web python manage.py collectstatic --noinput

# Vérifier dans nginx
docker-compose exec web ls -lah /app/staticfiles/

# Redémarrer nginx
docker-compose restart nginx
```

### Migration échouée
```bash
# Rollback (si possible)
docker-compose exec web python manage.py migrate <app_name> <previous_migration>

# Ou voir l'état
docker-compose exec web python manage.py showmigrations
```

### Sessions perdues après restart
```bash
# Sessions devraient être dans Redis
# Vérifier Redis est OK:
docker-compose exec redis redis-cli -h redis ping

# Ou forcer une migration des sessions:
docker-compose exec web python manage.py migrate sessions
```

---

## 📈 Performance & Monitoring

### Tester la vitesse
```bash
# Sur le serveur ou client
time curl http://10.105.42.118/

# Ou avec Apache Bench (si installé)
ab -n 100 -c 10 http://10.105.42.118/
```

### Vérifier la compression
```bash
curl -H "Accept-Encoding: gzip" -I http://10.105.42.118/
# Doit voir "Content-Encoding: gzip"
```

### Logs de requête Nginx
```bash
docker-compose exec nginx tail -f /var/log/nginx/access.log
```

### Top requêtes
```bash
docker-compose exec nginx grep "GET" /var/log/nginx/access.log | awk '{print $7}' | sort | uniq -c | sort -rn | head -10
```

---

## 🔐 Sécurité

### Vérifier les variables d'env
```bash
cat .env
# Ne doit pas contenir de vraies credentials en git!
```

### Vérifier que DEBUG=False
```bash
docker-compose exec web python -c "from django.conf import settings; print(settings.DEBUG)"
# Doit retourner: False
```

### Vérifier SECRET_KEY
```bash
docker-compose exec web python -c "from django.conf import settings; print(settings.SECRET_KEY)"
# Doit être une clé aléatoire longue
```

---

## 📞 Aide rapide

**Port 80 occupé?**
```bash
docker-compose down && docker-compose up -d
```

**Django ne démarre pas?**
```bash
docker-compose logs web
# Regarder la dernière erreur, google l'erreur
```

**Redis ne répond?**
```bash
docker-compose restart redis
docker-compose exec redis redis-cli -h redis ping
```

**Besoin de réinitialiser complètement?**
```bash
docker-compose down -v              # Supprimer tout
docker-compose up -d                # Redémarrer
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

---

## 📅 Maintenance régulière

### Chaque jour
- [ ] Consulter logs pour erreurs: `docker-compose logs web`
- [ ] Vérifier health: `curl http://10.105.42.118/health/`

### Chaque semaine
- [ ] Sauvegarder BD: `docker cp radgestmat_web:/app/db.sqlite3 ./backup/`
- [ ] Vérifier espace disque: `docker-compose exec web df -h`

### Chaque mois
- [ ] Nettoyer les sessions anciennes: `docker-compose exec web python manage.py clearsessions`
- [ ] Vérifier les updates Django/dépendances

### Annuel
- [ ] Archive des anciens backups
- [ ] Vérifier la sécurité globale

---

**Last updated:** Décembre 2025  
**Serveur:** 10.105.42.118  
**BD:** SQLite (local)
