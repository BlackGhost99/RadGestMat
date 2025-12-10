# Checklist de Sécurité et Conformité — RadGestMat

Ce document synthétise les contrôles de sécurité essentiels à valider avant et après mise en production.

## 1. Paramètres Django et environnement
- `DEBUG`: must be `False` en production.
- `ALLOWED_HOSTS`: définir explicitement les hôtes autorisés.
- `SECRET_KEY`: stocker dans un gestionnaire de secrets (Vault, AWS Secrets Manager, Azure Key Vault). Ne jamais committer.
- `CSRF_COOKIE_SECURE` et `SESSION_COOKIE_SECURE`: `True`.
- `CSRF_COOKIE_HTTPONLY` / `SESSION_COOKIE_HTTPONLY`: `True` (selon compatibilité).
- `SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD`: configurer HSTS.
- `SECURE_SSL_REDIRECT`: `True` si TLS géré par proxy.
- `SECURE_CONTENT_TYPE_NOSNIFF` and CSP headers: ajouter Content-Security-Policy.

## 2. Gestion des secrets et chiffrement
- Utiliser un gestionnaire de secrets (HashiCorp Vault, AWS Secrets Manager, Azure Key Vault).
- Rotation régulière des clés/credentials.
- Chiffrement des données sensibles au repos (Postgres column encryption ou chiffrement disque géré par le cloud).

## 3. Accès et permissions
- RBAC : définir groupes `superuser`, `it_staff`, `reception`, `direction` avec permissions minimales.
- Révoquer l'accès par défaut (compte `admin` sans mot de passe).
- Authentification forte : mot de passe fort + 2FA pour comptes administratifs.
- Limiter accès SSH/DB par IP (bastion host si besoin).

## 4. Réseau et infrastructure
- TLS obligatoire (Let's Encrypt / CertManager) pour front-end.
- Segmenter réseau : DB/Redis non exposés publiquement.
- Firewall & security groups : n'autoriser que le trafic nécessaire.

## 5. Conteneurs et images
- Signer et scanner images (trivy, clair).
- Minimiser images (base alpine/python slim), limiter privilèges (non-root run).
- Utiliser scanning SCA pour dépendances (Dependabot, pip-audit, safety).

## 6. Tests de sécurité
- SAST: bandit, semgrep, pylint rules de sécurité.
- DAST: ZAP, Burp (scan avant mise en prod).
- Tests de dépendances: pip-audit, safety, dependabot alerts.

## 7. Journaux, monitoring et alerting
- Logs structurés (JSON) pour ingestion ELK/Opensearch.
- Rétention définie (politique PII et conformité). Archive vers cold storage.
- Alerts Prometheus: erreurs 5xx, latence, file Celery, backlog Redis.

## 8. Sauvegardes et restauration
- Sauvegardes Postgres : combiné `pg_dump` (logical) + WAL archiving (physical PITR).
- Tester restaurations périodiquement (voir runbook `docs/runbooks/restore.md`).

## 9. Conformité et données personnelles
- RGPD: définir durée de conservation, procédure de suppression/anonymisation.
- Journaliser accès et modifications sur données sensibles.

## 10. Politique opérationnelle
- Plan d'incident et contacts (on-call rota), playbooks runbook.
- Tests de reprise (DR drills) trimestriels.
- Revue de sécurité avant chaque release majeure.

## 11. Recommandations opérationnelles (actions rapides)
- Mettre `DEBUG=False`, vérifier `ALLOWED_HOSTS` et `SECRET_KEY` immédiatement.
- Activer rotation des secrets et configurer un gestionnaire de secrets.
- Ajouter SAST (Bandit) et SCA (pip-audit) dans CI.

## 12. Outils et commandes utiles
- Bandit: `bandit -r assets users radgestmat`.
- Pip-audit: `pip-audit`.
- Trivy (image): `trivy image myapp:latest`.
- ZAP baseline: `zap-baseline.py -t https://staging.example.com`.

---
Fichiers recommandés à fournir : `docs/runbooks/restore.md`, `.env.example`, exemples de configurations Nginx/TLS, politique de sauvegarde.
