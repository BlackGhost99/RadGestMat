## Chapitre III — Modélisation UML et spécifications techniques

**Objectif :** fournir une spécification technique structurée (diagrammes UML, descriptions de cas d'utilisation, diagrammes de séquence et mappings vers les modèles Django existants) pour guider l'implémentation et les revues d'architecture.

### 1. Contexte et périmètre
- **Périmètre fonctionnel :** gestion des matériels, attributions (Client ou Salle), check-in/check-out, détection automatique d'alertes (retard, défectueux, perdu, stock critique, rappels), audit des actions.
- **Public cible :** Service IT (utilisateurs principaux), administration (direction), personnels opérationnels (réception, maintenance).

### 2. Objectifs du chapitre
- Formaliser cas d'utilisation clés.
- Fournir diagrammes de classes alignés aux modèles Django.
- Décrire scénarios de séquence pour les flows critiques (check-out, check-in, détection d'alertes).
- Donner critères d'acceptation et plan d'implémentation minimal viable.

### 3. Cas d'utilisation (synthèse)
- UC1 — Authentification et gestion des rôles : connexion, restrictions superuser / read-only pour le staff.
- UC2 — Enregistrer matériel : CRUD pour `Materiel` (valeur, état, références).
- UC3 — Attribuer matériel : créer `Attribution` vers `Client` ou `Salle` (sélection de destination, durée, caution si valeur élevée).
- UC4 — Check-out : confirmer sortie matérielle (générer attribution si nécessaire).
- UC5 — Check-in : enregistrement retour, état (OK, endommagé, perdu), générer alertes si nécessaire.
- UC6 — Détection automatique : exécution périodique du `AlerteService` (détecter retards, rappels, défauts, pertes, stock critique).
- UC7 — Audit et traçabilité : création d'`AuditLog` pour actions sensibles.

Voir le diagramme de cas d'utilisation détaillé (PlantUML) dans `docs/diagrams/chapter3_usecases.puml`.

### 4. Diagramme de classes (synthèse)
Le diagramme de classes présente les entités principales et leurs relations. Mapping principal vers Django :
- `Materiel` -> `assets.models.Materiel`
- `Client` -> `users.models.Client` (ou `assets.models.Client` selon implémentation actuelle)
- `Salle` -> `assets.models.Salle`
- `Attribution` -> `assets.models.Attribution` (FK vers `Materiel`, nullable FK vers `Client` et FK vers `Salle`)
- `Alerte` -> `assets.models.Alerte` (champ `severite`, `categorie`, `description`)
- `AuditLog` -> `assets.models.AuditLog` (user nullable)

Le diagramme de classes détaillé se trouve dans `docs/diagrams/chapter3_class_diagram.puml`.

### 5. Scénarios de séquence critiques
5.1 Check-out (simplifié)
- Acteur : Agent (Service IT / Réception)
- Étapes :
  1. Agent initie `Check-out`
  2. Système vérifie disponibilité du `Materiel`
  3. Système crée `Attribution` avec destination (`Client` ou `Salle`)
  4. Système crée `AuditLog` et, si valeur élevée, instancie workflow d'approbation/dépôt

5.2 Check-in (simplifié)
- Acteur : Agent
- Étapes :
  1. Agent enregistre retour via `CheckInForm` en précisant `etat` (OK / endommagé / perdu)
  2. Système met à jour `Attribution` (date_retour_effective)
  3. Système crée `AuditLog`
  4. Si `etat` est endommagé/perdu -> créer `Alerte` (sévérité CRITICAL pour perte/dommage majeur)

5.3 Exécution du `AlerteService`
- Composant : Tâche périodique (cron / Celery beat)
- Étapes :
  1. Charger attributions actives (select_related client/salle, materiel)
  2. Appliquer règles (retards, rappels, défectueux, stock critique)
  3. Créer `Alerte` si condition remplie
  4. Créer `AuditLog` pour chaque alerte créée

Ces scénarios peuvent être traduits en PlantUML séquence au besoin (optionnel).

### 6. Contraintes non-fonctionnelles
- **Sécurité :** authentification forte (Django auth, 2FA optionnel), permissions strictes pour actions critiques.
- **Disponibilité :** detection d'alertes via tâches asynchrones (Celery + Redis) pour ne pas charger le web worker.
- **Performances :** indexer les colonnes fréquemment filtrées (`materiel_id`, `date_retour_prevue`, `etat`).
- **Observabilité :** logs structurés (JSON) + métriques (Prometheus) pour taux d'alertes, latence de détection.
- **Sauvegarde :** sauvegardes régulières base de données et export CSV d'inventaire.

### 7. Règles métier notables (rappel depuis Chapitre II)
- Les matériels de valeur >= 50 000 FCFA déclenchent process d'approbation/dépôt.
- Le Service IT est prioritaire pour toutes les actions d'inventaire et d'attribution.
- Les alertes de défaut/perte doivent être escaladées (notification direction + création d'un ticket interne).

### 8. Critères d'acceptation (MUST)
- CA1 : On peut créer une `Attribution` vers un `Client` ou vers une `Salle` via l'interface.
- CA2 : Les check-in/check-out mettent correctement à jour les dates et créent les `AuditLog`.
- CA3 : `AlerteService` détecte et persiste au minimum les retards et rappels (tests unitaires couvrant ces règles).
- CA4 : Les utilisateurs non-superuser ne peuvent pas créer/supprimer `Alerte` depuis l'admin (read-only view).
- CA5 : Les matériels de haute valeur doivent requérir une saisie de dépôt/caution lors de l'attribution.

### 9. Plan d'implémentation (itérations recommandées)
- Sprint 1 (MVP) : diagrammes + endpoints CRUD `Materiel`/`Attribution`; check-in/check-out; tests unitaires de base.
- Sprint 2 : `AlerteService` et tasks périodiques; PlantUML séquence + monitoring minimal.
- Sprint 3 : Workflows d'approbation pour matériels à haute valeur; notifications/escaliers d'alerte.

### 10. Annexes
- Diagrammes source (PlantUML) :
  - `docs/diagrams/chapter3_usecases.puml`
  - `docs/diagrams/chapter3_class_diagram.puml`

---
Fin du Chapitre III (brouillon). Indiquez si vous voulez que je :
- génère les images PNG/SVG depuis PlantUML,
- exporte le chapitre en `.docx`,
- ou que je détaille les diagrammes de séquence en PlantUML.
