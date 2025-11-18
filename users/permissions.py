# users/permissions.py
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages

def role_required(*roles):
    """
    Décorateur qui vérifie que l'utilisateur connecté possède l'un des rôles fournis.
    Ex : @role_required('SUPER_ADMIN', 'DEPT_MANAGER')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            profil = getattr(request, 'profil_utilisateur', None)
            if not profil or profil.role not in roles:
                raise PermissionDenied("Accès refusé. Rôle insuffisant.")
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator

def super_admin_required(view_func):
    """Décorateur pour restreindre l'accès aux Super Administrateurs"""
    return role_required('SUPER_ADMIN')(view_func)

def dept_manager_or_super_required(view_func):
    """Décorateur pour restreindre l'accès aux Managers de Département et Super Admins"""
    return role_required('SUPER_ADMIN', 'DEPT_MANAGER')(view_func)

def check_department_access(func):
    """
    Décorateur qui vérifie que l'utilisateur a accès au département du matériel/client.
    Les Super Admins ont accès à tous les départements.
    Les autres utilisateurs ne voient que leur département.
    """
    @wraps(func)
    @login_required
    def wrapper(request, *args, **kwargs):
        profil = getattr(request, 'profil_utilisateur', None)
        
        # Super Admin a accès à tout
        if profil and profil.role == 'SUPER_ADMIN':
            return func(request, *args, **kwargs)
        
        # Autres utilisateurs : déterminera dans la vue selon le contexte
        return func(request, *args, **kwargs)
    return wrapper

def allow_department_or_super(func):
    """
    Décorateur pass-through : laisse la vue gérer la logique de vérification
    (utilisé pour marquer l'intention). Les vues doivent comparer
    explicitement les départements si nécessaire.
    """
    @wraps(func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # On laisse la vue effectuer le contrôle (mais requiert un utilisateur connecté)
        return func(request, *args, **kwargs)
    return wrapper

# Utilitaires de vérification (à utiliser dans les vues)

def can_view_department(user_profil, target_department):
    """Vérifie si un utilisateur peut voir un département"""
    if not user_profil:
        return False
    if user_profil.role == 'SUPER_ADMIN':
        return True
    if user_profil.role in ['DEPT_MANAGER', 'DEPT_USER']:
        return user_profil.departement_id == target_department.id
    return False

def can_manage_department(user_profil, target_department):
    """Vérifie si un utilisateur peut gérer un département"""
    if not user_profil:
        return False
    if user_profil.role == 'SUPER_ADMIN':
        return True
    if user_profil.role == 'DEPT_MANAGER':
        return user_profil.departement_id == target_department.id
    return False

def can_perform_checkout(user_profil, materiel):
    """Vérifie si un utilisateur peut faire un check-out"""
    if not user_profil:
        return False
    if user_profil.role == 'SUPER_ADMIN':
        return True
    if user_profil.role in ['DEPT_MANAGER', 'DEPT_USER']:
        return user_profil.departement_id == materiel.departement_id
    return False