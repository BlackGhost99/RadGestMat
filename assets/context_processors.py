# assets/context_processors.py
"""
Context processors pour les alertes
"""
from .services import AlerteService


def alertes_context(request):
    """Ajoute les informations sur les alertes au contexte de tous les templates"""
    if not request.user.is_authenticated:
        return {}
    
    try:
        departement = request.departement
        profil = request.profil_utilisateur
        
        # Super Admin peut voir toutes les alertes
        if profil and profil.role == 'SUPER_ADMIN':
            nombre_alertes = AlerteService.get_alertes_non_reglementees().count()
            nombre_alertes_critiques = AlerteService.get_nombre_alertes_critiques()
        else:
            nombre_alertes = AlerteService.get_alertes_non_reglementees(departement).count()
            nombre_alertes_critiques = AlerteService.get_nombre_alertes_critiques(departement)
        
        return {
            'nombre_alertes': nombre_alertes,
            'nombre_alertes_critiques': nombre_alertes_critiques,
        }
    except Exception:
        return {
            'nombre_alertes': 0,
            'nombre_alertes_critiques': 0,
        }

