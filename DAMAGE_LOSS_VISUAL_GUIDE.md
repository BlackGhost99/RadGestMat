# Damage/Loss Tracking - Quick Visual Test

## How the Feature Works

### 1. Check-in Form Workflow

When a material is being returned (check-in), the system now shows:

```
┌─────────────────────────────────────┐
│   📥 Check-in: TV-001               │
│                                     │
│  MATERIAL INFO                      │
│  ├─ Name: Samsung TV 55"            │
│  ├─ Asset: TV-001                   │
│  └─ State: ATTRIBUE                 │
│                                     │
│  CLIENT                             │
│  └─ John Doe (john@example.com)     │
│                                     │
│  RETURN FORM                        │
│  ├─ Date: [_______________]         │
│  ├─ Reason: [NORMAL ▼]              │
│  │  Options:                        │
│  │  • Retour normal                 │
│  │  • Matériel endommagé ✗ DAMAGE   │
│  │  • Matériel perdu ✗ LOST        │
│  │  • Autre raison                  │
│  │                                  │
│  ├─ [Description field appears]     │
│  ├─ Notes: [_______________]        │
│  ├─ ☐ Mettre en maintenance         │
│  └─ [✓ Confirm] [✕ Cancel]        │
└─────────────────────────────────────┘
```

### 2. User Selects "Damaged" Reason

```
┌─────────────────────────────────────┐
│   📥 Check-in: TV-001               │
│                                     │
│  Reason: [Matériel endommagé ▼]    │
│                                     │
│  ⚠️  Description des dégâts:       │
│  ┌────────────────────────────────┐ │
│  │ Écran fissé, coin inférieur   │ │
│  │ droit, apparemment de chute.  │ │
│  │ Ne s'allume plus correctement.│ │
│  └────────────────────────────────┘ │
│                                     │
│  Notes:                             │
│  ┌────────────────────────────────┐ │
│  │ À réparer avant réutilisation  │ │
│  └────────────────────────────────┘ │
│                                     │
│  ☑ Mettre en maintenance           │
│  [✓ Confirm] [✕ Cancel]           │
└─────────────────────────────────────┘
```

### 3. System Auto-Creates Alert

When form is submitted:

```
✅ Success: Retour enregistré
⚠️  Alert: Matériel endommagé - une alerte a été créée

DATABASE CHANGES:
│
├─ Attribution CLOSED
│  └─ date_retour_effective: 2025-01-15
│
├─ Material UPDATED
│  └─ statut_disponibilite: MAINTENANCE
│
├─ HistoriqueAttribution CREATED
│  ├─ action: CHECK_IN
│  ├─ user: john_admin
│  ├─ timestamp: 2025-01-15 14:30:00
│  └─ notes: "À réparer avant réutilisation
│            [Raison: Matériel endommagé]
│            [Détails: Écran fissé...]"
│
└─ ⚠️  Alerte CREATED (CRITICAL)
   ├─ type: DEFECTUEUX
   ├─ severite: CRITICAL
   ├─ materiel: TV-001
   ├─ attribution: #123
   ├─ description: "Matériel endommagé lors de 
   │               l'attribution à John Doe
   │               Dégâts: Écran fissé, coin 
   │               inférieur droit..."
   ├─ date_creation: 2025-01-15 14:30:00
   └─ department: IT_DEPT
```

### 4. Admin View Alerts

In Django Admin:

```
ADMIN > ALERTS > ALERTES

┌──────────────────────────────────────────┐
│ Type        │ Severity │ Material │ Date │
├──────────────────────────────────────────┤
│ DEFECTUEUX  │ CRITICAL │ TV-001   │ Today│
│ PERDU       │ CRITICAL │ CAM-045  │ Today│
│ DEFECTUEUX  │ CRITICAL │ PROJ-12  │ Today│
└──────────────────────────────────────────┘

FILTER OPTIONS:
☐ RETARD (Late return)
☑ DEFECTUEUX (Damaged)  ← Shows damaged items
☑ STOCK_CRITIQUE (Low stock)
☑ PERDU (Lost)          ← Shows lost items

CLICK ON ALERT:
┌──────────────────────────────────────┐
│ Alert Details                         │
├──────────────────────────────────────┤
│ Type:          DEFECTUEUX            │
│ Severity:      CRITICAL ⚠️             │
│ Material:      TV-001                │
│ Client:        John Doe              │
│ Department:    IT_DEPT               │
│ Description:   Écran fissé, ne       │
│                s'allume plus         │
│ Date Created:  2025-01-15 14:30:00  │
│ Status:        Active                │
│                                      │
│ RELATED:                             │
│ • Attribution #123                   │
│ • HistoriqueAttribution (details)   │
│ • Material (TV-001)                 │
└──────────────────────────────────────┘
```

### 5. Material Status Locked

Material is now in MAINTENANCE and cannot be checked out:

```
MATERIAL DETAIL VIEW
┌──────────────────────────────┐
│ TV-001 - Samsung TV 55"       │
├──────────────────────────────┤
│ Status: MAINTENANCE 🔒        │
│                              │
│ Last Attribution:            │
│ ├─ Client: John Doe          │
│ ├─ Checked out: 2025-01-10  │
│ ├─ Checked in: 2025-01-15   │
│ ├─ Reason: DAMAGED ⚠️         │
│ └─ Description: Écran fissé  │
│                              │
│ Related Alert:               │
│ ├─ Type: DEFECTUEUX (CRITICAL)│
│ ├─ Created: 2025-01-15       │
│ └─ Link: View Alert          │
│                              │
│ ACTIONS:                     │
│ [⚠️  Check In] ← Disabled    │
│ [📤 Check Out] ← Disabled   │
│ (Admin can change status)    │
└──────────────────────────────┘
```

---

## Real-World Usage Examples

### Example 1: Damaged Projector

```
WHAT HAPPENED:
- Projector borrowed for conference
- Accidentally dropped during transport
- Glass lens cracked, won't turn on

CHECKIN PROCESS:
1. User scans QR code
2. Selects: "Matériel endommagé"
3. Describes: "Verre du projecteur cassé, 
   ne s'allume plus après chute"
4. Notes: "Devis réparation demandé"
5. Submits

RESULT:
✅ Attribution closed
✅ Material: MAINTENANCE
✅ Alert CRITICAL: TYPE_DEFECTUEUX
✅ Full audit trail with damage details
```

### Example 2: Lost Camera

```
WHAT HAPPENED:
- Camera borrowed for outdoor photography
- Lost somewhere between Site A and Site B
- Cannot be found despite search

CHECKIN PROCESS:
1. User scans QR code
2. Selects: "Matériel perdu"
3. Describes: "Perdu lors du transport
   entre Genève (depart 14h) et Lausanne
   (arrivée 16h30). Inclure dans 
   recherche sites"
4. Notes: "À signaler à l'assurance,
   valeur: 2500 CHF"
5. Submits

RESULT:
✅ Attribution closed
✅ Material: MAINTENANCE
✅ Alert CRITICAL: TYPE_PERDU
✅ Full audit trail with loss circumstances
✅ Insurance team notified to review alert
```

### Example 3: Normal Return

```
WHAT HAPPENED:
- Laptop borrowed and returned in good condition
- No issues, works perfectly

CHECKIN PROCESS:
1. User scans QR code
2. Selects: "Retour normal" (default)
3. Submits with optional notes

RESULT:
✅ Attribution closed
✅ Material: DISPONIBLE ✓
✓ NO ALERT CREATED (expected)
✅ Audit trail: normal return
```

---

## Key Audit Trail Information

Every damage/loss check-in creates permanent records:

### HistoriqueAttribution Entry
```
{
  "attribution": "Loan #123",
  "action": "CHECK_IN",
  "utilisateur": "john_admin",
  "etat_avant": "ATTRIBUE",
  "etat_apres": "MAINTENANCE",
  "notes": "À réparer avant réutilisation
            [Raison: Matériel endommagé]
            [Détails: Écran fissé, coin 
            inférieur droit, apparemment 
            de chute]",
  "date_action": "2025-01-15T14:30:00Z"
}
```

### Alerte Entry
```
{
  "type_alerte": "DEFECTUEUX",
  "severite": "CRITICAL",
  "materiel": "TV-001",
  "attribution": "#123",
  "departement": "IT_DEPT",
  "description": "Matériel endommagé lors de 
                 l'attribution à John Doe
                 Dégâts: Écran fissé, coin
                 inférieur droit",
  "reglementee": false,
  "date_creation": "2025-01-15T14:30:00Z"
}
```

---

## ✅ Complete Tracking Achieved

✓ **WHO**: User recorded (john_admin)
✓ **WHEN**: Timestamp recorded (2025-01-15 14:30:00)
✓ **WHAT**: Damage/loss reason + description
✓ **WHY**: Full details captured
✓ **WHERE**: Material ID, department
✓ **HOW**: Material status change tracking

---

**Feature Status: ✅ COMPLETE AND TESTED**

All tests passing. Ready for production deployment.
