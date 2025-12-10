# Chapitre II — Étude de l'existant et analyse des besoins

## I. INTRODUCTION

But du chapitre
Ce chapitre présente la méthode d'analyse utilisée pour diagnostiquer l'existant au sein du Radisson Blu et formaliser les besoins métiers et techniques du projet RadGestMat. L'objectif est d'aboutir à un cahier des charges priorisé et vérifiable, aligné sur les besoins du Service IT (acteur prioritaire) et les usages des autres services (Technique, Magasinier, Banquet, Housekeeping).

Méthodologie
- Entretiens ciblés avec les responsables (Service IT, Responsable Technique, Magasinier, Responsable Banquet, Direction).
- Observation in situ des processus d'attribution et de restitution (conférences, évènements, gestion stock). 
- Analyse documentaire (inventaires Excel, procédures internes, contrats d'assurance, politiques de remplacement).
- Benchmark de solutions existantes et identification des meilleures pratiques.

Livrables attendus pour ce chapitre : document d'analyse, matrice besoins vs priorité, tableau comparatif solutions.

---

## II. DESCRIPTION DU PROJET

### A. Domaine d’application

Périmètre fonctionnel
- Gestion centralisée du parc matériel : inventaire unifié (chambres, A/V, IT, restauration), identification par `asset_id` et `numero_serie`.
- Workflows d’attribution (check‑out) et de restitution (check‑in) : traçabilité complète avec horodatage et acteur responsable.
- Gestion de la maintenance : tickets, planification préventive et interventions correctives.
- Détection automatique d'alertes : retards, pannes, perte, seuils de stock critique.
- Reporting et audit : dashboard pour la Direction et rapports détaillés pour le Service IT.

Périmètre organisationnel
- Acteurs principaux : **Service IT** (prioritaire) — installation et attribution matérielle pour conférences/événements ; gestion des actifs de haute valeur (50k–5M FCFA).
- Acteurs secondaires : Service Technique / Sono, Magasinier, Banquet, Housekeeping, Direction.

Interfaces potentielles
- PMS / solution de réservation (pour lier événements et attributions), messagerie (email/SMS), stockage médias (S3) et outils analytiques (Google Analytics / YouTube analytics pour contenus de formation).

---

### B. Spécification des besoins

Acteurs et besoins (synthèse)
- Service IT (PRIORITAIRE)
  - Besoins : création rapide d’attributions, validation des retours, approbation des sorties d’équipements de forte valeur, reporting financier et opérationnel, gestion des incidents A/V.
- Service Technique / Sono
  - Besoins : accès pour attribuer/retourner matériel dépendant de la sono, suivi des interventions, consultation des plans de salle.
- Magasinier
  - Besoins : gestion du stock physique, préparation des sorties, prise en charge des inventaires périodiques.
- Housekeeping
  - Besoins : suivi des consommables, enregistrements simples d’entrées/sorties (pas d’attente de retour pour la plupart des consommables).
- Banquet / Événements
  - Besoins : demandes d’équipements, planning et validation d’allocation selon disponibilité.
- Direction
  - Besoins : KPIs consolidés, rapports financiers et opérationnels, alertes critiques.

Exemples de besoins fonctionnels (premier niveau)
- Enregistrement unifié des actifs avec métadonnées financières et assurances.
- Workflows d’autorisation selon seuils de valeur (valeur configurable en FCFA).
- Fonction mobile (scan QR) pour accélérer check‑in/out sur le terrain.
- Génération automatique d’alertes et envoi de notifications instantanées pour actifs de haute valeur.

---

## III. ETUDE DE L'EXISTANT

### A. Importance de RadGestMat

RadGestMat est conçu pour répondre aux lacunes observées dans la gestion du parc matériel au sein d’un hôtel de standing tel que Radisson Blu. Sa valeur ajoutée réside dans :
- Centralisation des informations et traçabilité complète des opérations.
- Automatisation des alertes et rappels pour réduire les pertes et incidents.
- Protection renforcée des actifs de forte valeur et réduction des coûts liés aux remplacements.
- Interface adaptée au Service IT (utilisateurs avancés) et aux techniciens (mobile/scan).

### B. Exemples de logiciels similaires sur le marché


## IV. CAHIER DES CHARGES

### A. Exigences fonctionnelles (MoSCoW)

**MUST**
1. Référentiel matériel unique (CRUD) : `asset_id`, `type`, `marque`, `modele`, `numero_serie`, `valeur_FCFA`, `localisation`, `statut`, `date_achat`, `date_garantie`, `assurance`, `responsable_it`.
2. Workflows d’attribution/check‑in avec audit complet et historique immuable.
3. QR codes pour check‑in/out et inventaire mobile.
4. Alertes automatiques : retards, maintenance, seuils stock, matériels perdus/détériorés.
5. Dashboard pour Direction et rapports pour Service IT.
6. Gestion des rôles et permissions (RBAC) détaillée.
7. Sauvegarde/restauration et journalisation des transactions.

**SHOULD**
1. Intégration API PMS.
2. Application mobile ou interface responsive pour scan QR.
3. Import/export CSV/Excel et scripts de migration.
4. Rapports programmés et envoi automatique.

**COULD**
1. Intégration Google Calendar, tutoriels YouTube intégrés.
2. Assistant ChatGPT pour support opérateur.
3. Moteur de règles proactif.

**WON'T**
1. Remplacement du PMS.
2. Modules comptables avancés.


### B. Exigences non‑fonctionnelles

- Performance : <300ms pour opérations standards ; scalabilité horizontale.
- Sécurité : TLS, chiffrement des exports sensibles, RBAC strict.
- Disponibilité : SLA cible 99.5% pour services critiques.
- Sauvegarde : dumps journaliers, sauvegardes incrémentales.
- Conformité : RGPD, conservation des logs.
- Exploitabilité : logs structurés, intégration Sentry/Prometheus.
- Internationalisation : FR/EN.

### C. Conclusion synthétique

Le cahier des charges impose la centralisation des actifs, des workflows d’attribution robustes, des règles spéciales pour actifs de forte valeur et des interfaces adaptées au Service IT. Les besoins prioritaires (MUST) conditionnent le déploiement d’un MVP utile au métier.

---

## LIVRABLES ET ESTIMATION DE LONGUEUR

- Document d'analyse complet (chapitre) : 6–10 pages. 
- Matrice besoins vs priorité (MoSCoW) : tableau.
- Tableau comparatif solutions (benchmark) : 1–2 pages.

---

## ANNEXE — Modèle CSV d'inventaire (colonnes recommandées)

asset_id,type,marque,modele,numero_serie,valeur_FCFA,localisation,statut,date_achat,date_garantie,assurance,responsable_it,notes

Exemple:
OKP-0001,Projecteur,Epson,EB-2245U,SN123456,1200000,Salle A,DISPONIBLE,2021-03-15,2024-03-15,AssureurX,sylvain.it,"Vérifier lampe"

---

*Fin du Chapitre II. Pour personnaliser ce chapitre, fournis s'il te plaît : organigramme officiel, échantillon d'inventaire, seuil de valeur à appliquer, et noms des référents IT/Technique.*
