# Playbooks — README

Ce répertoire contient playbooks Ansible utiles pour l'exploitation du projet RadGestMat.

## Playbook : `restore.yml`
Objectif : automatiser la restauration d'une base PostgreSQL à partir d'un dump et la synchronisation des médias depuis S3/MinIO.

Prérequis :
- Ansible installé sur la machine d'administration.
- Accès SSH vers les hôtes cibles et permissions `become` pour exécuter les commandes postgres/docker/systemd.
- Fichier de dump PostgreSQL accessible depuis l'hôte cible (chemin absolu) ou via un partage monté.
- `aws` CLI configuré si `s3_backup_path` utilisé.

Exemple d'exécution :

```bash
ansible-playbook -i inventory playbooks/restore.yml \
  -e "dump_file=/backups/mydb_20251125.dump" \
  -e "s3_backup_path=s3://backup-bucket/radgestmat-media/" \
  -e "media_path=/var/www/app/media" \
  -e "service_manager=docker_compose" \
  -e "docker_compose_file=/opt/radgestmat/docker-compose.prod.yml"
```

Variables clés (peuvent être surchargées via `-e` ou `group_vars`):
- `db_name` : nom de la base (default: `radgestmat_db`)
- `dump_file` : chemin absolu vers le dump (OBLIGATOIRE)
- `s3_backup_path` : chemin S3/MinIO pour les médias (optionnel)
- `media_path` : chemin local où sont stockés les médias
- `service_manager` : `systemd` ou `docker_compose`

Notes de sécurité et bonnes pratiques :
- Tester le playbook sur une VM de staging avant utilisation en production.
- Vérifier les permissions et l'authentification AWS avant la synchronisation des médias.
- Conserver une copie du backup courant avant toute opération destructive.
