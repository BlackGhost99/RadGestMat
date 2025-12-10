# README — Annexes et scripts utiles

Ce fichier décrit les scripts et annexes fournis dans le dépôt et explique comment les utiliser.

## Emplacement des scripts
- `scripts/install_requirements.ps1` : installe les dépendances Python dans la virtualenv (`.venv`).
- `scripts/start_dev.ps1` : active l'environnement, applique les migrations, collecte les statics et démarre le serveur de développement sur le port `8001`.
- `scripts/backup_db.ps1` : script de sauvegarde de la base. Supporte SQLite (copie du fichier `db.sqlite3`) et Postgres (`pg_dump`) via variables d'environnement.
- `playbooks/restore.yml` : playbook Ansible pour restauration automatisée (voir `playbooks/README.md`).

## Utilisation rapide (PowerShell)

1) Créer et activer un venv (si nécessaire) :

```
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
```

2) Installer les dépendances :

```
./scripts/install_requirements.ps1
```

3) Démarrer le serveur de développement :

```
./scripts/start_dev.ps1
```

4) Sauvegarder la base de données :

```
./scripts/backup_db.ps1 -BackupDir .\backups
```

## PlantUML export (diagrammes)
Si vous voulez générer des images PNG depuis les fichiers `.puml`, la façon la plus simple est d'utiliser l'image Docker officielle `plantuml/plantuml` :

```
docker run --rm -v "${PWD}:/workspace" plantuml/plantuml:latest -tpng /workspace/docs/diagrams/chapter3_usecases.puml
```

Si vous êtes sur Windows et rencontrez des problèmes avec `${PWD}`, remplacez par le chemin absolu :

```
docker run --rm -v "C:\Users\Admin\source\repos\BlackGhost99\RadGestMat":/workspace plantuml/plantuml:latest -tpng /workspace/docs/diagrams/chapter3_deployment.puml
```

## Remarques de sécurité
- Exécuter ces scripts dans un environnement contrôlé et vérifier les variables d'environnement (secrets) avant utilisation.
- Les scripts sont minimaux et destinés à accélérer les opérations courantes; pour la production, utiliser playbooks Ansible / pipelines CI/Cd avec gestion sécurisée des secrets.

## Prochaines étapes recommandées
- Convertir `backup_db.ps1` en job périodique (Task Scheduler / Cron) et pousser les sauvegardes chiffrées vers un bucket S3.
- Ajouter la conversion des playbooks shell vers modules Ansible plus robustes (`community.postgresql`, `community.aws`).
