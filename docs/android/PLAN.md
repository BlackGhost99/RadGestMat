# RadGestMat Android — plan de développement

Branche de travail : `feature/android-offline-app`. La branche `main` et le déploiement Render ne sont pas modifiés.

## État vérifié dans le dépôt

- Django REST Framework est présent dans `requirements.txt`.
- `assets/urls.py` expose déjà `scan/`, `scan/<asset_id>/`, `materiel/<asset_id>/checkout/` et `materiel/<asset_id>/checkin/`.
- Dans `radgestmat/urls.py`, la route REST `api/v1/` est commentée. Vérifier les vues et permissions avant de l'activer.

## Architecture cible

- Application Android native légère (Kotlin, WebView pour les écrans en ligne et écrans natifs pour le scanner et les opérations hors ligne).
- Django sur Render reste le serveur métier et le point d'accès aux données PostgreSQL Supabase.
- Stockage Android local chiffré selon la sensibilité des données; file d'opérations persistante.
- API versionnée avec authentification, contrôle des rôles, validation serveur, identifiant d'opération idempotent et gestion des conflits.
- Les opérations hors ligne sont **en attente**, jamais considérées comme validées par le serveur avant synchronisation.

## Étapes

1. Auditer les modèles, vues de scan/check-in/check-out, authentification et permissions.
2. Définir les contrats API et tests d'autorisation/idempotence/conflits.
3. Implémenter les API Django sans casser les routes HTML existantes.
4. Ajouter l'application Android, caméra QR et stockage local.
5. Implémenter la synchronisation résiliente et les tests sans réseau.
6. Générer et tester un APK de développement signé pour les essais, puis préparer la signature de distribution.

## Précautions

Ne pas ajouter de secrets, mot de passe, URL de base avec identifiants ou données réelles au dépôt. Ne pas fusionner dans `main` ni déployer avant tests et validation.
