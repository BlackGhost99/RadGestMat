# Damage/Loss Tracking - User Guide

## Quick Start

When checking in a material that has been lost or damaged, the system now allows you to record this information with an automatic audit trail.

## Workflow

### 1. Scan QR Code or Navigate to Check-in
- Material enters check-in workflow
- Form displays with return reason options

### 2. Select Return Reason
Four options available:

#### ✓ Retour normal
- Material returned in good condition
- No damage, not lost
- Material returns to DISPONIBLE status
- **No alert created**

#### ⚠️ Matériel endommagé (DAMAGE)
- Material has damage/defects
- Examples: Cracked screen, broken button, liquid damage
- Material moves to MAINTENANCE status
- **Auto-creates CRITICAL alert (TYPE_DEFECTUEUX)**
- Requires description of damage

#### 🚨 Matériel perdu (LOST)
- Material cannot be found
- Examples: Lost in transport, lost during event
- Material moves to MAINTENANCE status
- **Auto-creates CRITICAL alert (TYPE_PERDU)**
- Requires description of where/how lost

#### ℹ️ Autre raison (OTHER)
- Unusual situation not covered by above
- Material moves to MAINTENANCE status
- No automatic alert
- Use when situation needs manual review

### 3. Provide Details (if applicable)
- For DAMAGE: Describe the damage in detail
  - Example: "Écran fissué, ne s'allume plus"
  - Example: "Batterie ne charge plus"
  
- For LOST: Describe loss circumstances
  - Example: "Perdu lors du transport entre Genève et Lausanne"
  - Example: "Oublié sur place après l'événement"

### 4. Add Additional Notes (optional)
- Any extra information for the record
- Examples:
  - "À signaler à l'assurance"
  - "Client à contacter"
  - "Garantie encore valide"

### 5. Check Maintenance (if needed)
- Mark "Mettre en maintenance après le retour" if material needs inspection
- Automatically checked for DAMAGE and OTHER reasons

### 6. Submit
- Form validates that required fields are filled
- For DAMAGE/LOST: Description is required
- Submission creates:
  - Attribution closure
  - HistoriqueAttribution record with full details
  - Alerte record (for DAMAGE/LOST) with CRITICAL severity

## Alert Management

### Where to Find Alerts
- Django Admin: Alerts > Alertes
- Alerts are linked to:
  - Material (for quick reference)
  - Attribution (for context)
  - Department (for filtering)

### Alert Details Visible
- **Type**: PERDU or DEFECTUEUX
- **Severity**: CRITICAL (red flag)
- **Material**: Which item was affected
- **Attribution**: Which client was involved
- **Description**: Full details of damage/loss
- **Date Created**: Automatic timestamp
- **Department**: For departmental tracking

## Example Scenarios

### Scenario 1: Normal Return
```
1. Check in laptop
2. Select: "Retour normal"
3. Leave description empty
4. Submit
→ Result: Laptop → DISPONIBLE, no alert
```

### Scenario 2: Damaged Hardware
```
1. Check in projector
2. Select: "Matériel endommagé"
3. Describe: "Ventilateur cassé, fait du bruit"
4. Add note: "À faire réparer avant réutilisation"
5. Check: "Mettre en maintenance"
6. Submit
→ Result: 
   - Projector → MAINTENANCE
   - Alerte CRITICAL (TYPE_DEFECTUEUX)
   - HistoriqueAttribution contains all details
```

### Scenario 3: Lost Equipment
```
1. Check in camera
2. Select: "Matériel perdu"
3. Describe: "Perdu lors du transport entre sites"
4. Add note: "À signaler aux autorités"
5. Submit
→ Result:
   - Camera → MAINTENANCE
   - Alerte CRITICAL (TYPE_PERDU)
   - Full audit trail for insurance claim
```

## Important Notes

⚠️ **Materials marked as DAMAGE or LOST automatically move to MAINTENANCE status**
- They cannot be checked out again until status is changed
- Admin must review before returning to DISPONIBLE

✓ **All information is permanently recorded**
- Check HistoriqueAttribution for detailed action log
- Alertes table maintains CRITICAL alerts
- Full audit trail with user, timestamp, and description

🔍 **Alerts are CRITICAL severity**
- Red flag for management attention
- Should be reviewed daily
- Document any follow-up actions

## Troubleshooting

**Q: Form won't submit with DAMAGE/LOST reason?**
A: Description field is required for these reasons. Fill in "Description des dégâts" field.

**Q: How do I undo a DAMAGE/LOST check-in?**
A: You cannot undo. Contact admin to modify the record.

**Q: Material shows as MAINTENANCE after my check-in?**
A: This is expected for DAMAGE, LOST, or OTHER reasons. Admin must manually change status when ready.

**Q: Where can I see all the alerts?**
A: Django Admin → Alerts > Alertes. You can filter by type (PERDU/DEFECTUEUX) or severity.

## For Administrators

### Daily Tasks
- Review CRITICAL alerts in admin panel
- Check for PERDU (lost) materials - may need insurance documentation
- Check for DEFECTUEUX (damaged) materials - schedule repairs
- Contact departments about missing materials

### Weekly Tasks
- Generate report of DAMAGE/LOST materials
- Identify patterns (which materials/clients have issues)
- Follow up on material recovery
- Update insurance/maintenance records

### Monthly Tasks
- Reconcile MAINTENANCE items with actual repairs done
- Document cost of damage/loss
- Review trends and implement prevention measures

---

**For questions or issues:** Contact IT/RadGestMat support
