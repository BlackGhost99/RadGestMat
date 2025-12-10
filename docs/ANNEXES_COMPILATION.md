## Annexes — Compilation

Ce document indexe les annexes fournies avec le dossier de livraison. Il contient les références aux diagrammes UML sources, scripts d'installation, fichiers `.env.example`, spécifications API et autres artefacts.

Contenu recommandé :
- `docs/diagrams/` : fichiers PlantUML sources (.puml) — cas d'utilisation, classes, séquences, déploiement.
- `docs/CHAPITRE_III_UML_ET_MODELES.md` : chapitre UML et mapping aux modèles.
- `docs/CHAPITRE_IV_REALISATION.md` : chapitre réalisation (implémentation, tests, déploiement).
- `docs/CHAPITRE_V_CONCLUSION.md` : conclusion et recommandations.
- `.env.example` : variables d'environnement recommandées pour staging/prod.
- `scripts/` : scripts d'installation / gestion (si présent). Si absent, inclure un ensemble minimal : `install_requirements.ps1`, `start_dev.ps1`, `backup_db.ps1`.
- `docker-compose.yml` et `Dockerfile` : images et composition pour dev/prod.
- `docs/inventaire_template.csv` : modèle CSV pour inventaire (à générer si demandé).
- `specs/api_openapi.yaml` : (optionnel) export OpenAPI/Swagger si disponible.
- `logs/` : exemple de logs anonymisés d'entretiens et tests (à fournir séparément si nécessaire).

Instructions de compilation des annexes
1. Rassembler les fichiers listés ci-dessus.
2. Zipper le répertoire `docs/` + scripts + `docker-compose.yml` pour distribution.
3. Fournir un fichier `README-ANNEXES.md` expliquant comment reproduire les diagrammes (commande PlantUML) et exécuter les scripts.

---
Faites-moi savoir si vous voulez que je :
- génère le `README-ANNEXES.md` et les scripts d'exemple,
- exporte les `.puml` en images et les place dans `docs/diagrams/exports/`,
- crée le fichier `docs/inventaire_template.csv`.
