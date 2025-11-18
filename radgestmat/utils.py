"""
Utility functions for RadGestMat
"""
import logging
from functools import wraps
from django.core.cache import cache
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import redirect

logger = logging.getLogger(__name__)


def cache_result(timeout=300):
    """
    Decorator to cache function results
    Usage: @cache_result(timeout=600)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            result = cache.get(cache_key)
            if result is None:
                result = func(*args, **kwargs)
                cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator


def log_action(action_name):
    """
    Decorator to log user actions
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            try:
                result = func(request, *args, **kwargs)
                logger.info(
                    f"Action: {action_name} | User: {request.user.username} | "
                    f"Path: {request.path} | Method: {request.method}"
                )
                return result
            except Exception as e:
                logger.error(
                    f"Action failed: {action_name} | User: {request.user.username} | "
                    f"Error: {str(e)}",
                    exc_info=True
                )
                raise
        return wrapper
    return decorator


def handle_exception(view_func):
    """
    Decorator to handle exceptions gracefully
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Exception in {view_func.__name__}: {str(e)}", exc_info=True)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Une erreur est survenue'}, status=500)
            messages.error(request, 'Une erreur est survenue. Veuillez réessayer.')
            return redirect('assets:dashboard')
    return wrapper


def format_currency(amount):
    """Format amount as currency"""
    if amount is None:
        return "N/A"
    return f"{amount:,.2f} €"


def format_date(date):
    """Format date in French format"""
    if date is None:
        return "N/A"
    return date.strftime("%d/%m/%Y")


def generate_asset_id(departement_code, last_number=0):
    """Generate asset ID in format OKP-XXXXXX"""
    next_number = last_number + 1
    return f"OKP-{next_number:06d}"


def generate_inventory_number(departement_code, last_number=0):
    """Generate inventory number in format RAD-XXXXXX"""
    next_number = last_number + 1
    return f"RAD-{next_number:06d}"

