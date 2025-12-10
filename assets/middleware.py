import threading

_thread_locals = threading.local()


def set_current_request(request):
    _thread_locals.request = request


def get_current_request():
    return getattr(_thread_locals, 'request', None)


def get_current_user():
    request = get_current_request()
    if request:
        user = getattr(request, 'user', None)
        # Only return an actual User instance when the user is authenticated.
        # Avoid returning AnonymousUser (or a SimpleLazyObject wrapping it)
        # because assigning that to FK fields (e.g. AuditLog.user) raises
        # a ValueError. Return None for anonymous requests.
        if user is not None and getattr(user, 'is_authenticated', False):
            return user
        return None
    return None


class CurrentUserMiddleware:
    """Middleware that stores the current request in thread-local storage so
    signals and other non-request code can access the current user and request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_request(request)
        response = self.get_response(request)
        return response
