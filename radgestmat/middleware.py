"""
Custom middleware for RadGestMat
"""
import logging
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(MiddlewareMixin):
    """
    Middleware to handle exceptions globally
    """
    def process_exception(self, request, exception):
        logger.error(
            f"Unhandled exception: {type(exception).__name__}: {str(exception)}",
            exc_info=True,
            extra={
                'user': request.user.username if request.user.is_authenticated else 'anonymous',
                'path': request.path,
                'method': request.method,
            }
        )
        
        # Return JSON for API requests
        if request.path.startswith('/api/') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'error': 'Une erreur est survenue',
                'detail': str(exception) if getattr(settings, 'DEBUG', False) else None
            }, status=500)
        
        # Return HTML error page for regular requests
        return render(request, 'errors/500.html', {'exception': exception}, status=500)


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add security headers
    """
    def process_response(self, request, response):
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Remove server header
        if 'Server' in response:
            del response['Server']
        
        return response

