# 🧪 Guide de Test - Alertes Visibles

## Comment Tester les Améliorations

### Prérequis
- ✅ Django server running: `http://127.0.0.1:8000/`
- ✅ Accès admin: `/admin/`
- ✅ Compte utilisateur avec accès materials

---

## Test 1: Admin des Alertes

### Étapes
1. Allez à `/admin/` → Alertes → Alertes
2. Observez la nouvelle liste avec colonnes visuelles

### Attendu
```
❌ PERDU     | TV-001 - Samsung 55"  | John Doe | IT_DEPT | 🔴 CRITIQUE | □ | 15/01
⚠️  DEFECT.  | CAM-045 - Canon EOS  | Jane     | HR_DEPT | 🔴 CRITIQUE | □ | 15/01
```

✓ **Vérifier:**
- [ ] Icônes visibles (❌ ⚠️ etc.)
- [ ] Asset ID + nom du matériel affichés
- [ ] Nom du client affichable
- [ ] Sévérité colorée (🔴 rouge)
- [ ] Recherche fonctionne sur asset_id, nom
- [ ] Cliquer sur une alerte affiche détails
- [ ] Boutons d'action présents (marquer réglementée, rouvrir)

---

## Test 2: Workflow Check-in Complet

### Scénario: Matériel Endommagé

#### Étape 1 - Check-out (pré-requis)
```
1. Materiel detail page → [📤 Check Out]
2. Sélectionner un client
3. Confirm → Material ATTRIBUE
```

#### Étape 2 - Check-in avec DAMAGE
```
1. Materiel detail page → [📥 Check In]
2. Form affiche:
   ├─ Date de retour
   ├─ Raison: [NORMAL ▼]
   ├─ (Description cachée)
   ├─ Notes
   └─ Maintenance
   
3. Sélectionner "Matériel endommagé"
   → Description field s'affiche
   
4. Entrer: "Écran fissé après chute"

5. Cocher "Mettre en maintenance"

6. Click [✓ Enregistrer le retour]
```

#### Étape 3 - Page de Confirmation
```
Attendu de voir:

⚠️ ALERTE - Matériel Endommagé
│
├─ Une alerte a été créée dans le système
│
├─ Alerte ID: <id>
├─ Type: Matériel endommagé
├─ Sévérité: CRITIQUE
├─ Créée le: 15/01/2025 14:30
│
└─ [Voir l'alerte dans l'admin →]

RÉCAPITULATIF DU CHECK-IN

Matériel: TV-001 - Samsung 55"
Statut: MAINTENANCE
Client: John Doe
Check-out: 10/01/2025
Check-in: 15/01/2025

Raison du retour: Matériel endommagé
Maintenance requise: Oui - Matériel en maintenance

[← Retour au matériel] [Liste des matériels] [Aller à l'admin]
```

✓ **Vérifier:**
- [ ] Page de confirmation s'affiche
- [ ] Alerte ID affiché
- [ ] Lien "Voir l'alerte" cliquable
- [ ] Récapitulatif complet visible
- [ ] Raison "Matériel endommagé" affichée
- [ ] Statut "MAINTENANCE" correct

#### Étape 4 - Vérifier l'Admin
```
1. Click [Voir l'alerte dans l'admin →]
   → S'ouvre sur l'alerte dans l'admin
   
2. Vérifier:
   ├─ Type: DEFECTUEUX ✓
   ├─ Sévérité: CRITICAL ✓
   ├─ Matériel: TV-001 ✓
   ├─ Client: John Doe ✓
   ├─ Description: "Écran fissé..." ✓
   └─ Date création: Correcte ✓

3. Revenir à la liste des alertes
   → TV-001 visible avec icône ⚠️
```

---

## Test 3: Workflow Check-in - Matériel Perdu

### Scénario: Matériel Perdu

#### Étape 1 - Check-in avec LOST
```
1. /materiel/<asset_id>/checkin/ → Check In form

2. Sélectionner "Matériel perdu"
   → Description field s'affiche

3. Entrer: "Perdu lors du transport entre A et B"

4. Notes: "À signaler à l'assurance"

5. Click [✓ Enregistrer le retour]
```

#### Étape 2 - Page de Confirmation
```
Attendu:

❌ ALERTE CRITIQUE - Matériel Perdu
│
├─ Une alerte a été créée dans le système.
│
├─ Alerte ID: <id>
├─ Type: Matériel perdu
├─ Sévérité: CRITIQUE
├─ Créée le: 15/01/2025 15:30
│
└─ [Voir l'alerte dans l'admin →]

...

Matériel perdu lors de l'attribution à John Doe
Perdu lors du transport entre A et B
```

✓ **Vérifier:**
- [ ] Alerte avec icône ❌ (rouge)
- [ ] Type "Matériel perdu" correct
- [ ] Description affichée

---

## Test 4: Page Admin des Alertes

### Vérifications
```
1. /admin/assets/alerte/

[ ] Liste des alertes visible
[ ] Colonnes: Icône | Type | Matériel | Client | Dept | Sévérité | Reg. | Date
[ ] Icônes affichées correctement
[ ] Tri par date descending (plus récentes d'abord)

2. Filtres
[ ] Filtrer par Type (PERDU, DEFECTUEUX, etc.)
[ ] Filtrer par Sévérité (CRITICAL, WARNING, INFO)
[ ] Filtrer par Département
[ ] Filtrer par Reglementee (Oui/Non)

3. Recherche
[ ] Chercher par asset_id (ex: "TV-001")
[ ] Chercher par nom (ex: "Samsung")
[ ] Chercher par client (ex: "John")
[ ] Chercher par département (ex: "IT")

4. Actions
[ ] Sélectionner une alerte
[ ] Cliquer: "Marquer comme réglementées"
[ ] Vérifier: "reglementee" passe à ✓
[ ] Cliquer: "Rouvrir les alertes"
[ ] Vérifier: "reglementee" repasse à □

5. Détails d'une alerte
[ ] Cliquer sur une alerte
[ ] Vérifier tous les champs:
    ├─ Type d'alerte
    ├─ Sévérité
    ├─ Matériel (lien cliquable?)
    ├─ Attribution (lien cliquable?)
    ├─ Département
    ├─ Description complète
    ├─ Reglementee (checkbox)
    └─ Date création (read-only)
```

---

## Test 5: Historique du Matériel

### Vérification de la Trace

```
1. Aller à: /admin/assets/materiel/<id>/change/

[ ] Statut: MAINTENANCE ✓
[ ] Etat technique: EN_MAINTENANCE ✓

2. Chercher HistoriqueAttribution pour ce matériel
   /admin/assets/historiqueattribution/

[ ] Dernier entrée est CHECK_IN
[ ] Notes contient:
    ├─ "[Raison: Matériel endommagé]" OU
    ├─ "[Raison: Matériel perdu]"
    ├─ "[Détails: <description>]"
    └─ Autres notes utilisateur
```

---

## Test 6: Messages Django

### Vérification du Template

```
1. Pendant le check-in, observer les messages:
   [ ] Messages s'affichent avec animations
   [ ] Couleurs correctes:
       ├─ Success (vert)
       ├─ Warning (orange) pour DAMAGE
       └─ Error (rouge) pour LOST

2. Liens cliquables dans messages:
   [ ] "Voir l'alerte →" ouvre l'admin
   [ ] Target="_blank" (ouvre dans nouvel onglet)
```

---

## Checklist Complète

### Configuration
- [ ] Django server running
- [ ] Tests passants (5/5)
- [ ] No syntax errors
- [ ] Admin enregistré

### Admin Interface
- [ ] Alertes visibles en liste
- [ ] Icônes affichées
- [ ] Colonnes complètes
- [ ] Recherche fonctionne
- [ ] Filtres fonctionnent
- [ ] Actions disponibles

### Workflow
- [ ] Check-out fonctionne
- [ ] Check-in form affiche nouvelle raison
- [ ] Description conditionnelle visible
- [ ] Page de confirmation s'affiche
- [ ] Alerte créée et visible en admin

### Audit Trail
- [ ] HistoriqueAttribution créé
- [ ] Alerte créée (si DAMAGE/LOST)
- [ ] Matériel → MAINTENANCE
- [ ] Timestamps correctes
- [ ] Utilisateur enregistré

### Données
- [ ] Raison sauvegardée
- [ ] Description sauvegardée
- [ ] Notes sauvegardées
- [ ] Liens corrects (materiel, attribution, client)

---

## 🎉 Si Tout Passe

Vous avez:
✅ Alertes de dégâts/pertes VISIBLES
✅ Admin enrichi avec colonnes utiles
✅ Page de confirmation immédiate
✅ Audit trail complète
✅ Workflow clair et transparent

**Le système est prêt pour la production!**

---

## 🐛 Si Quelque Chose Ne Fonctionne Pas

### Problème: Page de confirmation ne s'affiche pas
```
→ Vérifier: URL /checkin/success/ enregistrée?
→ Vérifier: Vue checkin_success existe?
→ Vérifier: Template check_in_success.html existe?
```

### Problème: Alerte non créée
```
→ Vérifier: Raison = 'DAMAGE' ou 'LOST' exactement
→ Vérifier: Alerte table non readonly
→ Vérifier: Pas d'erreur dans console serveur
```

### Problème: Colonnes non affichées
```
→ Vérifier: AlerteAdmin.list_display correcte
→ Vérifier: Méthodes get_* définies
→ Vérifier: Syntaxe correcte (virgules, parenthèses)
```

### Problème: Admin ne sauvegarde pas reglementee
```
→ Vérifier: Field not readonly
→ Vérifier: Pas d'erreur SQL
→ Vérifier: Permission user correcte
```

---

**Documentation complète: VISIBILITY_SUMMARY.md**
**Questions? Voir: ALERT_VISIBILITY_IMPROVEMENT.md**
