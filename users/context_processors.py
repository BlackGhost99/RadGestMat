# users/context_processors.py
"""Context processors for the users app.

Provides user profile and department information to templates.
"""


# users/context_processors.py
from .models import UserPreferences
from .account_admin import can_administer_accounts

def user_profile(request):
    if request.user.is_authenticated:
        try:
            return {
                'user_profile': request.user.profilutilisateur,
                'user_departement': request.user.profilutilisateur.departement,
            }
        except:
            return {}
    return {}

def theme_context(request):
    # La préférence persistante doit rester prioritaire, y compris après une modification administrative.
    theme = request.session.get('theme', None)
    
    # Priorité 2: Préférences utilisateur (persistant)
    if request.user.is_authenticated:
        try:
            prefs = request.user.preferences
            theme = 'dark' if prefs.dark_mode else 'light'
        except UserPreferences.DoesNotExist:
            # Pas encore de préférences, utiliser le défaut
            theme = 'light'
        except AttributeError:
            # Relation preferences n'existe pas encore
            theme = 'light'
        except:
            theme = 'light'
    
    return {'theme': theme or 'light', 'can_administer_accounts': can_administer_accounts(request.user)}