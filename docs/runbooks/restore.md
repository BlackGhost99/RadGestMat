# Runbook — Restauration et reprise après sinistre (PostgreSQL + média)

Objectif : procédures pas-à-pas pour restaurer la base de données PostgreSQL et les fichiers médias (S3/MinIO) en cas de perte ou corruption.

Important : vérifier les sauvegardes et tester ces procédures en environnement de staging avant toute urgence réelle.

## Pré-requis
- Accès SSH au serveur de backup / cluster Postgres.
- Accès aux buckets S3 / MinIO pour restaurer les médias.
- Identifiants pour le gestionnaire de secrets si utilisés.

## 1. Restauration depuis un dump logique (`pg_dump`)
Cas d'usage : récupération d'une base cohérente à partir d'un dump complet.

Étapes :
1. Stopper les services applicatifs (Gunicorn / Celery) en lecture-écriture pour éviter conflits :
   - `systemctl stop radgestmat-gunicorn` (ou docker-compose down)
2. Créer une sauvegarde rapide de l'état actuel (si possible) :
   - `pg_dump -Fc -f /backups/pre_restore_$(date +%Y%m%d_%H%M).dump mydb`
3. Restaurer le dump :
   - Supprimer / recréer la base :
     - `psql -c "DROP DATABASE IF EXISTS mydb; CREATE DATABASE mydb;"`
   - `pg_restore -d mydb /backups/mydb_full.dump`
4. Recharger les assets/médias depuis S3 si nécessaire (voir section médias).
5. Appliquer les migrations Django si requis :
   - `python manage.py migrate --settings=radgestmat.settings.production`
6. Redémarrer services et vérifier logs :
   - `systemctl start radgestmat-gunicorn` ou `docker-compose up -d`
7. Valider l'intégrité applicative (smoke tests) : endpoints critiques, login, recherche matériel.

## 2. Point-In-Time Recovery (PITR) — WAL archiving
Cas d'usage : restaurer jusqu'à un instant précis en utilisant WAL archives.

Étapes (résumé) :
1. Préparer un serveur de restauration (instance PostgreSQL propre).
2. Copier les fichiers base backup (base backup) dans le répertoire `pg_wal` du serveur de restauration.
3. Placer le `recovery.conf` / `postgresql.conf` avec `restore_command` pointant vers l'archive WAL.
4. Démarrer PostgreSQL en mode recovery et laisser appliquer les WAL jusqu'au `recovery_target_time` souhaité.
5. Une fois terminé, promouvoir la base restaurée si nécessaire.

Notes : lire la documentation officielle PostgreSQL sur PITR (pg_basebackup, archive_command, restore_command).

## 3. Restauration des médias (S3 / MinIO)
1. Vérifier le bucket et la versioning (si activé).
2. Pour MinIO local : utiliser `mc` (MinIO client) pour copier les fichiers restaurés :
   - `mc cp --recursive backup/minio/bucketname/ s3/bucketname/`
3. Pour S3 (AWS) : utiliser `aws s3 sync` :
   - `aws s3 sync s3://backup-bucket/path s3://production-bucket/path --delete`

## 4. Validation post-restore
- Exécuter smoke tests :
  - Login admin
  - Lister matériels
  - Vérifier attributions récentes
- Vérifier tâches asynchrones (Celery) : file queue length, workers healthy.
- Vérifier intégrité des fichiers médias (aperçus, opens).

## 5. Rollback de migrations problématiques
- Si une migration casse l'application, restaurer la base depuis backup avant la migration et annuler la migration défaillante.
- Alternativement, préparer des migrations réversibles (operations reversible)

## 6. Communications et reporting
- Notifier les personnes listées dans l'on-call (voir fichier `docs/contacts_oncall.md` si existant).
- Documenter l'incident : date/heure, cause, actions prises, temps de restauration (RTO), perte de données estimée (RPO).

## 7. Tests périodiques
- Planifier DR drills (restauration complète) au moins une fois par trimestre.

## 8. Commandes utiles (exemples)
- Dump complet : `pg_dump -Fc -f /backups/mydb_$(date +%Y%m%d).dump mydb`
- Restore : `pg_restore -d mydb /backups/mydb_20251125.dump`
- Base backup (physical): `pg_basebackup -D /var/lib/postgresql/backup -F tar -z -P -U replicator`

---
Conserver ce runbook à jour et tester toutes les étapes en staging. Je peux créer un playbook Ansible pour automatiser ces étapes si vous le souhaitez.
