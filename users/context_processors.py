# users/context_processors.py
"""Context processors for the users app.

Provides user profile and department information to templates.
"""


# users/context_processors.py
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