# Audit technique Android — 23 octobre 2026

Analyse statique du dépôt sur `feature/android-offline-app`. Aucun test d'exécution ni test Android n'a encore été réalisé.

## Existant confirmé

- `assets/urls.py` : routes HTML `scan/`, `scan/<asset_id>/`, `materiel/<asset_id>/checkout/`, `materiel/<asset_id>/checkin/`.
- `assets/views.py` : `scan_qr` rend un template ; `scan_result` recherche `Materiel.asset_id` ; `checkout` et `checkin` traitent des formulaires Django et redirigent vers des pages HTML.
- `assets/models.py` : `Materiel.asset_id` unique, `date_modification` automatique, `Attribution` et `HistoriqueAttribution`.
- `users/models.py` : rôles `SUPER_ADMIN`, `DEPT_MANAGER`, `DEPT_USER`, associés à un département.
- `assets/views.py` : `api_materiel_snapshot` est une réponse JSON authentifiée, limitée au département, mais ne renvoie que nombre et dernière modification.
- `radgestmat/urls.py` : inclusion `api/v1/` commentée.

## Risques relevés dans le code existant

1. **Contrôle d'accès incohérent :** `checkout` vérifie le rôle/département seulement si `request.profil_utilisateur` existe. `checkin` ne réalise pas dans son corps de vérification explicite équivalente. Vérifier les middlewares et autres protections avant toute exposition API.
2. **Concurrence :** les vues de sortie/retour effectuent lecture, validation et écriture sans transaction/lock explicites dans les extraits examinés. Risque de double attribution ou retour concurrent. L'API mobile devra utiliser `transaction.atomic`, `select_for_update` et des règles d'unicité pertinentes.
3. **Idempotence :** aucune clé unique d'opération mobile n'a été identifiée dans les modèles consultés. Une nouvelle tentative de synchronisation pourrait doubler les mouvements sans déduplication serveur.
4. **Versionnement :** `Materiel.date_modification` peut aider aux conflits, mais ne suffit pas à lui seul pour toutes les transitions d'attribution. Définir un jeton/version de référence serveur.
5. **Sécurité :** ne pas exposer PostgreSQL/Supabase directement à l'APK ; utiliser uniquement l'API Django HTTPS et un mécanisme d'authentification adapté au mobile. Les secrets restent côté serveur.
6. **Compatibilité :** les pages HTML et le workflow existant doivent rester fonctionnels. Éviter de réutiliser directement les endpoints HTML comme protocole de synchronisation.

## Contrat API proposé (non implémenté)

- `GET /api/v1/mobile/assets/?updated_since=...` : lecture paginée, filtrée par permissions, avec horodatage/version serveur.
- `GET /api/v1/mobile/assets/<asset_id>/` : fiche autorisée, statut courant, version.
- `POST /api/v1/mobile/operations/` : `operation_id` UUID unique, type `CHECKOUT`/`CHECKIN`, asset, référence d'attribution, version attendue, payload validé ; réponse `applied`, `already_applied`, `conflict` ou `rejected`.
- `GET /api/v1/mobile/operations/<operation_id>/` : état fiable après coupure réseau.

## Critères avant APK de test

- Tests de rôles et d'accès inter-département, utilisateur sans profil, session expirée.
- Tests de deux téléphones effectuant une attribution concurrente.
- Tests de rejouabilité des requêtes et de perte réseau après commit serveur.
- Tests d'absence de doublons d'attributions, historique et alertes.
- Tests caméra/QR, cache local, déconnexion, restauration réseau et conflits.
- Audit des informations personnelles conservées hors ligne, chiffrement local et effacement à la déconnexion.

**Mise à jour du 23 octobre 2026 :** une première API mobile en lecture seule est implémentée sur la branche de travail : `GET /api/v1/mobile/assets/` (pagination et `updated_since`) et `GET /api/v1/mobile/assets/<asset_id>/` (recherche par identifiant QR). Elle exige une authentification et un profil actif, et limite les résultats au département de l'utilisateur sauf `SUPER_ADMIN`. Des tests automatisés ont été ajoutés, mais ils n'ont pas encore été exécutés dans un environnement Django. Les opérations check-out/check-in hors ligne, l'authentification par jeton mobile et l'APK restent à faire. Aucune migration, modification de base de données ou modification du déploiement de production n'a été effectuée.
