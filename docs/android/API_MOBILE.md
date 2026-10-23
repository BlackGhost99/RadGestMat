# API mobile RadGestMat — première tranche

Cette version expose uniquement la lecture du matériel. Les opérations de sortie/retour ne sont volontairement pas exposées tant que l'idempotence, les transactions et les conflits de synchronisation ne sont pas implémentés.

Base : `/api/v1/mobile/`

## Authentification et autorisations

- Requiert une session Django authentifiée ou HTTP Basic Authentication.
- HTTP Basic doit être utilisé uniquement sur HTTPS.
- Un profil RadGestMat actif est obligatoire.
- `SUPER_ADMIN` peut consulter tous les départements ; les autres rôles sont limités à leur département.
- Une fiche d'un autre département renvoie 404 afin de ne pas révéler l'existence de l'identifiant.
- Aucun endpoint mobile d'écriture n'est exposé dans cette tranche.

## Endpoints

### `GET /api/v1/mobile/assets/`

Paramètres facultatifs :
- `limit` : 1 à 100, défaut 50.
- `offset` : entier positif ou nul, défaut 0.
- `updated_since` : date ISO-8601 ; renvoie les matériels modifiés après cette date.

La réponse contient `results`, `pagination` et `server_time`. Pour une synchronisation complète, parcourir les pages jusqu'à ce que `next_offset` soit nul. Pour une synchronisation différentielle, conserver l'heure serveur après avoir terminé toutes les pages.

### `GET /api/v1/mobile/assets/<asset_id>/`

Recherche une fiche par identifiant matériel, utilisable après lecture du QR code. La recherche reste limitée aux permissions du compte connecté.

## Hors ligne

Le client Android pourra conserver localement les fiches déjà téléchargées. Toute opération qui modifie l'inventaire doit rester en attente locale et ne pas être affichée comme confirmée avant réponse du serveur. Les endpoints de check-out/check-in seront ajoutés dans une étape ultérieure après mise en place d'une clé d'opération unique, de transactions et de tests de concurrence.
