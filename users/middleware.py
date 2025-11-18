"""Minimal middleware for the users app.

Provides a DepartementMiddleware class (placeholder) so Django can import
`users.middleware.DepartementMiddleware` from settings without errors.

This middleware currently does nothing harmful: it adds an attribute
`request.departement` set to None. You can extend it later to read from the
user profile, session, or request headers.
"""
from typing import Callable
from .models import ProfilUtilisateur


class DepartementMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                request.departement = request.user.profilutilisateur.departement
                request.profil_utilisateur = request.user.profilutilisateur
            except ProfilUtilisateur.DoesNotExist:
                request.departement = None
                request.profil_utilisateur = None
        else:
            request.departement = None
            request.profil_utilisateur = None
        
        response = self.get_response(request)
        return response