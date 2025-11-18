from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import logout
from django.views.decorators.http import require_http_methods

# Create your views here.
def index(request):
    """Simple placeholder view for the users app."""
    return HttpResponse('Users app: index')


@require_http_methods(["GET", "POST"])
def logout_view(request):
    """Logout user and redirect to logout confirmation page."""
    logout(request)
    return render(request, 'users/logout.html')
