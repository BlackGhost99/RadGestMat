from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.forms.models import model_to_dict
from django.utils.timezone import now

from .models import AuditLog
from .middleware import get_current_user, get_current_request


def _safe_repr(obj):
    try:
        return str(obj)
    except Exception:
        return repr(obj)


def _safe_jsonify(value):
    """Recursively convert common Python objects into JSON-serializable forms.

    - datetimes/dates/times -> isoformat string
    - Decimals, UUIDs, bytes -> str
    - dict/list/tuple/set -> converted recursively
    - other unknown objects -> string repr
    """
    from datetime import date, datetime, time
    from decimal import Decimal
    import uuid

    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, date, time)):
        try:
            return value.isoformat()
        except Exception:
            return _safe_repr(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, bytes):
        try:
            return value.decode('utf-8')
        except Exception:
            return str(value)
    if isinstance(value, dict):
        return {k: _safe_jsonify(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_safe_jsonify(v) for v in value]
    # Fallback: try to stringify model instances or other objects
    return _safe_repr(value)


def _diff_instance(old, new):
    """Return a dict of changed fields: {field: [old, new]}"""
    changes = {}
    old_dict = model_to_dict(old) if old is not None else {}
    new_dict = model_to_dict(new)
    # Compare keys present in new
    for k, new_val in new_dict.items():
        old_val = old_dict.get(k)
        if old is None:
            # creation: record initial values
            if new_val is not None:
                changes[k] = [_safe_jsonify(old_val), _safe_jsonify(new_val)]
        else:
            if old_val != new_val:
                changes[k] = [_safe_jsonify(old_val), _safe_jsonify(new_val)]
    return changes


@receiver(post_save)
def audit_post_save(sender, instance, created, **kwargs):
    # Skip AuditLog itself to avoid recursion
    if sender.__name__ == 'AuditLog':
        return

    user = get_current_user()
    request = get_current_request()
    ct = ContentType.objects.get_for_model(sender)
    object_repr = _safe_repr(instance)
    obj_id = getattr(instance, 'pk', None)

    if created:
        changes = _diff_instance(None, instance)
        AuditLog.objects.create(
            user=user,
            action=AuditLog.ACTION_CREATE,
            content_type=ct,
            object_id=str(obj_id) if obj_id is not None else None,
            object_repr=object_repr,
            changes=changes or None,
            ip_address=getattr(request, 'META', {}).get('REMOTE_ADDR') if request else None,
            metadata=_safe_jsonify({'path': getattr(request, 'path', None)}) if request else None,
        )
    else:
        # For update, we try to get previous state by fetching fresh from DB
        try:
            old = sender.objects.get(pk=instance.pk)
        except Exception:
            old = None
        # If old is equal to instance as fetched (unlikely), record diffs by comparing field values
        changes = _diff_instance(old, instance)
        if changes:
            AuditLog.objects.create(
                user=user,
                action=AuditLog.ACTION_UPDATE,
                content_type=ct,
                object_id=str(obj_id) if obj_id is not None else None,
                object_repr=object_repr,
                changes=changes,
                ip_address=getattr(request, 'META', {}).get('REMOTE_ADDR') if request else None,
                metadata=_safe_jsonify({'path': getattr(request, 'path', None)}) if request else None,
            )


@receiver(post_delete)
def audit_post_delete(sender, instance, **kwargs):
    if sender.__name__ == 'AuditLog':
        return
    user = get_current_user()
    request = get_current_request()
    ct = ContentType.objects.get_for_model(sender)
    object_repr = _safe_repr(instance)
    obj_id = getattr(instance, 'pk', None)
    # Capture a snapshot of the instance fields
    try:
        snapshot = {k: _safe_jsonify(v) for k, v in model_to_dict(instance).items()}
    except Exception:
        snapshot = None
    AuditLog.objects.create(
        user=user,
        action=AuditLog.ACTION_DELETE,
        content_type=ct,
        object_id=str(obj_id) if obj_id is not None else None,
        object_repr=object_repr,
        changes={'snapshot': snapshot} if snapshot else None,
        ip_address=getattr(request, 'META', {}).get('REMOTE_ADDR') if request else None,
        metadata=_safe_jsonify({'path': getattr(request, 'path', None)}) if request else None,
    )
