# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import ProfilUtilisateur
from assets.models import Departement


class ProfilUtilisateurInline(admin.StackedInline):
    model = ProfilUtilisateur
    can_delete = False
    verbose_name_plural = 'Profil Utilisateur'
    fieldsets = (
        ('Rôle et département', {
            'fields': ('role', 'departement')
        }),
        ('Informations personnelles', {
            'fields': ('telephone', 'date_embauche')
        }),
        ('Statut', {
            'fields': ('actif',)
        }),
    )
    
    def get_extra(self, request, obj=None, **kwargs):
        # Toujours afficher 1 profil à créer (au lieu de 3 par défaut)
        return 1 if obj is None else 0


class CustomUserAdmin(BaseUserAdmin):
    inlines = (ProfilUtilisateurInline,)
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'get_role', 'get_departement')
    list_filter = ('is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    def get_role(self, obj):
        """Affiche le rôle de l'utilisateur"""
        try:
            return obj.profilutilisateur.get_role_display()
        except ProfilUtilisateur.DoesNotExist:
            return '-'
    get_role.short_description = 'Rôle'
    
    def get_departement(self, obj):
        """Affiche le département de l'utilisateur"""
        try:
            return obj.profilutilisateur.departement
        except ProfilUtilisateur.DoesNotExist:
            return '-'
    get_departement.short_description = 'Département'


# Réenregistrer User avec le nouvel admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)