# assets/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Max
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import PermissionDenied
from .forms import MaterielForm, ClientForm, AttributionForm
from .models import Materiel, Departement, Categorie, Attribution, Client, Alerte, Salle
from .models import AuditLog
from .forms import CheckInForm
from django.utils import timezone
from django.contrib import messages
from .models import HistoriqueAttribution
from users.permissions import role_required, can_view_department, can_manage_department, can_perform_checkout
from .services import AlerteService

from django.utils.text import capfirst
from django.utils.formats import date_format


def _human_label_for_field(model_class, field_name):
    """Return a human readable label for a field name on model_class if available."""
    if not model_class:
        return field_name.replace('_', ' ').capitalize()
    try:
        field = model_class._meta.get_field(field_name)
        return capfirst(str(field.verbose_name))
    except Exception:
        # fallback
        return field_name.replace('_', ' ').capitalize()


def _resolve_relation_value(model_class, field_name, val):
    """If the field is a FK, try to fetch the related object's display value.

    val may already be stringified; we try int conversion where appropriate.
    """
    if val is None:
        return None
    if not model_class:
        return val
    try:
        field = model_class._meta.get_field(field_name)
    except Exception:
        return val

    # If it's a relation, attempt to load related instance
    related_model = None
    try:
        related_model = getattr(field, 'related_model', None) or getattr(field.remote_field, 'model', None)
    except Exception:
        related_model = None

    if related_model:
        # val may be numeric id or string id; try to coerce to int
        try:
            pk = int(val)
        except Exception:
            pk = val
        try:
            obj = related_model.objects.filter(pk=pk).first()
            if obj:
                return str(obj)
        except Exception:
            return val

    return val


def _is_technical_field(field_name):
    """Return True if the given field name looks like a technical/meta field we should hide.

    This covers common names like 'path', 'meta', 'metadata', 'traceback', 'url', etc.
    """
    if not field_name:
        return False
    try:
        fn = str(field_name).lower()
    except Exception:
        return False

    blacklist = ('meta', 'metadata', 'path', 'traceback', 'stack', 'url', 'full_path', 'request_path')
    for b in blacklist:
        if fn == b or fn.endswith(b) or fn.startswith(b) or (b in fn):
            return True
    return False


def _sanitize_change_value(val):
    """Redact or shorten values that look like file-system paths, long dumps, or URLs.

    Returns a human-friendly placeholder for technical values.
    """
    if val is None:
        return None
    try:
        s = str(val)
    except Exception:
        return val

    # If it's obviously a URL, return a concise host+path label
    try:
        from urllib.parse import urlparse
        parsed = urlparse(s)
    except Exception:
        parsed = None

    if parsed and parsed.scheme and parsed.netloc:
        # keep host + first 3 path segments
        path_parts = [p for p in (parsed.path or '').split('/') if p]
        short_path = '/' + '/'.join(path_parts[:3]) + ('/' if len(path_parts) > 3 else '') if path_parts else '/'
        return f"[Méta] {parsed.netloc}{short_path}"

    # Windows absolute path like C:\ or UNC \\share -> return short prefix
    try:
        if (len(s) > 2 and s[1] == ':' and s[2] == '\\') or s.startswith('\\'):
            # split on backslash, keep drive + up to 2 next components
            parts = s.split('\\')
            short = '\\'.join(parts[:3])
            if len(parts) > 3:
                short = short + '\\...'
            return f"[Méta] {short}"
    except Exception:
        pass

    # Unix absolute path -> keep up to first 3 segments
    if s.startswith('/') and '/' in s:
        parts = [p for p in s.split('/') if p]
        short = '/' + '/'.join(parts[:3])
        if len(parts) > 3:
            short = short + '/...'
        return f"[Méta] {short}"

    # Very long strings (e.g. dumps) -> truncate
    if len(s) > 200:
        return s[:200] + '...'

    return s


def _format_changes_for_display(report):
    """Convert report.changes JSON into a list of human-readable change rows.

    Returns list of dicts: {'field': ..., 'old': ..., 'new': ...}
    """
    changes = report.changes or {}
    ct_model = None
    try:
        ct_model = report.content_type.model_class()
    except Exception:
        ct_model = None

    rows = []
    # special-case snapshot (delete)
    if isinstance(changes, dict) and 'snapshot' in changes:
        snap = changes.get('snapshot') or {}
        for k, v in (snap.items() if isinstance(snap, dict) else []):
            label = _human_label_for_field(ct_model, k)
            if _is_technical_field(k):
                new_val = _sanitize_change_value(v)
                explicit = f"[Méta] champ technique: {label} — {new_val}"
                rows.append({'field': label, 'old': None, 'new': explicit, 'field_name': k})
                continue
            new_val = _sanitize_change_value(v)
            rows.append({'field': label, 'old': None, 'new': new_val, 'field_name': k})
        return rows

    # Normal diffs: {field: [old, new], ...}
    if isinstance(changes, dict):
        for field, pair in changes.items():
            # pair expected like [old, new]
            old_val, new_val = (pair[0], pair[1]) if isinstance(pair, (list, tuple)) and len(pair) >= 2 else (None, pair)
            label = _human_label_for_field(ct_model, field)

            # For technical fields, produce explicit, user-friendly label
            if _is_technical_field(field):
                old_h = _sanitize_change_value(old_h)
                new_h = _sanitize_change_value(new_h)
                explicit = f"[Méta] champ technique: {label} — {new_h}"
                rows.append({'field': label, 'old': old_h, 'new': explicit, 'field_name': field})
                continue

            # Try to resolve relations to readable strings
            old_h = _resolve_relation_value(ct_model, field, old_val)
            new_h = _resolve_relation_value(ct_model, field, new_val)

            # Sanitize values that look like paths/urls or are excessively long
            old_h = _sanitize_change_value(old_h)
            new_h = _sanitize_change_value(new_h)

            # include the raw field name so callers can reorder or prioritize fields
            rows.append({'field': label, 'old': old_h, 'new': new_h, 'field_name': field})

    return rows


def _sanitize_metadata(metadata):
    """Return a sanitized metadata mapping ready for UI display.

    Replaces long dumps, paths and URLs with concise placeholders to avoid
    leaking technical data in the reports UI.
    """
    if not metadata:
        return {}
    out = {}
    try:
        for k, v in (metadata.items() if isinstance(metadata, dict) else []):
            try:
                # For technical keys, always sanitize the value
                if _is_technical_field(k):
                    out[k] = _sanitize_change_value(v)
                else:
                    # still coerce to string safely and truncate if too long
                    if v is None:
                        out[k] = None
                    else:
                        s = str(v)
                        out[k] = s if len(s) <= 200 else s[:200] + '...'
            except Exception:
                out[k] = '[Méta] — contenu non affichable'
    except Exception:
        return {}
    return out


def _build_human_readable_sentence(report, formatted_changes=None):
    """Build a clear, human-readable French sentence for important audit events.

    Currently specialises for Attribution events (create/update/delete).
    Falls back to the existing short `summary` when it cannot build a detailed sentence.
    """
    try:
        ct_model = report.content_type.model_class()
    except Exception:
        ct_model = None

    user_label = report.user.username if report.user else 'Système'

    # Special handling for Attribution model
    if ct_model and ct_model.__name__ == 'Attribution':
        # Try to load the Attribution instance if still present
        from .models import Attribution
        attribution = None
        try:
            attribution = Attribution.objects.select_related(
                'materiel', 'client', 'employe_responsable', 'client__salle'
            ).filter(pk=report.object_id).first()
        except Exception:
            attribution = None

        # Helper to format date/time nicely
        def _fmt_dt(dt):
            try:
                return date_format(dt, 'd/m/Y H:i')
            except Exception:
                return str(dt)

        # If we have the live attribution object, use it
        if attribution:
            materiel = attribution.materiel
            client = attribution.client
            responsable = getattr(attribution.employe_responsable, 'username', None) or str(attribution.employe_responsable or '')
            salle = getattr(client, 'salle', None)
            salle_label = salle.nom if salle else None

            parts = []
            parts.append(f"L'utilisateur \"{user_label}\" a attribué")
            # matériel description
            if materiel:
                sn = f" (s/n {materiel.numero_serie})" if materiel.numero_serie else ''
                parts.append(f"le matériel \"{materiel.nom}\" [{materiel.asset_id}]{sn}")
            # au client
            if client:
                parts.append(f"au client \"{client.nom}\"")
                if client.type_client == client.TYPE_CONFERENCE and salle_label:
                    parts.append(f"dans la salle \"{salle_label}\"")
            # date/time
            when = attribution.date_attribution or report.timestamp
            parts.append(f"le {_fmt_dt(when)}")
            # retour prévue
            if attribution.date_retour_prevue:
                parts.append(f"(retour prévu: {attribution.date_retour_prevue.isoformat()})")
            # notes
            if attribution.notes:
                parts.append(f"Notes: {attribution.notes}")

            return ' '.join(parts)

        # If no live object, try snapshot in changes
        changes = report.changes or {}
        snap = None
        if isinstance(changes, dict) and 'snapshot' in changes:
            snap = changes.get('snapshot') or {}

        if snap:
            parts = [f"L'utilisateur \"{user_label}\" a attribué"]
            # materiel
            m_nom = snap.get('materiel') or snap.get('materiel_id') or ''
            if m_nom:
                parts.append(f"le matériel \"{m_nom}\"")
            # client
            c_nom = snap.get('client') or snap.get('client_id') or ''
            if c_nom:
                parts.append(f"au client \"{c_nom}\"")
            # date
            when = snap.get('date_attribution') or report.timestamp
            parts.append(f"le {_fmt_dt(when)}")
            return ' '.join(parts)

    # Fallback: return None to let caller use the short summary
    return None


def _build_context_sentence(report):
    """Build a short, creative French context sentence for the report header.

    Examples:
      "Création — Attribution de matériel (OKP-000001) attribuée à M. Dupont par admin depuis 127.0.0.1"
      "Modification — Matériel: PC portable OKP-000123 (changement de statut) — par admin"
    """
    try:
        ct_model = report.content_type.model_class()
    except Exception:
        ct_model = None

    # action verb mapping
    action_map = {
        AuditLog.ACTION_CREATE: 'Création',
        AuditLog.ACTION_UPDATE: 'Modification',
        AuditLog.ACTION_DELETE: 'Suppression'
    }
    verb = action_map.get(report.action, report.get_action_display() or 'Action')

    action_verbose = report.get_action_display() or ''

    user_label = None
    try:
        user_label = report.user.get_full_name() or report.user.username
    except Exception:
        user_label = 'Système' if not report.user else str(report.user)

    # Determine a friendly object label
    obj_label = report.object_repr or ''
    friendly_model = None
    if ct_model:
        name = ct_model.__name__.lower()
        model_map = {
            'attribution': 'Attribution de matériel',
            'materiel': 'Matériel',
            'client': 'Client',
            'alerte': 'Alerte',
            'historiqueattribution': 'Historique d\'attribution'
        }
        friendly_model = model_map.get(name, ct_model._meta.verbose_name.title() if getattr(ct_model, '_meta', None) else ct_model.__name__)

    # For Attribution, try to extract the asset id and client from the object_repr or load the object
    object_desc = obj_label
    if ct_model and ct_model.__name__ == 'Attribution':
        # Try to load the Attribution instance when possible
        try:
            from .models import Attribution
            attribution = Attribution.objects.filter(pk=report.object_id).select_related('materiel', 'client').first()
            if attribution:
                mat = getattr(attribution.materiel, 'asset_id', '') or str(attribution.materiel or '')
                client = getattr(attribution.client, 'nom', '') or str(attribution.client or '')
                object_desc = f"{mat} → {client}"
        except Exception:
            # fallback: try to parse a common asset id pattern from object_repr
            import re
            m = re.search(r'(OKP-\d+)', obj_label)
            if m:
                aid = m.group(1)
                # try to append trailing name if present
                rest = obj_label.replace(aid, '').strip(' -:')
                if rest:
                    object_desc = f"{aid} — {rest}"
                else:
                    object_desc = aid

    # For clarity (Option 2): produce a formal, readable sentence
    # e.g. "Historique d'attribution créé (Check-in) — Objet: OKP-1000000 — Bénéficiaire: M. Brice Moukabi Ngwa — Par: admin (IP 127.0.0.1)"
    # past participle mapping for concise wording
    past_map = {
        AuditLog.ACTION_CREATE: 'créé',
        AuditLog.ACTION_UPDATE: 'modifié',
        AuditLog.ACTION_DELETE: 'supprimé',
    }
    action_label = past_map.get(report.action, (report.get_action_display() or '').lower() or verb.lower())

    # Try to extract asset id and client name for Attribution-like models
    asset_id = ''
    client_label = ''
    if ct_model and ct_model.__name__.lower() in ('attribution', 'historiqueattribution'):
        try:
            from .models import Attribution
            at = Attribution.objects.filter(pk=report.object_id).select_related('materiel', 'client').first()
            if at:
                asset_id = getattr(at.materiel, 'asset_id', '') or getattr(at.materiel, 'nom', '') or ''
                client_label = getattr(at.client, 'nom', '') or ''
        except Exception:
            # fallback: try parse from object_repr
            import re
            m = re.search(r'(OKP-\d+)', obj_label)
            if m:
                asset_id = m.group(1)
            # try to pull a trailing name
            rest = obj_label.replace(asset_id, '').strip(' -:,')
            if rest and not client_label:
                client_label = rest

    # Normalize actor label
    try:
        actor = report.user.get_full_name() or report.user.username
    except Exception:
        actor = 'Système' if not report.user else str(report.user)

    ip = report.ip_address or 'adresse inconnue'

    # Build readable pieces
    pieces = []
    if friendly_model:
        pieces.append(f"{friendly_model} {action_label}")
    else:
        pieces.append(f"{action_label}")

    if action_verbose:
        pieces[0] = f"{pieces[0]} ({action_verbose})"

    if asset_id:
        pieces.append(f"Objet: {asset_id}")
    elif object_desc:
        pieces.append(f"Objet: {object_desc}")

    if client_label:
        pieces.append(f"Bénéficiaire: {client_label}")

    pieces.append(f"Par: {actor} (IP {ip})")

    return ' — '.join(pieces)


def _build_creative_summary(report):
    """Return a compact, creative French summary for the report header.

    Examples:
      "admin a créé une Attribution de matériel — OKP-000001 → M. Dupont"
      "admin a modifié Matériel — PC portable OKP-000123 (statut: DISPONIBLE)"
    """
    try:
        ct_model = report.content_type.model_class()
    except Exception:
        ct_model = None

    # nice model name mapping
    model_map = {
        'attribution': 'Attribution de matériel',
        'materiel': 'Matériel',
        'client': 'Client',
        'alerte': 'Alerte',
        'historiqueattribution': "Historique d'attribution",
    }

    # action humanisation
    action_map = {
        AuditLog.ACTION_CREATE: 'a créé',
        AuditLog.ACTION_UPDATE: 'a modifié',
        AuditLog.ACTION_DELETE: 'a supprimé',
    }
    verb = action_map.get(report.action, report.get_action_display() or 'a fait')

    # actor label
    try:
        actor = report.user.get_full_name() or report.user.username
    except Exception:
        actor = 'Système' if not report.user else str(report.user)

    # object short description
    obj = report.object_repr or ''
    friendly_model = None
    if ct_model:
        friendly_model = model_map.get(ct_model.__name__.lower()) or getattr(ct_model._meta, 'verbose_name', ct_model.__name__)

    # For attribution try to extract asset and client names
    if ct_model and ct_model.__name__ == 'Attribution':
        try:
            from .models import Attribution
            attr = Attribution.objects.filter(pk=report.object_id).select_related('materiel', 'client').first()
            if attr:
                mat = getattr(attr.materiel, 'asset_id', None) or getattr(attr.materiel, 'nom', '')
                client = getattr(attr.client, 'nom', '')
                if mat and client:
                    obj = f"{mat} → {client}"
                elif mat:
                    obj = str(mat)
        except Exception:
            pass

    # Option 2: readable/formal summary
    # e.g. "Historique d'attribution créé (Check-in) pour OKP-1000000 — bénéficiaire : M. Brice Moukabi Ngwa."
    past_map = {
        AuditLog.ACTION_CREATE: 'créé',
        AuditLog.ACTION_UPDATE: 'modifié',
        AuditLog.ACTION_DELETE: 'supprimé',
    }
    action_label = past_map.get(report.action, (report.get_action_display() or '').lower() or 'fait')

    action_verbose = report.get_action_display() or ''

    # Try to extract asset and client like above
    asset_id = ''
    client_label = ''
    if ct_model and ct_model.__name__.lower() in ('attribution', 'historiqueattribution'):
        try:
            from .models import Attribution
            at = Attribution.objects.filter(pk=report.object_id).select_related('materiel', 'client').first()
            if at:
                asset_id = getattr(at.materiel, 'asset_id', '') or getattr(at.materiel, 'nom', '') or ''
                client_label = getattr(at.client, 'nom', '') or ''
        except Exception:
            pass

    # Friendly model name
    model_part = friendly_model or (ct_model._meta.verbose_name.title() if ct_model and getattr(ct_model, '_meta', None) else '')

    # Build summary
    summary_parts = []
    if model_part:
        summary_parts.append(f"{model_part} {action_label}")
    else:
        summary_parts.append(f"{action_label}")

    if action_verbose:
        summary_parts[0] = f"{summary_parts[0]} ({action_verbose})"

    if asset_id:
        summary_parts.append(f"pour {asset_id}")
    elif obj:
        summary_parts.append(f"pour {obj}")

    if client_label:
        summary_parts.append(f"— bénéficiaire : {client_label}")

    return ' '.join(summary_parts)

@login_required
def materiel_create(request):
    # récupère département injecté par votre middleware si présent
    departement = getattr(request, 'departement', None)

    # Assurer un département par défaut si le middleware ne l'a pas injecté
    # Évite l'erreur "Materiel has no departement" lors de la génération du QR code
    if not departement:
        departement, _ = Departement.objects.get_or_create(
            code='DEF',
            defaults={'nom': 'Département par défaut'}
        )

    if request.method == 'POST':
        form = MaterielForm(request.POST, request.FILES, departement=departement, user=request.user)
        if form.is_valid():
            materiel = form.save(commit=False)
            
            # Assigner le département : si le form (super-admin) a choisi un departement,
            # il aura été appliqué dans MaterielForm.save() logic when commit=False.
            # Sinon, fallback to middleware-injected department.
            if not getattr(materiel, 'departement_id', None) and departement:
                materiel.departement = departement
            
            # Générer automatiquement asset_id (toujours pour les nouvelles créations)
            # Si asset_id est vide, 'NEW', ou ne commence pas par 'OKP-', on génère un nouveau
            asset_id_value = getattr(materiel, 'asset_id', '') or ''
            if (not asset_id_value or 
                asset_id_value.strip() == '' or 
                asset_id_value == 'NEW' or 
                (asset_id_value and not asset_id_value.startswith('OKP-'))):
                
                # Trouver le dernier asset_id pour ce département (approche robuste)
                if materiel.departement:
                    # Récupérer tous les asset_id OKP et extraire le max numérique
                    existing_assets = Materiel.objects.filter(
                        departement=materiel.departement,
                        asset_id__startswith='OKP-'
                    ).values_list('asset_id', flat=True)
                    
                    max_num = 0
                    for aid in existing_assets:
                        try:
                            num = int(aid.split('-')[1])
                            if num > max_num:
                                max_num = num
                        except (ValueError, IndexError):
                            continue
                    
                    nouveau_num = max_num + 1
                    materiel.asset_id = f"OKP-{nouveau_num:06d}"
                else:
                    materiel.asset_id = "OKP-000001"
            
            # Générer automatiquement numero_inventaire (toujours pour les nouvelles créations)
            numero_inv_value = getattr(materiel, 'numero_inventaire', '') or ''
            if (not numero_inv_value or 
                numero_inv_value.strip() == '' or
                (numero_inv_value and not numero_inv_value.startswith('RAD-'))):
                
                # Trouver le dernier numero_inventaire pour ce département (approche robuste)
                if materiel.departement:
                    existing_invs = Materiel.objects.filter(
                        departement=materiel.departement,
                        numero_inventaire__startswith='RAD-'
                    ).values_list('numero_inventaire', flat=True)
                    
                    max_num = 0
                    for inv in existing_invs:
                        try:
                            num = int(inv.split('-')[1])
                            if num > max_num:
                                max_num = num
                        except (ValueError, IndexError):
                            continue
                    
                    nouveau_num = max_num + 1
                    materiel.numero_inventaire = f"RAD-{nouveau_num:06d}"
                else:
                    materiel.numero_inventaire = "RAD-000001"
            
            materiel.save()
            # form.save_m2m() si champs M2M présents
            try:
                form.save_m2m()
            except Exception:
                pass
            return redirect('assets:materiel_detail', pk=materiel.pk)
        else:
            # utile pour debug : vérifiez form.errors dans la console serveur
            print("Materiel create errors:", form.errors)
    else:
        initial = {}
        if departement:
            initial['departement'] = departement
        form = MaterielForm(initial=initial, departement=departement, user=request.user)
    
    # Récupérer les noms de matériels existants pour le département
    noms_existants = Materiel.objects.filter(departement=departement).values_list('nom', flat=True).distinct().order_by('nom')
    categories = Categorie.objects.filter(departement=departement).order_by('nom')
    
    # Générer les valeurs par défaut pour asset_id et numero_inventaire
    if departement:
        # Trouver le dernier asset_id (approche robuste)
        existing_assets = Materiel.objects.filter(
            departement=departement,
            asset_id__startswith='OKP-'
        ).values_list('asset_id', flat=True)
        
        max_num = 0
        for aid in existing_assets:
            try:
                num = int(aid.split('-')[1])
                if num > max_num:
                    max_num = num
            except (ValueError, IndexError):
                continue
        
        nouveau_num = max_num + 1
        asset_id_default = f"OKP-{nouveau_num:06d}"
        
        # Trouver le dernier numero_inventaire (approche robuste)
        existing_invs = Materiel.objects.filter(
            departement=departement,
            numero_inventaire__startswith='RAD-'
        ).values_list('numero_inventaire', flat=True)
        
        max_num = 0
        for inv in existing_invs:
            try:
                num = int(inv.split('-')[1])
                if num > max_num:
                    max_num = num
            except (ValueError, IndexError):
                continue
        
        nouveau_num = max_num + 1
        numero_inv_default = f"RAD-{nouveau_num:06d}"
    else:
        asset_id_default = "OKP-000001"
        numero_inv_default = "RAD-000001"

    return render(request, 'assets/materiel_form.html', {
        'form': form,
        'title': 'Ajouter du matériel',
        'materiel': None,
        'noms_existants': noms_existants,
        'categories': categories,
        'asset_id_default': asset_id_default,
        'numero_inv_default': numero_inv_default,
    })

@login_required
def api_noms_materiels(request):
    """API pour récupérer les noms de matériels existants"""
    departement = getattr(request, 'departement', None)
    if not departement:
        return JsonResponse({'error': 'Département non trouvé'}, status=400)
    
    categorie_id = request.GET.get('categorie_id')
    query = request.GET.get('q', '')
    
    materiels = Materiel.objects.filter(departement=departement)
    
    if categorie_id:
        materiels = materiels.filter(categorie_id=categorie_id)
    
    if query:
        materiels = materiels.filter(nom__icontains=query)
    
    noms = materiels.values_list('nom', flat=True).distinct().order_by('nom')
    
    return JsonResponse({'noms': list(noms)})

@login_required
def api_creer_nom_materiel(request):
    """API pour créer un nouveau nom de matériel"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    departement = getattr(request, 'departement', None)
    if not departement:
        return JsonResponse({'error': 'Département non trouvé'}, status=400)
    
    nom = request.POST.get('nom', '').strip()
    categorie_id = request.POST.get('categorie_id')
    
    if not nom:
        return JsonResponse({'error': 'Le nom est requis'}, status=400)
    
    # Vérifier si le nom existe déjà
    if Materiel.objects.filter(departement=departement, nom=nom).exists():
        return JsonResponse({'error': 'Ce nom de matériel existe déjà'}, status=400)
    
    # Vérifier la catégorie
    if categorie_id:
        try:
            categorie = Categorie.objects.get(id=categorie_id, departement=departement)
        except Categorie.DoesNotExist:
            return JsonResponse({'error': 'Catégorie non trouvée'}, status=400)
    else:
        categorie = None
    
    return JsonResponse({
        'success': True,
        'nom': nom,
        'categorie_id': categorie_id,
        'message': 'Nom de matériel créé avec succès'
    })

@login_required
def api_creer_categorie(request):
    """API pour créer une nouvelle catégorie"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    departement = getattr(request, 'departement', None)
    if not departement:
        return JsonResponse({'error': 'Département non trouvé'}, status=400)
    
    nom = request.POST.get('nom', '').strip()
    description = request.POST.get('description', '').strip()
    
    if not nom:
        return JsonResponse({'error': 'Le nom est requis'}, status=400)
    
    # Vérifier si la catégorie existe déjà pour ce département
    if Categorie.objects.filter(departement=departement, nom=nom).exists():
        return JsonResponse({'error': 'Cette catégorie existe déjà'}, status=400)
    
    # Créer la catégorie
    try:
        categorie = Categorie.objects.create(
            nom=nom,
            departement=departement,
            description=description or f'Catégorie {nom}'
        )
        return JsonResponse({
            'success': True,
            'categorie_id': categorie.id,
            'nom': categorie.nom,
            'message': 'Catégorie créée avec succès'
        })
    except Exception as e:
        return JsonResponse({'error': f'Erreur lors de la création: {str(e)}'}, status=500)

@login_required
def dashboard(request):
    """Tableau de bord avec données filtrées selon le rôle"""
    profil = getattr(request, 'profil_utilisateur', None)
    
    # Super Admin: voir tous les données
    if profil and profil.role == 'SUPER_ADMIN':
        total_materiel = Materiel.objects.count()
        materiel_disponible = Materiel.objects.filter(statut_disponibilite='DISPONIBLE').count()
        materiel_attribue = Materiel.objects.filter(statut_disponibilite='ATTRIBUE').count()
        materiel_defectueux = Materiel.objects.filter(etat_technique='DEFECTUEUX').count()
        materiel_recent = Materiel.objects.select_related('categorie', 'departement')\
                            .order_by('-date_creation')[:3]
        departements_list = Departement.objects.all()
    else:
        # Utilisateur du département: voir seulement son département
        departement = getattr(request, 'departement', None)
        if not departement:
            departement, _ = Departement.objects.get_or_create(
                code='DEF',
                defaults={'nom': 'Département par défaut'}
            )
        
        total_materiel = Materiel.objects.filter(departement=departement).count()
        materiel_disponible = Materiel.objects.filter(departement=departement, statut_disponibilite='DISPONIBLE').count()
        materiel_attribue = Materiel.objects.filter(departement=departement, statut_disponibilite='ATTRIBUE').count()
        materiel_defectueux = Materiel.objects.filter(departement=departement, etat_technique='DEFECTUEUX').count()
        materiel_recent = Materiel.objects.filter(departement=departement)\
                            .select_related('categorie', 'departement')\
                            .order_by('-date_creation')[:3]
        departements_list = [departement]

    # Statistiques par département
    departements = []
    for dept in departements_list:
        total = Materiel.objects.filter(departement=dept).count()
        disponible = Materiel.objects.filter(departement=dept, statut_disponibilite='DISPONIBLE').count()
        attribue = Materiel.objects.filter(departement=dept, statut_disponibilite='ATTRIBUE').count()
        departements.append({
            'nom': dept.nom,
            'total': total,
            'disponible': disponible,
            'attribue': attribue,
        })
    
    # Récupérer les alertes non réglées (limité à 3 pour le dashboard)
    departement = getattr(request, 'departement', None)
    alertes_recentes = AlerteService.get_alertes_non_reglementees(departement)[:3]
    nombre_alertes_critiques = AlerteService.get_nombre_alertes_critiques(departement)

    context = {
        'total_materiel': total_materiel,
        'materiel_disponible': materiel_disponible,
        'materiel_attribue': materiel_attribue,
        'materiel_defectueux': materiel_defectueux,
        'materiel_recent': materiel_recent,
        'departements': departements,
        'alertes_recentes': alertes_recentes,
        'nombre_alertes_critiques': nombre_alertes_critiques,
    }
    return render(request, 'assets/dashboard.html', context)

@login_required
def materiel_list(request):
    """Liste tous les matériels groupés par nom d'équipement avec quantités."""
    departement = getattr(request, 'departement', None)
    if not departement:
        departement, _ = Departement.objects.get_or_create(
            code='DEF',
            defaults={'nom': 'Département par défaut'}
        )
    
    query = request.GET.get('q', '')
    categorie_filter = request.GET.get('categorie', '')
    
    # Base QuerySet filtré par département
    materiels_base = Materiel.objects.filter(departement=departement).select_related('categorie', 'departement')
    
    # Filtres de recherche
    if query:
        materiels_base = materiels_base.filter(
            Q(nom__icontains=query) |
            Q(numero_inventaire__icontains=query) |
            Q(numero_serie__icontains=query) |
            Q(modele__icontains=query) |
            Q(marque__icontains=query) |
            Q(asset_id__icontains=query)
        )
    
    if categorie_filter:
        materiels_base = materiels_base.filter(categorie_id=categorie_filter)
    
    # Grouper par nom d'équipement
    groupes_materiels = materiels_base.values('nom', 'categorie').annotate(
        quantite=Count('id'),
        date_modification_max=Max('date_modification')
    ).order_by('nom')
    
    # Enrichir avec les informations de catégorie
    groupes_enrichis = []
    for groupe in groupes_materiels:
        nom = groupe['nom']
        categorie_id = groupe.get('categorie')
        
        # Récupérer un exemple de matériel pour obtenir la catégorie
        materiel_exemple = materiels_base.filter(nom=nom).first()
        
        # Compter les statuts
        total = materiels_base.filter(nom=nom).count()
        disponible = materiels_base.filter(nom=nom, statut_disponibilite='DISPONIBLE', etat_technique='FONCTIONNEL').count()
        attribue = materiels_base.filter(nom=nom, statut_disponibilite='ATTRIBUE').count()
        maintenance = materiels_base.filter(nom=nom, statut_disponibilite='MAINTENANCE').count()
        
        groupes_enrichis.append({
            'nom': nom,
            'categorie': materiel_exemple.categorie if materiel_exemple else None,
            'quantite': total,
            'disponible': disponible,
            'attribue': attribue,
            'maintenance': maintenance,
            'date_modification': groupe['date_modification_max'],
        })
    
    # Statistiques pour les filtres
    total_materiels = Materiel.objects.filter(departement=departement).count()
    stats = {
        'total': total_materiels,
        'disponible': Materiel.objects.filter(departement=departement, statut_disponibilite='DISPONIBLE').count(),
        'attribue': Materiel.objects.filter(departement=departement, statut_disponibilite='ATTRIBUE').count(),
        'maintenance': Materiel.objects.filter(departement=departement, statut_disponibilite='MAINTENANCE').count(),
        'hors_service': Materiel.objects.filter(departement=departement, statut_disponibilite='HORS_SERVICE').count(),
    }
    
    # Catégories disponibles pour les filtres
    categories = Categorie.objects.filter(departement=departement)
    
    context = {
        'groupes_materiels': groupes_enrichis,
        'query': query,
        'categorie_filter': categorie_filter,
        'stats': stats,
        'categories': categories,
    }
    
    return render(request, 'assets/materiel_list.html', context)

@login_required
def materiel_group_detail(request, nom):
    """Affiche tous les matériels d'un groupe (même nom d'équipement)"""
    departement = getattr(request, 'departement', None)
    if not departement:
        departement, _ = Departement.objects.get_or_create(
            code='DEF',
            defaults={'nom': 'Département par défaut'}
        )
    
    # Récupérer tous les matériels avec ce nom
    materiels = Materiel.objects.filter(
        nom=nom,
        departement=departement
    ).select_related('categorie', 'departement').order_by('asset_id')
    
    if not materiels.exists():
        messages.error(request, f'Aucun matériel trouvé avec le nom "{nom}".')
        return redirect('assets:materiel_list')
    
    # Statistiques du groupe
    stats_groupe = {
        'total': materiels.count(),
        'disponible': materiels.filter(statut_disponibilite='DISPONIBLE', etat_technique='FONCTIONNEL').count(),
        'attribue': materiels.filter(statut_disponibilite='ATTRIBUE').count(),
        'maintenance': materiels.filter(statut_disponibilite='MAINTENANCE').count(),
        'defectueux': materiels.filter(etat_technique='DEFECTUEUX').count(),
    }
    
    # Catégorie (tous les matériels du groupe ont la même catégorie normalement)
    categorie = materiels.first().categorie if materiels.exists() else None
    
    context = {
        'nom_equipement': nom,
        'materiels': materiels,
        'stats_groupe': stats_groupe,
        'categorie': categorie,
    }
    
    return render(request, 'assets/materiel_group_detail.html', context)

@login_required
def materiel_detail(request, pk):
    """Affiche les détails d'un matériel."""
    # Permettre l'accès à tous les matériels (Phase 1 MVP)
    # Phase 2: implémenter les permissions par département
    materiel = get_object_or_404(Materiel, pk=pk)
    
    # Attribution active
    attribution_active = Attribution.objects.filter(
        materiel=materiel, 
        date_retour_effective__isnull=True
    ).select_related('client', 'employe_responsable').first()
    
    # Historique des attributions
    historique = Attribution.objects.filter(
        materiel=materiel
    ).select_related('client', 'employe_responsable').order_by('-date_attribution')[:10]
    
    # Alertes liées à ce matériel
    alertes = Alerte.objects.filter(
        materiel=materiel,
        reglementee=False
    ).order_by('-date_creation')[:5]
    
    context = {
        'materiel': materiel,
        'attribution_active': attribution_active,
        'historique': historique,
        'alertes': alertes,
    }
    
    return render(request, 'assets/materiel_detail.html', context)


@login_required
def materiel_update(request, pk):
    """Met à jour un matériel existant."""
    materiel = get_object_or_404(Materiel, pk=pk)
    departement = materiel.departement
    
    if request.method == 'POST':
        form = MaterielForm(request.POST, request.FILES, instance=materiel, departement=departement)
        if form.is_valid():
            form.save()
            return redirect('assets:materiel_detail', pk=materiel.pk)
    else:
        form = MaterielForm(instance=materiel, departement=departement)
    
    # Récupérer les noms de matériels existants pour le département
    noms_existants = Materiel.objects.filter(departement=departement).values_list('nom', flat=True).distinct().order_by('nom')
    categories = Categorie.objects.filter(departement=departement).order_by('nom')
    
    return render(request, 'assets/materiel_form.html', {
        'form': form, 
        'materiel': materiel,
        'title': 'Modifier le matériel',
        'noms_existants': noms_existants,
        'categories': categories,
        'asset_id_default': None,
        'numero_inv_default': None,
    })


@login_required
def materiel_delete(request, pk):
    """Supprime un matériel."""
    materiel = get_object_or_404(Materiel, pk=pk)
    # Vérifier les permissions: seul le SUPER_ADMIN ou le manager du département peut supprimer
    profil = getattr(request, 'profil_utilisateur', None)
    # Autoriser les superusers Django également
    if not (request.user.is_superuser or (profil and (
            profil.role == 'SUPER_ADMIN' or (
                profil.role == 'DEPT_MANAGER' and profil.departement_id == materiel.departement_id
            )
        ))):
        raise PermissionDenied("Vous n'avez pas la permission de supprimer ce matériel.")

    if request.method == 'POST':
        materiel.delete()
        return redirect('assets:materiel_list')

    return render(request, 'assets/materiel_confirm_delete.html', {'materiel': materiel})

# Vues temporaires pour les autres fonctionnalités
@login_required
def scan_qr(request):
    """Affiche la page de scan de code QR."""
    return render(request, 'assets/scan_qr.html')


@login_required
def scan_result(request, asset_id):
    """Affiche le résultat du scan QR."""
    try:
        materiel = Materiel.objects.get(asset_id=asset_id)
        return render(request, 'assets/scan_result.html', {'materiel': materiel})
    except Materiel.DoesNotExist:
        messages.error(request, 'Matériel non trouvé.')
        return redirect('assets:scan_qr')


@login_required
def checkout(request, asset_id):
    """Check-out (attribution) pour le matériel identifié par `asset_id`."""
    from .forms import QuickClientForm
    
    materiel = get_object_or_404(Materiel, asset_id=asset_id)
    profil = getattr(request, 'profil_utilisateur', None)
    
    # Vérifier les permissions: l'utilisateur doit avoir accès au département
    if profil and profil.role not in ['SUPER_ADMIN', 'DEPT_MANAGER', 'DEPT_USER']:
        raise PermissionDenied("Vous n'avez pas les permissions pour effectuer un check-out.")
    
    if profil and profil.role != 'SUPER_ADMIN' and profil.departement_id != materiel.departement_id:
        raise PermissionDenied("Vous n'avez accès qu'à votre département.")

    if materiel.statut_disponibilite != Materiel.STATUT_DISPONIBLE:
        messages.error(request, 'Ce matériel n\'est pas disponible pour attribution.')
        return redirect('assets:materiel_detail', pk=materiel.pk)

    # Initialiser les formulaires
    form = None
    quick_form = QuickClientForm()

    # Gérer la création rapide d'un client (AJAX ou POST)
    if request.method == 'POST' and request.POST.get('action') == 'create_client':
        quick_form = QuickClientForm(request.POST)
        if quick_form.is_valid():
            client = quick_form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Réponse AJAX
                return JsonResponse({'success': True, 'client_id': client.id, 'client_name': client.nom})
            else:
                # Redirection standard
                messages.success(request, f'Client "{client.nom}" créé avec succès.')
                return redirect('assets:materiel_checkout', asset_id=asset_id)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': quick_form.errors}, status=400)
            form = AttributionForm(initial={'materiel': materiel.pk})
    # Traiter le formulaire d'attribution
    elif request.method == 'POST':
        form = AttributionForm(request.POST)
        if form.is_valid():
            attribution = form.save(commit=False)
            # Destination handling: client or salle
            dest = form.cleaned_data.get('destination_type', 'client')
            if dest == 'client':
                attribution.client = form.cleaned_data.get('client')
                attribution.salle = None
            else:
                attribution.salle = form.cleaned_data.get('salle')
                attribution.client = None

            attribution.employe_responsable = request.user
            attribution.departement = materiel.departement
            attribution.materiel = materiel

            # If assigned to a salle, also mark the materiel's salle (optional behaviour)
            if attribution.salle:
                try:
                    materiel.salle = attribution.salle
                except Exception:
                    pass

            attribution.save()

            # Historique
            HistoriqueAttribution.objects.create(
                attribution=attribution,
                action=HistoriqueAttribution.ACTION_CHECK_OUT,
                utilisateur=request.user,
                etat_avant=Materiel.STATUT_DISPONIBLE,
                etat_apres=Materiel.STATUT_ATTRIBUE,
                notes=attribution.notes
            )

            # Créer une alerte d'information pour le mouvement (matériel attribué)
            try:
                dest_label = ''
                if attribution.client:
                    dest_label = str(attribution.client)
                elif attribution.salle:
                    dest_label = f"Salle: {attribution.salle}"
                else:
                    dest_label = 'Destination inconnue'

                Alerte.objects.create(
                    type_alerte=Alerte.TYPE_RETARD,
                    severite=Alerte.SEVERITE_INFO,
                    materiel=materiel,
                    attribution=attribution,
                    departement=materiel.departement,
                    description=f"Matériel attribué à {dest_label} (Date: {attribution.date_attribution.date()})"
                )
            except Exception:
                # Ne pas bloquer le flux en cas d'erreur d'alerte
                pass

            messages.success(request, 'Attribution enregistrée.')
            return redirect('assets:materiel_detail', pk=materiel.pk)
    else:
        # Préremplir le formulaire pour ce matériel (GET)
        form = AttributionForm(initial={'materiel': materiel.pk})

    return render(request, 'assets/check_out.html', {
        'form': form, 
        'quick_form': quick_form,
        'materiel': materiel
    })


@login_required
def checkin(request, asset_id):
    """Check-in (retour) pour le matériel identifié par `asset_id`."""
    materiel = get_object_or_404(Materiel, asset_id=asset_id)
    attribution = Attribution.objects.filter(materiel=materiel, date_retour_effective__isnull=True).select_related('client', 'salle').first()

    if not attribution:
        messages.error(request, 'Aucune attribution active trouvée pour ce matériel.')
        return redirect('assets:materiel_detail', pk=materiel.pk)

    if request.method == 'POST':
        form = CheckInForm(request.POST, attribution=attribution)
        if form.is_valid():
            date_retour = form.cleaned_data.get('date_retour_effective') or timezone.now().date()
            raison_non_retour = form.cleaned_data.get('raison_non_retour')
            description_damage = form.cleaned_data.get('description_damage')
            notes = form.cleaned_data.get('notes')
            maintenance = form.cleaned_data.get('mettre_en_maintenance')

            attribution.date_retour_effective = date_retour
            if notes:
                attribution.notes = (attribution.notes or '') + '\n' + notes
            attribution.save()

            # Mettre à jour le matériel
            etat_avant = materiel.statut_disponibilite
            if maintenance or raison_non_retour in ['DAMAGE', 'OTHER']:
                materiel.statut_disponibilite = Materiel.STATUT_MAINTENANCE
                materiel.etat_technique = Materiel.ETAT_EN_MAINTENANCE
            else:
                materiel.statut_disponibilite = Materiel.STATUT_DISPONIBLE
            materiel.save()

            # Historique
            historique_notes = notes or ''
            if raison_non_retour != 'NORMAL':
                historique_notes += f'\n[Raison: {dict(CheckInForm.RAISON_CHOICES).get(raison_non_retour)}]'
                if description_damage:
                    historique_notes += f'\n[Détails: {description_damage}]'
            
            HistoriqueAttribution.objects.create(
                attribution=attribution,
                action=HistoriqueAttribution.ACTION_CHECK_IN,
                utilisateur=request.user,
                etat_avant=etat_avant,
                etat_apres=materiel.statut_disponibilite,
                notes=historique_notes
            )

            # Créer une alerte d'information pour le mouvement (matériel retourné normalement)
            try:
                if raison_non_retour == 'NORMAL':
                    Alerte.objects.create(
                        type_alerte=Alerte.TYPE_RETARD,
                        severite=Alerte.SEVERITE_INFO,
                        materiel=materiel,
                        attribution=attribution,
                        departement=materiel.departement,
                        description=f"Matériel retourné par {attribution.client.nom} le {date_retour}."
                    )
            except Exception:
                # Ne pas bloquer le flux en cas d'erreur d'alerte
                pass

            # Auto-créer une Alerte si matériel perdu ou endommagé
            alerte_created = None
            if raison_non_retour == 'LOST':
                dest_label = attribution.client.nom if attribution.client else (f"Salle: {attribution.salle}" if attribution.salle else 'Inconnu')
                alerte_created = Alerte.objects.create(
                    type_alerte=Alerte.TYPE_PERDU,
                    severite=Alerte.SEVERITE_CRITICAL,
                    materiel=materiel,
                    attribution=attribution,
                    departement=materiel.departement,
                    description=f"Matériel perdu lors de l'attribution à {dest_label}\n{description_damage or ''}"
                )
            elif raison_non_retour == 'DAMAGE':
                dest_label = attribution.client.nom if attribution.client else (f"Salle: {attribution.salle}" if attribution.salle else 'Inconnu')
                alerte_created = Alerte.objects.create(
                    type_alerte=Alerte.TYPE_DEFECTUEUX,
                    severite=Alerte.SEVERITE_CRITICAL,
                    materiel=materiel,
                    attribution=attribution,
                    departement=materiel.departement,
                    description=f"Matériel endommagé lors de l'attribution à {dest_label}\nDégâts: {description_damage or 'Non spécifiés'}"
                )

            # Stocker les données dans la session pour la page de confirmation
            request.session['checkin_data'] = {
                'materiel_asset_id': materiel.asset_id,
                'materiel_nom': materiel.nom,
                'materiel_pk': materiel.pk,
                'materiel_statut': materiel.get_statut_disponibilite_display(),
                'client_nom': (attribution.client.nom if attribution.client else (str(attribution.salle) if attribution.salle else '')),
                'date_attribution': attribution.date_attribution.isoformat(),
                'date_retour': date_retour.isoformat(),
                'raison': raison_non_retour,
                'description_damage': description_damage,
                'notes': notes,
                'maintenance': maintenance,
                'alerte_id': alerte_created.id if alerte_created else None,
                'statut_color': 'warning' if maintenance else 'success',
            }

            return redirect('assets:checkin_success')
    else:
        form = CheckInForm(initial={'date_retour_effective': timezone.now().date()}, attribution=attribution)

    return render(request, 'assets/check_in.html', {'form': form, 'materiel': materiel, 'attribution': attribution})

@login_required
def checkin_success(request):
    """Page de confirmation du check-in avec détails."""
    # Récupérer les données de la session
    checkin_data = request.session.pop('checkin_data', None)
    
    if not checkin_data:
        return redirect('assets:materiel_list')
    
    # Récupérer l'alerte si créée
    alerte = None
    if checkin_data.get('alerte_id'):
        alerte = Alerte.objects.filter(id=checkin_data['alerte_id']).first()
    
    context = {
        **checkin_data,
        'alerte': alerte,
    }
    
    return render(request, 'assets/check_in_success.html', context)

# ========== CLIENT VIEWS ===========
@login_required
def client_list(request):
    clients = Client.objects.all()
    search = request.GET.get('search', '')
    # accept either 'type' (legacy) or 'type_client' from the querystring
    type_filter = request.GET.get('type', '') or request.GET.get('type_client', '')
    
    if search:
        clients = clients.filter(nom__icontains=search)
    if type_filter:
        # The model field is `type_client`
        clients = clients.filter(type_client=type_filter)
    
    return render(request, 'assets/client_list.html', {'clients': clients})


@login_required
def report_list(request):
    """Liste des rapports d'audit (read-only for non-admins)."""
    qs = AuditLog.objects.select_related('user', 'content_type').all()
    action = request.GET.get('action')
    ct = request.GET.get('content_type')
    user = request.GET.get('user')

    if action:
        qs = qs.filter(action=action)
    if ct:
        qs = qs.filter(content_type__model=ct)
    if user:
        qs = qs.filter(user__username__icontains=user)

    qs = qs.order_by('-timestamp')[:200]
    return render(request, 'assets/report_list.html', {'reports': qs})


@login_required
def report_detail(request, pk):
    report = get_object_or_404(AuditLog, pk=pk)
    # Prepare formatted changes and a short human summary for the UI
    formatted_changes = _format_changes_for_display(report)

    # If this is an Attribution event, prefer showing key fields first for clarity
    try:
        ct_model = report.content_type.model_class()
    except Exception:
        ct_model = None
    if ct_model and ct_model.__name__ == 'Attribution' and formatted_changes:
        priority = ['id', 'materiel', 'client', 'employe_responsable', 'departement', 'date_retour_prevue', 'notes']
        ordered = []
        rest = []
        for p in priority:
            for c in formatted_changes:
                if c.get('field_name') == p:
                    ordered.append(c)
        for c in formatted_changes:
            if c.get('field_name') not in priority:
                rest.append(c)
        formatted_changes = ordered + rest

    # Build a short summary sentence
    user_label = report.user.username if report.user else 'System'
    action = report.get_action_display()
    obj_label = report.object_repr or ''

    if report.action == AuditLog.ACTION_CREATE:
        summary = f"{user_label} a créé {report.content_type.model.capitalize()} — {obj_label}"
    elif report.action == AuditLog.ACTION_UPDATE:
        # Build short list of changed fields
        changed_fields = ', '.join([c['field'] for c in formatted_changes]) if formatted_changes else ''
        summary = f"{user_label} a modifié {report.content_type.model.capitalize()} — {obj_label}. Champs modifiés: {changed_fields}"
    elif report.action == AuditLog.ACTION_DELETE:
        summary = f"{user_label} a supprimé {report.content_type.model.capitalize()} — {obj_label}"
    else:
        summary = f"{user_label} — {action} — {obj_label}"

    # Try to build a more detailed human-readable sentence for Attribution
    human_sentence = _build_human_readable_sentence(report, formatted_changes)

    # Build a creative context sentence for display
    context_sentence = _build_context_sentence(report)

    # Build a creative summary sentence for the 'Résumé' field
    creative_summary = _build_creative_summary(report)

    # Only admins can modify/delete via admin; in UI everyone can view
    return render(request, 'assets/report_detail.html', {
        'report': report,
        'formatted_changes': formatted_changes,
        'summary': creative_summary or summary,
        'human_sentence': human_sentence,
        'context_sentence': context_sentence,
        'sanitized_metadata': _sanitize_metadata(getattr(report, 'metadata', None)),
    })


@login_required
def report_pdf(request, pk):
    """Return a PDF version of the report detail. Uses WeasyPrint if available.

    Falls back to returning the HTML view with a warning if PDF library isn't present.
    """
    report = get_object_or_404(AuditLog, pk=pk)
    formatted_changes = _format_changes_for_display(report)
    human_sentence = _build_human_readable_sentence(report, formatted_changes)
    summary = None
    # reuse summary logic from report_detail
    user_label = report.user.username if report.user else 'System'
    action = report.get_action_display()
    obj_label = report.object_repr or ''
    if report.action == AuditLog.ACTION_CREATE:
        summary = f"{user_label} a créé {report.content_type.model.capitalize()} — {obj_label}"
    elif report.action == AuditLog.ACTION_UPDATE:
        changed_fields = ', '.join([c['field'] for c in formatted_changes]) if formatted_changes else ''
        summary = f"{user_label} a modifié {report.content_type.model.capitalize()} — {obj_label}. Champs modifiés: {changed_fields}"
    elif report.action == AuditLog.ACTION_DELETE:
        summary = f"{user_label} a supprimé {report.content_type.model.capitalize()} — {obj_label}"
    else:
        summary = f"{user_label} — {action} — {obj_label}"

    context = {
        'report': report,
        'formatted_changes': formatted_changes,
        'summary': _build_creative_summary(report) or summary,
        'human_sentence': human_sentence,
        'context_sentence': _build_context_sentence(report),
        'sanitized_metadata': _sanitize_metadata(getattr(report, 'metadata', None)),
    }

    # Render the HTML for the PDF (include `request` so context processors run)
    from django.template.loader import render_to_string
    html = render_to_string('assets/report_pdf.html', context, request=request)

    # Try to generate PDF using WeasyPrint if available. If it fails (native libs missing),
    # fall back to wkhtmltopdf via `pdfkit` if available. If both fail, return HTML fallback.
    try:
        from weasyprint import HTML
        try:
            pdf = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = f"rapport_{report.pk}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception:
            # WeasyPrint present but failed to render (likely missing native libs)
            pass
    except Exception:
        # WeasyPrint not installed -- continue to next backend
        pass

    # Try wkhtmltopdf via pdfkit (requires wkhtmltopdf binary on PATH or WKHTMLTOPDF_CMD env var)
    try:
        import pdfkit
        import shutil, os
        from django.conf import settings

        # Prefer explicit env var, then PATH, then a bundled copy under <project>/bin/
        wkhtml_cmd = os.environ.get('WKHTMLTOPDF_CMD') or shutil.which('wkhtmltopdf')

        # Look for a local copy under the repository `bin/` directory (common for portable zip)
        if not wkhtml_cmd:
            try:
                base = getattr(settings, 'BASE_DIR', os.getcwd())
            except Exception:
                base = os.getcwd()

            bin_dir = os.path.join(base, 'bin')
            candidate = None
            if os.path.isdir(bin_dir):
                # search for an executable named wkhtmltopdf(.exe)
                for root, dirs, files in os.walk(bin_dir):
                    for f in files:
                        if f.lower().startswith('wkhtmltopdf'):
                            candidate = os.path.join(root, f)
                            break
                    if candidate:
                        break
            if candidate and os.path.exists(candidate):
                wkhtml_cmd = candidate

        if wkhtml_cmd:
            try:
                config = pdfkit.configuration(wkhtmltopdf=wkhtml_cmd)
                # Allow local file access and ignore minor load errors so wkhtmltopdf
                # can render templates referencing /static/... files when no HTTP server
                # is available during headless requests.
                options = {
                    'enable-local-file-access': '',
                    'load-error-handling': 'ignore',
                    'encoding': 'UTF-8',
                }
                pdf = pdfkit.from_string(html, False, options=options, configuration=config)
                response = HttpResponse(pdf, content_type='application/pdf')
                filename = f"rapport_{report.pk}.pdf"
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
            except Exception as e:
                # pdfkit/wkhtmltopdf invocation failed — capture the error for debugging.
                try:
                    base = getattr(settings, 'BASE_DIR', os.getcwd())
                    tmpdir = os.path.join(base, 'tmp')
                    os.makedirs(tmpdir, exist_ok=True)
                    errfile = os.path.join(tmpdir, f'report_{report.pk}_pdf_error.txt')
                    with open(errfile, 'w', encoding='utf-8') as ef:
                        ef.write(str(e))
                except Exception:
                    # ignore file-writing errors
                    pass
                # fall through to HTML fallback
                pass
    except Exception:
        # pdfkit not installed
        pass

    # Nothing worked: show the HTML fallback with a helpful message
    return render(request, 'assets/report_detail.html', dict(context, pdf_unavailable=True))

@login_required
def client_create(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('assets:client_list')
    else:
        form = ClientForm()
    return render(request, 'assets/client_form.html', {'form': form})

@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    # Utiliser une requête explicite au lieu de l'attribut related_name
    # (utile si le FK dans Attribution n'a pas related_name='attribution_set')
    attributions = Attribution.objects.filter(client=client).order_by('-date_attribution')
    return render(request, 'assets/client_detail.html', {
        'client': client,
        'attributions': attributions
    })

@login_required
def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect('assets:client_detail', pk=client.pk)
    else:
        form = ClientForm(instance=client)
    return render(request, 'assets/client_form.html', {'form': form, 'client': client})

@login_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        client.delete()
        return redirect('assets:client_list')
    return render(request, 'assets/client_confirm_delete.html', {'client': client})

# ========== ATTRIBUTION VIEWS ==========
@login_required
def attribution_list(request):
    attributions = Attribution.objects.all().order_by('-date_attribution')
    status = request.GET.get('status', 'ACTIF')
    
    # Filtrer par statut (actif = date_retour_effective null)
    if status == 'ACTIF':
        attributions = attributions.filter(date_retour_effective__isnull=True)
    elif status == 'COMPLETED':
        attributions = attributions.filter(date_retour_effective__isnull=False)
    
    return render(request, 'assets/attribution_list.html', {
        'attributions': attributions,
        'status': status
    })

@login_required
def attribution_update(request, pk):
    attribution = get_object_or_404(Attribution, pk=pk)
    if request.method == 'POST':
        form = AttributionForm(request.POST, instance=attribution)
        if form.is_valid():
            form.save()
            return redirect('assets:attribution_list')
    else:
        form = AttributionForm(instance=attribution)
    return render(request, 'assets/attribution_form.html', {
        'form': form,
        'attribution': attribution
    })

# ========== ALERTES VIEWS ==========
@login_required
def alerte_list(request):
    """Liste toutes les alertes non réglées"""
    departement = getattr(request, 'departement', None)
    profil = getattr(request, 'profil_utilisateur', None)
    
    # Super Admin peut voir toutes les alertes
    if profil and profil.role == 'SUPER_ADMIN':
        alertes = AlerteService.get_alertes_non_reglementees()
    else:
        alertes = AlerteService.get_alertes_non_reglementees(departement)
    
    # Filtres
    type_filter = request.GET.get('type', '')
    severite_filter = request.GET.get('severite', '')
    
    if type_filter:
        alertes = alertes.filter(type_alerte=type_filter)
    
    if severite_filter:
        alertes = alertes.filter(severite=severite_filter)
    
    # Statistiques
    stats = {
        'total': alertes.count(),
        'critique': alertes.filter(severite=Alerte.SEVERITE_CRITICAL).count(),
        'warning': alertes.filter(severite=Alerte.SEVERITE_WARNING).count(),
        'info': alertes.filter(severite=Alerte.SEVERITE_INFO).count(),
        'retard': alertes.filter(type_alerte=Alerte.TYPE_RETARD).count(),
        'defectueux': alertes.filter(type_alerte=Alerte.TYPE_DEFECTUEUX).count(),
        'stock_critique': alertes.filter(type_alerte=Alerte.TYPE_STOCK_CRITIQUE).count(),
        'perdu': alertes.filter(type_alerte=Alerte.TYPE_PERDU).count(),
    }
    
    context = {
        'alertes': alertes,
        'stats': stats,
        'type_filter': type_filter,
        'severite_filter': severite_filter,
        'type_choices': Alerte.TYPE_CHOICES,
        'severite_choices': Alerte.SEVERITE_CHOICES,
    }
    
    return render(request, 'assets/alerte_list.html', context)


@login_required
def alerte_detail(request, pk):
    """Affiche les détails d'une alerte"""
    alerte = get_object_or_404(Alerte, pk=pk)
    
    # Vérifier les permissions
    departement = getattr(request, 'departement', None)
    profil = getattr(request, 'profil_utilisateur', None)
    
    if profil and profil.role != 'SUPER_ADMIN' and departement and alerte.departement != departement:
        raise PermissionDenied("Vous n'avez pas accès à cette alerte.")
    
    context = {
        'alerte': alerte,
    }
    
    return render(request, 'assets/alerte_detail.html', context)


@login_required
def alerte_marquer_reglementee(request, pk):
    """Marque une alerte comme réglée"""
    alerte = get_object_or_404(Alerte, pk=pk)
    
    # Vérifier les permissions
    departement = getattr(request, 'departement', None)
    profil = getattr(request, 'profil_utilisateur', None)
    
    if profil and profil.role != 'SUPER_ADMIN' and departement and alerte.departement != departement:
        raise PermissionDenied("Vous n'avez pas accès à cette alerte.")
    
    if request.method == 'POST':
        alerte.reglementee = True
        alerte.save()
        messages.success(request, 'Alerte marquée comme réglée.')
        return redirect('assets:alerte_list')
    
    return render(request, 'assets/alerte_confirm_reglementee.html', {'alerte': alerte})


@login_required
def alerte_detecter(request):
    """Déclenche manuellement la détection de toutes les alertes"""
    profil = getattr(request, 'profil_utilisateur', None)
    
    # Seuls les managers et super admins peuvent déclencher la détection
    if not profil or profil.role not in ['SUPER_ADMIN', 'DEPT_MANAGER']:
        raise PermissionDenied("Vous n'avez pas les permissions pour cette action.")
    
    resultats = AlerteService.detecter_toutes_alertes()
    
    messages.success(
        request,
        f"Détection terminée: {resultats['total']} nouvelle(s) alerte(s) créée(s) "
        f"(Retards: {len(resultats['retards'])}, "
        f"Défectueux: {len(resultats['defectueux'])}, "
        f"Stock critique: {len(resultats['stock_critique'])}, "
        f"Perdus: {len(resultats['perdus'])})"
    )
    
    return redirect('assets:alerte_list')


# ============================================================================
# VUES POUR LE DASHBOARD DE NOTIFICATIONS (PHASE 6)
# ============================================================================

@login_required
def notifications_dashboard(request):
    """
    Dashboard de suivi des notifications envoyées
    Affiche les statistiques et l'historique
    """
    from .models import NotificationLog
    from django.db.models import Count, Q
    
    # Vérifier les permissions
    profil = getattr(request, 'profil_utilisateur', None)
    if not profil or profil.role not in ['SUPER_ADMIN', 'DEPT_MANAGER']:
        raise PermissionDenied("Accès réservé aux managers et super admins.")
    
    # Récupérer toutes les notifications
    all_notifications = NotificationLog.objects.select_related(
        'attribution__materiel', 'attribution__client'
    ).order_by('-date_envoi')
    
    # Statistiques globales
    stats = {
        'total_envoyees': all_notifications.count(),
        'emails_envoyes': all_notifications.filter(canal='EMAIL').count(),
        'whatsapp_envoyes': all_notifications.filter(canal='WHATSAPP').count(),
        'taux_succes': 0,
        'par_type': {}
    }
    
    # Calculer le taux de succès
    if stats['total_envoyees'] > 0:
        succes = all_notifications.filter(statut='ENVOYEE').count()
        stats['taux_succes'] = round((succes / stats['total_envoyees']) * 100, 1)
    
    # Statistiques par type
    type_counts = all_notifications.values('type_notification').annotate(
        count=Count('id')
    ).order_by('-count')
    
    for item in type_counts:
        type_name = dict(NotificationLog.TYPE_CHOICES).get(item['type_notification'], item['type_notification'])
        stats['par_type'][type_name] = item['count']
    
    # Dernières notifications (limité à 50)
    notifications = all_notifications[:50]
    has_pagination = all_notifications.count() > 50
    
    context = {
        'stats': stats,
        'notifications': notifications,
        'has_pagination': has_pagination,
    }
    
    return render(request, 'assets/notifications_dashboard.html', context)


@login_required
def notification_preferences(request):
    """
    Permet à un utilisateur de gérer ses préférences de notification
    """
    from .models import NotificationPreferences
    from django import forms
    
    # Créer ou récupérer les préférences
    preferences, created = NotificationPreferences.objects.get_or_create(
        user=request.user
    )
    
    # Formulaire de préférences
    class NotificationPreferencesForm(forms.ModelForm):
        class Meta:
            model = NotificationPreferences
            fields = [
                'notifications_email', 'notifications_whatsapp', 'phone_number',
                'rappel_j_moins_2', 'rappel_j_moins_1', 'rappel_final', 'rappel_2h_avant'
            ]
            widgets = {
                'notifications_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
                'notifications_whatsapp': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
                'rappel_j_moins_2': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
                'rappel_j_moins_1': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
                'rappel_final': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
                'rappel_2h_avant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
                'phone_number': forms.TextInput(attrs={
                    'class': 'form-control',
                    'placeholder': '+24105339274'
                }),
            }
    
    if request.method == 'POST':
        form = NotificationPreferencesForm(request.POST, instance=preferences)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Vos préférences ont été enregistrées avec succès!')
            return redirect('assets:notification_preferences')
    else:
        form = NotificationPreferencesForm(instance=preferences)
    
    context = {
        'form': form,
        'preferences': preferences,
    }
    
    return render(request, 'assets/notification_preferences.html', context)

