import json
import os
from django.contrib.admin.sites import site
from django.template.response import TemplateResponse
from django.template.loader import get_template, select_template

LOG_PATH = r's:\Brice\RadGestMat\.cursor\debug.log'

def log_debug(hypothesis_id, location, message, data):
    """Log debug information to NDJSON file"""
    try:
        log_entry = {
            "id": f"log_{os.getpid()}_{id(data)}",
            "timestamp": int(__import__('time').time() * 1000),
            "location": location,
            "message": message,
            "data": data,
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": hypothesis_id
        }
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception:
        pass

def custom_app_index(request, app_label, extra_context=None):
    """Custom app_index view with debugging"""
    # #region agent log
    log_debug('A', 'admin_debug_views.py:custom_app_index', 'App index view called', {
        'app_label': app_label,
        'path': request.path,
        'user': str(request.user) if hasattr(request, 'user') else None,
        'user_is_authenticated': request.user.is_authenticated if hasattr(request, 'user') else False,
        'user_is_staff': request.user.is_staff if hasattr(request, 'user') else False
    })
    # #endregion
    
    # Check registered models
    # #region agent log
    registered_models = list(site._registry.keys())
    models_for_app = [m for m in registered_models if m._meta.app_label == app_label]
    log_debug('H', 'admin_debug_views.py:custom_app_index', 'Registered models check', {
        'total_registered': len(registered_models),
        'models_for_app': [str(m) for m in models_for_app],
        'app_label': app_label
    })
    # #endregion
    
    # Check permissions for each model
    # #region agent log
    model_permissions = []
    for model in models_for_app:
        model_admin = site._registry[model]
        has_view_permission = model_admin.has_view_permission(request)
        has_add_permission = model_admin.has_add_permission(request)
        has_change_permission = model_admin.has_change_permission(request)
        model_permissions.append({
            'model': str(model),
            'has_view_permission': has_view_permission,
            'has_add_permission': has_add_permission,
            'has_change_permission': has_change_permission,
        })
    log_debug('I', 'admin_debug_views.py:custom_app_index', 'Model permissions check', {
        'model_permissions': model_permissions
    })
    # #endregion
    
    # Build app_dict manually to ensure it works
    # #region agent log
    log_debug('J', 'admin_debug_views.py:custom_app_index', 'Building app_dict manually', {
        'app_label': app_label
    })
    # #endregion
    
    # Get app config
    from django.apps import apps
    try:
        app_config = apps.get_app_config(app_label)
        app_name = app_config.verbose_name
    except LookupError:
        app_name = app_label
    
    # Build models list with permissions
    models_list = []
    for model in models_for_app:
        model_admin = site._registry[model]
        # Check if user has any permission on this model
        has_any_permission = (
            model_admin.has_view_permission(request) or
            model_admin.has_add_permission(request) or
            model_admin.has_change_permission(request) or
            model_admin.has_delete_permission(request)
        )
        
        if has_any_permission:
            model_dict = {
                'name': model._meta.verbose_name_plural,
                'object_name': model.__name__,
                'perms': {
                    'add': model_admin.has_add_permission(request),
                    'change': model_admin.has_change_permission(request),
                    'delete': model_admin.has_delete_permission(request),
                    'view': model_admin.has_view_permission(request),
                },
            }
            
            # Add URLs if user has permissions
            if model_admin.has_view_permission(request) or model_admin.has_change_permission(request):
                model_dict['admin_url'] = f'/admin/{app_label}/{model._meta.model_name}/'
            if model_admin.has_add_permission(request):
                model_dict['add_url'] = f'/admin/{app_label}/{model._meta.model_name}/add/'
            
            models_list.append(model_dict)
    
    # Build app_dict
    app_dict = {
        'name': app_name,
        'app_label': app_label,
        'app_url': f'/admin/{app_label}/',
        'models': models_list,
    }
    
    # #region agent log
    log_debug('B', 'admin_debug_views.py:custom_app_index', 'App dict built manually', {
        'app_label': app_label,
        'app_dict': app_dict,
        'models_count': len(models_list),
        'app_dict_keys': list(app_dict.keys())
    })
    # #endregion
    
    if not app_dict or not models_list:
        # #region agent log
        log_debug('C', 'admin_debug_views.py:custom_app_index', 'No app dict - returning 404', {
            'app_label': app_label
        })
        # #endregion
        from django.http import Http404
        raise Http404('The requested admin page does not exist.')
    
    context = {
        **site.each_context(request),
        'title': f'{app_dict.get("name", app_label)} administration',
        'app_list': [app_dict],
        'app': app_dict,
        'app_label': app_label,
        **(extra_context or {}),
    }
    
    # #region agent log
    log_debug('D', 'admin_debug_views.py:custom_app_index', 'Context prepared', {
        'context_keys': list(context.keys()),
        'has_app': 'app' in context,
        'has_app_list': 'app_list' in context
    })
    # #endregion
    
    # Try to find templates
    template_names = [
        f'admin/{app_label}/app_index.html',
        'admin/app_index.html',
    ]
    
    # #region agent log
    log_debug('E', 'admin_debug_views.py:custom_app_index', 'Template search started', {
        'template_names': template_names
    })
    # #endregion
    
    # Try to get template
    try:
        template = select_template(template_names)
        # #region agent log
        log_debug('F', 'admin_debug_views.py:custom_app_index', 'Template found', {
            'template_name': template.origin.name if hasattr(template, 'origin') else str(template),
            'template_names_tried': template_names
        })
        # #endregion
    except Exception as e:
        # #region agent log
        log_debug('G', 'admin_debug_views.py:custom_app_index', 'Template not found', {
            'error': str(e),
            'template_names_tried': template_names
        })
        # #endregion
        # Fallback to default Django Admin template
        template = get_template('admin/index.html')
    
    return TemplateResponse(request, template, context)
