# assets/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Max
from django.db.models.functions import TruncDate
from django.db import models
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from .forms import MaterielForm, ClientForm, AttributionForm, CategorieForm
from .models import Materiel, Departement, Categorie, Attribution, Client, Alerte, Salle
from .models import AuditLog
from .forms import CheckInForm
from django.utils import timezone
from django.contrib import messages
from .models import HistoriqueAttribution
from users.permissions import role_required, can_view_department, can_manage_department, can_perform_checkout
from .services import AlerteService
from types import SimpleNamespace
import re

from django.utils.text import capfirst
from django.utils.formats import date_format


@require_http_methods(["GET"])
def health_check(request):
    """
    Health check endpoint pour Docker et monitoring.
    Retourne JSON avec le statut de l'application.
    """
    try:
        # Vérifier la connexion BD
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Vérifier Redis si disponible
        try:
            from django.core.cache import cache
            cache.set('health_check', 'ok', 10)
            redis_status = 'ok'
        except Exception:
            redis_status = 'unavailable'
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'ok',
            'cache': redis_status,
            'timestamp': timezone.now().isoformat(),
        }, status=200)
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat(),
        }, status=503)


def _split_search_terms(raw_query):
    if not raw_query:
        return []
    return [term for term in re.split(r'\s+', raw_query.strip()) if term]


def _apply_multi_term_search(queryset, terms, fields):
    if not terms or not fields:
        return queryset
    for term in terms:
        term_q = Q()
        for field in fields:
            term_q |= Q(**{f"{field}__icontains": term})
        queryset = queryset.filter(term_q)
    return queryset


def _human_label_for_field(model_class, field_name):
    """Return a human readable label for a field name on model_class if available.
    
    Uses explicit French labels for better readability in audit reports.
    """
    if not model_class:
        return field_name.replace('_', ' ').capitalize()
    
    # Mapping explicite des champs vers des libellés français complets
    model_name = model_class.__name__ if model_class else ''
    
    # Mapping par modèle pour des libellés explicites
    field_mappings = {
        'Materiel': {
            'asset_id': 'Identifiant du matériel',
            'numero_inventaire': 'Numéro d\'inventaire',
            'nom': 'Nom du matériel',
            'description': 'Description',
            'categorie': 'Catégorie',
            'marque': 'Marque',
            'modele': 'Modèle',
            'numero_serie': 'Numéro de série',
            'etat_technique': 'État technique',
            'statut_disponibilite': 'Statut de disponibilité',
            'departement': 'Département',
            'date_achat': 'Date d\'achat',
            'prix': 'Prix',
            'qr_code': 'Code QR',
            'salle': 'Salle',
            'notes': 'Notes',
            'date_creation': 'Date de création',
            'date_modification': 'Date de modification',
        },
        'Attribution': {
            'materiel': 'Matériel',
            'client': 'Client',
            'employe_responsable': 'Employé responsable',
            'departement': 'Département',
            'date_attribution': 'Date d\'attribution',
            'date_retour_prevue': 'Date de retour prévue',
            'date_retour_effective': 'Date de retour effective',
            'motif': 'Motif',
            'notes': 'Notes',
            'salle': 'Salle',
            'duree_emprunt': 'Durée d\'emprunt',
            'heure_retour_prevue': 'Heure de retour prévue',
            'heure_retour_effective': 'Heure de retour effective',
        },
        'Alerte': {
            'type_alerte': 'Type d\'alerte',
            'severite': 'Sévérité',
            'materiel': 'Matériel concerné',
            'attribution': 'Attribution concernée',
            'departement': 'Département',
            'description': 'Description',
            'reglementee': 'Réglementée',
            'date_creation': 'Date de création',
        },
        'Client': {
            'nom': 'Nom du client',
            'type_client': 'Type de client',
            'email': 'Adresse e-mail',
            'telephone': 'Téléphone',
            'numero_chambre': 'Numéro de chambre',
            'nom_evenement': 'Nom de l\'événement',
            'date_arrivee': 'Date d\'arrivée',
            'date_depart': 'Date de départ',
            'departement': 'Département',
            'salle': 'Salle',
            'notes': 'Notes',
            'date_creation': 'Date de création',
            'date_modification': 'Date de modification',
        },
        'Categorie': {
            'nom': 'Nom de la catégorie',
            'departement': 'Département',
            'description': 'Description',
            'date_creation': 'Date de création',
        },
        'Departement': {
            'code': 'Code du département',
            'nom': 'Nom du département',
            'description': 'Description',
            'date_creation': 'Date de création',
        },
        'Salle': {
            'nom': 'Nom de la salle',
            'code': 'Code de la salle',
            'description': 'Description',
            'departement': 'Département',
            'date_creation': 'Date de création',
        },
        'HistoriqueAttribution': {
            'attribution': 'Attribution',
            'action': 'Action',
            'utilisateur': 'Utilisateur',
            'etat_avant': 'État avant',
            'etat_apres': 'État après',
            'notes': 'Notes',
            'date_action': 'Date de l\'action',
        },
        'Session': {
            'session_key': 'Clé de session',
            'session_data': 'Données de session',
            'expire_date': 'Date d\'expiration',
        },
    }
    
    # Vérifier si on a un mapping explicite pour ce modèle et ce champ
    if model_name in field_mappings and field_name in field_mappings[model_name]:
        return field_mappings[model_name][field_name]
    
    # Sinon, essayer d'utiliser le verbose_name du modèle
    try:
        field = model_class._meta.get_field(field_name)
        verbose_name = str(field.verbose_name)
        if verbose_name and verbose_name != field_name:
            return capfirst(verbose_name)
    except Exception:
        pass
    
    # Fallback: convertir le nom de champ en libellé lisible
    return field_name.replace('_', ' ').replace('id', 'ID').capitalize()


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

    # Fields that should be completely hidden (even from admins) - they're not useful
    completely_hidden = (
        'session_key', 'session_data',  # Encrypted session data - useless even for admins
        'password', 'secret', 'salt', 'token', 'hash',  # Security-sensitive fields
    )
    for b in completely_hidden:
        if fn == b or fn.endswith(b) or fn.startswith(b):
            return 'HIDE'  # Special marker to completely hide
    
    # Fields that are technical but can be shown (formatted) to admins
    technical_but_showable = (
        'meta', 'metadata', 'path', 'traceback', 'stack', 'url', 'full_path', 'request_path',
        'expire_date',  # Can be formatted as readable date
        'data', 'key',  # Can be shown if formatted
    )
    for b in technical_but_showable:
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


def _generate_materiel_qr_code(materiel):
    """Generate and attach a QR code for a materiel instance."""
    try:
        import qrcode
        from django.core.files.base import ContentFile
        import io
        import os

        domain = os.environ.get('QR_DOMAIN', 'http://localhost:8000')
        checkin_url = f"{domain}/materiel/{materiel.asset_id}/checkin/"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(checkin_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        qr_io = io.BytesIO()
        img.save(qr_io, format='PNG')
        qr_io.seek(0)
        filename = f"qr_{materiel.departement.code}_{materiel.asset_id}.png"
        materiel.qr_code.save(filename, ContentFile(qr_io.read()), save=False)
        materiel.save(update_fields=['qr_code'])
        return True, None
    except Exception as e:
        return False, str(e)


def _format_field_value(model_class, field_name, value, is_admin=False):
    """Format a field value in an explicit, human-readable way.
    
    Converts Django choices to readable labels, formats dates, booleans, etc.
    
    Args:
        model_class: Django model class
        field_name: Name of the field
        value: Value to format
        is_admin: If True, show technical data; if False, mask sensitive data
    """
    if value is None:
        return None
    
    # Always try to format dates first, even if they look like technical strings
    if isinstance(value, str):
        # Try to parse ISO date strings first (before checking if it's encrypted data)
        try:
            from django.utils.dateparse import parse_datetime, parse_date
            dt = parse_datetime(value)
            if dt:
                return date_format(dt, 'd F Y à H:i')
            d = parse_date(value)
            if d:
                return date_format(d, 'd F Y')
            # If parsing failed but it looks like an ISO date, try manual parsing
            if 'T' in value and len(value) > 10:
                try:
                    # Extract date and time from ISO: 2026-01-11T10:37:21.015163+00:00
                    parts = value.split('T')
                    if len(parts) == 2:
                        date_str = parts[0]  # 2026-01-11
                        if len(date_str) == 10 and date_str.count('-') == 2:
                            time_str = parts[1].split('.')[0].split('+')[0].split('-')[0]  # 10:37:21
                            # Parse date manually
                            year, month, day = date_str.split('-')
                            months = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 
                                     'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']
                            month_name = months[int(month) - 1]
                            if ':' in time_str:
                                hour, minute = time_str.split(':')[:2]
                                return f"{int(day)} {month_name} {year} à {hour}:{minute}"
                            else:
                                return f"{int(day)} {month_name} {year}"
                except Exception:
                    pass
        except Exception:
            pass
        
        # Handle encrypted/session data - only mask for non-admins (after date check)
        if not is_admin:
            # Session keys and encrypted data are long alphanumeric strings
            # But don't mask if it's clearly a date
            if 'T' not in value and len(value) > 30 and all(c.isalnum() or c in ':-_./' for c in value):
                # Check if it looks like encrypted session data
                if ':' in value and len(value.split(':')) >= 2:
                    return '[Données cryptées]'
                # Check if it's a long random-looking string (session key)
                if len(value) > 40:
                    return '[Clé technique]'
    
    if not model_class:
        return value
    
    try:
        field = model_class._meta.get_field(field_name)
    except Exception:
        # Even without field, value was already checked for dates above
        return value
    
    # Format boolean values
    if isinstance(field, models.BooleanField):
        if value is True:
            return 'Oui'
        elif value is False:
            return 'Non'
        return value
    
    # Format choice fields (CharField with choices)
    if hasattr(field, 'choices') and field.choices:
        # Try to find the display value - handle both string and original value types
        value_str = str(value) if value is not None else None
        for choice_value, choice_label in field.choices:
            # Compare both as strings and as original types
            if choice_value == value or str(choice_value) == value_str:
                return str(choice_label)
        # If not found, return the value as-is but try to make it readable
        if isinstance(value, str):
            # Try to convert common choice values to readable format
            readable = value.replace('_', ' ').title()
            # Handle common patterns
            if value.upper() in ['STOCK_CRITIQUE', 'RETARD', 'DEFECTUEUX', 'PERDU']:
                readable = value.replace('_', ' ').title()
            elif value.upper() in ['INFO', 'WARNING', 'CRITICAL']:
                readable = {'INFO': 'Information', 'WARNING': 'Avertissement', 'CRITICAL': 'Critique'}.get(value.upper(), readable)
            return readable
    
    # Format date fields
    if isinstance(field, (models.DateField, models.DateTimeField)):
        if value:
            try:
                # Handle both datetime objects and ISO string formats
                if isinstance(value, str):
                    from django.utils.dateparse import parse_datetime, parse_date
                    if isinstance(field, models.DateTimeField):
                        dt = parse_datetime(value)
                        if dt:
                            return date_format(dt, 'd F Y à H:i')
                        # If parse_datetime failed, try manual parsing of ISO format
                        if 'T' in value:
                            try:
                                # Extract date and time from ISO: 2026-01-11T10:37:21.015163+00:00
                                parts = value.split('T')
                                if len(parts) == 2:
                                    date_str = parts[0]  # 2026-01-11
                                    time_str = parts[1].split('.')[0].split('+')[0].split('-')[0]  # 10:37:21
                                    # Parse date manually
                                    year, month, day = date_str.split('-')
                                    months = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 
                                             'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']
                                    month_name = months[int(month) - 1]
                                    hour, minute = time_str.split(':')[:2]
                                    return f"{int(day)} {month_name} {year} à {hour}:{minute}"
                            except Exception:
                                pass
                    else:
                        d = parse_date(value)
                        if d:
                            return date_format(d, 'd F Y')
                else:
                    # It's already a datetime/date object
                    if isinstance(field, models.DateTimeField):
                        return date_format(value, 'd F Y à H:i')
                    else:
                        return date_format(value, 'd F Y')
            except Exception:
                # If formatting fails, try to make it more readable
                if isinstance(value, str) and 'T' in value:
                    # ISO format: try to extract readable parts
                    try:
                        date_part = value.split('T')[0]
                        return date_part.replace('-', '/')
                    except Exception:
                        pass
                return str(value)
    
    # Format time fields
    if isinstance(field, models.TimeField):
        if value:
            try:
                return value.strftime('%H:%M')
            except Exception:
                return str(value)
    
    # Format decimal/float fields
    if isinstance(field, (models.DecimalField, models.FloatField)):
        if value is not None:
            try:
                if isinstance(field, models.DecimalField):
                    return f"{value:,.2f}".replace(',', ' ').replace('.', ',')
                return f"{value:,.2f}".replace(',', ' ').replace('.', ',')
            except Exception:
                return str(value)
    
    # Format ForeignKey relations - already handled by _resolve_relation_value
    # but we can add more context here if needed
    if isinstance(field, models.ForeignKey):
        # The value should already be resolved by _resolve_relation_value
        # but we can add more context
        if value and isinstance(value, str):
            return value
    
    return value


def _format_changes_for_display(report, user=None):
    """Convert report.changes JSON into a list of human-readable change rows.

    Args:
        report: AuditLog instance
        user: User instance to check permissions (if None, data will be masked)
    
    Returns list of dicts: {'field': ..., 'old': ..., 'new': ...}
    """
    # Check if user is admin/staff - admins can see all technical data
    is_admin = user and (user.is_superuser or user.is_staff) if user else False
    
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
            tech_field_result = _is_technical_field(k)
            
            # Completely hide certain fields (even from admins) - they're not useful
            if tech_field_result == 'HIDE':
                continue  # Skip this field entirely
            
            if tech_field_result:
                # Technical field that can be shown (formatted)
                if is_admin:
                    # Admin: show formatted values
                    resolved_val = _resolve_relation_value(ct_model, k, v)
                    formatted_val = _format_field_value(ct_model, k, resolved_val, is_admin=True)
                    new_val = _sanitize_change_value(formatted_val)
                    rows.append({
                        'field': label, 
                        'old': None, 
                        'new': new_val, 
                        'field_name': k
                    })
                else:
                    # Non-admin: show masked version
                    rows.append({
                        'field': label, 
                        'old': None, 
                        'new': '[Données techniques - non affichables]', 
                        'field_name': k
                    })
                continue
            
            # Resolve relations first, then format the value
            resolved_val = _resolve_relation_value(ct_model, k, v)
            formatted_val = _format_field_value(ct_model, k, resolved_val, is_admin=is_admin)
            new_val = _sanitize_change_value(formatted_val)
            rows.append({'field': label, 'old': None, 'new': new_val, 'field_name': k})
        return rows

    # Normal diffs: {field: [old, new], ...}
    if isinstance(changes, dict):
        for field, pair in changes.items():
            # pair expected like [old, new]
            old_val, new_val = (pair[0], pair[1]) if isinstance(pair, (list, tuple)) and len(pair) >= 2 else (None, pair)
            label = _human_label_for_field(ct_model, field)

            # For technical fields, produce explicit, user-friendly label or hide them
            tech_field_result = _is_technical_field(field)
            
            # Completely hide certain fields (even from admins) - they're not useful
            if tech_field_result == 'HIDE':
                continue  # Skip this field entirely
            
            if tech_field_result:
                # Technical field that can be shown (formatted)
                if is_admin:
                    # Admin: show formatted values
                    old_h = _format_field_value(ct_model, field, old_h, is_admin=True)
                    new_h = _format_field_value(ct_model, field, new_h, is_admin=True)
                    old_h = _sanitize_change_value(old_h) if old_h else None
                    new_h = _sanitize_change_value(new_h) if new_h else None
                    rows.append({
                        'field': label, 
                        'old': old_h, 
                        'new': new_h, 
                        'field_name': field
                    })
                else:
                    # Non-admin: show masked version
                    rows.append({
                        'field': label, 
                        'old': '[Données techniques]' if old_val else None, 
                        'new': '[Données techniques - non affichables]', 
                        'field_name': field
                    })
                continue

            # Try to resolve relations to readable strings
            old_h = _resolve_relation_value(ct_model, field, old_val)
            new_h = _resolve_relation_value(ct_model, field, new_val)

            # Format values using the new formatter (for choices, dates, booleans, etc.)
            old_h = _format_field_value(ct_model, field, old_h, is_admin=is_admin)
            new_h = _format_field_value(ct_model, field, new_h, is_admin=is_admin)

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

    # Special handling for Alerte model
    if ct_model and ct_model.__name__ == 'Alerte':
        from .models import Alerte
        alerte = None
        try:
            alerte = Alerte.objects.select_related('materiel', 'client', 'departement').filter(pk=report.object_id).first()
        except Exception:
            alerte = None
        
        if alerte:
            parts = []
            parts.append(f"L'utilisateur \"{user_label}\" a")
            if report.action == AuditLog.ACTION_CREATE:
                parts.append("créé une alerte")
            elif report.action == AuditLog.ACTION_UPDATE:
                parts.append("modifié une alerte")
            elif report.action == AuditLog.ACTION_DELETE:
                parts.append("supprimé une alerte")
            
            parts.append(f"de type \"{alerte.get_type_alerte_display()}\"")
            parts.append(f"avec une sévérité \"{alerte.get_severite_display()}\"")
            
            if alerte.materiel:
                parts.append(f"pour le matériel \"{alerte.materiel.nom}\" [{alerte.materiel.asset_id}]")
            if alerte.departement:
                parts.append(f"du département \"{alerte.departement.nom}\"")
            if alerte.description:
                desc_short = alerte.description[:100] + '...' if len(alerte.description) > 100 else alerte.description
                parts.append(f"Description: {desc_short}")
            
            return ' '.join(parts)
    
    # Special handling for Materiel model
    if ct_model and ct_model.__name__ == 'Materiel':
        from .models import Materiel
        materiel = None
        try:
            materiel = Materiel.objects.select_related('departement', 'categorie').filter(pk=report.object_id).first()
        except Exception:
            materiel = None
        
        if materiel:
            parts = []
            parts.append(f"L'utilisateur \"{user_label}\" a")
            if report.action == AuditLog.ACTION_CREATE:
                parts.append("créé un matériel")
            elif report.action == AuditLog.ACTION_UPDATE:
                parts.append("modifié un matériel")
            elif report.action == AuditLog.ACTION_DELETE:
                parts.append("supprimé un matériel")
            
            parts.append(f"\"{materiel.nom}\"")
            parts.append(f"[{materiel.asset_id}]")
            
            if materiel.departement:
                parts.append(f"du département \"{materiel.departement.nom}\"")
            if materiel.categorie:
                parts.append(f"de la catégorie \"{materiel.categorie.nom}\"")
            if report.action == AuditLog.ACTION_UPDATE and formatted_changes:
                changed_fields = [c['field'] for c in formatted_changes[:3]]
                if changed_fields:
                    parts.append(f"(champs modifiés: {', '.join(changed_fields)})")
            
            return ' '.join(parts)
    
    # Special handling for Client model
    if ct_model and ct_model.__name__ == 'Client':
        from .models import Client
        client = None
        try:
            client = Client.objects.select_related('departement', 'salle').filter(pk=report.object_id).first()
        except Exception:
            client = None
        
        if client:
            parts = []
            parts.append(f"L'utilisateur \"{user_label}\" a")
            if report.action == AuditLog.ACTION_CREATE:
                parts.append("créé un client")
            elif report.action == AuditLog.ACTION_UPDATE:
                parts.append("modifié un client")
            elif report.action == AuditLog.ACTION_DELETE:
                parts.append("supprimé un client")
            
            parts.append(f"\"{client.nom}\"")
            parts.append(f"({client.get_type_client_display()})")
            
            if client.departement:
                parts.append(f"du département \"{client.departement.nom}\"")
            if client.salle:
                parts.append(f"associé à la salle \"{client.salle.nom}\"")
            
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
            'historiqueattribution': 'Historique d\'attribution',
            'session': 'Session utilisateur',
        }
        friendly_model = model_map.get(name, ct_model._meta.verbose_name.title() if getattr(ct_model, '_meta', None) else ct_model.__name__)
        
        # For Session model, simplify the object representation
        if name == 'session' and obj_label:
            # Session keys are long random strings - show a simplified version
            if len(obj_label) > 30:
                obj_label = "Session utilisateur (données techniques)"
            else:
                obj_label = "Session utilisateur"

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
    
    # For Alerte, add more context
    if ct_model and ct_model.__name__ == 'Alerte':
        try:
            from .models import Alerte
            alerte = Alerte.objects.filter(pk=report.object_id).select_related('materiel', 'departement').first()
            if alerte:
                type_display = alerte.get_type_alerte_display()
                severite_display = alerte.get_severite_display()
                if alerte.materiel:
                    object_desc = f"[{severite_display}] {type_display} — Matériel: {alerte.materiel.asset_id}"
                else:
                    object_desc = f"[{severite_display}] {type_display}"
        except Exception:
            pass
    
    # For Materiel, add more context
    if ct_model and ct_model.__name__ == 'Materiel':
        try:
            from .models import Materiel
            materiel = Materiel.objects.filter(pk=report.object_id).select_related('departement').first()
            if materiel:
                object_desc = f"{materiel.nom} [{materiel.asset_id}]"
                if materiel.departement:
                    object_desc += f" — Département: {materiel.departement.nom}"
        except Exception:
            pass
    
    # For Client, add more context
    if ct_model and ct_model.__name__ == 'Client':
        try:
            from .models import Client
            client = Client.objects.filter(pk=report.object_id).first()
            if client:
                object_desc = f"{client.nom} ({client.get_type_client_display()})"
        except Exception:
            pass

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
        'session': 'Session utilisateur',
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
    
    # For Alerte, add more context
    if ct_model and ct_model.__name__ == 'Alerte':
        try:
            from .models import Alerte
            alerte = Alerte.objects.filter(pk=report.object_id).select_related('materiel').first()
            if alerte:
                type_display = alerte.get_type_alerte_display()
                severite_display = alerte.get_severite_display()
                if alerte.materiel:
                    obj = f"[{severite_display}] {type_display} — {alerte.materiel.asset_id}"
                else:
                    obj = f"[{severite_display}] {type_display}"
        except Exception:
            pass
    
    # For Materiel, add more context
    if ct_model and ct_model.__name__ == 'Materiel':
        try:
            from .models import Materiel
            materiel = Materiel.objects.filter(pk=report.object_id).first()
            if materiel:
                obj = f"{materiel.nom} [{materiel.asset_id}]"
        except Exception:
            pass
    
    # For Client, add more context
    if ct_model and ct_model.__name__ == 'Client':
        try:
            from .models import Client
            client = Client.objects.filter(pk=report.object_id).first()
            if client:
                obj = f"{client.nom} ({client.get_type_client_display()})"
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
    
    # Add more context for Alerte
    if ct_model and ct_model.__name__ == 'Alerte':
        try:
            from .models import Alerte
            alerte = Alerte.objects.filter(pk=report.object_id).select_related('departement').first()
            if alerte and alerte.departement:
                summary_parts.append(f"— Département: {alerte.departement.nom}")
        except Exception:
            pass

    return ' '.join(summary_parts)

@login_required
def materiel_create(request):
    # #region agent log
    import json, time
    with open(r's:\Brice\RadGestMat\.cursor\debug.log', 'a', encoding='utf-8') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"assets/views.py:1131","message":"materiel_create entry","data":{"method":request.method},"timestamp":int(time.time()*1000)}) + '\n')
    # #endregion
    # récupère département injecté par votre middleware si présent
    departement = None
    # #region agent log
    with open(r's:\Brice\RadGestMat\.cursor\debug.log', 'a', encoding='utf-8') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"assets/views.py:1142","message":"Departement obtenu","data":{"dept_id":departement.id if departement else None,"dept_code":departement.code if departement else None},"timestamp":int(time.time()*1000)}) + '\n')
    # #endregion

    if request.method == 'POST':
        # #region agent log
        with open(r's:\Brice\RadGestMat\.cursor\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"assets/views.py:1144","message":"Creation form POST","data":{"has_location":'location' in request.POST},"timestamp":int(time.time()*1000)}) + '\n')
        # #endregion
        form = MaterielForm(request.POST, request.FILES, departement=departement, user=request.user, allow_all_categories=True)
        # #region agent log
        with open(r's:\Brice\RadGestMat\.cursor\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"assets/views.py:1146","message":"Form validation","data":{"is_valid":form.is_valid(),"errors":dict(form.errors) if not form.is_valid() else {}},"timestamp":int(time.time()*1000)}) + '\n')
        # #endregion
        if form.is_valid():
            # #region agent log
            with open(r's:\Brice\RadGestMat\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"assets/views.py:1147","message":"Before form.save","data":{"cleaned_location":form.cleaned_data.get('location','NOT_FOUND')},"timestamp":int(time.time()*1000)}) + '\n')
            # #endregion
            materiel = form.save(commit=False)
            # #region agent log
            with open(r's:\Brice\RadGestMat\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"assets/views.py:1149","message":"After form.save commit=False","data":{"materiel_location":getattr(materiel,'location',None),"materiel_departement_id":getattr(materiel,'departement_id',None)},"timestamp":int(time.time()*1000)}) + '\n')
            # #endregion
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
                
                # Trouver le dernier asset_id globalement (pour garantir l'unicité)
                # Récupérer tous les asset_id OKP et extraire le max numérique
                existing_assets = Materiel.objects.filter(
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
            
            # Générer automatiquement numero_inventaire (toujours pour les nouvelles créations)
            numero_inv_value = getattr(materiel, 'numero_inventaire', '') or ''
            if (not numero_inv_value or 
                numero_inv_value.strip() == '' or
                (numero_inv_value and not numero_inv_value.startswith('RAD-'))):
                
                # Trouver le dernier numero_inventaire globalement (pour garantir l'unicité)
                existing_invs = Materiel.objects.filter(
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
            
            # #region agent log
            with open(r's:\Brice\RadGestMat\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"assets/views.py:1203","message":"Before materiel.save","data":{"asset_id":getattr(materiel,'asset_id',None),"numero_inv":getattr(materiel,'numero_inventaire',None)},"timestamp":int(time.time()*1000)}) + '\n')
            # #endregion
            try:
                materiel.save()
                # #region agent log
                with open(r's:\Brice\RadGestMat\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"assets/views.py:1206","message":"After materiel.save success","data":{"materiel_id":materiel.pk},"timestamp":int(time.time()*1000)}) + '\n')
                # #endregion
            except Exception as e:
                # #region agent log
                with open(r's:\Brice\RadGestMat\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"assets/views.py:1209","message":"Error during materiel.save","data":{"error":str(e),"error_type":type(e).__name__},"timestamp":int(time.time()*1000)}) + '\n')
                # #endregion
                raise
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
        form = MaterielForm(initial=initial, departement=departement, user=request.user, allow_all_categories=True)
    
    # Récupérer les noms de matériels existants pour le département
    noms_existants = Materiel.objects.values_list('nom', flat=True).distinct().order_by('nom')
    categories = Categorie.objects.all().order_by('nom')
    # Récupérer les locations existantes (toutes, pas seulement pour le département)
    try:
        locations_existantes = Materiel.objects.exclude(location__isnull=True).exclude(location='').values_list('location', flat=True).distinct().order_by('location')
    except Exception as e:
        # #region agent log
        import json
        with open(r's:\Brice\RadGestMat\.cursor\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"assets/views.py:1222","message":"Erreur recuperation locations","data":{"error":str(e)},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        # #endregion
        locations_existantes = []
    
    # Générer les valeurs par défaut pour asset_id et numero_inventaire (recherche globale)
    # Trouver le dernier asset_id globalement
    existing_assets = Materiel.objects.filter(
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
    
    # Trouver le dernier numero_inventaire globalement
    existing_invs = Materiel.objects.filter(
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

    # #region agent log
    with open(r's:\Brice\RadGestMat\.cursor\debug.log', 'a', encoding='utf-8') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"assets/views.py:1258","message":"Before render template","data":{"has_locations":'locations_existantes' in locals(),"locations_count":len(locations_existantes) if 'locations_existantes' in locals() else 0},"timestamp":int(time.time()*1000)}) + '\n')
    # #endregion
    try:
        return render(request, 'assets/materiel_form.html', {
            'form': form,
            'title': 'Ajouter du matériel',
            'materiel': None,
            'noms_existants': noms_existants,
            'categories': categories,
            'locations_existantes': locations_existantes,
            'asset_id_default': asset_id_default,
            'numero_inv_default': numero_inv_default,
        })
    except Exception as e:
        # #region agent log
        with open(r's:\Brice\RadGestMat\.cursor\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"assets/views.py:1270","message":"Error during render","data":{"error":str(e),"error_type":type(e).__name__},"timestamp":int(time.time()*1000)}) + '\n')
        # #endregion
        raise

@login_required
def api_search_suggestions(request):
    scope = (request.GET.get('scope') or 'all').strip().lower()
    raw_query = (request.GET.get('q') or '').strip()

    try:
        limit = int(request.GET.get('limit', 12))
    except (TypeError, ValueError):
        limit = 12
    limit = max(1, min(limit, 20))

    if not raw_query:
        return JsonResponse({'suggestions': []})

    terms = _split_search_terms(raw_query)
    terms_lower = [t.lower() for t in terms]
    suggestions = []
    seen = set()

    def add_suggestions(qs, fields):
        if not fields or len(suggestions) >= limit:
            return
        sample_limit = max(limit * 5, 25)
        for row in qs.values_list(*fields)[:sample_limit]:
            if len(suggestions) >= limit:
                break
            row_values = row if isinstance(row, tuple) else (row,)
            for val in row_values:
                if val is None:
                    continue
                val_str = str(val).strip()
                if not val_str:
                    continue
                val_lower = val_str.lower()
                if terms_lower and not any(term in val_lower for term in terms_lower):
                    continue
                if val_str in seen:
                    continue
                seen.add(val_str)
                suggestions.append(val_str)
                if len(suggestions) >= limit:
                    break

    if scope in {'all', 'materiel', 'materiels'}:
        profil = getattr(request, 'profil_utilisateur', None)
        departement = getattr(request, 'departement', None)
        allow_all = bool(profil and profil.role == 'SUPER_ADMIN')

        materiel_search_fields = [
            'nom',
            'asset_id',
            'numero_inventaire',
            'numero_serie',
            'modele',
            'marque',
            'location',
            'description',
            'notes',
            'categorie__nom',
            'departement__nom',
            'salle__nom',
        ]
        materiel_suggest_fields = [
            'nom',
            'asset_id',
            'numero_inventaire',
            'numero_serie',
            'modele',
            'marque',
            'location',
            'categorie__nom',
            'departement__nom',
            'salle__nom',
        ]
        materiel_qs = Materiel.objects.all()
        if not allow_all:
            if not departement:
                return JsonResponse({'suggestions': []})
            materiel_qs = materiel_qs.filter(departement=departement)
        materiel_qs = _apply_multi_term_search(materiel_qs, terms, materiel_search_fields)
        add_suggestions(materiel_qs, materiel_suggest_fields)

    if scope in {'all', 'client', 'clients'} and len(suggestions) < limit:
        client_search_fields = [
            'nom',
            'email',
            'telephone',
            'numero_chambre',
            'nom_evenement',
            'departement__nom',
            'salle__nom',
            'notes',
        ]
        client_suggest_fields = [
            'nom',
            'email',
            'telephone',
            'numero_chambre',
            'nom_evenement',
            'departement__nom',
            'salle__nom',
        ]
        client_qs = Client.objects.select_related('departement', 'salle').all()
        client_qs = _apply_multi_term_search(client_qs, terms, client_search_fields)
        add_suggestions(client_qs, client_suggest_fields)

    return JsonResponse({'suggestions': suggestions})


@login_required
def api_noms_materiels(request):
    """API pour récupérer les noms de matériels existants"""
    departement = getattr(request, 'departement', None)
    if not departement:
        return JsonResponse({'error': 'Département non trouvé'}, status=400)
    
    categorie_id = request.GET.get('categorie_id')
    query = request.GET.get('q', '').strip()
    
    materiels = Materiel.objects.filter(departement=departement)
    
    if categorie_id:
        materiels = materiels.filter(categorie_id=categorie_id)
    
    if query:
        materiels = materiels.filter(nom__icontains=query)
    
    noms = materiels.values_list('nom', flat=True).distinct().order_by('nom')
    
    return JsonResponse({'noms': list(noms)})


@login_required
def api_materiel_snapshot(request):
    """Renvoie un petit snapshot JSON avec le nombre total et la dernière modification.

    Utilisé par le frontend pour détecter si la liste a changé (polling léger).
    """
    departement = getattr(request, 'departement', None)
    if not departement:
        return JsonResponse({'error': 'Département non trouvé'}, status=400)

    total = Materiel.objects.filter(departement=departement).count()
    last_mod = Materiel.objects.filter(departement=departement).aggregate(Max('date_modification'))['date_modification__max']

    return JsonResponse({
        'total': total,
        'last_modification': last_mod.isoformat() if last_mod else None,
    })

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
    show_all = True
    
    # Super Admin: voir tous les données
    if show_all:
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
    alertes_recentes = AlerteService.get_alertes_non_reglementees()[:3]
    nombre_alertes_critiques = AlerteService.get_nombre_alertes_critiques()

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
    """Liste des materiels avec filtres avances, regroupes par equipement."""
    departement = getattr(request, 'departement', None)
    profil = getattr(request, 'profil_utilisateur', None)
    if not departement:
        departement, _ = Departement.objects.get_or_create(
            code='DEF',
            defaults={'nom': 'Departement par defaut'}
        )

    query = request.GET.get('q', '')
    categorie_filter = request.GET.get('categorie', '')
    location_filter = request.GET.get('location', '')
    statut_filter = (request.GET.get('statut_disponibilite') or '').strip()
    marque_filter = (request.GET.get('marque') or '').strip()
    etat_filter = (request.GET.get('etat_technique') or '').strip()
    date_achat_from_raw = (request.GET.get('date_achat_from') or '').strip()
    date_achat_to_raw = (request.GET.get('date_achat_to') or '').strip()

    from django.utils.dateparse import parse_date
    date_achat_from = parse_date(date_achat_from_raw) if date_achat_from_raw else None
    date_achat_to = parse_date(date_achat_to_raw) if date_achat_to_raw else None
    if date_achat_from and date_achat_to and date_achat_from > date_achat_to:
        date_achat_from, date_achat_to = date_achat_to, date_achat_from

    show_all = True
    if show_all:
        dept_id_param = request.GET.get('departement')
        if dept_id_param:
            try:
                sel_dept = Departement.objects.get(id=dept_id_param)
                materiels_base = Materiel.objects.filter(departement=sel_dept).select_related('categorie', 'departement')
            except Departement.DoesNotExist:
                materiels_base = Materiel.objects.all().select_related('categorie', 'departement')
        else:
            materiels_base = Materiel.objects.all().select_related('categorie', 'departement')
    else:
        materiels_base = Materiel.objects.filter(departement=departement).select_related('categorie', 'departement')

    # Filtres de base (multi-termes, insensible a la casse)
    if query:
        terms = _split_search_terms(query)
        search_fields = [
            'nom',
            'asset_id',
            'numero_inventaire',
            'numero_serie',
            'modele',
            'marque',
            'location',
            'description',
            'notes',
            'categorie__nom',
            'departement__nom',
            'salle__nom',
        ]
        materiels_base = _apply_multi_term_search(materiels_base, terms, search_fields)

    if categorie_filter:
        materiels_base = materiels_base.filter(categorie_id=categorie_filter)
    if location_filter:
        materiels_base = materiels_base.filter(location=location_filter)

    # Source pour les listes de filtres (avant filtres specifiques)
    options_qs = materiels_base

    # Filtres avances
    if statut_filter:
        materiels_base = materiels_base.filter(statut_disponibilite=statut_filter)
    if marque_filter:
        materiels_base = materiels_base.filter(marque__iexact=marque_filter)
    if etat_filter:
        materiels_base = materiels_base.filter(etat_technique=etat_filter)
    if date_achat_from:
        materiels_base = materiels_base.filter(date_achat__gte=date_achat_from)
    if date_achat_to:
        materiels_base = materiels_base.filter(date_achat__lte=date_achat_to)

    # Regroupement fixe par nom d'equipement
    if show_all:
        grouped_rows = materiels_base.values('nom', 'categorie', 'departement').annotate(
            quantite=Count('id'),
            date_modification=Max('date_modification')
        ).order_by('departement__nom', 'nom')
    else:
        grouped_rows = materiels_base.values('nom', 'categorie').annotate(
            quantite=Count('id'),
            date_modification=Max('date_modification')
        ).order_by('nom')

    groupes_enrichis = []
    for row in grouped_rows:
        nom = row['nom']
        departement_id = row.get('departement')
        if show_all and departement_id:
            materiel_exemple = materiels_base.filter(
                nom=nom,
                departement_id=departement_id
            ).select_related('categorie', 'departement').first()
            materiels_groupe = materiels_base.filter(nom=nom, departement_id=departement_id)
        else:
            materiel_exemple = materiels_base.filter(nom=nom).select_related('categorie', 'departement').first()
            materiels_groupe = materiels_base.filter(nom=nom)

        groupes_enrichis.append({
            'nom': nom,
            'group_display': nom or 'Non renseigne',
            'categorie': materiel_exemple.categorie if materiel_exemple else None,
            'departement': materiel_exemple.departement if materiel_exemple else None,
            'quantite': materiels_groupe.count(),
            'disponible': materiels_groupe.filter(
                statut_disponibilite=Materiel.STATUT_DISPONIBLE,
                etat_technique=Materiel.ETAT_FONCTIONNEL
            ).count(),
            'attribue': materiels_groupe.filter(statut_disponibilite=Materiel.STATUT_ATTRIBUE).count(),
            'maintenance': materiels_groupe.filter(statut_disponibilite=Materiel.STATUT_MAINTENANCE).count(),
            'hors_service': materiels_groupe.filter(statut_disponibilite=Materiel.STATUT_HORS_SERVICE).count(),
            'date_modification': row['date_modification'],
        })

    total_materiels = materiels_base.count()
    stats = {
        'total': total_materiels,
        'disponible': materiels_base.filter(statut_disponibilite=Materiel.STATUT_DISPONIBLE).count(),
        'attribue': materiels_base.filter(statut_disponibilite=Materiel.STATUT_ATTRIBUE).count(),
        'maintenance': materiels_base.filter(statut_disponibilite=Materiel.STATUT_MAINTENANCE).count(),
        'hors_service': materiels_base.filter(statut_disponibilite=Materiel.STATUT_HORS_SERVICE).count(),
    }

    if show_all:
        categories = Categorie.objects.all()
        departements_list = Departement.objects.all()
    else:
        categories = Categorie.objects.filter(departement=departement)
        departements_list = None

    locations_list = options_qs.exclude(location__isnull=True).exclude(location='').values_list(
        'location',
        flat=True
    ).distinct().order_by('location')
    marques_list = options_qs.exclude(marque__isnull=True).exclude(marque='').values_list(
        'marque',
        flat=True
    ).distinct().order_by('marque')

    can_manage = request.user.is_superuser or (profil and profil.role in ['SUPER_ADMIN', 'DEPT_MANAGER'])

    context = {
        'groupes_materiels': groupes_enrichis,
        'query': query,
        'categorie_filter': categorie_filter,
        'location_filter': location_filter,
        'statut_filter': statut_filter,
        'marque_filter': marque_filter,
        'etat_filter': etat_filter,
        'date_achat_from': date_achat_from.isoformat() if date_achat_from else '',
        'date_achat_to': date_achat_to.isoformat() if date_achat_to else '',
        'stats': stats,
        'categories': categories,
        'locations': locations_list,
        'marques': marques_list,
        'statut_choices': Materiel.STATUT_CHOICES,
        'etat_choices': Materiel.ETAT_CHOICES,
        'departements': departements_list,
        'user_profile': profil,
        'can_manage': can_manage,
        'show_all': show_all,
        'last_modification': materiels_base.aggregate(Max('date_modification'))['date_modification__max'],
    }

    return render(request, 'assets/materiel_list.html', context)

@login_required
def materiel_group_detail(request, nom):
    """Affiche tous les matériels d'un groupe (même nom d'équipement)"""
    departement = getattr(request, 'departement', None)
    profil = getattr(request, 'profil_utilisateur', None)
    can_clone = request.user.is_superuser or (profil and profil.role in ['SUPER_ADMIN', 'DEPT_MANAGER', 'DEPT_USER'])
    
    if not departement:
        departement, _ = Departement.objects.get_or_create(code='DEF', defaults={'nom': 'Département par défaut'})

    materiels = Materiel.objects.filter(
        nom=nom
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
        'can_manage': can_clone,
        'can_clone': can_clone,
    }
    
    return render(request, 'assets/materiel_group_detail.html', context)

@login_required
def materiel_clone(request, pk):
    """Clone un matériel avec un nombre de copies dynamique"""
    # pk est le matériel par défaut, mais on peut en sélectionner un autre dans le formulaire
    materiel_par_defaut = get_object_or_404(Materiel, pk=pk)
    profil = getattr(request, 'profil_utilisateur', None)
    
    # Vérifier les permissions
    if not (request.user.is_superuser or (profil and profil.role in ['SUPER_ADMIN', 'DEPT_MANAGER', 'DEPT_USER'])):
        messages.error(request, "Vous n'avez pas les permissions nécessaires pour cloner un matériel.")
        return redirect('assets:materiel_detail', pk=pk)
    
    if request.method == 'POST':
        # Récupérer le matériel source sélectionné dans le formulaire
        materiel_source_id = request.POST.get('materiel_source', pk)
        try:
            source_queryset = Materiel.objects.all()
            if profil and profil.role == 'DEPT_USER':
                source_queryset = source_queryset.filter(departement=profil.departement)
            materiel_source = source_queryset.get(pk=materiel_source_id)
        except Materiel.DoesNotExist:
            messages.error(request, "Matériel source introuvable.")
            return redirect('assets:materiel_group_detail', nom=materiel_par_defaut.nom)
        
        try:
            nombre_copies = int(request.POST.get('nombre_copies', 1))
            if nombre_copies < 1 or nombre_copies > 100:
                messages.error(request, "Le nombre de copies doit être entre 1 et 100.")
                return redirect('assets:materiel_group_detail', nom=materiel_source.nom)
        except (ValueError, TypeError):
            messages.error(request, "Nombre de copies invalide.")
            return redirect('assets:materiel_group_detail', nom=materiel_source.nom)
        
        copies_creees = []
        erreurs = []
        
        for i in range(nombre_copies):
            try:
                # Créer une copie du matériel
                nouveau_materiel = Materiel(
                    nom=materiel_source.nom,
                    description=materiel_source.description,
                    categorie=materiel_source.categorie,
                    departement=materiel_source.departement,
                    marque=materiel_source.marque,
                    modele=materiel_source.modele,
                    # Ne pas copier le numéro de série (peut être vide)
                    numero_serie=None,
                    etat_technique=materiel_source.etat_technique,
                    statut_disponibilite=materiel_source.statut_disponibilite,
                    date_achat=materiel_source.date_achat,
                    prix=materiel_source.prix,
                    salle=materiel_source.salle,
                    location=materiel_source.location,
                    notes=materiel_source.notes,
                    # asset_id et numero_inventaire seront générés automatiquement par save()
                    asset_id='NEW',  # Sera généré automatiquement
                    numero_inventaire='',  # Sera généré automatiquement
                )
                nouveau_materiel.save()  # Génère automatiquement asset_id et numero_inventaire
                copies_creees.append(nouveau_materiel)
            except Exception as e:
                erreurs.append(f"Erreur lors de la création de la copie {i+1}: {str(e)}")
        
        if copies_creees:
            messages.success(request, f"{len(copies_creees)} copie(s) créée(s) avec succès!")
        if erreurs:
            for erreur in erreurs:
                messages.warning(request, erreur)
        
        return redirect('assets:materiel_group_detail', nom=materiel_source.nom)
    
    # GET: rediriger vers la page du groupe
    return redirect('assets:materiel_group_detail', nom=materiel_source.nom)

@login_required
def materiel_detail(request, pk):
    """Affiche les détails d'un matériel."""
    # Permettre l'accès à tous les matériels (Phase 1 MVP)
    # Phase 2: implémenter les permissions par département
    materiel = get_object_or_404(Materiel, pk=pk)

    qr_missing = False
    if materiel.qr_code:
        try:
            if not materiel.qr_code.storage.exists(materiel.qr_code.name):
                qr_missing = True
                materiel.qr_code = None
                materiel.save(update_fields=['qr_code'])
        except Exception:
            pass

    if qr_missing:
        ok, err = _generate_materiel_qr_code(materiel)
        if ok:
            messages.info(request, 'QR Code r?g?n?r? automatiquement.')
        else:
            messages.warning(request, f'QR Code indisponible: {err}')
    
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
    profil = getattr(request, 'profil_utilisateur', None)

    if not (
        request.user.is_superuser
        or (profil and profil.role == 'SUPER_ADMIN')
        or (
            profil
            and profil.role in ['DEPT_MANAGER', 'DEPT_USER']
            and profil.departement_id == materiel.departement_id
        )
    ):
        raise PermissionDenied("Vous n'avez pas la permission de modifier ce matériel.")
    
    if request.method == 'POST':
        # Vérifier si c'est une demande de génération de QR code

        if 'generate_qr' in request.POST:

            ok, err = _generate_materiel_qr_code(materiel)

            if ok:

                messages.success(request, 'QR Code généré avec succès!')

            else:

                messages.error(request, f'Erreur lors de la génération du QR code: {err}')


            return redirect('assets:materiel_detail', pk=materiel.pk)
        
        # Sinon, traitement normal du formulaire
        form = MaterielForm(request.POST, request.FILES, instance=materiel, departement=departement)
        if form.is_valid():
            form.save()
            return redirect('assets:materiel_detail', pk=materiel.pk)
    else:
        form = MaterielForm(instance=materiel, departement=departement)
    
    # Récupérer les noms de matériels existants pour le département
    noms_existants = Materiel.objects.filter(departement=departement).values_list('nom', flat=True).distinct().order_by('nom')
    categories = Categorie.objects.filter(departement=departement).order_by('nom')
    # Récupérer les locations existantes (toutes, pas seulement pour le département)
    locations_existantes = Materiel.objects.exclude(location__isnull=True).exclude(location='').values_list('location', flat=True).distinct().order_by('location')
    
    return render(request, 'assets/materiel_form.html', {
        'form': form, 
        'materiel': materiel,
        'title': 'Modifier le matériel',
        'noms_existants': noms_existants,
        'categories': categories,
        'locations_existantes': locations_existantes,
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


@login_required
@require_http_methods(["POST"])
def materiel_bulk_delete(request):
    """Supprime plusieurs matériels sélectionnés (par lot)."""
    profil = getattr(request, 'profil_utilisateur', None)
    can_manage = request.user.is_superuser or (profil and profil.role in ['SUPER_ADMIN', 'DEPT_MANAGER'])
    if not can_manage:
        raise PermissionDenied("Vous n'avez pas la permission de supprimer ces matériels.")

    raw_ids = request.POST.getlist('materiel_ids')
    if len(raw_ids) == 1 and raw_ids and ',' in raw_ids[0]:
        # Support comma-separated list if sent from a custom client
        raw_ids = [v.strip() for v in raw_ids[0].split(',') if v.strip()]

    materiel_ids = []
    for raw_id in raw_ids:
        try:
            materiel_ids.append(int(raw_id))
        except (TypeError, ValueError):
            continue

    if not materiel_ids:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': "Aucun matériel sélectionné."}, status=400)
        messages.error(request, "Aucun matériel sélectionné.")
        return redirect(request.POST.get('next') or request.META.get('HTTP_REFERER', 'assets:materiel_list'))

    qs = Materiel.objects.filter(pk__in=materiel_ids)
    if not (request.user.is_superuser or (profil and profil.role == 'SUPER_ADMIN')):
        if profil and profil.role == 'DEPT_MANAGER' and profil.departement_id:
            qs = qs.filter(departement_id=profil.departement_id)
        else:
            qs = qs.none()

    materiels = list(qs)
    deleted_ids = [m.pk for m in materiels]
    for m in materiels:
        m.delete()

    requested_ids = set(materiel_ids)
    deleted_set = set(deleted_ids)
    skipped_ids = sorted(requested_ids - deleted_set)

    deleted_count = len(deleted_ids)
    skipped_count = len(skipped_ids)

    message = f"{deleted_count} matériel(s) supprimé(s)."
    if skipped_count:
        message += f" {skipped_count} élément(s) non supprimé(s) (permissions insuffisantes ou déjà supprimés)."

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': message,
            'deleted_count': deleted_count,
            'deleted_ids': deleted_ids,
            'skipped_count': skipped_count,
            'skipped_ids': skipped_ids,
        })

    if deleted_count:
        messages.success(request, message)
    else:
        messages.warning(request, message)

    return redirect(request.POST.get('next') or request.META.get('HTTP_REFERER', 'assets:materiel_list'))


@login_required
@require_http_methods(["POST"])
def materiel_group_bulk_delete(request):
    """Supprime plusieurs groupes d'équipements (tous les matériels associés)."""
    profil = getattr(request, 'profil_utilisateur', None)
    can_manage = request.user.is_superuser or (profil and profil.role in ['SUPER_ADMIN', 'DEPT_MANAGER'])
    if not can_manage:
        raise PermissionDenied("Vous n'avez pas la permission de supprimer ces matériels.")

    groups_payload = []
    if request.content_type and 'application/json' in request.content_type:
        try:
            import json
            payload = json.loads(request.body.decode('utf-8') or '{}')
            groups_payload = payload.get('groups') or []
        except Exception:
            groups_payload = []
    else:
        raw_groups = request.POST.getlist('groups')
        for raw in raw_groups:
            # Expected format: nom||departement_id
            if isinstance(raw, str) and '||' in raw:
                nom_part, dept_part = raw.split('||', 1)
                groups_payload.append({'nom': nom_part, 'departement_id': dept_part})

    groups = []
    seen = set()
    for item in groups_payload:
        if not isinstance(item, dict):
            continue
        nom = (item.get('nom') or '').strip()
        if not nom:
            continue
        dept_raw = item.get('departement_id')
        dept_id = None
        if dept_raw not in (None, '', 'None'):
            try:
                dept_id = int(dept_raw)
            except (TypeError, ValueError):
                dept_id = None
        key = (nom, dept_id)
        if key in seen:
            continue
        seen.add(key)
        groups.append({'nom': nom, 'departement_id': dept_id})

    if not groups:
        return JsonResponse({'success': False, 'error': "Aucun groupe sélectionné."}, status=400)

    is_super_admin = request.user.is_superuser or (profil and profil.role == 'SUPER_ADMIN')
    manager_dept_id = profil.departement_id if (profil and profil.role == 'DEPT_MANAGER') else None

    deleted_groups = []
    skipped_groups = []
    deleted_count = 0

    for group in groups:
        nom = group['nom']
        dept_id = group.get('departement_id')

        qs = Materiel.objects.filter(nom=nom)
        if is_super_admin:
            if dept_id:
                qs = qs.filter(departement_id=dept_id)
        else:
            if manager_dept_id:
                qs = qs.filter(departement_id=manager_dept_id)
            else:
                qs = qs.none()

        materiels = list(qs)
        if not materiels:
            skipped_groups.append(group)
            continue

        for materiel in materiels:
            materiel.delete()
        deleted_count += len(materiels)
        deleted_groups.append(group)

    message = f"{deleted_count} matériel(s) supprimé(s) dans {len(deleted_groups)} groupe(s)."
    if skipped_groups:
        message += f" {len(skipped_groups)} groupe(s) ignoré(s)."

    return JsonResponse({
        'success': True,
        'message': message,
        'deleted_count': deleted_count,
        'deleted_groups': deleted_groups,
        'skipped_groups': skipped_groups,
    })

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
            lender_email = (request.user.email or '').strip()
            if not lender_email:
                messages.error(
                    request,
                    "Votre email est obligatoire pour effectuer un pret. "
                    "Mettez a jour votre profil puis recommencez.",
                )
                return redirect('assets:materiel_detail', pk=materiel.pk)

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
                etat_apres=Materiel.STATUT_HORS_SERVICE if attribution.type_attribution == Attribution.TYPE_USAGE_UNIQUE else Materiel.STATUT_ATTRIBUE,
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
    clients = Client.objects.select_related('departement', 'salle').all()
    search = request.GET.get('search', '').strip()
    # accept either 'type' (legacy) or 'type_client' from the querystring
    type_filter = request.GET.get('type', '') or request.GET.get('type_client', '')
    
    if search:
        terms = _split_search_terms(search)
        search_fields = [
            'nom',
            'email',
            'telephone',
            'numero_chambre',
            'nom_evenement',
            'departement__nom',
            'salle__nom',
            'notes',
        ]
        clients = _apply_multi_term_search(clients, terms, search_fields)
    if type_filter:
        # The model field is `type_client`
        clients = clients.filter(type_client=type_filter)
    
    return render(request, 'assets/client_list.html', {'clients': clients})


@login_required
def report_list(request):
    """Liste des rapports d'audit avec filtres sur les attributions de materiel."""
    from django.utils.dateparse import parse_date

    qs = AuditLog.objects.select_related('user', 'content_type').all()
    action = (request.GET.get('action') or '').strip()
    ct = (request.GET.get('content_type') or '').strip().lower()
    user = (request.GET.get('user') or '').strip()
    date_from_raw = (request.GET.get('date_from') or '').strip()
    date_to_raw = (request.GET.get('date_to') or '').strip()
    attribution_only = (request.GET.get('attribution_only') or '').strip().lower() in {'1', 'true', 'on', 'yes'}

    date_from = parse_date(date_from_raw) if date_from_raw else None
    date_to = parse_date(date_to_raw) if date_to_raw else None
    if date_from and date_to and date_from > date_to:
        date_from, date_to = date_to, date_from

    if action:
        qs = qs.filter(action=action)
    if ct:
        qs = qs.filter(content_type__model=ct)
    if user:
        qs = qs.filter(user__username__icontains=user)
    if date_from:
        qs = qs.filter(timestamp__date__gte=date_from)
    if date_to:
        qs = qs.filter(timestamp__date__lte=date_to)
    if attribution_only:
        qs = qs.filter(content_type__model='attribution')

    reports = qs.order_by('-timestamp')[:200]

    # Dataset d'attributions pour compter et organiser les attributions sur la periode.
    attributions_qs = Attribution.objects.select_related(
        'materiel', 'client', 'salle', 'employe_responsable'
    ).all()
    if user:
        attributions_qs = attributions_qs.filter(employe_responsable__username__icontains=user)
    if date_from:
        attributions_qs = attributions_qs.filter(date_attribution__date__gte=date_from)
    if date_to:
        attributions_qs = attributions_qs.filter(date_attribution__date__lte=date_to)

    attribution_total_count = attributions_qs.count()
    attribution_active_count = attributions_qs.filter(date_retour_effective__isnull=True).count()
    attribution_returned_count = attributions_qs.filter(date_retour_effective__isnull=False).count()

    type_labels = dict(Attribution.TYPE_ATTRIBUTION_CHOICES)
    attribution_counts_by_type = [
        {
            'code': row['type_attribution'],
            'label': type_labels.get(row['type_attribution'], row['type_attribution'] or 'Non defini'),
            'total': row['total'],
        }
        for row in attributions_qs.values('type_attribution').annotate(total=Count('id')).order_by('-total')
    ]

    attribution_counts_by_day = list(
        attributions_qs.annotate(day=TruncDate('date_attribution'))
        .values('day')
        .annotate(total=Count('id'))
        .order_by('-day')[:31]
    )

    available_content_types = sorted(filter(
        None,
        AuditLog.objects.values_list('content_type__model', flat=True).distinct()
    ))

    attributions_period = list(attributions_qs.order_by('-date_attribution')[:100])
    attribution_ids = [str(attr.pk) for attr in attributions_period if attr.pk is not None]
    latest_audit_by_attribution_id = {}
    if attribution_ids:
        for audit in AuditLog.objects.filter(
            content_type__model='attribution',
            object_id__in=attribution_ids
        ).order_by('-timestamp'):
            if audit.object_id not in latest_audit_by_attribution_id:
                latest_audit_by_attribution_id[audit.object_id] = audit.pk

    for attr in attributions_period:
        attr.latest_report_id = latest_audit_by_attribution_id.get(str(attr.pk))

    return render(request, 'assets/report_list.html', {
        'reports': reports,
        'action_choices': AuditLog.ACTION_CHOICES,
        'available_content_types': available_content_types,
        'filter_values': {
            'action': action,
            'content_type': ct,
            'user': user,
            'date_from': date_from.isoformat() if date_from else '',
            'date_to': date_to.isoformat() if date_to else '',
            'attribution_only': attribution_only,
        },
        'attribution_total_count': attribution_total_count,
        'attribution_active_count': attribution_active_count,
        'attribution_returned_count': attribution_returned_count,
        'attribution_counts_by_type': attribution_counts_by_type,
        'attribution_counts_by_day': attribution_counts_by_day,
        'attributions_period': attributions_period,
    })


@login_required
def report_attribution_detail(request, pk):
    """Affiche un rapport detaille d'attribution, meme sans AuditLog."""
    attribution = get_object_or_404(
        Attribution.objects.select_related('materiel', 'client', 'salle', 'employe_responsable', 'departement'),
        pk=pk
    )

    related_audit_reports = AuditLog.objects.select_related('user').filter(
        content_type__model='attribution',
        object_id=str(attribution.pk)
    ).order_by('-timestamp')[:20]

    return render(request, 'assets/report_attribution_detail.html', {
        'attribution': attribution,
        'related_audit_reports': related_audit_reports,
    })


@login_required
def report_detail(request, pk):
    report = get_object_or_404(AuditLog, pk=pk)
    # Prepare formatted changes with user permissions (admins see all data)
    formatted_changes = _format_changes_for_display(report, user=request.user)

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
    from django.templatetags.static import static
    logo_url = static('images/logo/rad.png')
    # Ensure it's a full URL if needed for proper display
    if not logo_url.startswith('http'):
        logo_url = request.build_absolute_uri(logo_url)
    
    return render(request, 'assets/report_detail.html', {
        'report': report,
        'formatted_changes': formatted_changes,
        'summary': creative_summary or summary,
        'human_sentence': human_sentence,
        'context_sentence': context_sentence,
        'sanitized_metadata': _sanitize_metadata(getattr(report, 'metadata', None)),
        'logo_url': logo_url,
        'is_admin': request.user.is_superuser or request.user.is_staff,
    })


@login_required
def report_pdf(request, pk):
    """Return a PDF version of the report detail. Uses WeasyPrint if available.

    Falls back to returning the HTML view with a warning if PDF library isn't present.
    """
    report = get_object_or_404(AuditLog, pk=pk)
    # Format changes with user permissions (admins see all data)
    formatted_changes = _format_changes_for_display(report, user=request.user)
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

    # Add logo URL - use absolute URL for PDF generation
    from django.templatetags.static import static
    from django.conf import settings
    import os
    static_path = static('images/logo/rad.png')
    # For PDF, try to use file path if available, otherwise use absolute URL
    logo_file_path = os.path.join(settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else settings.BASE_DIR / 'static', 'images', 'logo', 'rad.png')
    if os.path.exists(logo_file_path):
        # Use file:// URL for local file access in WeasyPrint
        logo_url = f"file://{os.path.abspath(logo_file_path).replace(os.sep, '/')}"
    else:
        # Fallback to HTTP URL
        logo_url = request.build_absolute_uri(static_path)
    
    context = {
        'report': report,
        'formatted_changes': formatted_changes,
        'summary': _build_creative_summary(report) or summary,
        'human_sentence': human_sentence,
        'context_sentence': _build_context_sentence(report),
        'sanitized_metadata': _sanitize_metadata(getattr(report, 'metadata', None)),
        'logo_url': logo_url,
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

# ========== CATEGORIE VIEWS ==========
@login_required
def categorie_list(request):
    """Liste des catégories avec filtres par département et recherche"""
    profil = getattr(request, 'profil_utilisateur', None)
    departement = getattr(request, 'departement', None)
    
    # Déterminer le scope selon le rôle
    if profil and profil.role == 'SUPER_ADMIN':
        categories = Categorie.objects.select_related('departement').all()
        departements_list = Departement.objects.all()
    else:
        if not departement:
            departement, _ = Departement.objects.get_or_create(
                code='DEF',
                defaults={'nom': 'Département par défaut'}
            )
        categories = Categorie.objects.filter(departement=departement).select_related('departement')
        departements_list = [departement]
    
    # Filtres de recherche
    search = request.GET.get('search', '')
    dept_filter = request.GET.get('departement', '')
    
    if search:
        categories = categories.filter(
            Q(nom__icontains=search) | Q(description__icontains=search)
        )
    
    if dept_filter and profil and profil.role == 'SUPER_ADMIN':
        try:
            sel_dept = Departement.objects.get(id=dept_filter)
            categories = categories.filter(departement=sel_dept)
        except Departement.DoesNotExist:
            pass
    
    # Compter les matériels par catégorie
    categories = categories.annotate(
        nb_materiels=Count('materiels')
    ).order_by('departement__nom', 'nom')
    
    context = {
        'categories': categories,
        'search': search,
        'departements': departements_list,
        'dept_filter': dept_filter,
        'user_profile': profil,
    }
    return render(request, 'assets/categorie_list.html', context)

@login_required
def categorie_create(request):
    """Création d'une nouvelle catégorie"""
    if request.method == 'POST':
        form = CategorieForm(request.POST, user=request.user)
        if form.is_valid():
            categorie = form.save()
            messages.success(request, f'Catégorie "{categorie.nom}" créée avec succès.')
            return redirect('assets:categorie_detail', pk=categorie.pk)
    else:
        form = CategorieForm(user=request.user)
    return render(request, 'assets/categorie_form.html', {
        'form': form,
        'title': 'Ajouter une catégorie'
    })

@login_required
def categorie_detail(request, pk):
    """Détails d'une catégorie avec liste des matériels associés"""
    categorie = get_object_or_404(Categorie, pk=pk)
    
    # Vérifier les permissions d'accès
    profil = getattr(request, 'profil_utilisateur', None)
    if not profil or (profil.role != 'SUPER_ADMIN' and categorie.departement != getattr(request, 'departement', None)):
        raise PermissionDenied("Vous n'avez pas accès à cette catégorie.")
    
    # Récupérer les matériels associés
    materiels = Materiel.objects.filter(categorie=categorie).select_related('departement', 'salle').order_by('nom', 'asset_id')
    
    context = {
        'categorie': categorie,
        'materiels': materiels,
    }
    return render(request, 'assets/categorie_detail.html', context)

@login_required
def categorie_update(request, pk):
    """Modification d'une catégorie"""
    categorie = get_object_or_404(Categorie, pk=pk)
    
    # Vérifier les permissions
    profil = getattr(request, 'profil_utilisateur', None)
    if not profil or (profil.role != 'SUPER_ADMIN' and categorie.departement != getattr(request, 'departement', None)):
        raise PermissionDenied("Vous n'avez pas accès à cette catégorie.")
    
    if request.method == 'POST':
        form = CategorieForm(request.POST, instance=categorie, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Catégorie "{categorie.nom}" modifiée avec succès.')
            return redirect('assets:categorie_detail', pk=categorie.pk)
    else:
        form = CategorieForm(instance=categorie, user=request.user)
    return render(request, 'assets/categorie_form.html', {
        'form': form,
        'categorie': categorie,
        'title': f'Modifier la catégorie "{categorie.nom}"'
    })

@login_required
def categorie_delete(request, pk):
    """Suppression d'une catégorie (avec vérification des matériels associés)"""
    categorie = get_object_or_404(Categorie, pk=pk)
    
    # Vérifier les permissions
    profil = getattr(request, 'profil_utilisateur', None)
    if not profil or (profil.role != 'SUPER_ADMIN' and categorie.departement != getattr(request, 'departement', None)):
        raise PermissionDenied("Vous n'avez pas accès à cette catégorie.")
    
    # Vérifier les matériels associés
    materiels = Materiel.objects.filter(categorie=categorie)
    nb_materiels = materiels.count()
    
    if request.method == 'POST':
        if nb_materiels > 0:
            # Si des matériels utilisent cette catégorie, on ne peut pas la supprimer
            messages.error(request, f'Impossible de supprimer la catégorie "{categorie.nom}" car {nb_materiels} matériel(s) l\'utilise(nt).')
            return redirect('assets:categorie_detail', pk=categorie.pk)
        else:
            nom_categorie = categorie.nom
            categorie.delete()
            messages.success(request, f'Catégorie "{nom_categorie}" supprimée avec succès.')
            return redirect('assets:categorie_list')
    
    context = {
        'categorie': categorie,
        'materiels': materiels,
        'nb_materiels': nb_materiels,
    }
    return render(request, 'assets/categorie_confirm_delete.html', context)

# ========== ATTRIBUTION VIEWS ==========
@login_required
def attribution_list(request):
    """Liste des attributions avec filtrage par departement"""
    profil = getattr(request, 'profil_utilisateur', None)
    departement = getattr(request, 'departement', None)
    # Tous les utilisateurs authentifiés voient les attributions de tous les départements.
    attributions_qs = Attribution.objects.select_related(
        'materiel', 'client', 'salle', 'departement', 'employe_responsable'
    ).all()
    
    # Filtrer par statut (actif = date_retour_effective null)
    status = request.GET.get('status', 'ACTIF')
    attributions = []

    if status == 'ACTIF':
        active_attributions = list(
            attributions_qs.filter(date_retour_effective__isnull=True).order_by('-date_attribution')
        )

        # Inclure aussi les materiels marques "ATTRIBUE" via ajout/modification
        # et, si besoin, prioriser cette source quand une attribution active est obsolète.
        materiels_attribues = Materiel.objects.select_related('salle').filter(
            statut_disponibilite=Materiel.STATUT_ATTRIBUE
        )
        active_by_materiel_id = {attr.materiel_id: attr for attr in active_attributions}

        # Si un materiel a ete modifie bien apres son attribution active
        # et pointe vers une autre destination (ex: "Commercial"),
        # on affiche l'etat "statut materiel" a la place de l'ancienne attribution.
        override_material_ids = set()
        for materiel in materiels_attribues:
            active_attr = active_by_materiel_id.get(materiel.id)
            if not active_attr:
                continue

            location_label = (materiel.location or '').strip().lower()
            client_label = ((active_attr.client.nom if active_attr.client else '') or '').strip().lower()
            salle_label = ((active_attr.salle.nom if active_attr.salle else '') or '').strip().lower()
            if not location_label:
                continue
            if location_label in {client_label, salle_label}:
                continue

            try:
                seconds_delta = (materiel.date_modification - active_attr.date_attribution).total_seconds()
            except Exception:
                seconds_delta = 0
            if seconds_delta > 300:
                override_material_ids.add(materiel.id)

        attributions = [
            attr for attr in active_attributions
            if attr.materiel_id not in override_material_ids
        ]

        synthetic_attributions = []
        for materiel in materiels_attribues.order_by('-date_modification'):
            active_attr = active_by_materiel_id.get(materiel.id)
            should_surface_status = (active_attr is None) or (materiel.id in override_material_ids)
            if not should_surface_status:
                continue
            synthetic_attributions.append(
                SimpleNamespace(
                    pk=None,
                    materiel=materiel,
                    client=None,
                    salle=materiel.salle,
                    type_attribution=None,
                    date_attribution=materiel.date_modification or materiel.date_creation,
                    date_retour_prevue=None,
                    date_retour_effective=None,
                    is_overdue=False,
                    is_synthetic=True,
                )
            )

        attributions.extend(synthetic_attributions)
        attributions.sort(key=lambda attr: attr.date_attribution, reverse=True)
    elif status == 'COMPLETED':
        attributions = attributions_qs.filter(date_retour_effective__isnull=False).order_by('-date_attribution')
    else:
        attributions = attributions_qs.order_by('-date_attribution')
    
    return render(request, 'assets/attribution_list.html', {
        'attributions': attributions,
        'status': status
    })

@login_required
def attribution_update(request, pk):
    """Modification d'une attribution avec vérification d'accès au département"""
    profil = getattr(request, 'profil_utilisateur', None)
    departement = getattr(request, 'departement', None)
    
    # Récupérer l'attribution
    attribution = get_object_or_404(Attribution, pk=pk)
    
    # Vérifier l'accès au département
    # SUPER_ADMIN a accès à tous les départements
    if not (profil and profil.role == 'SUPER_ADMIN'):
        # Vérifier que l'utilisateur a accès au département de l'attribution
        if not departement or attribution.departement != departement:
            raise PermissionDenied("Vous n'avez pas accès à cette attribution.")
    
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
            try:
                # S'assurer que le user est toujours assigné
                saved_preferences = form.save(commit=False)
                saved_preferences.user = request.user
                saved_preferences.client = None  # S'assurer que client est None pour les préférences utilisateur
                
                # Valider le modèle avant sauvegarde
                try:
                    saved_preferences.full_clean()
                except Exception as validation_error:
                    # Si la validation échoue, ajouter les erreurs au formulaire
                    if hasattr(validation_error, 'error_dict'):
                        for field, errors in validation_error.error_dict.items():
                            for error in errors:
                                form.add_error(field, error)
                        # Réafficher le formulaire avec les erreurs
                        context = {
                            'form': form,
                            'preferences': preferences,
                        }
                        return render(request, 'assets/notification_preferences.html', context)
                
                # Sauvegarder si la validation passe
                saved_preferences.save()
                messages.success(request, '✅ Vos préférences ont été enregistrées avec succès!')
                return redirect('assets:notification_preferences')
            except Exception as e:
                # Afficher les erreurs de validation
                logger.error(f"Error saving notification preferences: {e}", exc_info=True)
                messages.error(request, f'Erreur lors de la sauvegarde: {str(e)}')
        else:
            # Afficher les erreurs du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Erreur {field}: {error}')
    else:
        form = NotificationPreferencesForm(instance=preferences)
    
    context = {
        'form': form,
        'preferences': preferences,
    }
    
    return render(request, 'assets/notification_preferences.html', context)
