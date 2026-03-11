import json
import os
from django.utils.deprecation import MiddlewareMixin

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
        pass  # Silently fail if logging fails

class AdminDebugMiddleware(MiddlewareMixin):
    """Middleware to debug Django Admin template resolution"""
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        # #region agent log
        if request.path.startswith('/admin/assets/'):
            log_debug('A', 'admin_debug_middleware.py:process_view', 'Admin assets URL accessed', {
                'path': request.path,
                'view_func': str(view_func),
                'view_kwargs': view_kwargs
            })
        # #endregion
        return None
    
    def process_template_response(self, request, response):
        # #region agent log
        if request.path.startswith('/admin/assets/'):
            log_debug('B', 'admin_debug_middleware.py:process_template_response', 'Template response for admin assets', {
                'path': request.path,
                'template_name': getattr(response, 'template_name', None),
                'context_keys': list(response.context_data.keys()) if hasattr(response, 'context_data') else None
            })
        # #endregion
        return response
