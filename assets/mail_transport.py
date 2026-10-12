"""
Unified mail transport for SMTP and Microsoft Graph.
"""

import json
import logging
from email.utils import parseaddr
from urllib import error, parse, request

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import send_mail as django_send_mail

logger = logging.getLogger(__name__)

SMTP_METHOD = 'smtp'
GRAPH_METHOD = 'microsoft_graph'
AUTO_METHOD = 'auto'


def send_email(
    subject,
    message,
    recipient_list,
    from_email=None,
    html_message=None,
):
    """Send one email using the configured transport."""
    recipients = [email.strip() for email in (recipient_list or []) if email and email.strip()]
    if not recipients:
        return 0

    transport = _resolve_delivery_method()
    sender = from_email or settings.DEFAULT_FROM_EMAIL

    if transport == GRAPH_METHOD:
        return _send_via_microsoft_graph(
            subject=subject,
            message=message,
            recipient_list=recipients,
            from_email=sender,
            html_message=html_message,
        )

    return _send_via_smtp(
        subject=subject,
        message=message,
        recipient_list=recipients,
        from_email=sender,
        html_message=html_message,
    )


def _resolve_delivery_method():
    configured = (getattr(settings, 'EMAIL_DELIVERY_METHOD', SMTP_METHOD) or SMTP_METHOD).strip().lower()
    if configured == AUTO_METHOD:
        return GRAPH_METHOD if _is_microsoft_graph_configured() else SMTP_METHOD

    if configured in {SMTP_METHOD, GRAPH_METHOD}:
        return configured

    logger.warning("EMAIL_DELIVERY_METHOD=%s non supporte, fallback SMTP", configured)
    return SMTP_METHOD


def _is_microsoft_graph_configured():
    return all(
        [
            getattr(settings, 'MICROSOFT_TENANT_ID', '').strip(),
            getattr(settings, 'MICROSOFT_CLIENT_ID', '').strip(),
            getattr(settings, 'MICROSOFT_CLIENT_SECRET', '').strip(),
        ]
    )


def _send_via_smtp(subject, message, recipient_list, from_email, html_message=None):
    return django_send_mail(
        subject=subject,
        message=message,
        from_email=from_email,
        recipient_list=recipient_list,
        html_message=html_message,
        fail_silently=False,
    )


def _send_via_microsoft_graph(subject, message, recipient_list, from_email, html_message=None):
    if not _is_microsoft_graph_configured():
        raise ImproperlyConfigured(
            "Configuration Microsoft Graph incomplete: MICROSOFT_TENANT_ID, "
            "MICROSOFT_CLIENT_ID et MICROSOFT_CLIENT_SECRET sont requis."
        )

    sender = (
        getattr(settings, 'MICROSOFT_GRAPH_SENDER', '').strip()
        or getattr(settings, 'EMAIL_HOST_USER', '').strip()
        or parseaddr(from_email)[1]
    )
    if not sender:
        raise ImproperlyConfigured(
            "Aucun expediteur Microsoft Graph resolu. Configurez MICROSOFT_GRAPH_SENDER "
            "ou EMAIL_HOST_USER."
        )

    access_token = _fetch_microsoft_graph_access_token()
    endpoint = (
        "https://graph.microsoft.com/v1.0/users/"
        f"{parse.quote(sender)}/sendMail"
    )
    body_content = html_message or message or ""
    payload = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "HTML" if html_message else "Text",
                "content": body_content,
            },
            "toRecipients": [
                {"emailAddress": {"address": email}}
                for email in recipient_list
            ],
        },
        "saveToSentItems": bool(
            getattr(settings, 'MICROSOFT_GRAPH_SAVE_TO_SENT_ITEMS', True)
        ),
    }
    req = request.Request(
        endpoint,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    try:
        with request.urlopen(req, timeout=getattr(settings, 'EMAIL_TIMEOUT', 30)) as response:
            if response.status not in {200, 202}:
                raise RuntimeError(
                    f"Envoi Microsoft Graph echoue avec le statut HTTP {response.status}."
                )
    except error.HTTPError as exc:
        detail = exc.read().decode('utf-8', errors='ignore')
        raise RuntimeError(_format_graph_error(exc.code, detail)) from exc
    except error.URLError as exc:
        raise RuntimeError(f"Echec de connexion a Microsoft Graph: {exc}") from exc

    return 1


def _fetch_microsoft_graph_access_token():
    tenant_id = settings.MICROSOFT_TENANT_ID.strip()
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    payload = parse.urlencode(
        {
            'client_id': settings.MICROSOFT_CLIENT_ID.strip(),
            'client_secret': settings.MICROSOFT_CLIENT_SECRET.strip(),
            'scope': 'https://graph.microsoft.com/.default',
            'grant_type': 'client_credentials',
        }
    ).encode('utf-8')
    req = request.Request(
        token_url,
        data=payload,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        method='POST',
    )

    try:
        with request.urlopen(req, timeout=getattr(settings, 'EMAIL_TIMEOUT', 30)) as response:
            data = json.loads(response.read().decode('utf-8'))
    except error.HTTPError as exc:
        detail = exc.read().decode('utf-8', errors='ignore')
        raise RuntimeError(_format_graph_error(exc.code, detail, token_request=True)) from exc
    except error.URLError as exc:
        raise RuntimeError(f"Echec de connexion au service de token Microsoft: {exc}") from exc

    token = data.get('access_token')
    if not token:
        raise RuntimeError("Microsoft Graph n'a pas retourne d'access_token.")
    return token


def _format_graph_error(status_code, detail, token_request=False):
    prefix = "Token Microsoft" if token_request else "Envoi Microsoft Graph"
    message = detail
    try:
        data = json.loads(detail)
        error_obj = data.get('error')
        if isinstance(error_obj, dict):
            message = error_obj.get('message') or error_obj.get('code') or detail
        elif error_obj:
            message = str(error_obj)
    except (TypeError, ValueError):
        pass

    message = (message or '').strip() or 'erreur inconnue'
    return f"{prefix} refuse (HTTP {status_code}): {message}"
