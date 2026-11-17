from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import json
from .forms import UserForm, ProfilUtilisateurForm
from .models import UserPreferences

# Create your views here.
def index(request):
    """Simple placeholder view for the users app."""
    return HttpResponse('Users app: index')


@require_http_methods(["GET", "POST"])
def logout_view(request):
    """Logout user and redirect to logout confirmation page."""
    logout(request)
    return render(request, 'users/logout.html')


# Account management is implemented separately from personal settings.
from .account_admin import user_list, user_detail, user_create, user_update, user_delete

@login_required
@require_http_methods(["GET", "POST"])
def user_settings(request):
    preferences, created = UserPreferences.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        dark_mode_enabled = request.POST.get('dark_mode') == 'on'
        preferences.dark_mode = dark_mode_enabled
        preferences.save()
        request.session['theme'] = 'dark' if dark_mode_enabled else 'light'
        messages.success(request, "Vos préférences ont été enregistrées.")
        return redirect('users:user_settings')
    
    context = {
        'preferences': preferences,
    }
    return render(request, 'users/settings.html', context)


@login_required
@csrf_exempt  # Temporarily exempt for testing, should use proper CSRF handling in production AJAX
@require_http_methods(["POST"])
def toggle_dark_mode(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            dark_mode = data.get('dark_mode', False)
            
            preferences, created = UserPreferences.objects.get_or_create(user=request.user)
            preferences.dark_mode = dark_mode
            preferences.save()
            
            request.session['theme'] = 'dark' if dark_mode else 'light'
            
            return JsonResponse({'success': True, 'theme': request.session['theme']})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
