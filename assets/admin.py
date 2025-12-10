from django.contrib import admin, messages
from django.template.response import TemplateResponse
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME

from .models import (
    Departement, Categorie, Materiel, Client, Attribution, HistoriqueAttribution, 
    Alerte, Salle, AuditLog, NotificationLog, NotificationPreferences, WhatsAppConfig
)


@admin.register(Departement)
class DepartementAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'date_creation')
    list_filter = ('date_creation',)
    search_fields = ('code', 'nom')
    readonly_fields = ('date_creation',)
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('code', 'nom', 'description')
        }),
        ('Dates', {
            'fields': ('date_creation',)
        }),
    )


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'departement', 'date_creation')
    list_filter = ('departement', 'date_creation')
    search_fields = ('nom', 'departement__nom')
    readonly_fields = ('date_creation',)
    
    fieldsets = (
        ('Informations', {
            'fields': ('nom', 'description', 'departement')
        }),
        ('Dates', {
            'fields': ('date_creation',)
        }),
    )


@admin.register(Salle)
class SalleAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code', 'departement', 'date_creation')
    list_filter = ('departement', 'date_creation')
    search_fields = ('nom', 'code')
    readonly_fields = ('date_creation',)

    fieldsets = (
        ('Informations', {
            'fields': ('nom', 'code', 'description', 'departement')
        }),
        ('Dates', {
            'fields': ('date_creation',)
        }),
    )


@admin.register(Materiel)
class MaterielAdmin(admin.ModelAdmin):
    list_display = ('asset_id', 'nom', 'departement', 'salle', 'etat_technique', 'statut_disponibilite', 'date_creation')
    list_filter = ('departement', 'etat_technique', 'statut_disponibilite', 'date_creation')
    search_fields = ('asset_id', 'numero_inventaire', 'nom', 'marque')
    readonly_fields = ('qr_code', 'date_creation', 'date_modification')
    actions = ['force_delete_selected']
    fieldsets = (
        ('Identifiants', {
            'fields': ('asset_id', 'numero_inventaire')
        }),
        ('Informations générales', {
            'fields': ('nom', 'description', 'categorie', 'departement', 'salle')
        }),
        ('Caractéristiques techniques', {
            'fields': ('marque', 'modele', 'numero_serie')
        }),
        ('État et disponibilité', {
            'fields': ('etat_technique', 'statut_disponibilite')
        }),
        ('Informations financières', {
            'fields': ('date_achat', 'prix')
        }),
        ('QR Code', {
            'fields': ('qr_code',),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )

    def force_delete_selected(self, request, queryset):
        """Action admin pour forcer la suppression des matériels sélectionnés, y compris les objets liés.

        Cette action affiche d'abord une page de confirmation, puis supprime les objets si l'utilisateur
        confirme. Les superusers Django ou les utilisateurs ayant un `ProfilUtilisateur` avec le rôle
        `SUPER_ADMIN` peuvent exécuter cette action.
        """
        # Vérifier qu'il y a bien des objets sélectionnés
        if queryset.count() == 0:
            self.message_user(request, "Aucune sélection d'objets à supprimer.", level=messages.WARNING)
            return None

        # Autoriser Django superuser ou profil utilisateur SUPER_ADMIN
        profil = getattr(request.user, 'profilutilisateur', None)
        allowed = request.user.is_superuser or (profil and getattr(profil, 'role', None) == 'SUPER_ADMIN')
        if not allowed:
            self.message_user(request, "Vous devez être superuser ou avoir le rôle SUPER_ADMIN pour utiliser la suppression forcée.", level=messages.ERROR)
            return None

        # Si l'utilisateur a confirmé via le formulaire de confirmation
        if request.method == 'POST' and request.POST.get('confirm'):
            # Supprimer instance par instance afin d'appeler `Model.delete()` et déclencher les hooks
            deleted = 0
            for obj in list(queryset):
                try:
                    obj.delete()
                    deleted += 1
                except Exception as e:
                    # Continuer sur les erreurs individuelles et informer plus bas
                    messages.error(request, f"Erreur lors de la suppression de {obj}: {e}")

            self.message_user(request, f"Suppression forcée terminée : {deleted} matériel(s) supprimé(s)." , level=messages.SUCCESS)
            return None

        # Sinon, afficher la page de confirmation
        context = {
            **self.admin_site.each_context(request),
            'title': 'Confirmer la suppression forcée',
            'objects': queryset,
            'opts': self.model._meta,
            'action_checkbox_name': ACTION_CHECKBOX_NAME,
        }
        return TemplateResponse(request, "admin/assets/materiel/force_delete_confirmation.html", context)

    force_delete_selected.short_description = "Supprimer définitivement les matériels sélectionnés (FORCE)"


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('nom', 'type_client', 'email', 'telephone', 'date_creation')
    list_filter = ('type_client', 'date_creation')
    search_fields = ('nom', 'email', 'telephone')
    readonly_fields = ('date_creation', 'date_modification')
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'type_client')
        }),
        ('Coordonnées', {
            'fields': ('email', 'telephone')
        }),
        ('Hébergement', {
            'fields': ('numero_chambre', 'date_arrivee', 'date_depart'),
            'classes': ('collapse',)
        }),
        ('Conférence/Événement', {
            'fields': ('nom_evenement', 'salle'),
            'classes': ('collapse',)
        }),
        ('Interne', {
            'fields': ('departement',),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Attribution)
class AttributionAdmin(admin.ModelAdmin):
    list_display = ('materiel', 'client', 'departement', 'date_attribution', 'date_retour_prevue', 'date_retour_effective')
    list_filter = ('departement', 'date_attribution', 'date_retour_effective')
    search_fields = ('materiel__asset_id', 'client__nom', 'motif')
    readonly_fields = ('date_attribution', 'materiel', 'client')
    date_hierarchy = 'date_attribution'
    
    fieldsets = (
        ('Matériel et client', {
            'fields': ('materiel', 'client')
        }),
        ('Responsable et département', {
            'fields': ('employe_responsable', 'departement')
        }),
        ('Dates', {
            'fields': ('date_attribution', 'date_retour_prevue', 'date_retour_effective')
        }),
        ('Informations', {
            'fields': ('motif', 'notes')
        }),
    )


@admin.register(HistoriqueAttribution)
class HistoriqueAttributionAdmin(admin.ModelAdmin):
    list_display = ('attribution', 'action', 'utilisateur', 'date_action')
    list_filter = ('action', 'date_action', 'utilisateur')
    search_fields = ('attribution__materiel__asset_id', 'attribution__client__nom')
    readonly_fields = ('date_action', 'attribution', 'action', 'utilisateur')
    date_hierarchy = 'date_action'
    
    fieldsets = (
        ('Attribution', {
            'fields': ('attribution',)
        }),
        ('Action', {
            'fields': ('action', 'utilisateur', 'date_action')
        }),
        ('États', {
            'fields': ('etat_avant', 'etat_apres')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        # L'historique ne doit pas être modifié manuellement
        return False

    def has_delete_permission(self, request, obj=None):
        # Empêcher la suppression d'historique
        # Allow superusers to delete history in exceptional cases
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        # Allow superusers to modify history in exceptional cases
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        # Allow staff users to view history (read-only)
        return request.user.is_staff
    
    # Use read-only admin templates so staff see a clear notice
    change_list_template = 'admin/read_only_change_list.html'
    change_form_template = 'admin/read_only_change_form.html'


@admin.register(Alerte)
class AlerteAdmin(admin.ModelAdmin):
    list_display = ('get_type_icon', 'type_alerte', 'get_materiel_display', 'get_client_display', 'departement', 'get_severite_color', 'reglementee', 'date_creation')
    list_filter = ('type_alerte', 'severite', 'departement', 'reglementee', 'date_creation')
    search_fields = ('description', 'materiel__asset_id', 'materiel__nom', 'attribution__client__nom', 'departement__nom')
    readonly_fields = ('date_creation', 'materiel', 'attribution', 'departement')
    date_hierarchy = 'date_creation'
    ordering = ('-date_creation',)
    
    def get_type_icon(self, obj):
        icons = {'PERDU': '—', 'DEFECTUEUX': '—', 'RETARD': '—', 'STOCK_CRITIQUE': '—'}
        return icons.get(obj.type_alerte, '•')
    get_type_icon.short_description = 'Type'
    
    def get_materiel_display(self, obj):
        if obj.materiel:
            return f'{obj.materiel.asset_id}'
        return '-'
    get_materiel_display.short_description = 'Matériel'
    
    def get_client_display(self, obj):
        if obj.attribution and obj.attribution.client:
            return obj.attribution.client.nom
        return '-'
    get_client_display.short_description = 'Client'
    
    def get_severite_color(self, obj):
        return obj.get_severite_display()
    get_severite_color.short_description = 'Sévérité'
    
    fieldsets = (
        ('Type d\'alerte', {
            'fields': ('type_alerte', 'severite')
        }),
        ('Objet', {
            'fields': ('materiel', 'attribution', 'departement')
        }),
        ('Contenu', {
            'fields': ('description',)
        }),
        ('Statut', {
            'fields': ('reglementee',)
        }),
        ('Dates', {
            'fields': ('date_creation',),
            'classes': ('collapse',)
        }),
    )

    actions = ['marquer_comme_reglementee', 'marquer_comme_non_reglementee']

    def marquer_comme_reglementee(self, request, queryset):
        updated = queryset.update(reglementee=True)
        self.message_user(request, f'{updated} alerte(s) marquée(s) comme réglementée(s).')
    marquer_comme_reglementee.short_description = "✓ Marquer comme réglementées"
    
    def marquer_comme_non_reglementee(self, request, queryset):
        updated = queryset.update(reglementee=False)
        self.message_user(request, f'{updated} alerte(s) réouvertes.')
    marquer_comme_non_reglementee.short_description = "✕ Rouvrir les alertes"
    
    def has_add_permission(self, request):
        # Only superusers may create alerts manually from admin
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        # Only superusers may delete alerts
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        # Only superusers may modify alerts
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        # Allow staff users to view alerts (read-only)
        return request.user.is_staff

    # Use read-only admin templates so staff see a clear notice
    change_list_template = 'admin/read_only_change_list.html'
    change_form_template = 'admin/read_only_change_form.html'


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'content_type', 'object_repr')
    list_filter = ('action', 'content_type', 'user')
    search_fields = ('object_repr', 'object_id', 'user__username')
    readonly_fields = ('user', 'action', 'content_type', 'object_id', 'object_repr', 'changes', 'ip_address', 'metadata', 'timestamp')
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        # Audit entries are created automatically by signals; disable manual add
        return False
    def has_change_permission(self, request, obj=None):
        # Only superusers may modify audit entries
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        # Only superusers may delete audit entries
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        # Allow staff users to view audit logs (read-only)
        return request.user.is_staff

    # Use read-only admin templates so staff see a clear notice
    change_list_template = 'admin/read_only_change_list.html'
    change_form_template = 'admin/read_only_change_form.html'


# ============================================================================
# ADMIN POUR LES NOTIFICATIONS
# ============================================================================

@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'attribution', 'type_notification', 'canal', 'statut', 'date_envoi', 'nb_tentatives')
    list_filter = ('type_notification', 'canal', 'statut', 'date_envoi', 'duree_emprunt')
    search_fields = ('attribution__materiel__asset_id', 'destinataire')
    readonly_fields = ('date_envoi', 'attribution')
    
    fieldsets = (
        ('Attribution', {
            'fields': ('attribution',)
        }),
        ('Notification', {
            'fields': ('type_notification', 'canal', 'duree_emprunt')
        }),
        ('Destinataire', {
            'fields': ('destinataire', 'message_id')
        }),
        ('État', {
            'fields': ('statut', 'erreur_message', 'nb_tentatives')
        }),
        ('Dates', {
            'fields': ('date_envoi', 'date_scheduled', 'date_tentative_prochaine')
        }),
    )
    
    def has_add_permission(self, request):
        # Les notifications sont créées automatiquement
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Audit trail - impossible de supprimer
        return False


@admin.register(NotificationPreferences)
class NotificationPreferencesAdmin(admin.ModelAdmin):
    list_display = ('get_destinataire', 'notifications_email', 'notifications_whatsapp', 'date_modification')
    list_filter = ('notifications_email', 'notifications_whatsapp', 'rappel_j_moins_2', 'rappel_j_moins_1')
    search_fields = ('user__username', 'client__nom', 'phone_number')
    readonly_fields = ('date_modification',)
    
    fieldsets = (
        ('Destinataire', {
            'fields': ('user', 'client')
        }),
        ('Canaux de notification', {
            'fields': ('notifications_email', 'notifications_whatsapp', 'phone_number')
        }),
        ('Rappels (Long terme)', {
            'fields': ('rappel_j_moins_2', 'rappel_j_moins_1', 'rappel_final')
        }),
        ('Rappels (Moyen terme)', {
            'fields': ('rappel_2h_avant',)
        }),
        ('Dates', {
            'fields': ('date_modification',)
        }),
    )
    
    def get_destinataire(self, obj):
        if obj.user:
            return f"User: {obj.user.username}"
        elif obj.client:
            return f"Client: {obj.client.nom}"
        return "N/A"
    get_destinataire.short_description = "Destinataire"


@admin.register(WhatsAppConfig)
class WhatsAppConfigAdmin(admin.ModelAdmin):
    list_display = ('api_provider', 'phone_number_sender', 'is_active', 'date_modification')
    list_filter = ('api_provider', 'is_active')
    readonly_fields = ('date_creation', 'date_modification')
    
    fieldsets = (
        ('Provider', {
            'fields': ('api_provider', 'is_active')
        }),
        ('Credentials', {
            'fields': ('api_key', 'api_secret'),
            'classes': ('collapse',),
            'description': 'Les credentials sont stockés en clair - à sécuriser en production!'
        }),
        ('Contact', {
            'fields': ('phone_number_sender',)
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_modification')
        }),
    )
